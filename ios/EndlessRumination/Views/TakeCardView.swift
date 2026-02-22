import SwiftUI

struct TakeCardView: View {
    let take: Take
    let lens: Lens

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Lens badge
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

            // Headline
            Text(take.headline)
                .font(ERTypography.serifHeadline())
                .foregroundStyle(ERColors.primaryText)
                .lineSpacing(4)

            // Body
            ScrollView {
                Text(take.body)
                    .font(ERTypography.body)
                    .foregroundStyle(ERColors.secondaryText)
                    .lineSpacing(6)
                    .fontWeight(.light)
            }
        }
    }
}
