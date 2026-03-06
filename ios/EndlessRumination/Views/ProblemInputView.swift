import SwiftUI

struct ProblemInputView: View {
    @Environment(AppState.self) private var appState
    @FocusState private var isTextFieldFocused: Bool
    @State private var isSubmitting = false

    var body: some View {
        @Bindable var state = appState

        ZStack {
            VStack(spacing: 0) {
                // Header
                HStack {
                    Text("What's on your mind?")
                        .font(ERTypography.serifTitle())
                        .foregroundStyle(ERColors.primaryText)

                    Spacer()

                    // Shop button
                    Button {
                        appState.showShop = true
                    } label: {
                        HStack(spacing: 4) {
                            Text("\u{2726}")
                            Text("Shop")
                        }
                        .font(.system(size: 11, weight: .bold))
                        .tracking(1)
                        .textCase(.uppercase)
                        .foregroundStyle(ERColors.background)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 5)
                        .background(ERColors.proGradient)
                        .clipShape(Capsule())
                    }
                    #if DEBUG
                    .onTapGesture(count: 3) {
                        appState.debugTogglePro()
                    }
                    #endif
                }
                .padding(.horizontal, 24)
                .padding(.top, 20)
                .padding(.bottom, 12)

                // Subtext
                Text("Describe what's bothering you. Be specific \u{2014} the more you share, the better the perspectives.")
                    .font(.system(size: 13))
                    .foregroundStyle(ERColors.secondaryText)
                    .lineSpacing(4)
                    .padding(.horizontal, 24)
                    .padding(.bottom, 12)

                // Text area with word counter
                ZStack(alignment: .bottomTrailing) {
                    TextEditor(text: $state.problemText)
                        .focused($isTextFieldFocused)
                        .font(.system(size: 16))
                        .lineSpacing(6)
                        .foregroundStyle(ERColors.primaryText)
                        .scrollContentBackground(.hidden)
                        .padding(16)
                        .background(ERColors.inputBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                        .overlay(
                            RoundedRectangle(cornerRadius: 16)
                                .stroke(ERColors.border, lineWidth: 1)
                        )
                        .overlay(alignment: .topLeading) {
                            if appState.problemText.isEmpty {
                                Text("I can't stop thinking about...")
                                    .font(.system(size: 16))
                                    .foregroundStyle(ERColors.dimText)
                                    .padding(.horizontal, 21)
                                    .padding(.vertical, 24)
                                    .allowsHitTesting(false)
                            }
                        }

                    // Word counter
                    Text("\(appState.wordCount) / 20 words")
                        .font(ERTypography.counter)
                        .foregroundStyle(wordCountColor)
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(ERColors.inputBackground)
                        .clipShape(RoundedRectangle(cornerRadius: 6))
                        .padding(14)
                        .animation(ERAnimations.wordCounter, value: appState.wordCount)
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 20)

                // Submit button
                Button {
                    submit()
                } label: {
                    Group {
                        if isSubmitting {
                            ProgressView()
                                .tint(ERColors.primaryText)
                        } else {
                            Text(buttonLabel)
                                .font(ERTypography.button)
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 18)
                    .foregroundStyle(appState.canSubmit ? .white : ERColors.dimText)
                    .background(appState.canSubmit ? AnyShapeStyle(ERColors.warmGradient) : AnyShapeStyle(ERColors.inputBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 14))
                }
                .disabled(!appState.canSubmit || isSubmitting)
                .padding(.horizontal, 24)
                .padding(.bottom, 16)

                // Disclaimers
                VStack(spacing: 4) {
                    HStack(spacing: 4) {
                        Image(systemName: "lock.shield.fill")
                            .font(.system(size: 10))
                        Text("Your thoughts never leave this device.")
                            .font(ERTypography.caption)
                    }
                    Text("Not a substitute for professional mental health care.")
                        .font(ERTypography.caption)
                }
                .foregroundStyle(ERColors.dimText)
                .padding(.bottom, 24)
            }

            // Safety overlay
            if appState.showSafetyOverlay {
                SafetyOverlayView()
            }
        }
    }

    private var wordCountColor: Color {
        let wc = appState.wordCount
        if wc >= 20 { return ERColors.accentGreen }
        if wc >= 15 { return ERColors.accentGold }
        return ERColors.dimText
    }

    private var buttonLabel: String {
        let wc = appState.wordCount
        if wc >= 20 { return "See perspectives" }
        if wc >= 15 { return "Need \(20 - wc) more words" }
        return "Need at least 20 words"
    }

    private func submit() {
        guard appState.canSubmit else { return }

        // Show AI consent dialog on first use
        if !appState.hasConsentedAI {
            appState.showAIConsent = true
            return
        }

        // Client-side safety check (only safety layer in on-device mode)
        guard SafetyService.clientSideCheck(appState.problemText) else {
            appState.showSafetyOverlay = true
            return
        }

        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        isSubmitting = true
        isTextFieldFocused = false

        Task {
            appState.currentScreen = .loading
            appState.isGenerating = true
            isSubmitting = false

            // Generate takes locally via on-device inference
            let generator = LocalTakeGenerator(engine: appState.inferenceEngine)
            await generator.generateTakes(
                problem: appState.problemText,
                lensIndices: appState.lensIndicesForRequest
            ) { take in
                appState.receiveTake(take)
            }

            appState.isGenerating = false
        }
    }
}
