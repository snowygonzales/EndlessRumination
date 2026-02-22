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

    var totalTakes: Int { 20 }
    var isPro: Bool { subscriptionTier == .pro }

    var freeTakesRemaining: Int {
        max(0, 10 - (currentTakeIndex + 1))
    }

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
