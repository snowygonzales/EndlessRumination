import SwiftUI

struct OnboardingView: View {
    @Environment(AppState.self) private var appState
    @State private var appeared = false

    var body: some View {
        ZStack {
            Color(hex: 0x0A0A0C).opacity(0.95)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

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

                // Title
                Text("How It Works")
                    .font(ERTypography.serifHeadline())
                    .foregroundStyle(ERColors.primaryText)
                    .padding(.bottom, 24)

                // Separator
                Rectangle()
                    .fill(ERColors.dimText.opacity(0.3))
                    .frame(height: 1)
                    .padding(.horizontal, 20)
                    .padding(.bottom, 24)

                // Steps
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
                .padding(.bottom, 24)

                // Separator
                Rectangle()
                    .fill(ERColors.dimText.opacity(0.3))
                    .frame(height: 1)
                    .padding(.horizontal, 20)
                    .padding(.bottom, 32)

                // Got it button
                Button {
                    withAnimation(.easeOut(duration: 0.25)) {
                        appState.dismissOnboarding()
                    }
                } label: {
                    Text("Got it")
                        .font(ERTypography.button)
                        .foregroundStyle(ERColors.background)
                        .padding(.horizontal, 48)
                        .padding(.vertical, 14)
                        .background(ERColors.primaryText)
                        .clipShape(Capsule())
                }

                Spacer()
            }
            .padding(.horizontal, 24)
        }
        .opacity(appeared ? 1 : 0)
        .onAppear {
            withAnimation(.easeIn(duration: 0.3)) {
                appeared = true
            }
        }
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
}
