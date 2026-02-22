import SwiftUI

struct SafetyOverlayView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        ZStack {
            Color(hex: 0x0A0A0C).opacity(0.95)
                .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                // Shield icon
                Circle()
                    .fill(ERColors.accentRed.opacity(0.15))
                    .frame(width: 64, height: 64)
                    .overlay(
                        Image(systemName: "shield.fill")
                            .font(.system(size: 28))
                            .foregroundStyle(ERColors.accentRed)
                    )
                    .padding(.bottom, 20)

                // Title
                Text("We can't process this")
                    .font(ERTypography.serifHeadline())
                    .foregroundStyle(ERColors.primaryText)
                    .padding(.bottom, 12)

                // Description
                Text("Your input was flagged by our safety system.")
                    .font(.system(size: 14))
                    .foregroundStyle(ERColors.secondaryText)
                    .multilineTextAlignment(.center)
                    .padding(.bottom, 8)

                // Crisis resources link
                Button {
                    if let url = URL(string: "tel:988") {
                        UIApplication.shared.open(url)
                    }
                } label: {
                    Text("If you're in crisis, tap here for resources \u{2192}")
                        .font(.system(size: 13))
                        .foregroundStyle(ERColors.accentCool)
                }
                .padding(.bottom, 28)

                // Edit button
                Button {
                    appState.showSafetyOverlay = false
                } label: {
                    Text("Edit my input")
                        .font(.system(size: 15))
                        .foregroundStyle(ERColors.primaryText)
                        .padding(.horizontal, 40)
                        .padding(.vertical, 14)
                        .background(ERColors.inputBackground)
                        .clipShape(Capsule())
                        .overlay(
                            Capsule()
                                .stroke(ERColors.border, lineWidth: 1)
                        )
                }

                Spacer()
            }
            .padding(.horizontal, 40)
        }
    }
}
