import StoreKit
import Shared

/// Swift bridge for StoreKit 2, conforming to the Kotlin StoreKitBridgeProtocol.
/// Wraps Swift async/await StoreKit 2 APIs into completion-handler-based calls
/// that Kotlin/Native can invoke.
class StoreKitBridge: StoreKitBridgeProtocol {
    private var products: [String: Product] = [:]
    private var transactionListener: Task<Void, Never>?
    private var entitlementCallback: ((KotlinBoolean, Set<String>) -> Void)?

    func initialize() {
        // Listen for transaction updates (renewals, refunds, etc.)
        transactionListener = Task.detached { [weak self] in
            for await result in Transaction.updates {
                if case .verified(let transaction) = result {
                    await transaction.finish()
                    self?.checkEntitlements()
                }
            }
        }
        // Check existing entitlements on launch
        checkEntitlements()
    }

    func setEntitlementCallback(callback: @escaping (KotlinBoolean, Set<String>) -> Void) {
        self.entitlementCallback = callback
    }

    func loadProducts(
        productIds: [String],
        completion: @escaping ([String: String]?, String?) -> Void
    ) {
        Task {
            do {
                let storeProducts = try await Product.products(for: Set(productIds))
                var prices: [String: String] = [:]
                for product in storeProducts {
                    self.products[product.id] = product
                    prices[product.id] = product.displayPrice
                }
                completion(prices, nil)
            } catch {
                completion(nil, error.localizedDescription)
            }
        }
    }

    func purchase(
        productId: String,
        completion: @escaping (KotlinBoolean, String?, String?) -> Void
    ) {
        guard let product = products[productId] else {
            completion(false, nil, "Product not found: \(productId)")
            return
        }

        Task {
            do {
                let result = try await product.purchase()
                switch result {
                case .success(let verification):
                    switch verification {
                    case .verified(let transaction):
                        await transaction.finish()
                        self.checkEntitlements()
                        completion(true, String(transaction.id), nil)
                    case .unverified(_, let error):
                        completion(false, nil, "Verification failed: \(error.localizedDescription)")
                    }
                case .userCancelled:
                    completion(false, nil, "cancelled")
                case .pending:
                    completion(false, nil, "pending")
                @unknown default:
                    completion(false, nil, "Unknown result")
                }
            } catch {
                completion(false, nil, error.localizedDescription)
            }
        }
    }

    func restorePurchases(
        completion: @escaping @Sendable (KotlinBoolean, Set<String>, String?) -> Void
    ) {
        Task {
            do {
                try await AppStore.sync()
                var isPro = false
                var ownedPacks = Set<String>()

                for await result in Transaction.currentEntitlements {
                    if case .verified(let transaction) = result {
                        if transaction.revocationDate == nil {
                            if transaction.productID == "com.endlessrumination.pro.monthly" {
                                isPro = true
                            } else {
                                ownedPacks.insert(transaction.productID)
                            }
                        }
                    }
                }

                self.checkEntitlements()
                completion(KotlinBoolean(value: isPro), ownedPacks, nil)
            } catch {
                completion(false, Set(), error.localizedDescription)
            }
        }
    }

    /// Lightweight entitlement check — reads cached Transaction.currentEntitlements
    /// WITHOUT calling AppStore.sync(), so no Apple ID prompt is triggered.
    func checkEntitlementsOnly(
        completion: @escaping @Sendable (KotlinBoolean, Set<String>, String?) -> Void
    ) {
        Task {
            var isPro = false
            var ownedPacks = Set<String>()

            for await result in Transaction.currentEntitlements {
                if case .verified(let transaction) = result {
                    if transaction.revocationDate == nil {
                        if transaction.productID == "com.endlessrumination.pro.monthly" {
                            isPro = true
                        } else {
                            ownedPacks.insert(transaction.productID)
                        }
                    }
                }
            }

            completion(KotlinBoolean(value: isPro), ownedPacks, nil)
        }
    }

    private func checkEntitlements() {
        Task {
            var isPro = false
            var ownedPacks = Set<String>()

            for await result in Transaction.currentEntitlements {
                if case .verified(let transaction) = result {
                    if transaction.revocationDate == nil {
                        if transaction.productID == "com.endlessrumination.pro.monthly" {
                            isPro = true
                        } else {
                            ownedPacks.insert(transaction.productID)
                        }
                    }
                }
            }

            entitlementCallback?(KotlinBoolean(value: isPro), ownedPacks)
        }
    }

    deinit {
        transactionListener?.cancel()
    }
}
