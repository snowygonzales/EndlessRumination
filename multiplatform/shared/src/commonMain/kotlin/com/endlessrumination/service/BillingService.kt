package com.endlessrumination.service

expect class BillingService(callback: BillingCallback) {
    fun initialize()
    fun dispose()

    suspend fun loadProducts(): BillingResult
    suspend fun purchaseSubscription(productId: String, activityProvider: () -> Any?): PurchaseResult
    suspend fun purchaseOneTime(productId: String, activityProvider: () -> Any?): PurchaseResult
    suspend fun restorePurchases(): RestoreResult

    val isPro: Boolean
    val ownedPackIDs: Set<String>
    val proPrice: String?
    fun packPrice(productId: String): String?

    suspend fun getReceiptForServer(): ReceiptPayload?
}
