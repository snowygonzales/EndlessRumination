package com.endlessrumination.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.theme.ERColors

@Composable
fun InstructionOverlayScreen(appState: AppState) {
    val infiniteTransition = rememberInfiniteTransition()
    val bobOffset by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = -6f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = EaseInOut),
            repeatMode = RepeatMode.Reverse
        )
    )

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(ERColors.background.copy(alpha = 0.7f))
            .clickable { appState.showInstructionOverlay = false },
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(
                "\u2191",
                fontSize = 36.sp,
                color = ERColors.secondaryText.copy(alpha = 0.6f),
                modifier = Modifier.offset(y = bobOffset.dp)
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                "SWIPE UP FOR NEXT TAKE",
                fontSize = 14.sp,
                fontWeight = FontWeight.Medium,
                letterSpacing = 2.sp,
                color = ERColors.secondaryText
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                "Each perspective disappears forever",
                fontSize = 11.sp,
                color = ERColors.dimText
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                "Free: 5 takes/day \u00B7 Pro: unlimited",
                fontSize = 11.sp,
                color = ERColors.accentGold
            )
        }
    }
}
