import SwiftUI

// MARK: - Multi-screen onboarding that masks the ~2.1 GB model download

struct OnboardingView: View {
    @Environment(AppState.self) private var appState
    @State private var currentPage = 0
    @State private var appeared = false
    @State private var selectedCategories: Set<String> = []

    private let totalPages = 4

    var body: some View {
        ZStack {
            Color(hex: 0x0A0A0C).opacity(0.97)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                // Page content
                TabView(selection: $currentPage) {
                    howItWorksPage.tag(0)
                    whatBothersYouPage.tag(1)
                    meetAdvisorsPage.tag(2)
                    privacyPage.tag(3)
                }
                .tabViewStyle(.page(indexDisplayMode: .never))
                .animation(.easeInOut(duration: 0.3), value: currentPage)

                // Bottom bar: download progress + page dots + button
                bottomBar
            }
        }
        .opacity(appeared ? 1 : 0)
        .onAppear {
            withAnimation(.easeIn(duration: 0.3)) {
                appeared = true
            }
        }
    }

    // MARK: - Page 0: How It Works

    private var howItWorksPage: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                Spacer(minLength: 40)

                // Logo
                RoundedRectangle(cornerRadius: 14)
                    .fill(ERColors.logoGradient)
                    .frame(width: 48, height: 48)
                    .overlay(
                        Text("\u{221E}")
                            .font(.system(size: 24))
                            .foregroundStyle(.white)
                    )
                    .padding(.bottom, 20)

                Text("How It Works")
                    .font(ERTypography.serifHeadline())
                    .foregroundStyle(ERColors.primaryText)
                    .padding(.bottom, 24)

                separator

                VStack(alignment: .leading, spacing: 20) {
                    stepRow(
                        emoji: "\u{1F4DD}",
                        title: "Write what's on your mind",
                        subtitle: "Any worry, decision, or thought"
                    )
                    stepRow(
                        emoji: "\u{1F3AD}",
                        title: "Get fresh perspectives",
                        subtitle: "AI personas react \u{2014} comedian, stoic, therapist, your dog..."
                    )
                    stepRow(
                        emoji: "\u{2191}",
                        title: "Swipe through & let go",
                        subtitle: "Each take fades forever.\nNo overthinking \u{2014} just new angles."
                    )
                }
                .padding(.horizontal, 32)

                Spacer(minLength: 40)
            }
            .frame(maxWidth: .infinity)
        }
    }

    // MARK: - Page 1: What Bothers You

    private let worryCategories = [
        ("Career", "\u{1F4BC}"),
        ("Relationships", "\u{2764}\u{FE0F}"),
        ("Health", "\u{1FA7A}"),
        ("Money", "\u{1F4B0}"),
        ("Family", "\u{1F3E0}"),
        ("Social", "\u{1F465}"),
        ("School", "\u{1F393}"),
        ("Big Decisions", "\u{1F914}"),
        ("Self-Worth", "\u{1FA9E}"),
        ("The Future", "\u{1F52E}"),
    ]

    private var whatBothersYouPage: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                Spacer(minLength: 40)

                Text("\u{1F4AD}")
                    .font(.system(size: 40))
                    .padding(.bottom, 12)

                Text("What's on your mind\nmost often?")
                    .font(ERTypography.serifHeadline())
                    .foregroundStyle(ERColors.primaryText)
                    .multilineTextAlignment(.center)
                    .padding(.bottom, 8)

                Text("Pick as many as you like")
                    .font(.system(size: 13))
                    .foregroundStyle(ERColors.secondaryText)
                    .padding(.bottom, 24)

                separator

                // Category chips in a flowing layout
                FlowLayout(spacing: 10) {
                    ForEach(worryCategories, id: \.0) { category, emoji in
                        let isSelected = selectedCategories.contains(category)
                        Button {
                            withAnimation(.easeInOut(duration: 0.15)) {
                                if isSelected {
                                    selectedCategories.remove(category)
                                } else {
                                    selectedCategories.insert(category)
                                }
                            }
                        } label: {
                            HStack(spacing: 6) {
                                Text(emoji)
                                    .font(.system(size: 16))
                                Text(category)
                                    .font(.system(size: 14, weight: .medium))
                            }
                            .padding(.horizontal, 16)
                            .padding(.vertical, 10)
                            .background(isSelected ? ERColors.accentWarm.opacity(0.2) : ERColors.inputBackground)
                            .foregroundStyle(isSelected ? ERColors.accentWarm : ERColors.primaryText)
                            .clipShape(Capsule())
                            .overlay(
                                Capsule()
                                    .stroke(isSelected ? ERColors.accentWarm.opacity(0.5) : ERColors.border, lineWidth: 1)
                            )
                        }
                    }
                }
                .padding(.horizontal, 24)

                Spacer(minLength: 40)
            }
            .frame(maxWidth: .infinity)
        }
    }

    // MARK: - Page 2: Meet Your Advisors

    private let previewAdvisors = [0, 1, 3, 5, 9, 19, 7, 6] // Comedian, Stoic, Optimist, Best Friend, Therapist, Dog, 5yo, Poet

    private var meetAdvisorsPage: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                Spacer(minLength: 40)

                Text("Meet Your Advisors")
                    .font(ERTypography.serifHeadline())
                    .foregroundStyle(ERColors.primaryText)
                    .padding(.bottom, 8)

                Text("Each one sees your problem differently")
                    .font(.system(size: 13))
                    .foregroundStyle(ERColors.secondaryText)
                    .padding(.bottom, 24)

                separator

                LazyVGrid(columns: [
                    GridItem(.flexible(), spacing: 12),
                    GridItem(.flexible(), spacing: 12),
                ], spacing: 12) {
                    ForEach(previewAdvisors, id: \.self) { index in
                        let info = Lens.displayInfo(at: index)
                        VStack(spacing: 8) {
                            Text(info.emoji)
                                .font(.system(size: 28))
                            Text(info.name)
                                .font(.system(size: 12, weight: .semibold))
                                .foregroundStyle(info.color)
                                .multilineTextAlignment(.center)
                                .lineLimit(2)
                        }
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(info.bgColor)
                        .clipShape(RoundedRectangle(cornerRadius: 14))
                        .overlay(
                            RoundedRectangle(cornerRadius: 14)
                                .stroke(ERColors.border, lineWidth: 1)
                        )
                    }
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 12)

                Text("+ 12 more perspectives")
                    .font(.system(size: 12))
                    .foregroundStyle(ERColors.dimText)

                Spacer(minLength: 40)
            }
            .frame(maxWidth: .infinity)
        }
    }

    // MARK: - Page 3: Privacy + Ready

    private var privacyPage: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 0) {
                Spacer(minLength: 60)

                Image(systemName: "lock.shield.fill")
                    .font(.system(size: 44))
                    .foregroundStyle(ERColors.accentGreen)
                    .padding(.bottom, 16)

                Text("100% Private")
                    .font(ERTypography.serifHeadline())
                    .foregroundStyle(ERColors.primaryText)
                    .padding(.bottom, 20)

                separator

                VStack(alignment: .leading, spacing: 16) {
                    privacyRow(
                        icon: "iphone",
                        text: "AI runs entirely on your iPhone"
                    )
                    privacyRow(
                        icon: "wifi.slash",
                        text: "Works offline after setup"
                    )
                    privacyRow(
                        icon: "eye.slash.fill",
                        text: "Your thoughts never leave this device"
                    )
                    privacyRow(
                        icon: "server.rack",
                        text: "No cloud. No servers. No tracking."
                    )
                }
                .padding(.horizontal, 32)

                Spacer(minLength: 60)
            }
            .frame(maxWidth: .infinity)
        }
    }

    // MARK: - Bottom Bar

    private var bottomBar: some View {
        VStack(spacing: 12) {
            // Download progress bar (always visible during download)
            downloadStatusBar

            // Page dots
            HStack(spacing: 8) {
                ForEach(0..<totalPages, id: \.self) { page in
                    Circle()
                        .fill(page == currentPage ? ERColors.primaryText : ERColors.dimText)
                        .frame(width: 6, height: 6)
                }
            }
            .padding(.bottom, 4)

            // Action button
            Button {
                if currentPage < totalPages - 1 {
                    withAnimation(.easeInOut(duration: 0.3)) {
                        currentPage += 1
                    }
                } else {
                    // Final page — dismiss if model is ready, otherwise wait
                    if appState.inferenceEngine.isLoaded {
                        persistCategoriesAndDismiss()
                    }
                    // If not loaded yet, button is disabled (visual state handles this)
                }
            } label: {
                Group {
                    if currentPage == totalPages - 1 {
                        if appState.inferenceEngine.isLoaded {
                            Text("Let's go")
                                .font(ERTypography.button)
                                .foregroundStyle(ERColors.background)
                        } else {
                            HStack(spacing: 8) {
                                ProgressView()
                                    .tint(ERColors.dimText)
                                    .scaleEffect(0.8)
                                Text("Setting up...")
                                    .font(ERTypography.button)
                                    .foregroundStyle(ERColors.dimText)
                            }
                        }
                    } else {
                        Text("Next")
                            .font(ERTypography.button)
                            .foregroundStyle(ERColors.background)
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 14)
                .background(actionButtonBackground)
                .clipShape(Capsule())
            }
            .disabled(currentPage == totalPages - 1 && !appState.inferenceEngine.isLoaded)
            .padding(.horizontal, 48)
            .padding(.bottom, 8)
        }
        .padding(.bottom, 16)
        .background(
            LinearGradient(
                colors: [Color(hex: 0x0A0A0C).opacity(0), Color(hex: 0x0A0A0C)],
                startPoint: .top,
                endPoint: .bottom
            )
            .frame(height: 40)
            .offset(y: -40)
            , alignment: .top
        )
    }

    private var actionButtonBackground: some ShapeStyle {
        if currentPage == totalPages - 1 && !appState.inferenceEngine.isLoaded {
            return AnyShapeStyle(ERColors.inputBackground)
        }
        return AnyShapeStyle(ERColors.primaryText)
    }

    // MARK: - Download Status Bar

    private var downloadStatusBar: some View {
        VStack(spacing: 4) {
            if appState.inferenceEngine.isDownloading {
                // Active download
                ProgressView(value: appState.inferenceEngine.downloadProgress)
                    .tint(ERColors.accentWarm)
                    .scaleEffect(y: 0.6)
                    .padding(.horizontal, 48)

                Text(downloadStatusText)
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundStyle(ERColors.dimText)
            } else if appState.inferenceEngine.isLoaded {
                // Done
                HStack(spacing: 4) {
                    Image(systemName: "checkmark.circle.fill")
                        .font(.system(size: 10))
                        .foregroundStyle(ERColors.accentGreen)
                    Text("AI model ready")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(ERColors.accentGreen.opacity(0.8))
                }
            } else if !appState.inferenceEngine.isDownloading && appState.inferenceEngine.loadError == nil {
                // Waiting to start
                HStack(spacing: 4) {
                    ProgressView()
                        .scaleEffect(0.5)
                    Text("Preparing download...")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundStyle(ERColors.dimText)
                }
            } else if let error = appState.inferenceEngine.loadError {
                // Error with retry
                VStack(spacing: 2) {
                    Button {
                        appState.inferenceEngine.retryLoading()
                    } label: {
                        HStack(spacing: 4) {
                            Image(systemName: "arrow.clockwise")
                                .font(.system(size: 10))
                                .foregroundStyle(ERColors.accentRed)
                            Text(error.contains("storage") ? "Not enough storage" : "Download failed -- tap to retry")
                                .font(.system(size: 10, design: .monospaced))
                                .foregroundStyle(ERColors.accentRed.opacity(0.8))
                        }
                    }
                }
            }
        }
        .frame(height: 28)
    }

    private var downloadStatusText: String {
        let pct = Int(appState.inferenceEngine.downloadProgress * 100)
        let downloadedMB = Int(Double(pct) / 100.0 * 2100)
        return "Downloading AI \u{2014} \(downloadedMB) MB / 2.1 GB (\(pct)%)"
    }

    // MARK: - Helpers

    private var separator: some View {
        Rectangle()
            .fill(ERColors.dimText.opacity(0.3))
            .frame(height: 1)
            .padding(.horizontal, 20)
            .padding(.bottom, 24)
    }

    private func stepRow(emoji: String, title: String, subtitle: String) -> some View {
        HStack(alignment: .top, spacing: 14) {
            Text(emoji)
                .font(.system(size: 22))
                .frame(width: 32)

            VStack(alignment: .leading, spacing: 3) {
                Text(title)
                    .font(.system(size: 14, weight: .semibold))
                    .foregroundStyle(ERColors.primaryText)

                Text(subtitle)
                    .font(.system(size: 12))
                    .foregroundStyle(ERColors.secondaryText)
                    .lineSpacing(2)
            }
        }
    }

    private func privacyRow(icon: String, text: String) -> some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.system(size: 16))
                .foregroundStyle(ERColors.accentGreen)
                .frame(width: 32)

            Text(text)
                .font(.system(size: 14))
                .foregroundStyle(ERColors.primaryText)
        }
    }

    private func persistCategoriesAndDismiss() {
        // Save selected categories for potential future use
        if !selectedCategories.isEmpty {
            UserDefaults.standard.set(Array(selectedCategories), forKey: "com.endlessrumination.worryCategories")
        }
        withAnimation(.easeOut(duration: 0.25)) {
            appState.dismissOnboarding()
        }
    }
}

// FlowLayout is defined in ShopView.swift and shared
