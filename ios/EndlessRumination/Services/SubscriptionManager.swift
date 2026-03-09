import StoreKit
import os

private let logger = Logger(subsystem: "com.endlessrumination", category: "SubscriptionManager")

@MainActor
@Observable
final class SubscriptionManager {
    private(set) var proProduct: Product?
    private(set) var packProducts: [String: Product] = [:]
    private(set) var purchaseState: PurchaseState = .idle
    private(set) var isProSubscribed: Bool = false
    private(set) var ownedPackIDs: Set<String> = []
    private(set) var productsLoaded: Bool = false

    static let proMonthlyID = "com.endlessrumination.pro.monthly"

    static let packProductIDs: Set<String> = Set(VoicePack.all.map(\.productID))

    static let allProductIDs: Set<String> = Set([proMonthlyID]).union(packProductIDs)

    private var updateListenerTask: Task<Void, Never>?

    enum PurchaseState {
        case idle
        case purchasing
        case purchased
        case failed(String)
    }

    func start() async {
        listenForTransactionUpdates()
        await loadProducts()
        await checkCurrentEntitlements()
    }

    // MARK: - Pro Purchase

    func purchase() async {
        guard let product = proProduct else { return }
        purchaseState = .purchasing

        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try checkVerified(verification)
                await transaction.finish()
                isProSubscribed = true
                purchaseState = .purchased

            case .userCancelled:
                purchaseState = .idle

            case .pending:
                purchaseState = .idle

            @unknown default:
                purchaseState = .idle
            }
        } catch {
            purchaseState = .failed(error.localizedDescription)
        }
    }

    // MARK: - Pack Purchase

    func purchasePack(_ productID: String) async -> Bool {
        guard let product = packProducts[productID] else { return false }
        purchaseState = .purchasing

        do {
            let result = try await product.purchase()
            switch result {
            case .success(let verification):
                let transaction = try checkVerified(verification)
                await transaction.finish()
                ownedPackIDs.insert(productID)
                purchaseState = .purchased
                return true

            case .userCancelled, .pending:
                purchaseState = .idle
                return false

            @unknown default:
                purchaseState = .idle
                return false
            }
        } catch {
            purchaseState = .failed(error.localizedDescription)
            return false
        }
    }

    // MARK: - Pack Helpers

    func isPackOwned(_ productID: String) -> Bool {
        ownedPackIDs.contains(productID)
    }

    var ownedPackVoiceIndices: [Int] {
        VoicePack.all
            .filter { ownedPackIDs.contains($0.productID) }
            .flatMap(\.voiceIndices)
    }

    #if DEBUG
    /// Toggle pack ownership for testing without IAP sandbox.
    func debugTogglePack(_ productID: String) {
        if ownedPackIDs.contains(productID) {
            ownedPackIDs.remove(productID)
        } else {
            ownedPackIDs.insert(productID)
        }
    }
    #endif

    // MARK: - Restore

    func restorePurchases() async {
        try? await AppStore.sync()
        await checkCurrentEntitlements()
    }

    // MARK: - Private

    /// Locale-formatted pack price fallback derived from the user's locale.
    /// Used when ASC hasn't returned pack products yet (e.g., missing review screenshots).
    var fallbackPackPrice: String {
        let formatter = NumberFormatter()
        formatter.numberStyle = .currency
        formatter.locale = Locale.current
        return formatter.string(from: 4.99 as NSNumber) ?? "4.99"
    }

    /// Display price for a pack — real StoreKit price if available, locale-formatted fallback otherwise.
    func packDisplayPrice(_ productID: String) -> String {
        packProducts[productID]?.displayPrice ?? fallbackPackPrice
    }

    private func loadProducts() async {
        logger.info("Fetching \(Self.allProductIDs.count) product IDs: \(Self.allProductIDs.sorted().joined(separator: ", "))")
        do {
            let products = try await Product.products(for: Self.allProductIDs)
            logger.info("StoreKit returned \(products.count) products: \(products.map(\.id).sorted().joined(separator: ", "))")
            for product in products {
                if product.id == Self.proMonthlyID {
                    proProduct = product
                } else if Self.packProductIDs.contains(product.id) {
                    packProducts[product.id] = product
                }
            }
            let missingPacks = Self.packProductIDs.subtracting(Set(packProducts.keys))
            if !missingPacks.isEmpty {
                logger.warning("Pack products not returned by StoreKit (likely missing metadata in ASC): \(missingPacks.sorted().joined(separator: ", "))")
            }
        } catch {
            logger.error("Product fetch failed: \(error.localizedDescription)")
        }
        productsLoaded = true
    }

    private func checkCurrentEntitlements() async {
        var hasProEntitlement = false
        var ownedPacks: Set<String> = []

        for await result in Transaction.currentEntitlements {
            if case .verified(let transaction) = result,
               transaction.revocationDate == nil {
                if transaction.productID == Self.proMonthlyID {
                    hasProEntitlement = true
                } else if Self.packProductIDs.contains(transaction.productID) {
                    ownedPacks.insert(transaction.productID)
                }
            }
        }

        isProSubscribed = hasProEntitlement
        ownedPackIDs = ownedPacks
    }

    private func listenForTransactionUpdates() {
        updateListenerTask = Task.detached { [weak self] in
            for await result in Transaction.updates {
                if case .verified(let transaction) = result {
                    await transaction.finish()
                    await self?.checkCurrentEntitlements()
                }
            }
        }
    }

    private func checkVerified(_ result: VerificationResult<Transaction>) throws -> Transaction {
        switch result {
        case .unverified(_, let error):
            throw error
        case .verified(let transaction):
            return transaction
        }
    }
}
