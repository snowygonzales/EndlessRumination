import StoreKit

@MainActor
@Observable
final class SubscriptionManager {
    private(set) var proProduct: Product?
    private(set) var purchaseState: PurchaseState = .idle
    private(set) var isProSubscribed: Bool = false

    static let proMonthlyID = "com.endlessrumination.pro.monthly"

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

    // MARK: - Purchase

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

    // MARK: - Restore

    func restorePurchases() async {
        try? await AppStore.sync()
        await checkCurrentEntitlements()
    }

    // MARK: - Private

    private func loadProducts() async {
        do {
            let products = try await Product.products(for: [Self.proMonthlyID])
            proProduct = products.first
        } catch {
            // Product fetch failed — user stays on free tier
        }
    }

    private func checkCurrentEntitlements() async {
        var hasProEntitlement = false
        for await result in Transaction.currentEntitlements {
            if case .verified(let transaction) = result,
               transaction.productID == Self.proMonthlyID,
               transaction.revocationDate == nil {
                hasProEntitlement = true
                break
            }
        }
        isProSubscribed = hasProEntitlement
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
