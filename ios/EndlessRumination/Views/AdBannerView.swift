import SwiftUI

struct AdBannerView: View {
    var body: some View {
        HStack {
            Spacer()

            Text("mindfulness app \u{2014} download free")
                .font(.system(size: 11))
                .foregroundStyle(ERColors.dimText)
                .tracking(1)

            Text("Remove")
                .font(.system(size: 11, weight: .semibold))
                .foregroundStyle(ERColors.accentGold)

            Spacer()
        }
        .frame(height: 50)
        .background(ERColors.inputBackground)
        .overlay(alignment: .top) {
            Rectangle()
                .fill(ERColors.border)
                .frame(height: 1)
        }
        .overlay(alignment: .topTrailing) {
            Text("AD")
                .font(.system(size: 8, weight: .regular))
                .tracking(1)
                .foregroundStyle(ERColors.dimText)
                .padding(.trailing, 10)
                .padding(.top, 4)
        }
    }
}
