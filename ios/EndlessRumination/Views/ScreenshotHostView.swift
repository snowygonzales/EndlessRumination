#if DEBUG
import SwiftUI

// MARK: - Screenshot Mode Detection

enum ScreenshotScreen: String {
    case splash
    case input
    case inputPro = "input-pro"
    case takes
    case takes2 = "takes-2"
    case takes3 = "takes-3"
    case takes4 = "takes-4"
    case takesPro = "takes-pro"
    case shop
    case paywall
    case packStrategists = "pack-strategists"
    case packRevolutionaries = "pack-revolutionaries"
    case packPhilosophers = "pack-philosophers"
    case packCreators = "pack-creators"
}

enum ScreenshotMode {
    static var activeScreen: ScreenshotScreen? {
        let args = ProcessInfo.processInfo.arguments
        guard let index = args.firstIndex(of: "-screenshot-screen"),
              index + 1 < args.count,
              let screen = ScreenshotScreen(rawValue: args[index + 1]) else {
            return nil
        }
        return screen
    }

    static var isActive: Bool { activeScreen != nil }
}

// MARK: - Screenshot Host View

/// Renders any screen with mock data for App Store screenshot capture.
/// Usage: launch with `-screenshot-screen <screen-name>` argument.
@MainActor
struct ScreenshotHostView: View {
    let screen: ScreenshotScreen
    @State private var appState = AppState()
    @State private var subscriptionManager = SubscriptionManager()

    var body: some View {
        ZStack {
            ERColors.background.ignoresSafeArea()

            Group {
                switch screen {
                case .splash:
                    SplashView()

                case .input:
                    setupInputView(pro: false)

                case .inputPro:
                    setupInputView(pro: true)

                case .takes, .takes2, .takes3, .takes4:
                    setupTakesView(pro: false)

                case .takesPro:
                    setupTakesView(pro: true)

                case .shop:
                    ShopView()

                case .paywall:
                    ProUpgradeView()

                case .packStrategists:
                    packDetailView(id: "strategists")

                case .packRevolutionaries:
                    packDetailView(id: "revolutionaries")

                case .packPhilosophers:
                    packDetailView(id: "philosophers")

                case .packCreators:
                    packDetailView(id: "creators")
                }
            }
        }
        .environment(appState)
        .environment(subscriptionManager)
        .preferredColorScheme(.dark)
        .onAppear {
            setupMockState()
        }
    }

    // MARK: - Mock State Setup

    private func setupMockState() {
        appState.showOnboarding = false
        appState.showAIConsent = false
        appState.showInstructionOverlay = false

        switch screen {
        case .input, .inputPro:
            appState.currentScreen = .input
            appState.problemText = "I keep replaying a conversation I had with my boss yesterday where I completely froze when asked about the project timeline and now I think everyone thinks I am incompetent"
            if screen == .inputPro {
                appState.subscriptionTier = .pro
            }

        case .takes, .takes2, .takes3, .takes4, .takesPro:
            appState.currentScreen = .takes
            if screen == .takesPro {
                appState.subscriptionTier = .pro
            }
            appState.takes = Self.mockTakes
            switch screen {
            case .takes2: appState.currentTakeIndex = 1
            case .takes3: appState.currentTakeIndex = 2
            case .takes4: appState.currentTakeIndex = 3
            default: appState.currentTakeIndex = 0
            }

        case .shop:
            appState.currentScreen = .input // underlying screen doesn't matter

        case .paywall:
            appState.currentScreen = .input

        default:
            break
        }
    }

    // MARK: - View Builders

    private func setupInputView(pro: Bool) -> some View {
        ProblemInputView()
    }

    private func setupTakesView(pro: Bool) -> some View {
        TakesView()
    }

    private func packDetailView(id: String) -> some View {
        let pack = VoicePack.all.first { $0.id == id } ?? VoicePack.all[0]
        return NavigationStack {
            PackDetailView(pack: pack)
        }
    }

    // MARK: - Mock Takes

    static let mockTakes: [Take] = [
        Take(
            lensIndex: 0, // The Comedian
            headline: "A Fresh Perspective",
            body: "OK so let me get this straight -- your boss asked you a question, your brain went on a coffee break, and now you're convinced the entire office has formed a secret committee called \"People Who Think You're Incompetent\"? That's not what happened. What happened is you had a human moment in front of other humans. I guarantee at least three people in that room were just thinking about lunch."
        ),
        Take(
            lensIndex: 1, // The Stoic
            headline: "Consider This",
            body: "You cannot control the words that did not come. You cannot control the judgments others may or may not form. What remains in your power is this: your response to this moment, and the preparation you bring to the next. The truly incompetent person does not lose sleep over competence -- your very concern is evidence against your fear."
        ),
        Take(
            lensIndex: 9, // The Therapist
            headline: "A New Take",
            body: "I'm noticing a pattern here -- you're engaging in what we call mind-reading, one of the most common cognitive distortions. You froze in one moment, and your brain filled in an entire narrative about what \"everyone\" thinks. But here's a powerful question to sit with: if a colleague froze in the same situation, would you conclude they were incompetent? Or would you barely remember it by tomorrow?"
        ),
        Take(
            lensIndex: 19, // Your Dog
            headline: "Something to Think About",
            body: "HEY HEY HEY you seem really sad and I don't understand all the words but LISTEN have you tried going outside?? Outside is SO GOOD. Also I noticed you haven't had a snack in a while and that's probably part of the problem. When I mess up and knock over the trash can nobody remembers the next day!! Let's go for a WALK and everything will be better I PROMISE."
        ),
        Take(
            lensIndex: 14, // Future You
            headline: "Here's Another Look",
            body: "Oh this. I barely remember this -- you'll have to remind me of the details. I think there was a meeting where something awkward happened? It's genuinely funny to me now that we spent three days replaying those fifteen seconds. What I remember more clearly is what came after: we got better at handling pressure, and that project actually turned out fine."
        ),
    ]
}
#endif
