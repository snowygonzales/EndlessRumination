package com.endlessrumination.service

import android.app.Activity
import android.content.Context
import com.android.billingclient.api.*
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume

actual class BillingService actual constructor(
    private val callback: BillingCallback
) {
    private var billingClient: BillingClient? = null
    private var productDetailsMap: MutableMap<String, ProductDetails> = mutableMapOf()
    private var _isPro = false
    private var _ownedPackIDs = mutableSetOf<String>()
    private var lastReceiptPayload: ReceiptPayload? = null

    actual val isPro: Boolean get() = _isPro
    actual val ownedPackIDs: Set<String> get() = _ownedPackIDs.toSet()

    actual val proPrice: String?
        get() = productDetailsMap[BillingProductIds.PRO_MONTHLY]
            ?.subscriptionOfferDetails?.firstOrNull()
            ?.pricingPhases?.pricingPhaseList?.firstOrNull()?.formattedPrice

    actual fun packPrice(productId: String): String? =
        productDetailsMap[productId]?.oneTimePurchaseOfferDetails?.formattedPrice

    private val purchasesUpdatedListener = PurchasesUpdatedListener { billingResult, purchases ->
        if (billingResult.responseCode == BillingClient.BillingResponseCode.OK && purchases != null) {
            for (purchase in purchases) {
                handlePurchase(purchase)
            }
        } else if (billingResult.responseCode == BillingClient.BillingResponseCode.USER_CANCELED) {
            callback.onPurchaseStateChanged(PurchaseUiState.IDLE)
        } else {
            callback.onPurchaseStateChanged(PurchaseUiState.FAILED)
        }
    }

    actual fun initialize() {
        val context = appContext ?: return
        billingClient = BillingClient.newBuilder(context)
            .setListener(purchasesUpdatedListener)
            .enablePendingPurchases()
            .build()

        billingClient?.startConnection(object : BillingClientStateListener {
            override fun onBillingSetupFinished(billingResult: com.android.billingclient.api.BillingResult) {
                // Connection ready
            }

            override fun onBillingServiceDisconnected() {
                // Try to restart the connection on the next request
            }
        })
    }

    actual fun dispose() {
        billingClient?.endConnection()
        billingClient = null
    }

    actual suspend fun loadProducts(): com.endlessrumination.service.BillingResult {
        val client = billingClient ?: return com.endlessrumination.service.BillingResult.Error("Billing not initialized")

        // Query subscriptions
        val subsParams = QueryProductDetailsParams.newBuilder()
            .setProductList(
                BillingProductIds.SUBSCRIPTION_IDS.map { id ->
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(id)
                        .setProductType(BillingClient.ProductType.SUBS)
                        .build()
                }
            )
            .build()

        val subsResult = suspendCancellableCoroutine { cont ->
            client.queryProductDetailsAsync(subsParams) { billingResult, productDetailsList ->
                if (billingResult.responseCode == BillingClient.BillingResponseCode.OK) {
                    productDetailsList.forEach { productDetailsMap[it.productId] = it }
                }
                cont.resume(billingResult)
            }
        }

        // Query in-app products (voice packs)
        val inAppParams = QueryProductDetailsParams.newBuilder()
            .setProductList(
                BillingProductIds.PACK_IDS.map { id ->
                    QueryProductDetailsParams.Product.newBuilder()
                        .setProductId(id)
                        .setProductType(BillingClient.ProductType.INAPP)
                        .build()
                }
            )
            .build()

        val inAppResult = suspendCancellableCoroutine { cont ->
            client.queryProductDetailsAsync(inAppParams) { billingResult, productDetailsList ->
                if (billingResult.responseCode == BillingClient.BillingResponseCode.OK) {
                    productDetailsList.forEach { productDetailsMap[it.productId] = it }
                }
                cont.resume(billingResult)
            }
        }

        return if (subsResult.responseCode == BillingClient.BillingResponseCode.OK ||
            inAppResult.responseCode == BillingClient.BillingResponseCode.OK
        ) {
            com.endlessrumination.service.BillingResult.Success
        } else {
            com.endlessrumination.service.BillingResult.Error("Failed to load products")
        }
    }

    actual suspend fun purchaseSubscription(
        productId: String,
        activityProvider: () -> Any?
    ): PurchaseResult {
        val activity = activityProvider() as? Activity
            ?: return PurchaseResult.Error("Activity not available")
        val productDetails = productDetailsMap[productId]
            ?: return PurchaseResult.Error("Product not loaded: $productId")
        val offerDetails = productDetails.subscriptionOfferDetails?.firstOrNull()
            ?: return PurchaseResult.Error("No subscription offer available")

        callback.onPurchaseStateChanged(PurchaseUiState.PURCHASING)

        val params = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(
                listOf(
                    BillingFlowParams.ProductDetailsParams.newBuilder()
                        .setProductDetails(productDetails)
                        .setOfferToken(offerDetails.offerToken)
                        .build()
                )
            )
            .build()

        val result = billingClient?.launchBillingFlow(activity, params)
        return if (result?.responseCode == BillingClient.BillingResponseCode.OK) {
            // Purchase result will come through PurchasesUpdatedListener
            PurchaseResult.Success
        } else {
            callback.onPurchaseStateChanged(PurchaseUiState.FAILED)
            PurchaseResult.Error("Failed to launch billing flow: ${result?.debugMessage}")
        }
    }

    actual suspend fun purchaseOneTime(
        productId: String,
        activityProvider: () -> Any?
    ): PurchaseResult {
        val activity = activityProvider() as? Activity
            ?: return PurchaseResult.Error("Activity not available")
        val productDetails = productDetailsMap[productId]
            ?: return PurchaseResult.Error("Product not loaded: $productId")

        callback.onPurchaseStateChanged(PurchaseUiState.PURCHASING)

        val params = BillingFlowParams.newBuilder()
            .setProductDetailsParamsList(
                listOf(
                    BillingFlowParams.ProductDetailsParams.newBuilder()
                        .setProductDetails(productDetails)
                        .build()
                )
            )
            .build()

        val result = billingClient?.launchBillingFlow(activity, params)
        return if (result?.responseCode == BillingClient.BillingResponseCode.OK) {
            PurchaseResult.Success
        } else {
            callback.onPurchaseStateChanged(PurchaseUiState.FAILED)
            PurchaseResult.Error("Failed to launch billing flow: ${result?.debugMessage}")
        }
    }

    actual suspend fun restorePurchases(): RestoreResult {
        val client = billingClient ?: return RestoreResult.Error("Billing not initialized")
        callback.onPurchaseStateChanged(PurchaseUiState.RESTORING)

        _isPro = false
        _ownedPackIDs.clear()

        // Check subscriptions
        val subsParams = QueryPurchasesParams.newBuilder()
            .setProductType(BillingClient.ProductType.SUBS)
            .build()

        val subsResult = suspendCancellableCoroutine { cont ->
            client.queryPurchasesAsync(subsParams) { billingResult, purchases ->
                if (billingResult.responseCode == BillingClient.BillingResponseCode.OK) {
                    for (purchase in purchases) {
                        if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
                            if (purchase.products.contains(BillingProductIds.PRO_MONTHLY)) {
                                _isPro = true
                            }
                        }
                    }
                }
                cont.resume(billingResult)
            }
        }

        // Check in-app purchases
        val inAppParams = QueryPurchasesParams.newBuilder()
            .setProductType(BillingClient.ProductType.INAPP)
            .build()

        val inAppResult = suspendCancellableCoroutine { cont ->
            client.queryPurchasesAsync(inAppParams) { billingResult, purchases ->
                if (billingResult.responseCode == BillingClient.BillingResponseCode.OK) {
                    for (purchase in purchases) {
                        if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
                            for (productId in purchase.products) {
                                if (productId in BillingProductIds.PACK_IDS) {
                                    _ownedPackIDs.add(productId)
                                }
                            }
                        }
                    }
                }
                cont.resume(billingResult)
            }
        }

        callback.onProStatusChanged(_isPro)
        callback.onOwnedPacksChanged(_ownedPackIDs.toSet())
        callback.onPurchaseStateChanged(PurchaseUiState.IDLE)

        return RestoreResult.Success(isPro = _isPro, ownedPackIDs = _ownedPackIDs.toSet())
    }

    // On Android, checkEntitlements is the same as restorePurchases
    // (Google Play doesn't prompt for login like Apple does with AppStore.sync())
    actual suspend fun checkEntitlements(): RestoreResult = restorePurchases()

    actual suspend fun getReceiptForServer(): ReceiptPayload? = lastReceiptPayload

    private fun handlePurchase(purchase: Purchase) {
        if (purchase.purchaseState == Purchase.PurchaseState.PURCHASED) {
            // Acknowledge the purchase
            if (!purchase.isAcknowledged) {
                val acknowledgeParams = AcknowledgePurchaseParams.newBuilder()
                    .setPurchaseToken(purchase.purchaseToken)
                    .build()
                billingClient?.acknowledgePurchase(acknowledgeParams) { /* result */ }
            }

            // Update entitlements
            for (productId in purchase.products) {
                if (productId == BillingProductIds.PRO_MONTHLY) {
                    _isPro = true
                    callback.onProStatusChanged(true)
                    lastReceiptPayload = ReceiptPayload(
                        platform = "android",
                        productId = productId,
                        purchaseToken = purchase.purchaseToken,
                        isSubscription = true
                    )
                } else if (productId in BillingProductIds.PACK_IDS) {
                    _ownedPackIDs.add(productId)
                    callback.onOwnedPacksChanged(_ownedPackIDs.toSet())
                    lastReceiptPayload = ReceiptPayload(
                        platform = "android",
                        productId = productId,
                        purchaseToken = purchase.purchaseToken,
                        isSubscription = false
                    )
                }
            }
            callback.onPurchaseStateChanged(PurchaseUiState.PURCHASED)
        } else if (purchase.purchaseState == Purchase.PurchaseState.PENDING) {
            callback.onPurchaseStateChanged(PurchaseUiState.IDLE)
        }
    }

    companion object {
        private var appContext: Context? = null

        fun init(context: Context) {
            appContext = context.applicationContext
        }
    }
}
