import UIKit
import GoogleMobileAds

/// Self-contained UIView that wraps a GADBannerView.
/// Automatically finds the hosting view controller and loads the ad
/// when added to a window. Used by PlatformAdBanner.ios.kt via factory lambda.
class AdBannerWrapperView: UIView, GADBannerViewDelegate {
    private let bannerView: GADBannerView
    private var hasLoadedAd = false

    init(adUnitId: String) {
        bannerView = GADBannerView(adSize: GADAdSizeBanner)
        super.init(frame: .zero)
        bannerView.adUnitID = adUnitId
        bannerView.delegate = self
        bannerView.translatesAutoresizingMaskIntoConstraints = false
        addSubview(bannerView)
        NSLayoutConstraint.activate([
            bannerView.centerXAnchor.constraint(equalTo: centerXAnchor),
            bannerView.centerYAnchor.constraint(equalTo: centerYAnchor)
        ])
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override func didMoveToWindow() {
        super.didMoveToWindow()
        if window != nil && !hasLoadedAd {
            // Try responder chain first, fall back to root VC
            let vc = findViewController()
                ?? UIApplication.shared.connectedScenes
                    .compactMap { ($0 as? UIWindowScene)?.keyWindow?.rootViewController }
                    .first
            bannerView.rootViewController = vc
            NSLog("AdBanner: Loading ad with rootVC=\(String(describing: vc)), adUnitID=\(bannerView.adUnitID ?? "nil")")
            bannerView.load(GADRequest())
            hasLoadedAd = true
        }
    }

    // MARK: - GADBannerViewDelegate

    func bannerViewDidReceiveAd(_ bannerView: GADBannerView) {
        NSLog("AdBanner: Successfully received ad")
    }

    func bannerView(_ bannerView: GADBannerView, didFailToReceiveAdWithError error: Error) {
        NSLog("AdBanner: Failed to receive ad — \(error.localizedDescription)")
        // Allow retry on next window attachment
        hasLoadedAd = false
    }

    /// Walk the responder chain to find the hosting UIViewController.
    private func findViewController() -> UIViewController? {
        var responder: UIResponder? = self
        while let next = responder?.next {
            if let vc = next as? UIViewController { return vc }
            responder = next
        }
        return nil
    }
}
