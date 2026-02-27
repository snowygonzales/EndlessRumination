package com.endlessrumination.ui

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.theme.ERColors

@Composable
actual fun PlatformAdBanner(modifier: Modifier) {
    // Placeholder until Google Mobile Ads SDK is integrated via CocoaPods/SPM
    // TODO: Replace with UIKitView wrapping GADBannerView once SDK is added to iosApp
    Box(
        modifier = modifier.fillMaxWidth().height(50.dp),
        contentAlignment = Alignment.Center
    ) {
        Text(
            "mindfulness app \u2014 download free",
            fontSize = 11.sp,
            color = ERColors.dimText,
            letterSpacing = 1.sp
        )
    }
}
