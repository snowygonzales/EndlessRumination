import SwiftUI

struct TakeCardView: View {
    let take: Take
    let lens: Lens

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Lens badge + Wise indicator
            HStack(spacing: 8) {
                // Lens name badge
                HStack(spacing: 8) {
                    Text(lens.emoji)
                        .font(.system(size: 12))
                    Text(lens.name.uppercased())
                        .font(.system(size: 12, weight: .bold))
                        .tracking(2)
                        .foregroundStyle(lens.color)
                }
                .padding(.horizontal, 14)
                .padding(.vertical, 6)
                .background(lens.bgColor)
                .clipShape(Capsule())

                // Wise badge for Sonnet-powered takes
                if take.wise {
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
            }

            // Headline
            Text(take.headline)
                .font(ERTypography.serifHeadline())
                .foregroundStyle(ERColors.primaryText)
                .lineSpacing(4)

            // Body
            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
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
    }
}
