package com.endlessrumination.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// API request/response DTOs

@Serializable
data class SafetyCheckRequest(val problem: String)

@Serializable
data class SafetyCheckResponse(
    val safe: Boolean,
    val category: String? = null
)

@Serializable
data class GenerateBatchRequest(
    val problem: String,
    @SerialName("lens_indices") val lensIndices: List<Int>,
    @SerialName("owned_pack_ids") val ownedPackIds: List<String> = emptyList()
)

@Serializable
data class VerifyReceiptRequest(
    val platform: String,
    @SerialName("product_id") val productId: String,
    @SerialName("purchase_token") val purchaseToken: String,
    @SerialName("is_subscription") val isSubscription: Boolean
)

@Serializable
data class VerifyReceiptResponse(
    val status: String,
    @SerialName("product_id") val productId: String,
    @SerialName("is_subscription") val isSubscription: Boolean
)
