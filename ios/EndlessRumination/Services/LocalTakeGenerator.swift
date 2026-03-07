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

        // Ensure model is loaded before starting
        do {
            log.info("Waiting for model to be ready...")
            try await engine.waitUntilReady()
            log.info("Model is ready, starting generation loop")
        } catch {
            log.error("Model not ready: \(error.localizedDescription)")
            log.error("Full error: \(String(describing: error))")
            return 0
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
        }

        log.info("generateTakes() finished — \(successCount)/\(lensIndices.count) succeeded")
        log.info("Memory at end: \(DeviceCapability.info)")
        return successCount
    }

    // MARK: - Input Sanitization

    /// Replace non-ASCII characters with safe ASCII equivalents.
    ///
    /// The pruned BPE vocab is missing 128 high-byte characters (bytes 0x80-0xFF),
    /// so any non-ASCII input would crash swift-transformers' tokenizer.
    private func sanitizeToASCII(_ text: String) -> String {
        var result = text
        // Common Unicode replacements
        let replacements: [(String, String)] = [
            ("\u{2014}", "--"),  // em dash
            ("\u{2013}", "-"),   // en dash
            ("\u{2018}", "'"),   // left single quote
            ("\u{2019}", "'"),   // right single quote
            ("\u{201C}", "\""),  // left double quote
            ("\u{201D}", "\""),  // right double quote
            ("\u{2026}", "..."), // ellipsis
            ("\u{00A0}", " "),   // non-breaking space
        ]
        for (from, to) in replacements {
            result = result.replacingOccurrences(of: from, with: to)
        }
        // Strip any remaining non-ASCII characters
        result = String(result.unicodeScalars.filter { $0.value < 128 })
        return result
    }

    // MARK: - Output Parsing

    /// Parse raw model output into a Take.
    ///
    /// Expected format (from FORMAT_INSTRUCTION):
    ///   Headline under 12 words
    ///
    ///   3-5 sentences of body text.
    private func parseTake(raw: String, lensIndex: Int) -> Take? {
        let cleaned = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleaned.isEmpty else {
            log.warning("parseTake: empty output for lens \(lensIndex)")
            return nil
        }

        // Split on first double-newline: headline \n\n body
        let parts = cleaned.components(separatedBy: "\n\n")

        if parts.count >= 2 {
            let headline = parts[0].trimmingCharacters(in: .whitespacesAndNewlines)
            let body = parts.dropFirst()
                .joined(separator: "\n\n")
                .trimmingCharacters(in: .whitespacesAndNewlines)

            guard !headline.isEmpty, !body.isEmpty else {
                log.warning("parseTake: headline or body empty after split for lens \(lensIndex)")
                return nil
            }
            return Take(lensIndex: lensIndex, headline: headline, body: body)
        } else {
            // No headline/body split — use the entire output as body
            log.info("parseTake: no headline/body split for lens \(lensIndex), using fallback headline")
            return Take(lensIndex: lensIndex, headline: "A Fresh Perspective", body: cleaned)
        }
    }
}
