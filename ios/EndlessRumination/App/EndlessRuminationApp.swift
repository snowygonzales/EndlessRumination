import SwiftUI

@main
struct EndlessRuminationApp: App {
    @State private var appState = AppState()
    @State private var subscriptionManager = SubscriptionManager()

    var body: some Scene {
        WindowGroup {
            Group {
                if DeviceCapability.canRunModel {
                    ContentView()
                } else {
                    UnsupportedDeviceView()
                }
            }
                .environment(appState)
                .environment(subscriptionManager)
                .task {
                    appState.subscriptionManager = subscriptionManager
                    await subscriptionManager.start()

                    // Only start model download on capable devices
                    if DeviceCapability.canRunModel {
                        appState.inferenceEngine.startLoading()
                    }
                }
                .preferredColorScheme(.dark)
        }
    }
}

struct ContentView: View {
    @Environment(AppState.self) private var appState
    @Environment(SubscriptionManager.self) private var subscriptionManager

    var body: some View {
        @Bindable var state = appState

        ZStack {
            ERColors.background.ignoresSafeArea()

            switch appState.currentScreen {
            case .splash:
                SplashView()
                    .transition(.opacity)
            case .input:
                ProblemInputView()
                    .transition(.move(edge: .trailing))
            case .loading:
                LoadingView()
                    .transition(.opacity)
            case .takes:
                TakesView()
                    .transition(.opacity)
            }

            // One-time onboarding overlay (shown after first "Begin" tap)
            if appState.showOnboarding && appState.currentScreen == .input {
                OnboardingView()
            }

            // AI consent dialog (shown before first submission)
            if appState.showAIConsent {
                AIConsentView()
            }
        }
        .animation(.easeInOut(duration: 0.35), value: appState.currentScreen)
        .sheet(isPresented: $state.showPaywall) {
            ProUpgradeView()
                .environment(appState)
                .environment(subscriptionManager)
        }
        .sheet(isPresented: $state.showShop) {
            ShopView()
                .environment(appState)
                .environment(subscriptionManager)
        }
    }
}
