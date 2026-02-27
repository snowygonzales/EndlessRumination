import SwiftUI

struct TakesView: View {
    @Environment(AppState.self) private var appState
    @State private var fadeState: FadeState = .visible
    @State private var showGoneForever = false
    @State private var isBusy = false
    @State private var dragOffset: CGFloat = 0

    enum FadeState {
        case visible, fadingOut, fadingIn
    }

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

                // Gone forever flash
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

            // Ad banner (free tier only)
            if !appState.isPro {
                AdBannerView()
            }
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

                    Text("SWIPE UP \u{00B7} FADES FOREVER")
                        .font(.system(size: 11))
                        .tracking(2)
                        .foregroundStyle(ERColors.dimText)
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
                if appState.freeTakesRemaining <= 0 {
                    HStack(spacing: 4) {
                        Text("Daily limit reached \u{00B7}")
                            .foregroundStyle(ERColors.dimText)
                        Button {
                            appState.showPaywall = true
                        } label: {
                            Text("Go Pro")
                                .foregroundStyle(ERColors.accentGold)
                        }
                    }
                } else if appState.freeTakesRemaining <= 3 {
                    HStack(spacing: 4) {
                        Text("\(appState.freeTakesRemaining)")
                            .foregroundStyle(ERColors.accentGold)
                        Text("free takes remaining")
                            .foregroundStyle(ERColors.dimText)
                    }
                } else {
                    EmptyView()
                }
            }
            .font(.system(size: 11, design: .monospaced))
            .padding(.bottom, 4)
        }
    }

    // MARK: - Animation State

    private var cardOffset: CGFloat {
        switch fadeState {
        case .visible: return dragOffset
        case .fadingOut: return -40
        case .fadingIn: return 40
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
                if value.translation.height < 0 {
                    dragOffset = value.translation.height * 0.3
                }
            }
            .onEnded { value in
                dragOffset = 0
                if value.translation.height < -40 {
                    advance()
                }
            }
    }

    // MARK: - Advance

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
        UIImpactFeedbackGenerator(style: .light).impactOccurred()

        // Show "gone forever" flash
        withAnimation(.easeOut(duration: 0.3)) {
            showGoneForever = true
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
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.9) {
                withAnimation {
                    showGoneForever = false
                }
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
