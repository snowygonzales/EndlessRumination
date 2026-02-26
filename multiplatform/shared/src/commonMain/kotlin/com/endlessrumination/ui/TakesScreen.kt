package com.endlessrumination.ui

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.IntOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.math.roundToInt

@Composable
fun TakesScreen(appState: AppState) {
    val scope = rememberCoroutineScope()
    var isBusy by remember { mutableStateOf(false) }
    var showGoneForever by remember { mutableStateOf(false) }
    var dragOffset by remember { mutableFloatStateOf(0f) }

    val offsetAnim = remember { Animatable(0f) }
    val opacityAnim = remember { Animatable(1f) }

    // Bob animation for swipe hint
    val infiniteTransition = rememberInfiniteTransition()
    val bobOffset by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = -6f,
        animationSpec = infiniteRepeatable(
            animation = tween(2000, easing = EaseInOut),
            repeatMode = RepeatMode.Reverse
        )
    )

    fun advance() {
        if (isBusy) return
        if (appState.showInstructionOverlay) {
            appState.showInstructionOverlay = false
            return
        }
        if (appState.currentTakeIndex >= appState.totalTakes - 1) return

        isBusy = true
        scope.launch {
            showGoneForever = true

            // Animate card out
            launch { offsetAnim.animateTo(-40f, tween(300)) }
            launch { opacityAnim.animateTo(0f, tween(300)) }
            delay(300)

            appState.currentTakeIndex++
            offsetAnim.snapTo(40f)
            opacityAnim.snapTo(0f)

            // Animate card in
            launch { offsetAnim.animateTo(0f, tween(300)) }
            launch { opacityAnim.animateTo(1f, tween(300)) }

            delay(900)
            showGoneForever = false
            delay(300)
            isBusy = false
        }
    }

    Column(
        modifier = Modifier
            .fillMaxSize()
            .background(ERColors.background)
    ) {
        // Header
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 24.dp, vertical = 16.dp),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "\u2190 New problem",
                fontSize = 14.sp,
                color = ERColors.secondaryText,
                modifier = Modifier.clickable { appState.navigateToInput() }
            )

            Text(
                text = "${appState.currentTakeIndex + 1} / ${appState.totalTakes}",
                style = ERTypography.counter.copy(color = ERColors.dimText),
                modifier = Modifier
                    .background(ERColors.inputBackground, RoundedCornerShape(8.dp))
                    .padding(horizontal = 10.dp, vertical = 4.dp)
            )
        }

        // Main content area
        Box(
            modifier = Modifier
                .weight(1f)
                .fillMaxWidth()
                .pointerInput(Unit) {
                    detectVerticalDragGestures(
                        onDragEnd = {
                            if (dragOffset < -40f) advance()
                            dragOffset = 0f
                        },
                        onVerticalDrag = { _, dragAmount ->
                            if (dragAmount < 0) {
                                dragOffset += dragAmount * 0.3f
                            }
                        }
                    )
                }
        ) {
            // Take card
            val take = appState.currentTake
            if (take != null) {
                Box(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 28.dp)
                        .padding(top = 24.dp, bottom = 70.dp)
                        .offset { IntOffset(0, (offsetAnim.value + dragOffset).dp.roundToPx()) }
                        .alpha(opacityAnim.value)
                ) {
                    TakeCardView(take = take)
                }
            } else if (appState.isGenerating) {
                Column(
                    modifier = Modifier.fillMaxSize(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.Center
                ) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(32.dp),
                        color = ERColors.accentWarm,
                        strokeWidth = 2.dp
                    )
                    Spacer(modifier = Modifier.height(12.dp))
                    Text(
                        "Waiting for next perspective...",
                        fontSize = 13.sp,
                        color = ERColors.secondaryText
                    )
                }
            }

            // "GONE FOREVER" flash
            Box(modifier = Modifier.align(Alignment.Center)) {
                androidx.compose.animation.AnimatedVisibility(
                    visible = showGoneForever,
                    enter = scaleIn(initialScale = 0.8f) + fadeIn(),
                    exit = fadeOut() + slideOutVertically(targetOffsetY = { -it / 4 })
                ) {
                    Text(
                        text = "GONE FOREVER",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Medium,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 3.sp,
                        color = ERColors.accentRed
                    )
                }
            }

            // Instruction overlay
            if (appState.showInstructionOverlay) {
                InstructionOverlayScreen(appState)
            }

            // Swipe hint (at bottom)
            if (!appState.showInstructionOverlay && opacityAnim.value > 0.9f) {
                Column(
                    modifier = Modifier
                        .align(Alignment.BottomCenter)
                        .padding(bottom = 16.dp)
                        .offset(y = bobOffset.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text("\u2191", fontSize = 16.sp, color = ERColors.dimText)
                    Text(
                        "SWIPE UP \u00B7 FADES FOREVER",
                        fontSize = 9.sp,
                        fontWeight = FontWeight.Medium,
                        letterSpacing = 2.sp,
                        color = ERColors.dimText
                    )
                }
            }

            // Free takes remaining
            if (!appState.isPro && opacityAnim.value > 0.9f) {
                val remaining = appState.freeTakesRemaining
                if (remaining <= 3) {
                    Box(
                        modifier = Modifier
                            .align(Alignment.BottomCenter)
                            .padding(bottom = 50.dp)
                    ) {
                        if (remaining <= 0) {
                            Text(
                                text = "Daily limit reached \u00B7 Go Pro",
                                fontSize = 11.sp,
                                color = ERColors.accentGold,
                                modifier = Modifier.clickable { appState.showPaywall = true }
                            )
                        } else {
                            Text(
                                text = "$remaining free takes remaining",
                                fontSize = 11.sp,
                                color = ERColors.secondaryText
                            )
                        }
                    }
                }
            }
        }

        // Ad banner (free tier)
        if (!appState.isPro) {
            AdBannerView(appState)
        }
    }
}
