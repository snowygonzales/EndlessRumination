import Foundation
import os.log

private let log = Logger(subsystem: "com.endlessrumination", category: "LocalTakeGenerator")

/// Generates takes locally using the on-device inference engine.
///
/// Replaces `APIClient.generateBatch()` — iterates lens indices sequentially,
/// calling the inference engine for each, and delivers takes one at a time
/// via the `onTakeReady` callback.
@MainActor
final class LocalTakeGenerator {
    private let engine: InferenceEngine

    init(engine: InferenceEngine) {
        self.engine = engine
    }

    /// Generate takes for all requested lenses.
    ///
    /// - Parameters:
    ///   - problem: The user's problem text.
    ///   - lensIndices: Which lens indices to generate (base 0-19, packs 20-39).
    ///   - onTakeReady: Called on main thread each time a take is ready.
    /// - Returns: The number of successfully generated takes.
    @discardableResult
    func generateTakes(
        problem: String,
        lensIndices: [Int],
        onTakeReady: @escaping (Take) -> Void
    ) async -> Int {
        log.info("generateTakes() called — problem length=\(problem.count), lensIndices=\(lensIndices)")
        log.info("Memory at start: \(DeviceCapability.info)")

        // Ensure model is loaded before starting.
        // Retry once if the first attempt fails (handles interrupted downloads
        // from auto-lock or background suspension).
        do {
            log.info("Waiting for model to be ready...")
            try await engine.waitUntilReady()
            log.info("Model is ready, starting generation loop")
        } catch {
            log.warning("First model load attempt failed: \(error.localizedDescription) — retrying...")
            engine.retryLoading()
            do {
                try await engine.waitUntilReady()
                log.info("Model ready after retry, starting generation loop")
            } catch {
                log.error("Model not ready after retry: \(error.localizedDescription)")
                return 0
            }
        }

        let safeProblem = sanitizeToASCII(problem)
        var successCount = 0

        for (i, index) in lensIndices.enumerated() {
            let systemPrompt = LensPrompts.systemPrompt(forLensIndex: index)
            log.info("[\(i+1)/\(lensIndices.count)] Generating lens \(index), prompt length=\(systemPrompt.count)")
            log.info("Memory before lens \(index): \(DeviceCapability.info)")

            do {
                let raw = try await engine.generate(
                    systemPrompt: systemPrompt,
                    userMessage: safeProblem
                )

                log.info("[\(i+1)/\(lensIndices.count)] Lens \(index) raw output length=\(raw.count)")

                if let take = parseTake(raw: raw, lensIndex: index) {
                    // Output safety check — suppress takes with harmful content
                    let fullText = "\(take.headline) \(take.body)"
                    if SafetyService.outputSafetyCheck(fullText) {
                        log.info("[\(i+1)/\(lensIndices.count)] Lens \(index) parsed OK — headline='\(take.headline)'")
                        onTakeReady(take)
                        successCount += 1
                    } else {
                        log.warning("[\(i+1)/\(lensIndices.count)] Lens \(index) SUPPRESSED by output safety check")
                    }
                } else {
                    log.warning("[\(i+1)/\(lensIndices.count)] Lens \(index) parse returned nil — raw: '\(raw.prefix(200))'")
                }
            } catch {
                // Skip failed lens — user sees fewer takes, not a crash
                log.error("[\(i+1)/\(lensIndices.count)] Lens \(index) FAILED: \(error.localizedDescription)")
                log.error("Full error: \(String(describing: error))")
                continue
            }

            // Clear GPU buffer cache between takes to reduce memory pressure
            #if !targetEnvironment(simulator)
            engine.clearCache()
            #endif
        }

        log.info("generateTakes() finished — \(successCount)/\(lensIndices.count) succeeded")
        log.info("Memory at end: \(DeviceCapability.info)")
        return successCount
    }

    // MARK: - Input Sanitization

    /// Convert non-ASCII characters to safe ASCII equivalents.
    ///
    /// The pruned BPE vocab is missing 128 high-byte characters (bytes 0x80-0xFF),
    /// so any non-ASCII input would crash swift-transformers' tokenizer.
    ///
    /// Strategy:
    /// 1. Transliterate to Latin (handles Cyrillic, CJK, Arabic, etc.)
    /// 2. Strip diacritics (ă→a, ș→s, ț→t, é→e, ñ→n, ü→u, etc.)
    /// 3. Replace common Unicode punctuation with ASCII equivalents
    /// 4. Strip any remaining non-ASCII as a safety net
    private func sanitizeToASCII(_ text: String) -> String {
        // Step 1: Transliterate non-Latin scripts to Latin approximations
        var result = text.applyingTransform(.toLatin, reverse: false) ?? text

        // Step 2: Strip combining marks (diacritics) — ă→a, î→i, ș→s, ț→t, etc.
        result = result.applyingTransform(.stripCombiningMarks, reverse: false) ?? result

        // Step 3: Common Unicode punctuation → ASCII
        let replacements: [(String, String)] = [
            ("\u{2014}", "--"),  // em dash
            ("\u{2013}", "-"),   // en dash
            ("\u{2018}", "'"),   // left single quote
            ("\u{2019}", "'"),   // right single quote
            ("\u{201C}", "\""),  // left double quote
            ("\u{201D}", "\""),  // right double quote
            ("\u{2026}", "..."), // ellipsis
            ("\u{00A0}", " "),   // non-breaking space
            ("\u{2022}", "-"),   // bullet
            ("\u{00B7}", "-"),   // middle dot
        ]
        for (from, to) in replacements {
            result = result.replacingOccurrences(of: from, with: to)
        }

        // Step 4: Safety net — strip anything still non-ASCII
        result = String(result.unicodeScalars.filter { $0.value < 128 })

        if result != text {
            log.info("Sanitized input: '\(text.prefix(60))' → '\(result.prefix(60))'")
        }

        return result
    }

    // MARK: - Output Parsing

    /// Pre-canned headlines — the 4-bit model doesn't reliably produce short headlines,
    /// so we use random display headlines and treat the entire model output as body text.
    private static let cannedHeadlines = [
        "A Fresh Perspective",
        "A New Take",
        "Here's Another Look",
        "Consider This",
        "A Different Angle",
        "Something to Think About",
        "One More Way to See It",
        "Flip the Script",
    ]

    /// Parse raw model output into a Take.
    ///
    /// Uses the entire model output as body text with a random pre-canned headline.
    /// The 4-bit quantized model doesn't reliably follow the headline+body format,
    /// so we skip headline parsing entirely and maximize body quality.
    private func parseTake(raw: String, lensIndex: Int) -> Take? {
        let cleaned = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleaned.isEmpty else {
            log.warning("parseTake: empty output for lens \(lensIndex)")
            return nil
        }

        let headline = Self.cannedHeadlines[lensIndex % Self.cannedHeadlines.count]
        return Take(lensIndex: lensIndex, headline: headline, body: cleaned)
    }
}
