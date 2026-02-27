package com.endlessrumination.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography

@Composable
fun LoadingScreen(appState: AppState) {
    val infiniteTransition = rememberInfiniteTransition()
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.5f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(1500, easing = EaseInOut),
            repeatMode = RepeatMode.Reverse
        )
    )

    Column(
        modifier = Modifier.fillMaxSize().background(ERColors.background),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        CircularProgressIndicator(
            modifier = Modifier.size(48.dp),
            color = ERColors.accentWarm,
            strokeWidth = 3.dp
        )

        Spacer(modifier = Modifier.height(20.dp))

        Text(
            text = if (appState.takes.isEmpty()) "Generating perspectives..." else "Almost ready...",
            style = ERTypography.ui.copy(fontSize = 14.sp, color = ERColors.secondaryText),
            modifier = Modifier.alpha(pulseAlpha)
        )

        if (appState.takes.isNotEmpty()) {
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "${appState.takes.size} / ${appState.totalTakes} perspectives ready",
                style = ERTypography.counter.copy(color = ERColors.dimText)
            )
        }
    }
}
