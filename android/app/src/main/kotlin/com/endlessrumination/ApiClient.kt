package com.endlessrumination

import com.endlessrumination.model.*
import io.ktor.client.HttpClient
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.request.bearerAuth
import io.ktor.client.request.header
import io.ktor.client.request.preparePost
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.client.statement.bodyAsChannel
import io.ktor.client.statement.bodyAsText
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.serialization.kotlinx.json.json
import io.ktor.utils.io.readUTF8Line
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.serialization.json.Json

class ApiClient {
    private val json = Json { ignoreUnknownKeys = true }

    private val client = HttpClient {
        install(ContentNegotiation) {
            json(json)
        }
    }

    // Auth

    suspend fun register(baseUrl: String, deviceId: String): AuthResponse {
        val response = client.post("$baseUrl/api/v1/auth/register") {
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(RegisterRequest.serializer(), RegisterRequest(deviceId)))
        }
        return json.decodeFromString(response.bodyAsText())
    }

    suspend fun login(baseUrl: String, deviceId: String): AuthResponse {
        val response = client.post("$baseUrl/api/v1/auth/login") {
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(RegisterRequest.serializer(), RegisterRequest(deviceId)))
        }
        return json.decodeFromString(response.bodyAsText())
    }

    // Safety

    suspend fun safetyCheck(baseUrl: String, problem: String): SafetyCheckResponse {
        val response = client.post("$baseUrl/api/v1/safety-check") {
            contentType(ContentType.Application.Json)
            setBody(json.encodeToString(SafetyCheckRequest.serializer(), SafetyCheckRequest(problem)))
        }
        return json.decodeFromString(response.bodyAsText())
    }

    suspend fun verifyReceipt(
        baseUrl: String,
        platform: String,
        productId: String,
        purchaseToken: String,
        isSubscription: Boolean,
        token: String? = null
    ): VerifyReceiptResponse {
        val request = VerifyReceiptRequest(
            platform = platform,
            productId = productId,
            purchaseToken = purchaseToken,
            isSubscription = isSubscription
        )
        val response = client.post("$baseUrl/api/v1/subscription/verify-receipt") {
            contentType(ContentType.Application.Json)
            token?.let { bearerAuth(it) }
            setBody(json.encodeToString(VerifyReceiptRequest.serializer(), request))
        }
        return json.decodeFromString(response.bodyAsText())
    }

    fun generateBatch(
        baseUrl: String,
        problem: String,
        lensIndices: List<Int>,
        ownedPackIds: List<String> = emptyList(),
        token: String? = null
    ): Flow<Take> = flow {
        val requestBody = json.encodeToString(
            GenerateBatchRequest.serializer(),
            GenerateBatchRequest(problem, lensIndices, ownedPackIds)
        )

        client.preparePost("$baseUrl/api/v1/generate-batch") {
            contentType(ContentType.Application.Json)
            header("Accept", "text/event-stream")
            token?.let { bearerAuth(it) }
            setBody(requestBody)
        }.execute { response ->
            val channel = response.bodyAsChannel()
            while (!channel.isClosedForRead) {
                val line = channel.readUTF8Line() ?: break
                if (line.isBlank()) continue
                if (!line.startsWith("data: ")) continue
                val payload = line.removePrefix("data: ")
                if (payload == "[DONE]") break
                try {
                    val take = json.decodeFromString(Take.serializer(), payload)
                    emit(take)
                } catch (_: Exception) {
                    // Skip malformed lines
                }
            }
        }
    }
}
