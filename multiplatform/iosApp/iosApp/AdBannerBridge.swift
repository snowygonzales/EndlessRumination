import UIKit
import GoogleMobileAds

/// Self-contained UIView that wraps a GADBannerView.
/// Automatically finds the hosting view controller and loads the ad
/// when added to a window. Used by PlatformAdBanner.ios.kt via factory lambda.
class AdBannerWrapperView: UIView {
    private let bannerView: GADBannerView
    private var hasLoadedAd = false

    init(adUnitId: String) {
        bannerView = GADBannerView(adSize: GADAdSizeBanner)
        super.init(frame: .zero)
        bannerView.adUnitID = adUnitId
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
            bannerView.rootViewController = findViewController()
            bannerView.load(GADRequest())
            hasLoadedAd = true
        }
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
