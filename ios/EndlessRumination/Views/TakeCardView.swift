import SwiftUI

struct TakeCardView: View {
    let take: Take

    private var display: (name: String, emoji: String, color: Color, bgColor: Color) {
        Lens.displayInfo(at: take.lensIndex)
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Lens badge + Wise indicator + Pack badge
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

                // Wise badge for Sonnet-powered takes (all pack voices are Sonnet)
                if take.wise || take.isPackVoice {
                    HStack(spacing: 4) {
                        Image(systemName: "sparkles")
                            .font(.system(size: 9))
                        Text("WISE")
                            .font(.system(size: 10, weight: .bold))
                            .tracking(1.5)
                    }
                    .foregroundStyle(ERColors.accentGold)
                    .padding(.horizontal, 10)
                    .padding(.vertical, 5)
                    .background(ERColors.accentGold.opacity(0.12))
                    .clipShape(Capsule())
                }

                // Pack name badge
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

            // Haiku model indicator for non-wise takes
            if !take.wise {
                Text("Quick take \u{00B7} Powered by Haiku")
                    .font(.system(size: 10))
                    .foregroundStyle(ERColors.dimText)
                    .padding(.top, 4)
            }
        }
    }
}
