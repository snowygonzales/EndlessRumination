package com.endlessrumination.theme

import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color

object ERColors {
    val background = Color(0xFF0A0A0C)
    val inputBackground = Color(0xFF1A1A20)
    val primaryText = Color(0xFFF0ECE4)
    val secondaryText = Color(0xFF8A8690)
    val dimText = Color(0xFF4A4650)
    val border = Color.White.copy(alpha = 0.06f)
    val accentWarm = Color(0xFFE8653A)
    val accentGold = Color(0xFFC9A84C)
    val accentCool = Color(0xFF4A7CFF)
    val accentGreen = Color(0xFF3ECF8E)
    val accentPurple = Color(0xFF9B6DFF)
    val accentPink = Color(0xFFFF6B9D)
    val accentCyan = Color(0xFF00D4AA)
    val accentRed = Color(0xFFFF4757)

    val warmGradient = Brush.linearGradient(
        colors = listOf(Color(0xFFE8653A), Color(0xFFD44A2A)),
        start = Offset.Zero,
        end = Offset.Infinite
    )

    val logoGradient = Brush.linearGradient(
        colors = listOf(Color(0xFFE8653A), Color(0xFF9B6DFF)),
        start = Offset.Zero,
        end = Offset.Infinite
    )

    val proGradient = Brush.linearGradient(
        colors = listOf(Color(0xFFC9A84C), Color(0xFFE8653A)),
        start = Offset.Zero,
        end = Offset.Infinite
    )

    val titleGradient = Brush.linearGradient(
        colors = listOf(Color(0xFFF0ECE4), Color(0xFFC9A84C)),
        start = Offset.Zero,
        end = Offset.Infinite
    )
}
