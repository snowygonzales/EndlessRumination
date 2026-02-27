import SwiftUI
import Shared
import GoogleMobileAds

@main
struct iOSApp: App {
    init() {
        // Initialize Google Mobile Ads SDK
        GADMobileAds.sharedInstance().start(completionHandler: nil)

        // Set up ad banner factory for Kotlin Compose to create native GADBannerView
        AdBannerProvider.shared.createBanner = {
            AdBannerWrapperView(adUnitId: "ca-app-pub-5300605522420042/1359255336")
        }

        // Set up StoreKit 2 bridge for Kotlin billing service
        BillingService.companion.storeKitBridge = StoreKitBridge()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
