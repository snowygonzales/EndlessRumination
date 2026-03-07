import Foundation
import os.log

#if !targetEnvironment(simulator)
import MLX
import MLXLLM
import MLXLMCommon
#endif

private let log = Logger(subsystem: "com.endlessrumination", category: "InferenceEngine")

// MARK: - Errors

enum InferenceError: LocalizedError {
    case modelNotLoaded
    case generationFailed(String)
    case deviceNotSupported

    var errorDescription: String? {
        switch self {
        case .modelNotLoaded:
            return "The AI model hasn't finished loading yet."
        case .generationFailed(let msg):
            return "Failed to generate perspective: \(msg)"
        case .deviceNotSupported:
            return "This device doesn't have enough memory to run the AI model."
        }
    }
}

// MARK: - InferenceEngine

/// On-device LLM inference via Apple MLX.
///
/// On simulator builds, returns mock responses for UI development.
/// On device, uses mlx-swift-lm to run the fine-tuned Qwen 3.5 4B model.
@MainActor
@Observable
final class InferenceEngine {

    // MARK: Observable state

    private(set) var isLoaded = false
    private(set) var downloadProgress: Double = 0
    private(set) var isDownloading = false
    var loadError: String?

    // MARK: Private

    private var loadTask: Task<Void, Error>?

    #if !targetEnvironment(simulator)
    private var modelContainer: ModelContainer?
    #endif

    // Stop sequences to detect end of useful output during streaming
    private let stopSequences = ["<|im_end|>", "<|endoftext|>", "<|im_start|>", "<think>"]

    // MARK: - Loading

    /// Begin downloading / loading the model in the background.
    /// Safe to call multiple times — only the first call starts work.
    func startLoading() {
        guard loadTask == nil else { return }
        log.info("startLoading() called. \(DeviceCapability.info)")

        #if !targetEnvironment(simulator)
        // Limit Metal buffer cache to reduce memory pressure on 6GB devices
        Memory.cacheLimit = 20 * 1024 * 1024
        log.info("MLX cache limit set to 20 MB")
        #endif
        loadTask = Task { [weak self] in
            do {
                try await self?.performLoad()
            } catch {
                log.error("loadTask caught error: \(error.localizedDescription)")
            }
        }
    }

    /// Await model readiness. If loading hasn't started, starts it.
    func waitUntilReady() async throws {
        log.info("waitUntilReady() — isLoaded=\(self.isLoaded)")
        if isLoaded { return }
        if loadTask == nil { startLoading() }
        try await loadTask?.value
    }

    #if !targetEnvironment(simulator)
    /// Clear MLX buffer cache to reclaim GPU memory between generations.
    func clearCache() {
        Memory.clearCache()
    }
    #endif

    // MARK: - Generation

    /// Generate a response for the given system prompt and user message.
    func generate(systemPrompt: String, userMessage: String) async throws -> String {
        log.info("generate() called — systemPrompt length=\(systemPrompt.count), userMessage length=\(userMessage.count)")
        #if targetEnvironment(simulator)
        return try await simulatorGenerate()
        #else
        return try await deviceGenerate(systemPrompt: systemPrompt, userMessage: userMessage)
        #endif
    }

    // MARK: - Private: Loading

    private func performLoad() async throws {
        #if targetEnvironment(simulator)
        // Simulate a 2-second download for UI testing
        isDownloading = true
        for i in 0...20 {
            try await Task.sleep(for: .milliseconds(100))
            downloadProgress = Double(i) / 20.0
        }
        isDownloading = false
        isLoaded = true

        #else
        log.info("performLoad() start. \(DeviceCapability.info)")

        guard DeviceCapability.canRunModel else {
            log.error("Device NOT supported — RAM too low. \(DeviceCapability.info)")
            throw InferenceError.deviceNotSupported
        }

        isDownloading = true
        do {
            let modelID = "sefiroth/er-qwen35-4b-mlx-4bit"
            log.info("Loading model: \(modelID)")

            let config = ModelConfiguration(id: modelID)

            log.info("Calling LLMModelFactory.shared.loadContainer...")
            modelContainer = try await LLMModelFactory.shared.loadContainer(
                configuration: config
            ) { [weak self] progress in
                Task { @MainActor [weak self] in
                    self?.downloadProgress = progress.fractionCompleted
                }
            }
            isDownloading = false

            // Warm up Metal shaders by running a tiny 1-token generation.
            // The first inference triggers JIT shader compilation (~2-3s overhead).
            // By paying that cost here (during load), the first real take starts fast.
            log.info("Warming up GPU shaders...")
            await warmUpGPU()

            isLoaded = true

            let snap = Memory.snapshot()
            log.info("Model loaded + GPU warm. Active: \(snap.activeMemory / 1024 / 1024) MB, Cache: \(snap.cacheMemory / 1024 / 1024) MB, Peak: \(snap.peakMemory / 1024 / 1024) MB")
        } catch {
            isDownloading = false
            loadError = error.localizedDescription
            log.error("Model load FAILED: \(error.localizedDescription)")
            log.error("Full error: \(String(describing: error))")
            throw error
        }
        #endif
    }

    // MARK: - Private: GPU Warm-Up

    #if !targetEnvironment(simulator)
    /// Run a minimal generation to trigger Metal shader compilation.
    /// This moves the ~2-3s JIT overhead from the first real take to the loading phase.
    private func warmUpGPU() async {
        guard let container = modelContainer else { return }
        do {
            let chat: [Chat.Message] = [
                .system("You are helpful."),
                .user("Hi"),
            ]
            let input = try await container.prepare(input: UserInput(chat: chat))
            let params = GenerateParameters(maxTokens: 1, temperature: 0.0)
            let stream = try await container.generate(input: input, parameters: params)
            // Consume the stream to trigger shader compilation
            for await _ in stream {}
            Memory.clearCache()
            log.info("GPU warm-up complete")
        } catch {
            log.warning("GPU warm-up failed (non-fatal): \(error.localizedDescription)")
        }
    }
    #endif

    // MARK: - Private: Device Generation

    #if !targetEnvironment(simulator)
    private func deviceGenerate(systemPrompt: String, userMessage: String) async throws -> String {
        guard let container = modelContainer else {
            log.error("deviceGenerate called but modelContainer is nil!")
            throw InferenceError.modelNotLoaded
        }

        // Build chat messages using the preferred Chat.Message API
        let chat: [Chat.Message] = [
            .system(systemPrompt),
            .user(userMessage),
        ]

        // Prepare input (applies chat template, tokenizes)
        let input: LMInput
        do {
            input = try await container.prepare(
                input: UserInput(chat: chat)
            )
            log.info("deviceGenerate: input prepared, token count=\(input.text.tokens.size)")
        } catch {
            log.error("deviceGenerate: prepare() FAILED: \(error.localizedDescription)")
            throw InferenceError.generationFailed("prepare failed: \(error.localizedDescription)")
        }

        // Generate via AsyncStream
        // maxTokens 200: takes are headline + 3-5 sentences (~120-180 tokens)
        // kvBits 4: quantize KV cache to reduce memory pressure on 6GB devices
        // topP 1.0: uses faster CategoricalSampler (vs TopPSampler which requires argSort on full vocab)
        let parameters = GenerateParameters(
            maxTokens: 200,
            kvBits: 4,
            kvGroupSize: 64,
            temperature: 0.7,
            topP: 1.0
        )

        let stream: AsyncStream<Generation>
        do {
            stream = try await container.generate(
                input: input,
                parameters: parameters
            )
        } catch {
            log.error("deviceGenerate: generate() FAILED: \(error.localizedDescription)")
            throw InferenceError.generationFailed("generate failed: \(error.localizedDescription)")
        }

        // Accumulate text chunks with early stop detection
        var output = ""
        var chunkCount = 0
        var stoppedEarly = false
        for await generation in stream {
            switch generation {
            case .chunk(let text):
                output += text
                chunkCount += 1

                // Early stop: check if any stop sequence appeared in the output.
                // This avoids generating useless tokens past the real response end.
                if stopSequences.contains(where: { output.contains($0) }) {
                    stoppedEarly = true
                    break
                }
            case .info(let info):
                log.info("deviceGenerate: \(String(format: "%.1f", info.tokensPerSecond)) tok/s, prompt=\(info.promptTokenCount), generated=\(info.generationTokenCount)\(stoppedEarly ? " (early stop)" : "")")
            case .toolCall:
                break
            }
            if stoppedEarly { break }
        }

        log.info("deviceGenerate: chunks=\(chunkCount), output length=\(output.count)\(stoppedEarly ? " [early stop]" : "")")

        let cleaned = cleanOutput(output)
        return cleaned
    }
    #endif

    /// Strip stop tokens and artifacts from raw model output.
    private func cleanOutput(_ raw: String) -> String {
        var text = raw
        // Trim at the first stop token
        let stopSequences = ["<|im_end|>", "<|endoftext|>", "<|im_start|>", "<think>"]
        for stop in stopSequences {
            if let range = text.range(of: stop) {
                text = String(text[..<range.lowerBound])
            }
        }
        return text.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    // MARK: - Private: Simulator Mock

    #if targetEnvironment(simulator)
    private func simulatorGenerate() async throws -> String {
        // Simulate realistic generation time (5-8s per take on device)
        try await Task.sleep(for: .milliseconds(Int.random(in: 400...900)))
        return mockResponses.randomElement()!
    }

    private let mockResponses = [
        """
        Your Problem Is Actually Pretty Hilarious

        Look, I get it. We've all been there, staring at the ceiling at 3 AM wondering if \
        we'll ever figure it out. The thing about worrying is that it's like paying interest \
        on a debt you might not even owe. What if this is actually the setup for the best \
        story you'll ever tell at parties? Every great comedian knows: tragedy plus time \
        equals comedy. You're just in the tragedy part right now.
        """,

        """
        The Current Has Already Carried You Past This

        Consider this: in the grand tapestry of human experience, your current worry is but \
        a single thread. Yet it's YOUR thread, and that makes it matter. The strength isn't \
        in avoiding the storm -- it's in learning to dance in the rain. Every person who has \
        ever lived has faced a moment exactly like this one, and the vast majority came \
        through it whole.
        """,

        """
        Your Amygdala Is Running the Show Right Now

        From a neuroscience perspective, what's happening is completely predictable. Your \
        amygdala has flagged this situation as a threat, triggering a cortisol cascade that's \
        hijacking your prefrontal cortex. This is fight-or-flight doing what evolution \
        designed -- the problem is, it can't tell the difference between a tiger and a Tuesday. \
        Try 4-7-8 breathing right now: inhale 4, hold 7, exhale 8. Three rounds.
        """,

        """
        OH BOY OH BOY You Seem Worried But Have You Tried Going Outside

        Hey hey hey! I can tell you're feeling not-so-great and that makes me feel \
        not-so-great too because when you're sad I'm sad! But LISTEN. Have you tried going \
        for a walk? Walking is THE BEST. Also snacks. Have you had a snack? Sometimes I feel \
        worried and then I eat something and I forget what I was worried about. Also I love \
        you SO MUCH no matter what.
        """,
    ]
    #endif
}
