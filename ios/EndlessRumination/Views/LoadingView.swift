import SwiftUI

struct LoadingView: View {
    @Environment(AppState.self) private var appState
    @State private var rotation: Double = 0
    @State private var pulseOpacity: Double = 0.5

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

            // Show recovery UI if generation stopped but we have partial results
            if !appState.isGenerating && !appState.takes.isEmpty {
                recoveryView
            } else if !appState.isGenerating && appState.takes.isEmpty {
                // Generation stopped with zero takes -- offer retry or go back
                failedView
            } else {
                // Normal loading state
                activeLoadingView
            }

            Spacer()
        }
    }

    // MARK: - Active Loading

    private var activeLoadingView: some View {
        VStack(spacing: 24) {
            // Spinner
            Circle()
                .trim(from: 0, to: 0.75)
                .stroke(ERColors.accentWarm, lineWidth: 3)
                .frame(width: 48, height: 48)
                .rotationEffect(.degrees(rotation))
                .onAppear {
                    withAnimation(ERAnimations.spin) {
                        rotation = 360
                    }
                }

            // Status text
            Text(statusText)
                .font(.system(size: 14))
                .foregroundStyle(ERColors.secondaryText)
                .multilineTextAlignment(.center)
                .opacity(pulseOpacity)
                .onAppear {
                    withAnimation(ERAnimations.pulse) {
                        pulseOpacity = 1
                    }
                }

            // Model download progress (shown while model is downloading)
            if appState.inferenceEngine.isDownloading {
                VStack(spacing: 8) {
                    ProgressView(value: appState.modelDownloadProgress)
                        .tint(ERColors.accentWarm)
                        .frame(width: 200)

                    Text("Downloading AI model \u{2014} \(Int(appState.modelDownloadProgress * 100))%")
                        .font(ERTypography.counter)
                        .foregroundStyle(ERColors.dimText)
                }
            }

            // Take count if generating
            if !appState.takes.isEmpty {
                Text("\(appState.takes.count) / \(appState.totalTakes) perspectives ready")
                    .font(ERTypography.counter)
                    .foregroundStyle(ERColors.dimText)
            }
        }
    }

    // MARK: - Recovery (partial takes available)

    private var recoveryView: some View {
        VStack(spacing: 16) {
            Image(systemName: "checkmark.circle")
                .font(.system(size: 36))
                .foregroundStyle(ERColors.accentGreen)

            Text("\(appState.takes.count) perspective\(appState.takes.count == 1 ? "" : "s") ready")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(ERColors.primaryText)

            Text("Generation was interrupted.\nYou can view what's ready.")
                .font(.system(size: 13))
                .foregroundStyle(ERColors.secondaryText)
                .multilineTextAlignment(.center)

            Button {
                appState.currentScreen = .takes
            } label: {
                Text("View perspectives")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(ERColors.warmGradient)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .padding(.horizontal, 48)
            .padding(.top, 8)

            Button {
                appState.navigateToInput()
            } label: {
                Text("Start over")
                    .font(.system(size: 13))
                    .foregroundStyle(ERColors.secondaryText)
            }
        }
    }

    // MARK: - Failed (no takes at all)

    private var failedView: some View {
        VStack(spacing: 16) {
            Image(systemName: "exclamationmark.triangle")
                .font(.system(size: 36))
                .foregroundStyle(ERColors.accentGold)

            Text("Generation interrupted")
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(ERColors.primaryText)

            Text("No perspectives were generated.\nYour problem text is still saved.")
                .font(.system(size: 13))
                .foregroundStyle(ERColors.secondaryText)
                .multilineTextAlignment(.center)

            Button {
                appState.returnToInputForRetry()
            } label: {
                Text("Try again")
                    .font(.system(size: 15, weight: .semibold))
                    .foregroundStyle(.white)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 14)
                    .background(ERColors.warmGradient)
                    .clipShape(RoundedRectangle(cornerRadius: 12))
            }
            .padding(.horizontal, 48)
            .padding(.top, 8)
        }
    }

    // MARK: - Status Text

    private var statusText: String {
        if appState.inferenceEngine.isDownloading {
            return "Preparing your private AI..."
        }
        if !appState.inferenceEngine.isLoaded {
            return "Loading AI model..."
        }
        if appState.takes.isEmpty {
            return "Generating perspectives...\nThis takes a moment on-device."
        }
        return "Almost ready..."
    }
}
