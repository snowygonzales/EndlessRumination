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

        var successCount = 0

        for (i, index) in lensIndices.enumerated() {
            let systemPrompt = LensPrompts.systemPrompt(forLensIndex: index)
            log.info("[\(i+1)/\(lensIndices.count)] Generating lens \(index), prompt length=\(systemPrompt.count)")
            log.info("Memory before lens \(index): \(DeviceCapability.info)")

            do {
                let raw = try await engine.generate(
                    systemPrompt: systemPrompt,
                    userMessage: problem
                )

                log.info("[\(i+1)/\(lensIndices.count)] Lens \(index) raw output length=\(raw.count)")

                if let take = parseTake(raw: raw, lensIndex: index) {
                    log.info("[\(i+1)/\(lensIndices.count)] Lens \(index) parsed OK — headline='\(take.headline)'")
                    onTakeReady(take)
                    successCount += 1
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
