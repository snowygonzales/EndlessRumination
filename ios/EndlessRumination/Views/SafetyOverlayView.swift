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
                Text("Your input was flagged by our safety system. If you\u{2019}re going through a difficult time, please reach out to a crisis resource.")
                    .font(.system(size: 14))
                    .foregroundStyle(ERColors.secondaryText)
                    .multilineTextAlignment(.center)
                    .padding(.bottom, 8)

                // Crisis resources
                VStack(spacing: 10) {
                    ForEach(Array(SafetyService.crisisResources.enumerated()), id: \.offset) { _, resource in
                        Button {
                            openCrisisResource(resource)
                        } label: {
                            HStack(spacing: 6) {
                                Image(systemName: crisisResourceIcon(resource))
                                    .font(.system(size: 12))
                                    .foregroundStyle(ERColors.accentCool)
                                VStack(spacing: 2) {
                                    if resource.action == "link" {
                                        Text(resource.name)
                                            .font(.system(size: 13))
                                            .foregroundStyle(ERColors.accentCool)
                                    } else {
                                        Text("\(resource.name): \(resource.value)")
                                            .font(.system(size: 13))
                                            .foregroundStyle(ERColors.accentCool)
                                    }
                                    Text(resource.description)
                                        .font(.system(size: 11))
                                        .foregroundStyle(ERColors.dimText)
                                }
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

    private func openCrisisResource(_ resource: SafetyService.CrisisResource) {
        let urlString: String
        switch resource.action {
        case "call":
            urlString = "tel:\(resource.value)"
        case "text":
            // Extract the number from "KEYWORD to NUMBER" format
            let parts = resource.value.components(separatedBy: " to ")
            let number = parts.count > 1 ? parts[1] : resource.value
            let keyword = parts.count > 1 ? parts[0] : ""
            urlString = "sms:\(number)&body=\(keyword)"
        case "link":
            urlString = resource.value
        default:
            return
        }
        if let url = URL(string: urlString) {
            UIApplication.shared.open(url)
        }
    }

    private func crisisResourceIcon(_ resource: SafetyService.CrisisResource) -> String {
        switch resource.action {
        case "call": return "phone.fill"
        case "text": return "message.fill"
        case "link": return "globe"
        default: return "phone.fill"
        }
    }
}
