import SwiftUI

struct TakeCardView: View {
    let take: Take
    @Environment(AppState.self) private var appState
    @State private var showReportConfirmation = false
    @State private var isReported = false

    private var display: (name: String, emoji: String, color: Color, bgColor: Color) {
        Lens.displayInfo(at: take.lensIndex)
    }

    var body: some View {
        if isReported {
            // Replace flagged take with acknowledgment + crisis resources
            reportedPlaceholder
        } else {
            takeCard
        }
    }

    private var takeCard: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Lens badge + Pack badge + Flag
            HStack(spacing: 8) {
                // Voice name badge
                HStack(spacing: 8) {
                    Text(display.emoji)
                        .font(.system(size: 12))
                    Text(display.name.uppercased())
                        .font(.system(size: 12, weight: .bold))
                        .tracking(2)
                        .foregroundStyle(display.color)
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 6)
                .background(display.bgColor)
                .clipShape(Capsule())

                // Pack name badge (for voice pack takes)
                if let packName = take.packName {
                    Text(packName.uppercased())
                        .font(.system(size: 9, weight: .bold))
                        .tracking(1.5)
                        .foregroundStyle(display.color.opacity(0.7))
                        .padding(.horizontal, 8)
                        .padding(.vertical, 4)
                        .background(display.color.opacity(0.08))
                        .clipShape(Capsule())
                }

                Spacer()

                // Report/flag button
                Button {
                    showReportConfirmation = true
                } label: {
                    Image(systemName: "flag")
                        .font(.system(size: 12))
                        .foregroundStyle(ERColors.dimText)
                }
            }
            .alert("Report Content", isPresented: $showReportConfirmation) {
                Button("Report & Hide", role: .destructive) {
                    withAnimation {
                        isReported = true
                    }
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Flag this AI-generated perspective as inappropriate or harmful? It will be hidden.")
            }

            // Headline
            Text(take.headline)
                .font(ERTypography.serifHeadline())
                .foregroundStyle(ERColors.primaryText)
                .lineSpacing(4)

            // Body
            Text(take.body)
                .font(ERTypography.body)
                .foregroundStyle(ERColors.secondaryText)
                .lineSpacing(6)
                .fontWeight(.light)
        }
    }

    private var reportedPlaceholder: some View {
        VStack(spacing: 16) {
            Image(systemName: "flag.fill")
                .font(.system(size: 24))
                .foregroundStyle(ERColors.dimText)

            Text("This perspective has been hidden.")
                .font(.system(size: 14))
                .foregroundStyle(ERColors.secondaryText)

            Text("If you're struggling, please reach out:")
                .font(.system(size: 12))
                .foregroundStyle(ERColors.dimText)

            VStack(spacing: 10) {
                ForEach(Array(SafetyService.crisisResources.enumerated()), id: \.offset) { _, resource in
                    Button {
                        openCrisisResource(resource)
                    } label: {
                        HStack(spacing: 8) {
                            Image(systemName: crisisResourceIcon(resource))
                                .font(.system(size: 12))
                                .foregroundStyle(ERColors.accentCool)
                            if resource.action == "link" {
                                Text(resource.name)
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundStyle(ERColors.accentCool)
                            } else {
                                Text("\(resource.name): \(resource.value)")
                                    .font(.system(size: 12, weight: .medium))
                                    .foregroundStyle(ERColors.primaryText)
                            }
                        }
                    }
                }
            }
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 40)
    }

    private func openCrisisResource(_ resource: SafetyService.CrisisResource) {
        let urlString: String
        switch resource.action {
        case "call":
            urlString = "tel:\(resource.value)"
        case "text":
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
