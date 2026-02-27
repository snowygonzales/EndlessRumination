package com.endlessrumination.service

import androidx.compose.runtime.Composable

@Composable
expect fun rememberActivityProvider(): () -> Any?
