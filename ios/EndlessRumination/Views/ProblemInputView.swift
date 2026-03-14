import SwiftUI

struct ProblemInputView: View {
    @Environment(AppState.self) private var appState
    @FocusState private var isTextFieldFocused: Bool
    @State private var isSubmitting = false
    @State private var cooldownInfo: UsageLimiter.CooldownInfo?
    @State private var cooldownTimer: Timer?
    @State private var freeLimitHit: FreeLimitType?
    @State private var showLensPicker = false

    enum FreeLimitType {
        case daily, monthly
    }

    var body: some View {
        @Bindable var state = appState

        ZStack {
            VStack(spacing: 0) {
                // Header
                HStack {
                    HStack(spacing: 8) {
                        Text("What's on your mind?")
                            .font(ERTypography.serifTitle())
                            .foregroundStyle(appState.isPro ? ERColors.accentGold : ERColors.primaryText)
                            .animation(.easeInOut(duration: 0.3), value: appState.isPro)

                        if appState.isPro {
                            Text("PRO")
                                .font(.system(size: 9, weight: .black))
                                .tracking(1.5)
                                .foregroundStyle(ERColors.background)
                                .padding(.horizontal, 7)
                                .padding(.vertical, 3)
                                .background(ERColors.proGradient)
                                .clipShape(Capsule())
                                .transition(.scale.combined(with: .opacity))
                        }
                    }

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
                    .simultaneousGesture(
                        LongPressGesture(minimumDuration: 2)
                            .onEnded { _ in
                                appState.debugResetAllData()
                                UINotificationFeedbackGenerator().notificationOccurred(.warning)
                            }
                    )
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

                // Text area
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
                    .padding(.horizontal, 24)
                    .padding(.bottom, 6)
                    .onChange(of: appState.problemText) {
                        UIImpactFeedbackGenerator(style: .light).impactOccurred(intensity: 0.4)
                    }

                // Word counter (outside text area to prevent overlap)
                HStack {
                    Spacer()
                    Text(wordCountLabel)
                        .font(ERTypography.counter)
                        .foregroundStyle(wordCountColor)
                        .animation(ERAnimations.wordCounter, value: appState.wordCount)
                }
                .padding(.horizontal, 28)
                .padding(.bottom, 8)

                // Pro lens picker
                if appState.isPro {
                    VStack(spacing: 0) {
                        Button {
                            withAnimation(.spring(duration: 0.3)) {
                                showLensPicker.toggle()
                            }
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: "slider.horizontal.3")
                                    .font(.system(size: 11))
                                Text("Perspectives (\(appState.selectedLensCount)/\(appState.allAvailableLensIndices.count))")
                                    .font(.system(size: 12))
                                Spacer()
                                Image(systemName: showLensPicker ? "chevron.up" : "chevron.down")
                                    .font(.system(size: 10, weight: .semibold))
                            }
                            .foregroundStyle(ERColors.secondaryText)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 10)
                            .background(ERColors.inputBackground)
                            .clipShape(RoundedRectangle(cornerRadius: 10))
                        }

                        if showLensPicker {
                            ScrollView {
                                LensPickerView()
                                    .padding(.horizontal, 4)
                            }
                            .frame(maxHeight: 200)
                            .transition(.opacity.combined(with: .move(edge: .top)))
                        }
                    }
                    .padding(.horizontal, 24)
                    .padding(.bottom, 8)
                }

                // Burst cooldown banner
                if let info = cooldownInfo {
                    limitBanner(
                        icon: "flame.fill",
                        iconColor: ERColors.accentRed,
                        title: "Take a breather",
                        message: "You've submitted a lot in a short time. New submissions available in \(info.displayText).",
                        borderColor: ERColors.accentRed
                    )
                }

                // Free-tier limit banner
                if let limitType = freeLimitHit {
                    limitBanner(
                        icon: "hourglass",
                        iconColor: ERColors.accentGold,
                        title: limitType == .daily ? "Daily limit reached" : "Monthly limit reached",
                        message: limitType == .daily
                            ? "Free accounts get \(UsageLimiter.freeDailyLimit) submissions per day. Come back tomorrow, or go Pro for unlimited."
                            : "Free accounts get \(UsageLimiter.freeMonthlyLimit) submissions per month. Go Pro for unlimited.",
                        borderColor: ERColors.accentGold,
                        showProButton: true
                    )
                }

                // Free usage counter (when not at limit)
                if !appState.isPro && freeLimitHit == nil && cooldownInfo == nil {
                    HStack(spacing: 4) {
                        Image(systemName: "circle.grid.2x1.fill")
                            .font(.system(size: 8))
                        Text("\(UsageLimiter.submissionsToday())/\(UsageLimiter.freeDailyLimit) today  \u{00B7}  \(UsageLimiter.submissionsThisMonth())/\(UsageLimiter.freeMonthlyLimit) this month")
                            .font(.system(size: 11))
                    }
                    .foregroundStyle(ERColors.dimText)
                    .padding(.bottom, 4)
                }

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
                    .foregroundStyle(submitEnabled ? .white : ERColors.dimText)
                    .background(submitEnabled ? AnyShapeStyle(ERColors.warmGradient) : AnyShapeStyle(ERColors.inputBackground))
                    .clipShape(RoundedRectangle(cornerRadius: 14))
                }
                .disabled(!submitEnabled || isSubmitting)
                .padding(.horizontal, 24)
                .padding(.bottom, 16)

                // Disclaimers (hidden when keyboard is up to save space)
                if !isTextFieldFocused {
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
            }

            // Safety overlay
            if appState.showSafetyOverlay {
                SafetyOverlayView()
            }
        }
        .onAppear {
            refreshLimits()
        }
        .onChange(of: appState.isPro) {
            refreshLimits()
        }
        .onChange(of: appState.showAIConsent) {
            // Auto-continue submission after AI consent dialog is dismissed.
            // Deferred via Task to escape the withAnimation transaction in AIConsentView.
            if !appState.showAIConsent && appState.hasConsentedAI && appState.canSubmit {
                Task { @MainActor in
                    submit()
                }
            }
        }
    }

    private var wordCountLabel: String {
        let wc = appState.wordCount
        if wc > AppState.maxWords {
            return "\(wc) / \(AppState.maxWords) words"
        }
        return "\(wc) / \(AppState.minWords) words"
    }

    private var wordCountColor: Color {
        let wc = appState.wordCount
        if wc > AppState.maxWords { return ERColors.accentRed }
        if wc >= AppState.minWords { return ERColors.accentGreen }
        if wc >= 15 { return ERColors.accentGold }
        return ERColors.dimText
    }

    private var submitEnabled: Bool {
        appState.canSubmit && cooldownInfo == nil && freeLimitHit == nil
    }

    private var buttonLabel: String {
        if cooldownInfo != nil { return "Cooling down..." }
        if freeLimitHit != nil { return "Limit reached" }
        let wc = appState.wordCount
        if wc > AppState.maxWords { return "Too many words (\(wc)/\(AppState.maxWords))" }
        if wc >= AppState.minWords { return "See perspectives" }
        if wc >= 15 { return "Need \(AppState.minWords - wc) more words" }
        return "Need at least \(AppState.minWords) words"
    }

    private func submit() {
        guard appState.canSubmit else { return }

        // Show AI consent dialog on first use
        if !appState.hasConsentedAI {
            appState.showAIConsent = true
            return
        }

        // Rate limit + free-tier check
        switch UsageLimiter.checkLimit(isPro: appState.isPro) {
        case .allowed:
            break
        case .burstCooldown(let info):
            cooldownInfo = info
            startCooldownTimer()
            UINotificationFeedbackGenerator().notificationOccurred(.warning)
            return
        case .dailyLimitReached:
            freeLimitHit = .daily
            UINotificationFeedbackGenerator().notificationOccurred(.warning)
            return
        case .monthlyLimitReached:
            freeLimitHit = .monthly
            UINotificationFeedbackGenerator().notificationOccurred(.warning)
            return
        }

        // Client-side safety check -- runs on both raw and normalized text
        // to catch Unicode homoglyphs, l33tspeak, and spacing evasion
        guard SafetyService.clientSideCheck(appState.problemText) else {
            appState.showSafetyOverlay = true
            return
        }

        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        isSubmitting = true
        isTextFieldFocused = false

        // Record this submission for rate limiting
        UsageLimiter.recordSubmission()

        appState.currentScreen = .loading
        appState.isGenerating = true
        isSubmitting = false

        // Compute lens indices and track them for potential extra takes later
        let indices = appState.lensIndicesForRequest
        appState.usedLensIndices = Set(indices)

        // Store the task so it survives view rebuilds and app interrupts
        appState.generationTask = Task {
            let generator = LocalTakeGenerator(engine: appState.inferenceEngine)
            await generator.generateTakes(
                problem: appState.problemText,
                lensIndices: indices
            ) { take in
                appState.receiveTake(take)
            }

            appState.isGenerating = false
            appState.generationTask = nil
        }
    }

    // MARK: - Limit Banner

    private func limitBanner(
        icon: String,
        iconColor: Color,
        title: String,
        message: String,
        borderColor: Color,
        showProButton: Bool = false
    ) -> some View {
        VStack(spacing: 8) {
            HStack(spacing: 6) {
                Image(systemName: icon)
                    .foregroundStyle(iconColor)
                Text(title)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(ERColors.primaryText)
            }
            Text(message)
                .font(.system(size: 12))
                .foregroundStyle(ERColors.secondaryText)
                .multilineTextAlignment(.center)

            if showProButton {
                Button {
                    appState.showPaywall = true
                } label: {
                    Text("Go Pro -- Unlimited")
                        .font(.system(size: 12, weight: .semibold))
                        .foregroundStyle(.white)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 8)
                        .background(ERColors.proGradient)
                        .clipShape(Capsule())
                }
                .padding(.top, 2)
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity)
        .background(ERColors.inputBackground)
        .clipShape(RoundedRectangle(cornerRadius: 12))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(borderColor.opacity(0.3), lineWidth: 1)
        )
        .padding(.horizontal, 24)
        .padding(.bottom, 8)
    }

    // MARK: - Cooldown Timer

    private func startCooldownTimer() {
        cooldownTimer?.invalidate()
        cooldownTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { _ in
            switch UsageLimiter.checkLimit(isPro: appState.isPro) {
            case .burstCooldown(let info):
                cooldownInfo = info
            default:
                cooldownInfo = nil
                cooldownTimer?.invalidate()
                cooldownTimer = nil
            }
        }
    }

    // MARK: - Refresh Limits

    private func refreshLimits() {
        switch UsageLimiter.checkLimit(isPro: appState.isPro) {
        case .burstCooldown(let info):
            cooldownInfo = info
            freeLimitHit = nil
            startCooldownTimer()
        case .dailyLimitReached:
            cooldownInfo = nil
            freeLimitHit = .daily
        case .monthlyLimitReached:
            cooldownInfo = nil
            freeLimitHit = .monthly
        case .allowed:
            cooldownInfo = nil
            freeLimitHit = nil
        }
    }
}
