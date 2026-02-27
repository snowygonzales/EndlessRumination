package com.endlessrumination.service

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

enum class PurchaseUiState {
    IDLE,
    PURCHASING,
    PURCHASED,
    FAILED,
    RESTORING
}

sealed class BillingResult {
    data object Success : BillingResult()
    data class Error(val message: String) : BillingResult()
}

sealed class PurchaseResult {
    data object Success : PurchaseResult()
    data object Cancelled : PurchaseResult()
    data object Pending : PurchaseResult()
    data class Error(val message: String) : PurchaseResult()
}

sealed class RestoreResult {
    data class Success(val isPro: Boolean, val ownedPackIDs: Set<String>) : RestoreResult()
    data class Error(val message: String) : RestoreResult()
}

@Serializable
data class ReceiptPayload(
    val platform: String,
    @SerialName("product_id") val productId: String,
    @SerialName("purchase_token") val purchaseToken: String,
    @SerialName("is_subscription") val isSubscription: Boolean
)

interface BillingCallback {
    fun onProStatusChanged(isPro: Boolean)
    fun onOwnedPacksChanged(packIDs: Set<String>)
    fun onPurchaseStateChanged(state: PurchaseUiState)
}

object BillingProductIds {
    const val PRO_MONTHLY = "com.endlessrumination.pro.monthly"

    const val PACK_STRATEGISTS = "com.endlessrumination.pack.strategists"
    const val PACK_REVOLUTIONARIES = "com.endlessrumination.pack.revolutionaries"
    const val PACK_PHILOSOPHERS = "com.endlessrumination.pack.philosophers"
    const val PACK_CREATORS = "com.endlessrumination.pack.creators"

    val PACK_IDS = setOf(
        PACK_STRATEGISTS,
        PACK_REVOLUTIONARIES,
        PACK_PHILOSOPHERS,
        PACK_CREATORS
    )

    val SUBSCRIPTION_IDS = setOf(PRO_MONTHLY)

    val ALL_IDS = SUBSCRIPTION_IDS + PACK_IDS
}
