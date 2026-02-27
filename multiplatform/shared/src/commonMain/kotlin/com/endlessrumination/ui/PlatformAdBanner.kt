package com.endlessrumination.ui

import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

/**
 * Platform-specific ad banner implementation.
 * Android: Google AdMob banner via AndroidView
 * iOS: Google AdMob banner via UIKitView (or placeholder until SDK integrated)
 */
@Composable
expect fun PlatformAdBanner(modifier: Modifier = Modifier)
