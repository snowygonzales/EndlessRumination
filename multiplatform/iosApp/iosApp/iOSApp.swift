import SwiftUI
import Shared

@main
struct iOSApp: App {
    init() {
        // Set up StoreKit 2 bridge for Kotlin billing service
        BillingService.companion.storeKitBridge = StoreKitBridge()
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
        }
    }
}
