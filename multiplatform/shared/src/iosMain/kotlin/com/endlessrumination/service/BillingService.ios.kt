package com.endlessrumination.service

import platform.Foundation.NSLog

/**
 * iOS StoreKit 2 billing implementation.
 *
 * StoreKit 2 uses Swift async/await which cannot be called directly from Kotlin/Native.
 * This implementation delegates to a Swift bridge class (StoreKitBridge) in iosApp/
 * that wraps the StoreKit 2 APIs with completion handlers callable from Kotlin.
 *
 * The bridge is set via `setStoreKitBridge()` from the iOS app's entry point.
 */
actual class BillingService actual constructor(
    private val callback: BillingCallback
) {
    private var _isPro = false
    private var _ownedPackIDs = mutableSetOf<String>()
    private var _proPrice: String? = null
    private var _packPrices = mutableMapOf<String, String>()
    private var lastReceiptPayload: ReceiptPayload? = null

    actual val isPro: Boolean get() = _isPro
    actual val ownedPackIDs: Set<String> get() = _ownedPackIDs.toSet()
    actual val proPrice: String? get() = _proPrice

    actual fun packPrice(productId: String): String? = _packPrices[productId]

    actual fun initialize() {
        val bridge = storeKitBridge
        if (bridge == null) {
            NSLog("BillingService: No StoreKit bridge set, running in stub mode")
            return
        }
        bridge.initialize()
        bridge.setEntitlementCallback { isPro, ownedPacks ->
            _isPro = isPro
            _ownedPackIDs.clear()
            _ownedPackIDs.addAll(ownedPacks)
            callback.onProStatusChanged(isPro)
            callback.onOwnedPacksChanged(_ownedPackIDs.toSet())
        }
    }

    actual fun dispose() {
        // StoreKit doesn't need explicit teardown
    }

    actual suspend fun loadProducts(): BillingResult {
        val bridge = storeKitBridge ?: return BillingResult.Success // Stub mode

        return kotlinx.coroutines.suspendCancellableCoroutine { cont ->
            bridge.loadProducts(BillingProductIds.ALL_IDS.toList()) { prices, error ->
                if (error != null) {
                    cont.resume(BillingResult.Error(error)) {}
                } else {
                    prices?.forEach { (id, price) ->
                        if (id == BillingProductIds.PRO_MONTHLY) {
                            _proPrice = price
                        } else {
                            _packPrices[id] = price
                        }
                    }
                    cont.resume(BillingResult.Success) {}
                }
            }
        }
    }

    actual suspend fun purchaseSubscription(
        productId: String,
        activityProvider: () -> Any?
    ): PurchaseResult {
        val bridge = storeKitBridge ?: return PurchaseResult.Error("No StoreKit bridge")
        callback.onPurchaseStateChanged(PurchaseUiState.PURCHASING)

        return kotlinx.coroutines.suspendCancellableCoroutine { cont ->
            bridge.purchase(productId) { success, transactionId, error ->
                if (success && transactionId != null) {
                    _isPro = true
                    callback.onProStatusChanged(true)
                    callback.onPurchaseStateChanged(PurchaseUiState.PURCHASED)
                    lastReceiptPayload = ReceiptPayload(
                        platform = "ios",
                        productId = productId,
                        purchaseToken = transactionId,
                        isSubscription = true
                    )
                    cont.resume(PurchaseResult.Success) {}
                } else if (error == "cancelled") {
                    callback.onPurchaseStateChanged(PurchaseUiState.IDLE)
                    cont.resume(PurchaseResult.Cancelled) {}
                } else {
                    callback.onPurchaseStateChanged(PurchaseUiState.FAILED)
                    cont.resume(PurchaseResult.Error(error ?: "Unknown error")) {}
                }
            }
        }
    }

    actual suspend fun purchaseOneTime(
        productId: String,
        activityProvider: () -> Any?
    ): PurchaseResult {
        val bridge = storeKitBridge ?: return PurchaseResult.Error("No StoreKit bridge")
        callback.onPurchaseStateChanged(PurchaseUiState.PURCHASING)

        return kotlinx.coroutines.suspendCancellableCoroutine { cont ->
            bridge.purchase(productId) { success, transactionId, error ->
                if (success && transactionId != null) {
                    _ownedPackIDs.add(productId)
                    callback.onOwnedPacksChanged(_ownedPackIDs.toSet())
                    callback.onPurchaseStateChanged(PurchaseUiState.PURCHASED)
                    lastReceiptPayload = ReceiptPayload(
                        platform = "ios",
                        productId = productId,
                        purchaseToken = transactionId,
                        isSubscription = false
                    )
                    cont.resume(PurchaseResult.Success) {}
                } else if (error == "cancelled") {
                    callback.onPurchaseStateChanged(PurchaseUiState.IDLE)
                    cont.resume(PurchaseResult.Cancelled) {}
                } else {
                    callback.onPurchaseStateChanged(PurchaseUiState.FAILED)
                    cont.resume(PurchaseResult.Error(error ?: "Unknown error")) {}
                }
            }
        }
    }

    actual suspend fun restorePurchases(): RestoreResult {
        val bridge = storeKitBridge
            ?: return RestoreResult.Success(isPro = false, ownedPackIDs = emptySet())

        callback.onPurchaseStateChanged(PurchaseUiState.RESTORING)

        return kotlinx.coroutines.suspendCancellableCoroutine { cont ->
            bridge.restorePurchases { isPro, ownedPacks, error ->
                if (error != null) {
                    callback.onPurchaseStateChanged(PurchaseUiState.FAILED)
                    cont.resume(RestoreResult.Error(error)) {}
                } else {
                    _isPro = isPro
                    _ownedPackIDs.clear()
                    _ownedPackIDs.addAll(ownedPacks)
                    callback.onProStatusChanged(isPro)
                    callback.onOwnedPacksChanged(_ownedPackIDs.toSet())
                    callback.onPurchaseStateChanged(PurchaseUiState.IDLE)
                    cont.resume(RestoreResult.Success(isPro, _ownedPackIDs.toSet())) {}
                }
            }
        }
    }

    actual suspend fun checkEntitlements(): RestoreResult {
        val bridge = storeKitBridge
            ?: return RestoreResult.Success(isPro = false, ownedPackIDs = emptySet())

        return kotlinx.coroutines.suspendCancellableCoroutine { cont ->
            bridge.checkEntitlementsOnly { isPro, ownedPacks, error ->
                if (error != null) {
                    cont.resume(RestoreResult.Error(error)) {}
                } else {
                    _isPro = isPro
                    _ownedPackIDs.clear()
                    _ownedPackIDs.addAll(ownedPacks)
                    callback.onProStatusChanged(isPro)
                    callback.onOwnedPacksChanged(_ownedPackIDs.toSet())
                    cont.resume(RestoreResult.Success(isPro, _ownedPackIDs.toSet())) {}
                }
            }
        }
    }

    actual suspend fun getReceiptForServer(): ReceiptPayload? = lastReceiptPayload

    companion object {
        /**
         * Set by the iOS app to bridge StoreKit 2 calls.
         * Must be set before BillingService.initialize() is called.
         */
        var storeKitBridge: StoreKitBridgeProtocol? = null
    }
}

/**
 * Protocol that the Swift StoreKitBridge must implement.
 * The iOS app creates a Swift class conforming to this interface
 * and sets it via BillingService.storeKitBridge.
 */
interface StoreKitBridgeProtocol {
    fun initialize()
    fun setEntitlementCallback(callback: (isPro: Boolean, ownedPacks: Set<String>) -> Unit)
    fun loadProducts(
        productIds: List<String>,
        completion: (prices: Map<String, String>?, error: String?) -> Unit
    )
    fun purchase(
        productId: String,
        completion: (success: Boolean, transactionId: String?, error: String?) -> Unit
    )
    fun restorePurchases(
        completion: (isPro: Boolean, ownedPacks: Set<String>, error: String?) -> Unit
    )
    fun checkEntitlementsOnly(
        completion: (isPro: Boolean, ownedPacks: Set<String>, error: String?) -> Unit
    )
}
