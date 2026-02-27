package com.endlessrumination.theme

import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

object ERTypography {
    val appTitle = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold, fontSize = 38.sp)
    val screenTitle = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold, fontSize = 28.sp)
    val headline = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.SemiBold, fontSize = 24.sp)
    val body = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Light, fontSize = 13.5.sp, lineHeight = 20.sp)
    val ui = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Normal, fontSize = 16.sp)
    val button = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 16.sp)
    val counter = TextStyle(fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Normal, fontSize = 12.sp)
    val caption = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Normal, fontSize = 11.sp)
    val smallCaps = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 12.sp)
    val badge = TextStyle(fontFamily = FontFamily.Default, fontWeight = FontWeight.Bold, fontSize = 12.sp)

    fun serifHeadline(size: Float = 24f) = TextStyle(
        fontFamily = FontFamily.Serif, fontWeight = FontWeight.SemiBold, fontSize = size.sp
    )

    fun serifTitle(size: Float = 28f) = TextStyle(
        fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold, fontSize = size.sp
    )

    fun serifLargeTitle(size: Float = 38f) = TextStyle(
        fontFamily = FontFamily.Serif, fontWeight = FontWeight.Bold, fontSize = size.sp
    )
}
