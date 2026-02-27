package com.endlessrumination.ui

import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.interop.UIKitView
import androidx.compose.ui.unit.dp
import kotlinx.cinterop.ExperimentalForeignApi
import platform.UIKit.UIView

/**
 * Factory set by the iOS app at startup to create a GADBannerView wrapper.
 * The Swift side provides a lambda that returns an AdBannerWrapperView.
 */
object AdBannerProvider {
    var createBanner: (() -> UIView)? = null
}

@OptIn(ExperimentalForeignApi::class)
@Composable
actual fun PlatformAdBanner(modifier: Modifier) {
    val factory = AdBannerProvider.createBanner
    if (factory != null) {
        UIKitView(
            factory = { factory() },
            modifier = modifier.fillMaxWidth().height(50.dp)
        )
    }
}
