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

    /// Maximum words allowed in a headline. Anything longer is body text, not a real headline.
    private static let maxHeadlineWords = 14

    /// Parse raw model output into a Take.
    ///
    /// Expected format (from FORMAT_INSTRUCTION):
    ///   Headline under 12 words
    ///
    ///   3-5 sentences of body text.
    ///
    /// Handles common model quirks:
    ///   - Missing double-newline (tries single newline as fallback)
    ///   - First line too long (body leaking into headline slot)
    ///   - No separation at all (entire output used as body)
    private func parseTake(raw: String, lensIndex: Int) -> Take? {
        let cleaned = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !cleaned.isEmpty else {
            log.warning("parseTake: empty output for lens \(lensIndex)")
            return nil
        }

        // Try double-newline split first, then single-newline
        let candidate = extractHeadlineAndBody(from: cleaned)

        if let (headline, body) = candidate {
            let wordCount = headline.split(separator: " ").count
            if wordCount <= Self.maxHeadlineWords && !body.isEmpty {
                return Take(lensIndex: lensIndex, headline: headline, body: body)
            }
            // Headline too long — it's really body text, not a headline
            log.info("parseTake: lens \(lensIndex) headline too long (\(wordCount) words), using fallback")
        }

        // Fallback: use entire output as body with generic headline
        return Take(lensIndex: lensIndex, headline: "A Fresh Perspective", body: cleaned)
    }

    /// Try to split output into (headline, body) using double-newline, then single-newline.
    private func extractHeadlineAndBody(from text: String) -> (String, String)? {
        // Try double-newline split first (expected format)
        let doubleParts = text.components(separatedBy: "\n\n")
        if doubleParts.count >= 2 {
            let headline = doubleParts[0].trimmingCharacters(in: .whitespacesAndNewlines)
            let body = doubleParts.dropFirst()
                .joined(separator: "\n\n")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            if !headline.isEmpty, !body.isEmpty {
                return (headline, body)
            }
        }

        // Fallback: try single-newline split (model sometimes uses \n instead of \n\n)
        let singleParts = text.components(separatedBy: "\n")
        if singleParts.count >= 2 {
            let headline = singleParts[0].trimmingCharacters(in: .whitespacesAndNewlines)
            let body = singleParts.dropFirst()
                .joined(separator: "\n")
                .trimmingCharacters(in: .whitespacesAndNewlines)
            if !headline.isEmpty, !body.isEmpty {
                return (headline, body)
            }
        }

        return nil
    }
}
