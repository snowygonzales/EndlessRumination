package com.endlessrumination

import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.endlessrumination.model.Lens
import com.endlessrumination.model.Take
import com.endlessrumination.model.VoicePack

enum class AppScreen { SPLASH, INPUT, LOADING, TAKES }

class AppState {
    var currentScreen by mutableStateOf(AppScreen.SPLASH)
    var problemText by mutableStateOf("")
    var takes by mutableStateOf<List<Take>>(emptyList())
    var currentTakeIndex by mutableIntStateOf(0)
    var showSafetyOverlay by mutableStateOf(false)
    var showInstructionOverlay by mutableStateOf(true)
    var isGenerating by mutableStateOf(false)
    var authToken by mutableStateOf<String?>(null)
    var isPro by mutableStateOf(false)
    var showPaywall by mutableStateOf(false)
    var showShop by mutableStateOf(false)
    var ownedPackIDs by mutableStateOf<Set<String>>(emptySet())

    val wordCount: Int
        get() = problemText.trim().split("\\s+".toRegex()).filter { it.isNotEmpty() }.size

    val canSubmit: Boolean get() = wordCount >= 20

    val currentTake: Take?
        get() {
            val sorted = takes.sortedBy { it.lensIndex }
            return sorted.getOrNull(currentTakeIndex)
        }

    val totalTakes: Int
        get() {
            val baseTakes = if (isPro) 20 else Lens.FREE_LENS_COUNT
            val packTakes = ownedPackVoiceIndices.size
            return baseTakes + packTakes
        }

    val freeTakesRemaining: Int
        get() = maxOf(0, Lens.FREE_LENS_COUNT - (currentTakeIndex + 1))

    val ownedPackVoiceIndices: List<Int>
        get() = VoicePack.all
            .filter { ownedPackIDs.contains(it.productID) }
            .flatMap { it.voiceIndices }

    val lensIndicesForRequest: List<Int>
        get() {
            val baseIndices = if (isPro) (0 until 20).toList() else (0 until Lens.FREE_LENS_COUNT).toList()
            return baseIndices + ownedPackVoiceIndices
        }

    val ownedPackProductIDs: List<String>
        get() = ownedPackIDs.toList()

    val hasTakeForCurrentIndex: Boolean
        get() = takes.any { it.lensIndex == currentTakeIndex }

    val nextTakeReady: Boolean
        get() = takes.any { it.lensIndex == currentTakeIndex + 1 }

    fun reset() {
        problemText = ""
        takes = emptyList()
        currentTakeIndex = 0
        showInstructionOverlay = true
        isGenerating = false
        showSafetyOverlay = false
    }

    fun navigateToInput() {
        reset()
        currentScreen = AppScreen.INPUT
    }

    fun receiveTake(take: Take) {
        if (takes.none { it.lensIndex == take.lensIndex }) {
            takes = takes + take
        }
        if (currentScreen == AppScreen.LOADING && hasTakeForCurrentIndex) {
            currentScreen = AppScreen.TAKES
        }
    }

    fun debugTogglePro() {
        isPro = !isPro
    }
}
