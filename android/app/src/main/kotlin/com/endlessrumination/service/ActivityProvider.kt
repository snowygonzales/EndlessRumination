package com.endlessrumination.service

import android.app.Activity
import androidx.compose.runtime.Composable
import androidx.compose.ui.platform.LocalContext

@Composable
fun rememberActivityProvider(): () -> Any? {
    val context = LocalContext.current
    return { context as? Activity }
}
