import SwiftUI

struct AIConsentView: View {
    @Environment(AppState.self) private var appState
    @State private var appeared = false

    var body: some View {
        ZStack {
            Color(hex: 0x0A0A0C).opacity(0.95)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                // Icon
                Image(systemName: "cpu")
                    .font(.system(size: 28))
                    .foregroundStyle(ERColors.accentWarm)
                    .padding(.bottom, 20)

                // Title
                Text("On-Device AI")
                    .font(ERTypography.serifHeadline())
                    .foregroundStyle(ERColors.primaryText)
                    .padding(.bottom, 12)

                // Description
                Text("This app uses an **on-device AI model running entirely on your iPhone** to generate perspectives. Your thoughts never leave this device.")
                    .font(.system(size: 14))
                    .foregroundStyle(ERColors.secondaryText)
                    .multilineTextAlignment(.center)
                    .lineSpacing(4)
                    .padding(.horizontal, 32)
                    .padding(.bottom, 20)

                // Links
                VStack(spacing: 8) {
                    Link(destination: URL(string: "https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md")!) {
                        Text("Privacy Policy")
                            .font(.system(size: 13))
                            .foregroundStyle(ERColors.accentCool)
                    }
                    Link(destination: URL(string: "https://github.com/snowygonzales/EndlessRumination/blob/master/docs/terms-of-service.md")!) {
                        Text("Terms of Service")
                            .font(.system(size: 13))
                            .foregroundStyle(ERColors.accentCool)
                    }
                }
                .padding(.bottom, 32)

                // Consent button
                Button {
                    withAnimation(.easeOut(duration: 0.25)) {
                        appState.consentToAI()
                    }
                } label: {
                    Text("I Agree")
                        .font(ERTypography.button)
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(ERColors.warmGradient)
                        .clipShape(RoundedRectangle(cornerRadius: 14))
                }
                .padding(.horizontal, 24)

                Spacer().frame(height: 12)

                // Decline text
                Text("You must agree to use the app.")
                    .font(.system(size: 11))
                    .foregroundStyle(ERColors.dimText)

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
}
