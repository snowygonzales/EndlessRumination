import SwiftUI

struct TakeCardView: View {
    let take: Take
    @State private var showReportConfirmation = false

    private var display: (name: String, emoji: String, color: Color, bgColor: Color) {
        Lens.displayInfo(at: take.lensIndex)
    }

    var body: some View {
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
                Button("Report", role: .destructive) {
                    // Content flagged — in a full implementation this would send to backend
                }
                Button("Cancel", role: .cancel) {}
            } message: {
                Text("Flag this AI-generated perspective as inappropriate or harmful?")
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
}
