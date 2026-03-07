import SwiftUI

/// Shown on devices with insufficient RAM (<6 GB) to run the on-device AI model.
/// Prevents downloading the 2.1 GB model on devices that can't use it.
struct UnsupportedDeviceView: View {
    var body: some View {
        ZStack {
            ERColors.background.ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                Image(systemName: "exclamationmark.triangle.fill")
                    .font(.system(size: 44))
                    .foregroundStyle(ERColors.accentGold)
                    .padding(.bottom, 20)

                Text("Device Not Supported")
                    .font(ERTypography.serifHeadline())
                    .foregroundStyle(ERColors.primaryText)
                    .padding(.bottom, 12)

                Text("Endless Rumination requires an iPhone with at least 6 GB of RAM to run the on-device AI model.")
                    .font(.system(size: 14))
                    .foregroundStyle(ERColors.secondaryText)
                    .multilineTextAlignment(.center)
                    .lineSpacing(4)
                    .padding(.horizontal, 40)
                    .padding(.bottom, 16)

                Text(String(format: "Your device has %.1f GB of RAM.", DeviceCapability.ramGB))
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundStyle(ERColors.dimText)
                    .padding(.bottom, 24)

                Text("Supported devices include iPhone 12 Pro and later Pro models, all iPhone 14 and later models, and select iPads.")
                    .font(.system(size: 12))
                    .foregroundStyle(ERColors.dimText)
                    .multilineTextAlignment(.center)
                    .lineSpacing(3)
                    .padding(.horizontal, 40)

                Spacer()
            }
        }
    }
}
