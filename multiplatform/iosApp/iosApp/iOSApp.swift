import SwiftUI
import Foundation
import Shared
import GoogleMobileAds

@main
struct iOSApp: App {
    init() {
        // Initialize Google Mobile Ads SDK
        GADMobileAds.sharedInstance().start(completionHandler: nil)

        #if DEBUG
        // Enable test ads on simulator and test devices
        GADMobileAds.sharedInstance().requestConfiguration.testDeviceIdentifiers = [
            GADSimulatorID  // Always include simulator
        ]
        NSLog("AdMob: Configured test device identifiers for DEBUG build")
        #endif

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
