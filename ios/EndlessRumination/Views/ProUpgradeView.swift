import SwiftUI
import StoreKit

struct ProUpgradeView: View {
    @Environment(AppState.self) private var appState
    @Environment(SubscriptionManager.self) private var subscriptionManager
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        ZStack {
            ERColors.background.ignoresSafeArea()

            VStack(spacing: 0) {
                // Dismiss button
                HStack {
                    Spacer()
                    Button {
                        dismiss()
                    } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 16, weight: .medium))
                            .foregroundStyle(ERColors.secondaryText)
                            .frame(width: 32, height: 32)
                            .background(ERColors.inputBackground)
                            .clipShape(Circle())
                    }
                }
                .padding(.horizontal, 24)
                .padding(.top, 16)

                Spacer().frame(height: 32)

                // Title
                Text("Go Pro")
                    .font(ERTypography.serifLargeTitle())
                    .foregroundStyle(ERColors.accentGold)

                Spacer().frame(height: 8)

                Text("Unlock the full experience")
                    .font(.system(size: 15))
                    .foregroundStyle(ERColors.secondaryText)

                Spacer().frame(height: 40)

                // Benefits
                VStack(alignment: .leading, spacing: 20) {
                    benefitRow(icon: "sparkles", text: "All 20 perspectives on every problem")
                    benefitRow(icon: "brain.head.profile", text: "Premium AI for deeper, wiser takes")
                    benefitRow(icon: "arrow.up.arrow.down", text: "Revisit takes -- swipe back anytime")
                }
                .padding(.horizontal, 32)

                Spacer().frame(height: 48)

                // Subscribe button
                Button {
                    Task { await subscriptionManager.purchase() }
                } label: {
                    Group {
                        if subscriptionManager.purchaseState.isPurchasing {
                            ProgressView()
                                .tint(.white)
                        } else {
                            Text("Subscribe for \(priceText)/month")
                                .font(.system(size: 17, weight: .semibold))
                        }
                    }
                    .frame(maxWidth: .infinity)
                    .padding(.vertical, 18)
                    .foregroundStyle(.white)
                    .background(ERColors.warmGradient)
                    .clipShape(RoundedRectangle(cornerRadius: 14))
                }
                .disabled(subscriptionManager.purchaseState.isPurchasing)
                .padding(.horizontal, 24)

                // Error message
                if case .failed(let message) = subscriptionManager.purchaseState {
                    Text(message)
                        .font(.system(size: 12))
                        .foregroundStyle(ERColors.accentRed)
                        .padding(.top, 8)
                        .padding(.horizontal, 24)
                }

                Spacer().frame(height: 16)

                // Restore
                Button {
                    Task { await subscriptionManager.restorePurchases() }
                } label: {
                    Text("Restore Purchases")
                        .font(.system(size: 14))
                        .foregroundStyle(ERColors.secondaryText)
                }

                Spacer()

                // Fine print + legal links
                VStack(spacing: 6) {
                    Text("Payment charged to your Apple ID at confirmation. Subscription auto-renews monthly unless cancelled at least 24 hours before the end of the current period. Manage in Settings \u{203A} Subscriptions.")
                        .font(.system(size: 10))
                        .foregroundStyle(ERColors.dimText)
                        .multilineTextAlignment(.center)
                        .lineSpacing(2)

                    HStack(spacing: 12) {
                        Link("Privacy Policy", destination: URL(string: "https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md")!)
                        Link("Terms of Service", destination: URL(string: "https://github.com/snowygonzales/EndlessRumination/blob/master/docs/terms-of-service.md")!)
                    }
                    .font(.system(size: 10))
                    .foregroundStyle(ERColors.accentCool)
                }
                .padding(.horizontal, 32)
                .padding(.bottom, 24)
            }
        }
        .onChange(of: subscriptionManager.isProSubscribed) { _, isPro in
            if isPro {
                dismiss()
            }
        }
    }

    // MARK: - Helpers

    private var priceText: String {
        subscriptionManager.proProduct?.displayPrice ?? "$9.99"
    }

    private func benefitRow(icon: String, text: String) -> some View {
        HStack(spacing: 14) {
            Image(systemName: icon)
                .font(.system(size: 18))
                .foregroundStyle(ERColors.accentGold)
                .frame(width: 28)

            Text(text)
                .font(.system(size: 15))
                .foregroundStyle(ERColors.primaryText)
        }
    }
}

// MARK: - PurchaseState helpers

extension SubscriptionManager.PurchaseState {
    var isPurchasing: Bool {
        if case .purchasing = self { return true }
        return false
    }
}
