import StoreKit

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

    // MARK: - Restore

    func restorePurchases() async {
        try? await AppStore.sync()
        await checkCurrentEntitlements()
    }

    // MARK: - Private

    private func loadProducts() async {
        do {
            let products = try await Product.products(for: Self.allProductIDs)
            for product in products {
                if product.id == Self.proMonthlyID {
                    proProduct = product
                } else if Self.packProductIDs.contains(product.id) {
                    packProducts[product.id] = product
                }
            }
        } catch {
            // Product fetch failed — user stays on free tier
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
