package com.endlessrumination.model

import androidx.compose.ui.graphics.Color

data class Lens(
    val id: Int,
    val name: String,
    val emoji: String,
    val color: Color,
    val bgColor: Color
) {
    /** Whether this lens is available to free-tier users */
    val isFree: Boolean get() = id < FREE_LENS_COUNT

    /** Whether this lens is powered by Sonnet (shown as "Wise") */
    val isWise: Boolean get() = wiseLensIndices.contains(id)

    companion object {
        const val FREE_LENS_COUNT = 5

        /** These lens indices use Sonnet ("Wise") even for free-tier users */
        val wiseLensIndices: Set<Int> = setOf(1, 9)

        val freeLenses: List<Lens> by lazy { all.take(FREE_LENS_COUNT) }

        val all: List<Lens> = listOf(
            Lens(0,  "The Comedian",       "\uD83D\uDE02", Color(0xFFFF6B9D), Color(0xFFFF6B9D).copy(alpha = 0.15f)),
            Lens(1,  "The Stoic",          "\uD83C\uDFDB", Color(0xFFC9A84C), Color(0xFFC9A84C).copy(alpha = 0.15f)),
            Lens(2,  "The Nihilist",       "\uD83D\uDD73", Color(0xFF8A8690), Color.White.copy(alpha = 0.06f)),
            Lens(3,  "The Optimist",       "\u2600\uFE0F", Color(0xFF3ECF8E), Color(0xFF3ECF8E).copy(alpha = 0.15f)),
            Lens(4,  "The Pessimist",      "\u26C8",       Color(0xFFFF4757), Color(0xFFFF4757).copy(alpha = 0.15f)),
            Lens(5,  "Your Best Friend",   "\uD83E\uDEC2", Color(0xFF4A7CFF), Color(0xFF4A7CFF).copy(alpha = 0.15f)),
            Lens(6,  "The Poet",           "\uD83E\uDEB6", Color(0xFF9B6DFF), Color(0xFF9B6DFF).copy(alpha = 0.15f)),
            Lens(7,  "A Five-Year-Old",    "\uD83E\uDDF8", Color(0xFFF0C832), Color(0xFFF0C832).copy(alpha = 0.15f)),
            Lens(8,  "The CEO",            "\uD83D\uDCCA", Color(0xFFF0ECE4), Color(0xFFF0ECE4).copy(alpha = 0.08f)),
            Lens(9,  "The Therapist",      "\uD83E\uDEB7", Color(0xFF00D4AA), Color(0xFF00D4AA).copy(alpha = 0.15f)),
            Lens(10, "Your Grandma",       "\uD83C\uDF6A", Color(0xFFE8653A), Color(0xFFE8653A).copy(alpha = 0.15f)),
            Lens(11, "The Alien",          "\uD83D\uDC7D", Color(0xFF4AFFB4), Color(0xFF4AFFB4).copy(alpha = 0.12f)),
            Lens(12, "The Historian",      "\uD83D\uDCDC", Color(0xFFD4A843), Color(0xFFD4A843).copy(alpha = 0.12f)),
            Lens(13, "The Philosopher",    "\uD83E\uDD89", Color(0xFFB08AFF), Color(0xFFB08AFF).copy(alpha = 0.12f)),
            Lens(14, "Future You",         "\u231B",       Color(0xFF6E9FFF), Color(0xFF6E9FFF).copy(alpha = 0.12f)),
            Lens(15, "Drill Sergeant",     "\uD83C\uDF96", Color(0xFFC8C0B4), Color(0xFFC8C0B4).copy(alpha = 0.10f)),
            Lens(16, "The Monk",           "\uD83E\uDDD8", Color(0xFF40DFB0), Color(0xFF40DFB0).copy(alpha = 0.10f)),
            Lens(17, "The Scientist",      "\uD83D\uDD2C", Color(0xFF5A8CFF), Color(0xFF5A8CFF).copy(alpha = 0.12f)),
            Lens(18, "Conspiracy Theorist","\uD83D\uDD3A", Color(0xFFE8B830), Color(0xFFE8B830).copy(alpha = 0.12f)),
            Lens(19, "Your Dog",           "\uD83D\uDC15", Color(0xFFF0A070), Color(0xFFF0A070).copy(alpha = 0.12f)),
        )

        /** Unified display info for both base lenses (0-19) and pack voices (20-39). */
        fun displayInfo(index: Int): DisplayInfo {
            if (index < all.size) {
                val l = all[index]
                return DisplayInfo(l.name, l.emoji, l.color, l.bgColor)
            }
            val v = VoicePack.voiceAt(index)
            if (v != null) {
                return DisplayInfo(v.name, v.emoji, v.color, v.bgColor)
            }
            return DisplayInfo("Unknown", "?", Color(0xFF4A4650), Color(0xFF1A1A20))
        }
    }

    data class DisplayInfo(
        val name: String,
        val emoji: String,
        val color: Color,
        val bgColor: Color
    )
}
