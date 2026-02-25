import SwiftUI

struct PackDetailView: View {
    let pack: VoicePack
    @Environment(SubscriptionManager.self) private var subscriptionManager

    private var isOwned: Bool {
        subscriptionManager.isPackOwned(pack.productID)
    }

    private var priceText: String {
        subscriptionManager.packProducts[pack.productID]?.displayPrice ?? "$4.99"
    }

    var body: some View {
        ZStack {
            ERColors.background.ignoresSafeArea()

            VStack(spacing: 0) {
                ScrollView {
                    VStack(spacing: 0) {
                        // Pack header
                        packHeader

                        // Voices
                        VStack(spacing: 10) {
                            ForEach(pack.voices) { voice in
                                VoicePreviewCard(voice: voice, packColor: pack.color)
                            }
                        }
                        .padding(.horizontal, 24)
                        .padding(.bottom, 20)
                    }
                }

                // Purchase bar
                purchaseBar
            }
        }
        .navigationBarTitleDisplayMode(.inline)
        .toolbar {
            ToolbarItem(placement: .principal) {
                Text("\(pack.voices.count) VOICES")
                    .font(.system(size: 10, weight: .medium, design: .monospaced))
                    .tracking(2)
                    .foregroundStyle(ERColors.dimText)
            }
        }
        .toolbarBackground(ERColors.background, for: .navigationBar)
    }

    // MARK: - Pack Header

    private var packHeader: some View {
        VStack(spacing: 4) {
            Text(pack.icon)
                .font(.system(size: 44))
                .padding(.bottom, 6)

            Text(pack.name)
                .font(ERTypography.serifTitle())
                .foregroundStyle(ERColors.primaryText)

            Text(pack.subtitle)
                .font(.system(size: 12))
                .foregroundStyle(ERColors.secondaryText)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, 24)
    }

    // MARK: - Purchase Bar

    private var purchaseBar: some View {
        VStack(spacing: 0) {
            Divider()
                .overlay(Color.white.opacity(0.04))

            Button {
                Task { await subscriptionManager.purchasePack(pack.productID) }
            } label: {
                Group {
                    if subscriptionManager.purchaseState.isPurchasing {
                        ProgressView()
                            .tint(.white)
                    } else if isOwned {
                        Text("\u{2713} Purchased \u{2014} Voices Active")
                            .font(.system(size: 15, weight: .bold))
                    } else {
                        Text("Unlock \(pack.voices.count) Voices \u{2014} \(priceText)")
                            .font(.system(size: 15, weight: .bold))
                    }
                }
                .frame(maxWidth: .infinity)
                .padding(.vertical, 16)
                .foregroundStyle(isOwned ? ERColors.accentGreen : .white)
                .background(isOwned ? AnyShapeStyle(ERColors.accentGreen.opacity(0.12)) : AnyShapeStyle(LinearGradient(colors: [pack.color, pack.color.opacity(0.6)], startPoint: .topLeading, endPoint: .bottomTrailing)))
                .clipShape(RoundedRectangle(cornerRadius: 14))
            }
            .disabled(isOwned || subscriptionManager.purchaseState.isPurchasing)
            .padding(.horizontal, 24)
            .padding(.vertical, 12)

            // Error
            if case .failed(let message) = subscriptionManager.purchaseState {
                Text(message)
                    .font(.system(size: 12))
                    .foregroundStyle(ERColors.accentRed)
                    .padding(.horizontal, 24)
                    .padding(.bottom, 8)
            }
        }
        .background(ERColors.background)
    }
}

// MARK: - Voice Preview Card

private struct VoicePreviewCard: View {
    let voice: VoicePackVoice
    let packColor: Color
    @State private var isExpanded = false

    var body: some View {
        VStack(spacing: 0) {
            // Header row
            Button {
                withAnimation(.easeInOut(duration: 0.25)) {
                    isExpanded.toggle()
                }
            } label: {
                HStack(spacing: 12) {
                    Text(voice.emoji)
                        .font(.system(size: 24))

                    VStack(alignment: .leading, spacing: 1) {
                        Text(voice.name)
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundStyle(ERColors.primaryText)
                        Text(voice.years)
                            .font(.system(size: 11))
                            .foregroundStyle(ERColors.dimText)
                    }

                    Spacer()

                    Image(systemName: "chevron.down")
                        .font(.system(size: 11))
                        .foregroundStyle(packColor)
                        .rotationEffect(.degrees(isExpanded ? 180 : 0))
                }
                .padding(14)
            }
            .buttonStyle(.plain)

            // Expanded content
            if isExpanded {
                VStack(alignment: .leading, spacing: 10) {
                    Divider()
                        .overlay(Color.white.opacity(0.04))

                    Text(voice.desc)
                        .font(.system(size: 12))
                        .foregroundStyle(ERColors.secondaryText)
                        .lineSpacing(4)

                    // Sample take
                    VStack(alignment: .leading, spacing: 8) {
                        Text("SAMPLE TAKE")
                            .font(.system(size: 10, weight: .medium, design: .monospaced))
                            .tracking(2)
                            .foregroundStyle(ERColors.dimText)

                        Text(voice.sampleHeadline)
                            .font(ERTypography.serifHeadline())
                            .foregroundStyle(ERColors.primaryText)
                            .lineSpacing(2)

                        Text(voice.sampleBody)
                            .font(.system(size: 11.5, weight: .light))
                            .foregroundStyle(ERColors.secondaryText)
                            .lineSpacing(5)
                    }
                    .padding(14)
                    .background(Color.white.opacity(0.02))
                    .clipShape(RoundedRectangle(cornerRadius: 12))
                }
                .padding(.horizontal, 14)
                .padding(.bottom, 14)
                .transition(.opacity)
            }
        }
        .background(Color.white.opacity(0.03))
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .overlay(
            RoundedRectangle(cornerRadius: 16)
                .stroke(Color.white.opacity(0.04), lineWidth: 1)
        )
    }
}
