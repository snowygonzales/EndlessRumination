import SwiftUI

struct SplashView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        VStack(spacing: 0) {
            Spacer()

            // Logo
            RoundedRectangle(cornerRadius: 20)
                .fill(ERColors.logoGradient)
                .frame(width: 80, height: 80)
                .overlay(
                    Text("\u{221E}")
                        .font(.system(size: 36))
                        .foregroundStyle(.white)
                )
                .padding(.bottom, 24)

            // Title
            Text("Endless Rumination")
                .font(ERTypography.serifLargeTitle())
                .foregroundStyle(ERColors.titleGradient)
                .padding(.bottom, 8)

            // Tagline
            Text("SCROLL YOUR WORRIES")
                .font(.system(size: 15, weight: .light))
                .tracking(3)
                .foregroundStyle(ERColors.secondaryText)
                .padding(.bottom, 48)

            // Begin button
            Button {
                appState.currentScreen = .input
            } label: {
                Text("Begin")
                    .font(ERTypography.button)
                    .foregroundStyle(ERColors.background)
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 16)
                    .padding(.horizontal, 48)
                    .background(ERColors.primaryText)
                    .clipShape(Capsule())
            }
            .padding(.horizontal, 80)

            Spacer()
        }
    }
}
