import SwiftUI

struct LoadingView: View {
    @Environment(AppState.self) private var appState
    @State private var rotation: Double = 0
    @State private var pulseOpacity: Double = 0.5

    var body: some View {
        VStack(spacing: 24) {
            Spacer()

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

            Spacer()
        }
    }

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
