import SwiftUI

struct TakesView: View {
    @Environment(AppState.self) private var appState
    @Environment(SubscriptionManager.self) private var subscriptionManager
    @State private var fadeState: FadeState = .visible
    @State private var showGoneForever = false
    @State private var isBusy = false
    @State private var dragOffset: CGFloat = 0
    @State private var isPurchasingExtra = false
    @State private var extraPurchaseError: String?

    enum FadeState {
        case visible, fadingOut, fadingIn
    }

    /// Direction of the current transition (for animation offset)
    enum TransitionDirection {
        case forward, backward
    }
    @State private var transitionDirection: TransitionDirection = .forward

    var body: some View {
        VStack(spacing: 0) {
            // Header
            header

            // Take content area
            ZStack {
                if let take = appState.currentTake {
                    takeContent(take: take)
                        .offset(y: cardOffset)
                        .opacity(cardOpacity)
                } else if appState.isGenerating {
                    waitingIndicator
                }

                // Gone forever flash (free users only)
                if showGoneForever {
                    goneForeverFlash
                }

                // Instruction overlay
                if appState.showInstructionOverlay {
                    InstructionOverlayView()
                }

                // Swipe hint at bottom
                if !appState.showInstructionOverlay && fadeState == .visible {
                    swipeHint
                }

                // Free takes remaining
                if !appState.isPro && fadeState == .visible {
                    remainingCounter
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .contentShape(Rectangle())
            .gesture(swipeGesture)

        }
    }

    // MARK: - Header

    private var header: some View {
        HStack {
            Button {
                appState.navigateToInput()
            } label: {
                Text("\u{2190} New problem")
                    .font(.system(size: 14))
                    .foregroundStyle(ERColors.secondaryText)
            }

            Spacer()

            Text("\(appState.currentTakeIndex + 1) / \(appState.totalTakes)")
                .font(ERTypography.counter)
                .foregroundStyle(ERColors.dimText)
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .background(ERColors.inputBackground)
                .clipShape(RoundedRectangle(cornerRadius: 8))
        }
        .padding(.horizontal, 24)
        .padding(.vertical, 12)
    }

    // MARK: - Take Content

    private func takeContent(take: Take) -> some View {
        TakeCardView(take: take)
            .padding(.horizontal, 28)
            .padding(.top, 24)
            .padding(.bottom, 70)
    }

    // MARK: - Waiting Indicator

    private var waitingIndicator: some View {
        VStack(spacing: 16) {
            ProgressView()
                .tint(ERColors.accentWarm)
            Text("Waiting for next perspective...")
                .font(.system(size: 14))
                .foregroundStyle(ERColors.secondaryText)
        }
    }

    // MARK: - Gone Forever Flash

    private var goneForeverFlash: some View {
        Text("GONE FOREVER")
            .font(.system(size: 11, design: .monospaced))
            .tracking(3)
            .foregroundStyle(ERColors.accentRed)
            .transition(.asymmetric(
                insertion: .scale(scale: 0.8).combined(with: .opacity),
                removal: .opacity.combined(with: .move(edge: .top))
            ))
    }

    // MARK: - Swipe Hint

    private var swipeHint: some View {
        VStack(spacing: 6) {
            Spacer()

            Button {
                advance()
            } label: {
                VStack(spacing: 6) {
                    Image(systemName: "chevron.up")
                        .font(.system(size: 16))
                        .foregroundStyle(ERColors.dimText)
                        .modifier(BobModifier())

                    if appState.isPro {
                        Text("SWIPE TO BROWSE")
                            .font(.system(size: 11))
                            .tracking(2)
                            .foregroundStyle(ERColors.dimText)
                    } else {
                        Text("SWIPE UP \u{00B7} FADES FOREVER")
                            .font(.system(size: 11))
                            .tracking(2)
                            .foregroundStyle(ERColors.dimText)
                    }
                }
            }

            Spacer().frame(height: 16)
        }
    }

    // MARK: - Remaining Counter

    private var remainingCounter: some View {
        VStack {
            Spacer()
            Group {
                if appState.freeTakesRemaining <= 0 && !appState.hasExtraTakes {
                    // Extra takes prompt
                    extraTakesPrompt
                } else if appState.freeTakesRemaining <= 0 && appState.hasExtraTakes {
                    // All done (including extras)
                    HStack(spacing: 4) {
                        Text("All perspectives delivered \u{00B7}")
                            .foregroundStyle(ERColors.dimText)
                        Button {
                            appState.showPaywall = true
                        } label: {
                            Text("Go Pro")
                                .foregroundStyle(ERColors.accentGold)
                        }
                    }
                    .font(.system(size: 11, design: .monospaced))
                } else if appState.freeTakesRemaining <= 3 {
                    HStack(spacing: 4) {
                        Text("\(appState.freeTakesRemaining)")
                            .foregroundStyle(ERColors.accentGold)
                        Text("free takes remaining")
                            .foregroundStyle(ERColors.dimText)
                    }
                    .font(.system(size: 11, design: .monospaced))
                } else {
                    EmptyView()
                }
            }
            .padding(.bottom, 4)
        }
    }

    // MARK: - Extra Takes Prompt

    private var extraTakesPrompt: some View {
        VStack(spacing: 6) {
            Button {
                purchaseExtraTakes()
            } label: {
                Group {
                    if isPurchasingExtra {
                        ProgressView()
                            .tint(ERColors.accentWarm)
                    } else {
                        HStack(spacing: 6) {
                            Text("+3 perspectives")
                                .font(.system(size: 12, weight: .semibold))
                            Text("\u{00B7}")
                            Text(subscriptionManager.extraTakesDisplayPrice)
                                .font(.system(size: 12, weight: .bold))
                        }
                    }
                }
                .foregroundStyle(ERColors.primaryText)
                .padding(.horizontal, 18)
                .padding(.vertical, 9)
                .background(ERColors.inputBackground)
                .clipShape(Capsule())
                .overlay(
                    Capsule()
                        .stroke(ERColors.accentWarm.opacity(0.3), lineWidth: 1)
                )
            }
            .disabled(isPurchasingExtra)

            Button {
                appState.showPaywall = true
            } label: {
                Text("or Go Pro for unlimited")
                    .font(.system(size: 10))
                    .foregroundStyle(ERColors.dimText)
            }

            if let error = extraPurchaseError {
                Text(error)
                    .font(.system(size: 10))
                    .foregroundStyle(ERColors.accentRed)
            }
        }
    }

    // MARK: - Animation State

    private var cardOffset: CGFloat {
        switch fadeState {
        case .visible: return dragOffset
        case .fadingOut: return transitionDirection == .forward ? -40 : 40
        case .fadingIn: return transitionDirection == .forward ? 40 : -40
        }
    }

    private var cardOpacity: Double {
        switch fadeState {
        case .visible: return 1
        case .fadingOut: return 0
        case .fadingIn: return 0
        }
    }

    // MARK: - Gesture

    private var swipeGesture: some Gesture {
        DragGesture(minimumDistance: 30, coordinateSpace: .local)
            .onChanged { value in
                let vertical = value.translation.height
                if vertical < 0 {
                    // Swipe up (forward)
                    dragOffset = vertical * 0.3
                } else if vertical > 0 && appState.isPro && appState.currentTakeIndex > 0 {
                    // Swipe down (backward) — Pro only
                    dragOffset = vertical * 0.3
                }
            }
            .onEnded { value in
                dragOffset = 0
                let vertical = value.translation.height
                if vertical < -40 {
                    advance()
                } else if vertical > 40 && appState.isPro && appState.currentTakeIndex > 0 {
                    goBack()
                }
            }
    }

    // MARK: - Extra Takes Purchase

    private func purchaseExtraTakes() {
        guard !isPurchasingExtra else { return }
        isPurchasingExtra = true
        extraPurchaseError = nil

        Task {
            let success = await subscriptionManager.purchaseExtraTakes()

            if success {
                appState.hasExtraTakes = true
                let extraIndices = appState.extraLensIndices
                appState.usedLensIndices.formUnion(extraIndices)

                // Generate extra takes
                appState.isGenerating = true
                let generator = LocalTakeGenerator(engine: appState.inferenceEngine)
                await generator.generateTakes(
                    problem: appState.problemText,
                    lensIndices: extraIndices
                ) { take in
                    appState.receiveTake(take)
                }
                appState.isGenerating = false

                // Auto-advance to the first extra take
                if appState.currentTakeIndex < appState.totalTakes - 1 {
                    advance()
                }
            } else if case .failed(let message) = subscriptionManager.purchaseState {
                extraPurchaseError = message
            }

            isPurchasingExtra = false
        }
    }

    // MARK: - Advance (forward)

    private func advance() {
        guard !isBusy else { return }

        // Dismiss instruction overlay first
        if appState.showInstructionOverlay {
            appState.showInstructionOverlay = false
            return
        }

        // Check if we have more takes
        guard appState.currentTakeIndex < appState.totalTakes - 1 else { return }

        isBusy = true
        transitionDirection = .forward
        UIImpactFeedbackGenerator(style: .light).impactOccurred()

        // Show "gone forever" flash only for free users
        if !appState.isPro {
            withAnimation(.easeOut(duration: 0.3)) {
                showGoneForever = true
            }
        }

        // Fade out current card
        withAnimation(ERAnimations.takeTransition) {
            fadeState = .fadingOut
        }

        // After fade out, switch to next take
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            appState.currentTakeIndex += 1
            fadeState = .fadingIn

            // Fade in new card
            withAnimation(ERAnimations.takeTransition) {
                fadeState = .visible
            }

            // Hide gone forever text
            if showGoneForever {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.9) {
                    withAnimation {
                        showGoneForever = false
                    }
                }
            }

            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                isBusy = false
            }
        }
    }

    // MARK: - Go Back (Pro only)

    private func goBack() {
        guard !isBusy else { return }
        guard appState.isPro else { return }
        guard appState.currentTakeIndex > 0 else { return }

        isBusy = true
        transitionDirection = .backward
        UIImpactFeedbackGenerator(style: .light).impactOccurred()

        // Fade out current card
        withAnimation(ERAnimations.takeTransition) {
            fadeState = .fadingOut
        }

        // After fade out, switch to previous take
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
            appState.currentTakeIndex -= 1
            fadeState = .fadingIn

            // Fade in previous card
            withAnimation(ERAnimations.takeTransition) {
                fadeState = .visible
            }

            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                isBusy = false
            }
        }
    }
}

// MARK: - Bob Animation Modifier

struct BobModifier: ViewModifier {
    @State private var offset: CGFloat = 0

    func body(content: Content) -> some View {
        content
            .offset(y: offset)
            .onAppear {
                withAnimation(ERAnimations.bob) {
                    offset = -6
                }
            }
    }
}
