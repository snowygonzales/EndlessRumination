import SwiftUI

/// Collapsible lens picker for Pro users. Shows toggleable capsules
/// organized by base perspectives and owned voice packs.
struct LensPickerView: View {
    @Environment(AppState.self) private var appState
    @Environment(SubscriptionManager.self) private var subscriptionManager

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            // Base perspectives
            lensSection(
                title: "Base Perspectives",
                indices: Array(0..<20)
            )

            // Owned voice pack sections
            ForEach(ownedPacks) { pack in
                lensSection(
                    title: pack.name,
                    indices: pack.voiceIndices
                )
            }
        }
        .padding(.vertical, 12)
    }

    // MARK: - Sections

    private func lensSection(title: String, indices: [Int]) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            // Header with Select All / Clear
            HStack {
                Text(title)
                    .font(.system(size: 11, weight: .semibold))
                    .foregroundStyle(ERColors.secondaryText)
                    .textCase(.uppercase)
                    .tracking(0.5)

                Spacer()

                let allSelected = indices.allSatisfy { appState.isLensSelected($0) }

                if allSelected {
                    Button {
                        appState.clearLenses(in: indices)
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    } label: {
                        Text("Clear")
                            .font(.system(size: 11))
                            .foregroundStyle(ERColors.dimText)
                    }
                } else {
                    Button {
                        appState.selectAllLenses(in: indices)
                        UIImpactFeedbackGenerator(style: .light).impactOccurred()
                    } label: {
                        Text("Select All")
                            .font(.system(size: 11))
                            .foregroundStyle(ERColors.accentCool)
                    }
                }
            }

            // Lens capsules
            FlowLayout(spacing: 6) {
                ForEach(indices, id: \.self) { index in
                    lensCapsule(index: index)
                }
            }
        }
    }

    // MARK: - Capsule

    private func lensCapsule(index: Int) -> some View {
        let info = Lens.displayInfo(at: index)
        let isSelected = appState.isLensSelected(index)
        let isLastSelected = appState.selectedLensCount <= 1 && isSelected

        return Button {
            if !isLastSelected {
                appState.toggleLens(index)
                UIImpactFeedbackGenerator(style: .light).impactOccurred(intensity: 0.5)
            }
        } label: {
            HStack(spacing: 4) {
                Text(info.emoji)
                    .font(.system(size: 11))
                Text(info.name)
                    .font(.system(size: 11))
                    .lineLimit(1)
            }
            .padding(.horizontal, 10)
            .padding(.vertical, 5)
            .foregroundStyle(isSelected ? ERColors.primaryText : ERColors.dimText)
            .background(
                isSelected
                    ? info.color.opacity(0.15)
                    : ERColors.inputBackground
            )
            .clipShape(Capsule())
            .overlay(
                Capsule()
                    .stroke(
                        isSelected ? info.color.opacity(0.3) : Color.clear,
                        lineWidth: 1
                    )
            )
        }
        .buttonStyle(.plain)
        .animation(.easeInOut(duration: 0.15), value: isSelected)
    }

    // MARK: - Helpers

    private var ownedPacks: [VoicePack] {
        VoicePack.all.filter { subscriptionManager.isPackOwned($0.productID) }
    }
}
