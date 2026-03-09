import Foundation
import os.log

#if !targetEnvironment(simulator)
import Hub
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
    case insufficientStorage(available: String, required: String)

    var errorDescription: String? {
        switch self {
        case .modelNotLoaded:
            return "The AI model hasn't finished loading yet."
        case .generationFailed(let msg):
            return "Failed to generate perspective: \(msg)"
        case .deviceNotSupported:
            return "This device doesn't have enough memory to run the AI model."
        case .insufficientStorage(let available, let required):
            return "Not enough storage space. \(available) available, \(required) required."
        }
    }
}

// MARK: - Download Error Classification

/// User-facing download error with friendly messages and retry semantics.
enum DownloadError: Equatable {
    case noInternet
    case timeout
    case connectionLost
    case serverError(statusCode: Int)
    case modelNotFound
    case accessDenied
    case insufficientStorage(available: String, required: String)
    case fileCorrupted
    case deviceNotSupported
    case downloadStalled
    case unknown(String)

    /// Whether this error is likely transient and worth auto-retrying.
    var isTransient: Bool {
        switch self {
        case .timeout, .connectionLost, .serverError, .downloadStalled:
            return true
        case .noInternet, .modelNotFound, .accessDenied,
             .insufficientStorage, .fileCorrupted, .deviceNotSupported, .unknown:
            return false
        }
    }

    /// Human-readable message for display in the UI.
    var userMessage: String {
        switch self {
        case .noInternet:
            return "No internet connection. Connect to Wi-Fi and try again."
        case .timeout:
            return "Connection timed out. Check your network and try again."
        case .connectionLost:
            return "Connection lost during download. Tap to retry."
        case .serverError(let code):
            return "Server error (\(code)). Please try again later."
        case .modelNotFound:
            return "Model not found on server. Please update the app."
        case .accessDenied:
            return "Access denied. Please update the app."
        case .insufficientStorage(let available, let required):
            return "Not enough storage. \(available) available, \(required) required."
        case .fileCorrupted:
            return "Download was corrupted. Tap to retry."
        case .deviceNotSupported:
            return "This device doesn't have enough memory to run the AI model."
        case .downloadStalled:
            return "Download appears stuck. Tap to retry."
        case .unknown:
            return "Something went wrong. Tap to retry."
        }
    }

    /// Whether the UI should show a retry button for this error.
    var isRetryable: Bool {
        switch self {
        case .modelNotFound, .accessDenied, .deviceNotSupported:
            return false
        default:
            return true
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
    private(set) var downloadError: DownloadError?
    private(set) var retryAttempt: Int = 0
    private(set) var isAutoRetrying: Bool = false

    /// Backward-compatible computed property (used by LoadingView).
    var loadError: String? { downloadError?.userMessage }

    // MARK: Private

    private var loadTask: Task<Void, Error>?

    // Stall watchdog
    private var lastProgressValue: Double = 0
    private var lastProgressTime: Date = .now
    private var stallCheckTask: Task<Void, Never>?
    private static let stallTimeout: TimeInterval = 60
    private static let retryDelays: [Duration] = [.seconds(10), .seconds(30), .seconds(60)]

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

    /// Reset error state and retry the download/load from scratch.
    func retryLoading() {
        log.info("retryLoading() called -- resetting state")
        loadTask?.cancel()
        loadTask = nil
        stallCheckTask?.cancel()
        stallCheckTask = nil
        downloadError = nil
        isDownloading = false
        isAutoRetrying = false
        retryAttempt = 0
        downloadProgress = 0
        startLoading()
    }

    /// Await model readiness. If loading hasn't started, starts it.
    /// Throws if loading finishes but model is not actually ready.
    func waitUntilReady() async throws {
        log.info("waitUntilReady() — isLoaded=\(self.isLoaded)")
        if isLoaded { return }
        if loadTask == nil { startLoading() }

        // Await the load task — it catches errors internally, so this won't throw.
        // We must check isLoaded afterward to detect silent failures.
        try await loadTask?.value

        guard isLoaded else {
            let msg = loadError ?? "Model loading completed but model is not ready."
            log.error("waitUntilReady() failed: \(msg)")
            throw InferenceError.generationFailed(msg)
        }
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

        // Pre-flight: device capability check
        guard DeviceCapability.canRunModel else {
            log.error("Device NOT supported -- RAM too low. \(DeviceCapability.info)")
            downloadError = .deviceNotSupported
            throw InferenceError.deviceNotSupported
        }

        // Pre-flight: storage check
        let requiredBytes: Int64 = 2_300_000_000 // 2.3 GB with headroom
        if let freeBytes = try? URL(fileURLWithPath: NSHomeDirectory())
            .resourceValues(forKeys: [.volumeAvailableCapacityForImportantUsageKey])
            .volumeAvailableCapacityForImportantUsage {
            let freeGB = Double(freeBytes) / 1_073_741_824
            log.info("Storage check: \(String(format: "%.1f", freeGB)) GB available")
            if freeBytes < requiredBytes {
                let available = String(format: "%.1f GB", freeGB)
                downloadError = .insufficientStorage(available: available, required: "2.1 GB")
                log.error("Insufficient storage: \(available) available, 2.1 GB required")
                throw InferenceError.insufficientStorage(available: available, required: "2.1 GB")
            }
        }

        // Attempt download with auto-retry for transient errors
        let maxAttempts = Self.retryDelays.count + 1 // 1 initial + 3 retries

        for attempt in 1...maxAttempts {
            do {
                try await attemptDownload()
                // Success -- clear retry state
                isAutoRetrying = false
                retryAttempt = 0
                return
            } catch {
                let classified = Self.classifyError(error)
                log.error("Download attempt \(attempt)/\(maxAttempts) failed: \(classified.userMessage) (raw: \(error.localizedDescription))")
                log.error("Full error: \(String(describing: error))")

                // If non-transient or last attempt, surface to user immediately
                let isLastAttempt = attempt == maxAttempts
                if !classified.isTransient || isLastAttempt {
                    isAutoRetrying = false
                    retryAttempt = 0
                    downloadError = classified
                    isDownloading = false
                    stopStallWatchdog()
                    throw error
                }

                // Transient error: auto-retry after delay
                let delayIndex = attempt - 1
                let delay = Self.retryDelays[delayIndex]
                retryAttempt = attempt
                isAutoRetrying = true
                downloadError = nil
                isDownloading = false

                log.info("Auto-retrying in \(delay) (attempt \(attempt + 1)/\(maxAttempts))...")

                try await Task.sleep(for: delay)
                try Task.checkCancellation()
            }
        }
        #endif
    }

    // MARK: - Private: Single Download Attempt

    #if !targetEnvironment(simulator)
    /// Execute a single download + load attempt. Starts the stall watchdog.
    private func attemptDownload() async throws {
        isDownloading = true
        downloadProgress = 0
        downloadError = nil
        startStallWatchdog()

        defer {
            stopStallWatchdog()
        }

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
    }
    #endif

    // MARK: - Private: Stall Watchdog

    /// Start monitoring download progress for stalls.
    /// Checks every 15 seconds if progress has advanced. If stuck for 60+ seconds, cancels.
    private func startStallWatchdog() {
        stallCheckTask?.cancel()
        lastProgressValue = downloadProgress
        lastProgressTime = .now

        stallCheckTask = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(15))
                guard !Task.isCancelled else { return }
                guard let self else { return }

                if self.isDownloading && !self.isLoaded {
                    let now = Date.now
                    if self.downloadProgress != self.lastProgressValue {
                        // Progress moved -- reset the clock
                        self.lastProgressValue = self.downloadProgress
                        self.lastProgressTime = now
                    } else if now.timeIntervalSince(self.lastProgressTime) >= Self.stallTimeout {
                        // Stalled for 60+ seconds
                        log.warning("Download stall detected: progress stuck at \(String(format: "%.1f%%", self.downloadProgress * 100)) for \(Int(now.timeIntervalSince(self.lastProgressTime)))s")
                        self.loadTask?.cancel()
                        self.isDownloading = false
                        self.downloadError = .downloadStalled
                        self.stallCheckTask?.cancel()
                        return
                    }
                }
            }
        }
    }

    /// Stop the stall watchdog.
    private func stopStallWatchdog() {
        stallCheckTask?.cancel()
        stallCheckTask = nil
    }

    // MARK: - Private: Error Classification

    /// Classify a raw error from loadContainer / Hub into a user-friendly DownloadError.
    private static func classifyError(_ error: Error) -> DownloadError {
        // 1. Our own InferenceError
        if let inferenceError = error as? InferenceError {
            switch inferenceError {
            case .deviceNotSupported:
                return .deviceNotSupported
            case .insufficientStorage(let available, let required):
                return .insufficientStorage(available: available, required: required)
            default:
                return .unknown(error.localizedDescription)
            }
        }

        #if !targetEnvironment(simulator)
        // 2. Hub.HubClientError
        if let hubError = error as? Hub.HubClientError {
            switch hubError {
            case .authorizationRequired:
                return .accessDenied
            case .fileNotFound, .resourceNotFound:
                return .modelNotFound
            case .httpStatusCode(let code):
                switch code {
                case 401, 403: return .accessDenied
                case 404: return .modelNotFound
                case 500...599: return .serverError(statusCode: code)
                default: return .serverError(statusCode: code)
                }
            case .networkError(let urlError):
                return classifyURLError(urlError)
            case .downloadError:
                return .connectionLost
            default:
                return .unknown(error.localizedDescription)
            }
        }

        // 3. HubApi.EnvironmentError
        if let envError = error as? HubApi.EnvironmentError {
            switch envError {
            case .fileIntegrityError:
                return .fileCorrupted
            case .offlineModeError:
                return .noInternet
            case .invalidMetadataError:
                return .fileCorrupted
            case .fileWriteError:
                return .unknown(error.localizedDescription)
            }
        }
        #endif

        // 4. Raw URLError
        if let urlError = error as? URLError {
            return classifyURLError(urlError)
        }

        // 5. NSError with URLError domain
        let nsError = error as NSError
        if nsError.domain == NSURLErrorDomain {
            return classifyURLErrorCode(nsError.code)
        }

        // 6. Task cancellation
        if error is CancellationError {
            return .downloadStalled
        }

        // 7. Fallback
        return .unknown(error.localizedDescription)
    }

    private static func classifyURLError(_ urlError: URLError) -> DownloadError {
        classifyURLErrorCode(urlError.code.rawValue)
    }

    private static func classifyURLErrorCode(_ code: Int) -> DownloadError {
        switch URLError.Code(rawValue: code) {
        case .notConnectedToInternet, .cannotFindHost, .cannotConnectToHost, .dnsLookupFailed:
            return .noInternet
        case .timedOut:
            return .timeout
        case .networkConnectionLost:
            return .connectionLost
        case .secureConnectionFailed:
            return .unknown("Secure connection failed. Check your network.")
        default:
            return .connectionLost
        }
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
