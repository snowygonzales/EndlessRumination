package com.endlessrumination.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

enum class SubscriptionTier { FREE, PRO }

@Serializable
data class AuthResponse(
    val token: String,
    val user: UserResponse
)

@Serializable
data class UserResponse(
    val id: String,
    @SerialName("device_id") val deviceId: String,
    val email: String? = null,
    @SerialName("subscription_tier") val subscriptionTier: String,
    @SerialName("daily_takes_used") val dailyTakesUsed: Int,
    @SerialName("created_at") val createdAt: String
)

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
data class RegisterRequest(
    @SerialName("device_id") val deviceId: String
)

@Serializable
data class HealthResponse(
    val status: String,
    val app: String
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
