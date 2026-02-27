package com.endlessrumination.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class Take(
    @SerialName("lens_index") val lensIndex: Int,
    val headline: String,
    val body: String,
    val wise: Boolean = true
) {
    val isPackVoice: Boolean get() = lensIndex >= 20

    val packName: String? get() = VoicePack.packForVoiceIndex(lensIndex)?.name
}
