package com.endlessrumination.service

import com.endlessrumination.ApiClient

object SafetyService {
    private val blocklist = listOf(
        "kill myself", "kill me", "suicide", "suicidal",
        "hurt myself", "harm myself", "self-harm", "self harm",
        "end it all", "end my life", "want to die",
        "cut myself", "cutting myself",
        "weapon", "gun", "shoot"
    )

    data class CrisisResource(
        val name: String,
        val action: String,
        val value: String,
        val description: String
    )

    val crisisResources = listOf(
        CrisisResource("988 Suicide & Crisis Lifeline", "call", "988", "Free, confidential, 24/7 support"),
        CrisisResource("Crisis Text Line", "text", "HOME to 741741", "Text-based crisis counseling")
    )

    /** Client-side keyword check for instant rejection. Returns true if safe. */
    fun clientSideCheck(text: String): Boolean {
        val lowered = text.lowercase()
        return blocklist.none { lowered.contains(it) }
    }

    /** Server-side safety check via Claude classification. Returns true if safe. */
    suspend fun serverSideCheck(apiClient: ApiClient, baseUrl: String, text: String): Boolean {
        val response = apiClient.safetyCheck(baseUrl, text)
        return response.safe
    }
}
