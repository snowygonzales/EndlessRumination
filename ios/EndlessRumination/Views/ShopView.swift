import SwiftUI

struct ShopView: View {
    @Environment(AppState.self) private var appState
    @Environment(SubscriptionManager.self) private var subscriptionManager
    @Environment(\.dismiss) private var dismiss
    @State private var selectedPack: VoicePack?
    @State private var isRestoring = false

    var body: some View {
        NavigationStack {
            ZStack {
                ERColors.background.ignoresSafeArea()

                ScrollView {
                    VStack(spacing: 20) {
                        // Pro subscription card
                        if !appState.isPro {
                            proCard
                        }

                        // Free perspectives
                        freeLensesSection

                        // Voice packs
                        voicePacksSection

                        // Coming soon
                        comingSoonCard

                        // Restore purchases
                        restoreButton

                        Spacer(minLength: 40)
                    }
                    .padding(.horizontal, 24)
                    .padding(.top, 12)
                }
            }
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .principal) {
                    Text("PERSPECTIVE SHOP")
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .tracking(2)
                        .foregroundStyle(ERColors.dimText)
                }
                ToolbarItem(placement: .navigationBarLeading) {
                    Button {
                        dismiss()
                    } label: {
                        Text("\u{2190} Back")
                            .font(.system(size: 14))
                            .foregroundStyle(ERColors.secondaryText)
                    }
                }
            }
            .toolbarBackground(ERColors.background, for: .navigationBar)
            .navigationDestination(item: $selectedPack) { pack in
                PackDetailView(pack: pack)
            }
        }
    }

    // MARK: - Pro Card

    private var proCard: some View {
        Button {
            dismiss()
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                appState.showPaywall = true
            }
        } label: {
            VStack(alignment: .leading, spacing: 0) {
                // Shimmer top bar
                Rectangle()
                    .fill(LinearGradient(colors: [.clear, ERColors.accentGold.opacity(0.4), .clear], startPoint: .leading, endPoint: .trailing))
                    .frame(height: 2)

                HStack {
                    VStack(alignment: .leading, spacing: 6) {
                        HStack(spacing: 8) {
                            Text("\u{221e}")
                                .font(.system(size: 20))
                            Text("Go Pro")
                                .font(ERTypography.serifTitle())
                                .foregroundStyle(ERColors.titleGradient)
                        }
                        Text("No ads \u{00B7} Unlimited daily takes \u{00B7} Save history")
                            .font(.system(size: 12))
                            .foregroundStyle(ERColors.secondaryText)
                    }

                    Spacer()

                    Text(subscriptionManager.proProduct?.displayPrice ?? "$9.99")
                        .font(.system(size: 13, weight: .bold))
                        .foregroundStyle(ERColors.background)
                        .padding(.horizontal, 16)
                        .padding(.vertical, 10)
                        .background(ERColors.proGradient)
                        .clipShape(Capsule())
                }
                .padding(20)
            }
            .background(
                LinearGradient(colors: [Color(hex: 0x1A1510), Color(hex: 0x1A1A20), Color(hex: 0x15101A)], startPoint: .topLeading, endPoint: .bottomTrailing)
            )
            .clipShape(RoundedRectangle(cornerRadius: 20))
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(ERColors.accentGold.opacity(0.2), lineWidth: 1)
            )
        }
    }

    // MARK: - Free Lenses Section

    private var freeLensesSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            HStack {
                Text("Free Perspectives")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundStyle(ERColors.primaryText)
                Spacer()
                Text("\(Lens.freeLensCount) included")
                    .font(.system(size: 11))
                    .foregroundStyle(ERColors.dimText)
            }

            FlowLayout(spacing: 6) {
                ForEach(Lens.freeLenses) { lens in
                    HStack(spacing: 4) {
                        Text(lens.emoji)
                            .font(.system(size: 11))
                        Text(lens.name)
                            .font(.system(size: 11))
                            .foregroundStyle(ERColors.secondaryText)
                    }
                    .padding(.horizontal, 10)
                    .padding(.vertical, 4)
                    .background(Color.white.opacity(0.04))
                    .clipShape(Capsule())
                }
            }
        }
    }

    // MARK: - Voice Packs Section

    private var voicePacksSection: some View {
        VStack(alignment: .leading, spacing: 14) {
            Text("Voice Packs")
                .font(.system(size: 13, weight: .semibold))
                .foregroundStyle(ERColors.primaryText)

            ForEach(VoicePack.all) { pack in
                PackCardView(pack: pack, isOwned: subscriptionManager.isPackOwned(pack.productID)) {
                    selectedPack = pack
                }
            }
        }
    }

    // MARK: - Coming Soon

    private var comingSoonCard: some View {
        VStack(spacing: 6) {
            Text("COMING SOON")
                .font(.system(size: 11, weight: .medium, design: .monospaced))
                .tracking(2)
                .foregroundStyle(ERColors.dimText)
            Text("The Scientists \u{00B7} The Leaders \u{00B7} The Writers")
                .font(.system(size: 12))
                .foregroundStyle(ERColors.secondaryText)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 28)
    }

    // MARK: - Restore Purchases

    private var restoreButton: some View {
        Button {
            isRestoring = true
            Task {
                await subscriptionManager.restorePurchases()
                isRestoring = false
            }
        } label: {
            if isRestoring {
                ProgressView()
                    .tint(ERColors.secondaryText)
            } else {
                Text("Restore Purchases")
                    .font(.system(size: 13))
                    .foregroundStyle(ERColors.secondaryText)
            }
        }
        .frame(maxWidth: .infinity)
        .disabled(isRestoring)
    }
}

// MARK: - Pack Card

private struct PackCardView: View {
    let pack: VoicePack
    let isOwned: Bool
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(alignment: .leading, spacing: 12) {
                HStack(alignment: .top) {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(pack.icon)
                            .font(.system(size: 28))
                            .padding(.bottom, 4)
                        Text(pack.name)
                            .font(ERTypography.serifHeadline())
                            .foregroundStyle(ERColors.primaryText)
                        Text(pack.subtitle)
                            .font(.system(size: 11))
                            .foregroundStyle(ERColors.secondaryText)
                    }

                    Spacer()

                    if isOwned {
                        Text("\u{2713} Owned")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(ERColors.accentGreen)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 6)
                            .background(ERColors.accentGreen.opacity(0.15))
                            .clipShape(Capsule())
                    } else {
                        Text("$4.99")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(pack.color)
                            .padding(.horizontal, 14)
                            .padding(.vertical, 6)
                            .background(pack.color.opacity(0.15))
                            .clipShape(Capsule())
                    }
                }

                FlowLayout(spacing: 6) {
                    ForEach(pack.voices) { voice in
                        HStack(spacing: 4) {
                            Text(voice.emoji)
                                .font(.system(size: 11))
                            Text(voice.name)
                                .font(.system(size: 11))
                                .foregroundStyle(ERColors.secondaryText)
                        }
                        .padding(.horizontal, 8)
                        .padding(.vertical, 3)
                        .background(Color.white.opacity(0.04))
                        .clipShape(Capsule())
                    }
                }
            }
            .padding(18)
            .background(pack.bgGradient)
            .clipShape(RoundedRectangle(cornerRadius: 20))
            .overlay(
                RoundedRectangle(cornerRadius: 20)
                    .stroke(pack.color.opacity(0.15), lineWidth: 1)
            )
        }
        .buttonStyle(.plain)
    }
}

// MARK: - Flow Layout

struct FlowLayout: Layout {
    var spacing: CGFloat = 6

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let result = arrange(proposal: proposal, subviews: subviews)
        return result.size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let result = arrange(proposal: proposal, subviews: subviews)
        for (index, position) in result.positions.enumerated() {
            subviews[index].place(at: CGPoint(x: bounds.minX + position.x, y: bounds.minY + position.y), proposal: .unspecified)
        }
    }

    private func arrange(proposal: ProposedViewSize, subviews: Subviews) -> (size: CGSize, positions: [CGPoint]) {
        let maxWidth = proposal.width ?? .infinity
        var positions: [CGPoint] = []
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0
        var totalHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > maxWidth && x > 0 {
                x = 0
                y += rowHeight + spacing
                rowHeight = 0
            }
            positions.append(CGPoint(x: x, y: y))
            rowHeight = max(rowHeight, size.height)
            x += size.width + spacing
            totalHeight = y + rowHeight
        }

        return (CGSize(width: maxWidth, height: totalHeight), positions)
    }
}

// MARK: - VoicePack Hashable conformance for navigation

extension VoicePack: Hashable {
    static func == (lhs: VoicePack, rhs: VoicePack) -> Bool {
        lhs.id == rhs.id
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(id)
    }
}
