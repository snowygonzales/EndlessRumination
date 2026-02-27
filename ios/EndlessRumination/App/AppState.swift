import SwiftUI

enum AppScreen {
    case splash
    case input
    case loading
    case takes
}

@MainActor
@Observable
final class AppState {
    var currentScreen: AppScreen = .splash
    var problemText: String = ""
    var takes: [Take] = []
    var currentTakeIndex: Int = 0
    var showSafetyOverlay: Bool = false
    var showInstructionOverlay: Bool = true
    var isGenerating: Bool = false
    var authToken: String?
    var subscriptionTier: SubscriptionTier = .free
    var subscriptionManager: SubscriptionManager?
    var showPaywall: Bool = false
    var showShop: Bool = false
    var productsLoaded: Bool = false

    var wordCount: Int {
        problemText.trimmingCharacters(in: .whitespacesAndNewlines)
            .split(separator: " ", omittingEmptySubsequences: true)
            .count
    }

    var canSubmit: Bool { wordCount >= 20 }

    var currentLens: Lens {
        Lens.lens(at: currentTakeIndex)
    }

    var currentTake: Take? {
        guard currentTakeIndex < takes.count else { return nil }
        return takes.sorted(by: { $0.lensIndex < $1.lensIndex })[currentTakeIndex]
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
        let baseIndices = isPro ? Array(0..<20) : Array(0..<Lens.freeLensCount)
        let packIndices = subscriptionManager?.ownedPackVoiceIndices ?? []
        return baseIndices + packIndices
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
        takes.contains(where: { $0.lensIndex == currentTakeIndex })
    }

    var nextTakeReady: Bool {
        takes.contains(where: { $0.lensIndex == currentTakeIndex + 1 })
    }
}
