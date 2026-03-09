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
    private static let selectedLensIndicesKey = "com.endlessrumination.selectedLensIndices"

    var currentScreen: AppScreen = .splash
    var problemText: String = ""
    var takes: [Take] = []
    var currentTakeIndex: Int = 0
    var showSafetyOverlay: Bool = false
    var showInstructionOverlay: Bool = true
    var showOnboarding: Bool = false
    var showAIConsent: Bool = false
    var isGenerating: Bool = false
    /// The active generation task -- stored so interrupts don't lose progress.
    var generationTask: Task<Void, Never>?
    var subscriptionTier: SubscriptionTier = .free
    var subscriptionManager: SubscriptionManager?
    var showPaywall: Bool = false
    var showShop: Bool = false
    var productsLoaded: Bool = false

    /// Whether the user purchased extra takes for the current submission (consumable).
    var hasExtraTakes: Bool = false
    /// Tracks which lens indices were already used in the current submission (to avoid repeats).
    var usedLensIndices: Set<Int> = []

    /// Pro lens selection — which lenses the user has toggled on.
    /// `nil` means "all available" (default). Only used for Pro users.
    var selectedLensIndices: Set<Int>?

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
        loadSelectedLenses()
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
        if isPro {
            let allAvailable = allAvailableLensIndices
            if let selected = selectedLensIndices {
                return selected.intersection(Set(allAvailable)).count
            }
            return allAvailable.count
        }
        return Lens.freeLensCount + (hasExtraTakes ? Lens.extraTakesCount : 0)
    }

    /// All lens indices available to the current Pro user (base 20 + owned packs).
    var allAvailableLensIndices: [Int] {
        let base = Array(0..<20)
        let packs = subscriptionManager?.ownedPackVoiceIndices ?? []
        return base + packs
    }

    var isPro: Bool {
        #if DEBUG
        if subscriptionTier == .pro { return true }
        #endif
        return subscriptionManager?.isProSubscribed ?? false
    }

    var freeTakesRemaining: Int {
        max(0, totalTakes - (currentTakeIndex + 1))
    }

    var lensIndicesForRequest: [Int] {
        if isPro {
            let all = allAvailableLensIndices
            if let selected = selectedLensIndices {
                // Only include selected lenses that are still available
                return all.filter { selected.contains($0) }.shuffled()
            }
            return all.shuffled()
        }
        // Free: pick 5 random from all 20 base lenses each run
        return Array(0..<20).shuffled().prefix(Lens.freeLensCount).map { $0 }
    }

    /// Pick extra lens indices that haven't been used yet in the current submission.
    var extraLensIndices: [Int] {
        Array(0..<20)
            .filter { !usedLensIndices.contains($0) }
            .shuffled()
            .prefix(Lens.extraTakesCount)
            .map { $0 }
    }

    var ownedPackProductIDs: [String] {
        Array(subscriptionManager?.ownedPackIDs ?? [])
    }

    #if DEBUG
    func debugTogglePro() {
        subscriptionTier = isPro ? .free : .pro
    }
    #endif

    // MARK: - Lens Selection Persistence

    func saveSelectedLenses() {
        if let selected = selectedLensIndices {
            UserDefaults.standard.set(Array(selected), forKey: Self.selectedLensIndicesKey)
        } else {
            UserDefaults.standard.removeObject(forKey: Self.selectedLensIndicesKey)
        }
    }

    private func loadSelectedLenses() {
        if let saved = UserDefaults.standard.array(forKey: Self.selectedLensIndicesKey) as? [Int] {
            selectedLensIndices = Set(saved)
        }
    }

    func toggleLens(_ index: Int) {
        var current = selectedLensIndices ?? Set(allAvailableLensIndices)

        if current.contains(index) {
            // Don't allow deselecting the last lens
            if current.count > 1 {
                current.remove(index)
            }
        } else {
            current.insert(index)
        }

        selectedLensIndices = current
        saveSelectedLenses()
    }

    func selectAllLenses(in indices: [Int]) {
        var current = selectedLensIndices ?? Set(allAvailableLensIndices)
        for i in indices { current.insert(i) }
        selectedLensIndices = current
        saveSelectedLenses()
    }

    func clearLenses(in indices: [Int], keepMinimum: Bool = true) {
        var current = selectedLensIndices ?? Set(allAvailableLensIndices)
        for i in indices { current.remove(i) }
        // Ensure at least 1 lens remains
        if current.isEmpty, let first = allAvailableLensIndices.first {
            current.insert(first)
        }
        selectedLensIndices = current
        saveSelectedLenses()
    }

    func isLensSelected(_ index: Int) -> Bool {
        guard let selected = selectedLensIndices else { return true }
        return selected.contains(index)
    }

    var selectedLensCount: Int {
        if let selected = selectedLensIndices {
            return selected.intersection(Set(allAvailableLensIndices)).count
        }
        return allAvailableLensIndices.count
    }

    func reset() {
        generationTask?.cancel()
        generationTask = nil
        problemText = ""
        takes = []
        currentTakeIndex = 0
        showInstructionOverlay = true
        isGenerating = false
        showSafetyOverlay = false
        hasExtraTakes = false
        usedLensIndices = []
    }

    func navigateToInput() {
        reset()
        currentScreen = .input
    }

    /// Return to input screen without clearing problem text (for retry after interrupt).
    func returnToInputForRetry() {
        generationTask?.cancel()
        generationTask = nil
        takes = []
        currentTakeIndex = 0
        isGenerating = false
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
