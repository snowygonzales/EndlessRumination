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

                // Crisis resources
                VStack(spacing: 10) {
                    ForEach(Array(SafetyService.crisisResources.enumerated()), id: \.offset) { _, resource in
                        Button {
                            if resource.action == "call", let url = URL(string: "tel:\(resource.value)") {
                                UIApplication.shared.open(url)
                            } else if resource.action == "text", let url = URL(string: "sms:741741&body=HOME") {
                                UIApplication.shared.open(url)
                            }
                        } label: {
                            VStack(spacing: 2) {
                                Text("\(resource.name): \(resource.value)")
                                    .font(.system(size: 13))
                                    .foregroundStyle(ERColors.accentCool)
                                Text(resource.description)
                                    .font(.system(size: 11))
                                    .foregroundStyle(ERColors.dimText)
                            }
                        }
                    }
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
