import SwiftUI
import GoogleMobileAds

struct AdBannerView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        VStack(spacing: 0) {
            Rectangle()
                .fill(ERColors.border)
                .frame(height: 1)

            ZStack(alignment: .topTrailing) {
                BannerAdRepresentable()
                    .frame(height: 50)
                    .background(ERColors.inputBackground)

                HStack(spacing: 6) {
                    Button {
                        appState.showPaywall = true
                    } label: {
                        Text("Remove")
                            .font(.system(size: 11, weight: .semibold))
                            .foregroundStyle(ERColors.accentGold)
                    }

                    Text("AD")
                        .font(.system(size: 8, weight: .regular))
                        .tracking(1)
                        .foregroundStyle(ERColors.dimText)
                }
                .padding(.trailing, 10)
                .padding(.top, 4)
            }
        }
    }
}

struct BannerAdRepresentable: UIViewRepresentable {
    #if DEBUG
    private let adUnitID = "ca-app-pub-3940256099942544/2435281174"
    #else
    private let adUnitID = "ca-app-pub-5300605522420042/1359255336"
    #endif

    func makeUIView(context: Context) -> GADBannerView {
        let bannerView = GADBannerView(adSize: GADAdSizeBanner)
        bannerView.adUnitID = adUnitID
        if let windowScene = UIApplication.shared.connectedScenes.first as? UIWindowScene,
           let rootVC = windowScene.windows.first?.rootViewController {
            bannerView.rootViewController = rootVC
        }
        bannerView.load(GADRequest())
        return bannerView
    }

    func updateUIView(_ uiView: GADBannerView, context: Context) {}
}
