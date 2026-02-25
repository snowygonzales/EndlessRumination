import SwiftUI

@main
struct EndlessRuminationApp: App {
    @State private var appState = AppState()
    @State private var subscriptionManager = SubscriptionManager()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environment(appState)
                .environment(subscriptionManager)
                .task {
                    appState.subscriptionManager = subscriptionManager
                    await subscriptionManager.start()
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
        }
        .animation(.easeInOut(duration: 0.35), value: appState.currentScreen)
        .sheet(isPresented: $state.showPaywall) {
            ProUpgradeView()
                .environment(appState)
                .environment(subscriptionManager)
        }
    }
}
