import SwiftUI

struct InstructionOverlayView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        ZStack {
            Color(hex: 0x0A0A0C).opacity(0.7)

            VStack(spacing: 0) {
                Spacer()

                VStack(spacing: 12) {
                    Text("\u{2191}")
                        .font(.system(size: 36))
                        .opacity(0.6)
                        .modifier(BobModifier())

                    Text("SWIPE UP FOR NEXT TAKE")
                        .font(.system(size: 14))
                        .tracking(2)
                        .foregroundStyle(ERColors.secondaryText)

                    Text("Each perspective disappears forever")
                        .font(.system(size: 11))
                        .foregroundStyle(ERColors.dimText)
                        .padding(.top, 4)

                    Text("Free: 10 takes/day \u{00B7} Pro: unlimited")
                        .font(.system(size: 11))
                        .foregroundStyle(ERColors.accentGold)
                        .padding(.top, 12)
                }

                Spacer()
            }
        }
        .contentShape(Rectangle())
        .onTapGesture {
            appState.showInstructionOverlay = false
        }
    }
}
