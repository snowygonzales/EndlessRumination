import SwiftUI

// MARK: - Subscription Tier (moved from User.swift — no backend auth needed)

enum SubscriptionTier: String, Codable {
    case free
    case pro
}

// MARK: - App Screen

enum AppScreen {
    case splash
    case input
    case loading
    case takes
}

// MARK: - App State

@MainActor
@Observable
final class AppState {
    private static let hasSeenOnboardingKey = "com.endlessrumination.hasSeenOnboarding"
    private static let hasConsentedAIKey = "com.endlessrumination.hasConsentedAI"

    var currentScreen: AppScreen = .splash
    var problemText: String = ""
    var takes: [Take] = []
    var currentTakeIndex: Int = 0
    var showSafetyOverlay: Bool = false
    var showInstructionOverlay: Bool = true
    var showOnboarding: Bool = false
    var showAIConsent: Bool = false
    var isGenerating: Bool = false
    var subscriptionTier: SubscriptionTier = .free
    var subscriptionManager: SubscriptionManager?
    var showPaywall: Bool = false
    var showShop: Bool = false
    var productsLoaded: Bool = false

    /// On-device inference engine (shared across the app lifecycle).
    var inferenceEngine: InferenceEngine = InferenceEngine()

    var hasConsentedAI: Bool {
        UserDefaults.standard.bool(forKey: Self.hasConsentedAIKey)
    }

    /// Whether the on-device model is downloaded and ready for inference.
    var isModelReady: Bool {
        inferenceEngine.isLoaded
    }

    /// Model download progress (0.0 to 1.0).
    var modelDownloadProgress: Double {
        inferenceEngine.downloadProgress
    }

    init() {
        let hasSeen = UserDefaults.standard.bool(forKey: Self.hasSeenOnboardingKey)
        showOnboarding = !hasSeen
    }

    func dismissOnboarding() {
        showOnboarding = false
        UserDefaults.standard.set(true, forKey: Self.hasSeenOnboardingKey)
    }

    func consentToAI() {
        showAIConsent = false
        UserDefaults.standard.set(true, forKey: Self.hasConsentedAIKey)
    }

    var wordCount: Int {
        problemText.trimmingCharacters(in: .whitespacesAndNewlines)
            .split(separator: " ", omittingEmptySubsequences: true)
            .count
    }

    static let minWords = 20
    static let maxWords = 50

    var canSubmit: Bool { wordCount >= Self.minWords && wordCount <= Self.maxWords }

    var isOverLimit: Bool { wordCount > Self.maxWords }

    var currentLens: Lens {
        Lens.lens(at: currentTakeIndex)
    }

    var currentTake: Take? {
        // Takes arrive in generation order (randomized) — show in arrival order
        guard currentTakeIndex < takes.count else { return nil }
        return takes[currentTakeIndex]
    }

    var totalTakes: Int {
        let baseTakes = isPro ? 20 : Lens.freeLensCount
        let packTakes = subscriptionManager?.ownedPackVoiceIndices.count ?? 0
        return baseTakes + packTakes
    }

    var isPro: Bool {
        #if DEBUG
        if subscriptionTier == .pro { return true }
        #endif
        return subscriptionManager?.isProSubscribed ?? false
    }

    var freeTakesRemaining: Int {
        max(0, Lens.freeLensCount - (currentTakeIndex + 1))
    }

    var lensIndicesForRequest: [Int] {
        // Free: pick 5 random from all 20 base lenses each run
        // Pro: all 20 base lenses, shuffled
        let baseIndices = isPro ? Array(0..<20).shuffled() : Array(0..<20).shuffled().prefix(Lens.freeLensCount).map { $0 }
        let packIndices = subscriptionManager?.ownedPackVoiceIndices ?? []
        return baseIndices + packIndices.shuffled()
    }

    var ownedPackProductIDs: [String] {
        Array(subscriptionManager?.ownedPackIDs ?? [])
    }

    #if DEBUG
    func debugTogglePro() {
        subscriptionTier = isPro ? .free : .pro
    }
    #endif

    func reset() {
        problemText = ""
        takes = []
        currentTakeIndex = 0
        showInstructionOverlay = true
        isGenerating = false
        showSafetyOverlay = false
    }

    func navigateToInput() {
        reset()
        currentScreen = .input
    }

    func receiveTake(_ take: Take) {
        if !takes.contains(where: { $0.lensIndex == take.lensIndex }) {
            takes.append(take)
        }
        // Transition from loading to takes as soon as first ordered take arrives
        if currentScreen == .loading && hasTakeForCurrentIndex {
            currentScreen = .takes
        }
    }

    var hasTakeForCurrentIndex: Bool {
        currentTakeIndex < takes.count
    }

    var nextTakeReady: Bool {
        currentTakeIndex + 1 < takes.count
    }
}
