package com.endlessrumination.ui

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.BasicTextField
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.SolidColor
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.ApiClient
import com.endlessrumination.AppScreen
import com.endlessrumination.AppState
import com.endlessrumination.BASE_URL
import com.endlessrumination.service.HapticService
import com.endlessrumination.service.SafetyService
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography
import kotlinx.coroutines.launch

@Composable
fun ProblemInputScreen(appState: AppState) {
    val scope = rememberCoroutineScope()
    val apiClient = remember { ApiClient() }
    val baseUrl = BASE_URL
    var isSubmitting by remember { mutableStateOf(false) }
    var shopTapCount by remember { mutableIntStateOf(0) }

    val wordCountColor by animateColorAsState(
        targetValue = when {
            appState.wordCount >= 20 -> ERColors.accentGreen
            appState.wordCount >= 15 -> ERColors.accentGold
            else -> ERColors.dimText
        },
        animationSpec = tween(300)
    )

    fun submit() {
        if (!appState.canSubmit || isSubmitting) return
        HapticService.medium()
        if (!SafetyService.clientSideCheck(appState.problemText)) {
            appState.showSafetyOverlay = true
            return
        }
        scope.launch {
            isSubmitting = true
            try {
                val safe = SafetyService.serverSideCheck(apiClient, baseUrl, appState.problemText)
                if (!safe) {
                    appState.showSafetyOverlay = true
                    isSubmitting = false
                    return@launch
                }
            } catch (_: Exception) { /* fail-open */ }

            appState.currentScreen = AppScreen.LOADING
            appState.isGenerating = true
            isSubmitting = false

            try {
                apiClient.generateBatch(
                    baseUrl,
                    appState.problemText,
                    appState.lensIndicesForRequest,
                    appState.ownedPackProductIDs,
                    appState.authToken
                ).collect { take ->
                    appState.receiveTake(take)
                }
            } catch (_: Exception) {
                if (appState.takes.isEmpty()) appState.currentScreen = AppScreen.INPUT
            }
            appState.isGenerating = false
        }
    }

    Box(modifier = Modifier.fillMaxSize().background(ERColors.background).imePadding()) {
        Column(modifier = Modifier.fillMaxSize()) {
            // Header
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "What\u2019s on your mind?",
                    style = ERTypography.serifTitle()
                        .copy(color = ERColors.primaryText),
                    modifier = Modifier.weight(1f, fill = false)
                )

                Spacer(modifier = Modifier.width(8.dp))

                // Shop button
                Row(
                    modifier = Modifier
                        .wrapContentWidth()
                        .background(ERColors.proGradient, RoundedCornerShape(50))
                        .clickable {
                            shopTapCount++
                            if (shopTapCount >= 3 && com.endlessrumination.BuildConfig.DEBUG) {
                                appState.debugTogglePro()
                                shopTapCount = 0
                            } else if (shopTapCount >= 3) {
                                shopTapCount = 0
                                appState.showShop = true
                            } else {
                                appState.showShop = true
                            }
                        }
                        .padding(horizontal = 12.dp, vertical = 5.dp),
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("\u2726", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = ERColors.background, maxLines = 1, softWrap = false)
                    Text("SHOP", fontSize = 11.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.sp, color = ERColors.background, maxLines = 1, softWrap = false)
                }
            }

            // Subtext
            Text(
                text = "Describe what\u2019s bothering you. Be specific \u2014 the more you share, the better the perspectives.",
                fontSize = 13.sp,
                color = ERColors.secondaryText,
                lineHeight = 17.sp,
                modifier = Modifier.padding(horizontal = 24.dp).padding(bottom = 12.dp)
            )

            // Text area with word counter
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .weight(1f)
                    .padding(horizontal = 24.dp)
                    .padding(bottom = 20.dp)
            ) {
                BasicTextField(
                    value = appState.problemText,
                    onValueChange = { newValue ->
                        val oldWordCount = appState.wordCount
                        appState.problemText = newValue
                        if (appState.wordCount != oldWordCount) {
                            HapticService.selection()
                        }
                    },
                    textStyle = TextStyle(color = ERColors.primaryText, fontSize = 16.sp, lineHeight = 22.sp),
                    cursorBrush = SolidColor(ERColors.accentWarm),
                    modifier = Modifier
                        .fillMaxSize()
                        .background(ERColors.inputBackground, RoundedCornerShape(16.dp))
                        .border(1.dp, ERColors.border, RoundedCornerShape(16.dp))
                        .padding(16.dp),
                    decorationBox = { innerTextField ->
                        Box {
                            if (appState.problemText.isEmpty()) {
                                Text(
                                    "I can\u2019t stop thinking about...",
                                    color = ERColors.dimText,
                                    fontSize = 16.sp
                                )
                            }
                            innerTextField()
                        }
                    }
                )

                // Word counter badge
                Text(
                    text = "${appState.wordCount} / 20 words",
                    style = ERTypography.counter.copy(color = wordCountColor),
                    modifier = Modifier
                        .align(Alignment.BottomEnd)
                        .padding(14.dp)
                        .background(ERColors.inputBackground, RoundedCornerShape(6.dp))
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }

            // Submit button
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp)
                    .padding(bottom = 16.dp)
                    .then(
                        if (appState.canSubmit) Modifier.background(ERColors.warmGradient, RoundedCornerShape(14.dp))
                        else Modifier.background(ERColors.inputBackground, RoundedCornerShape(14.dp))
                    )
                    .clickable(enabled = appState.canSubmit && !isSubmitting) { submit() }
                    .padding(vertical = 18.dp),
                contentAlignment = Alignment.Center
            ) {
                if (isSubmitting) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = ERColors.primaryText,
                        strokeWidth = 2.dp
                    )
                } else {
                    Text(
                        text = when {
                            appState.wordCount >= 20 -> "See perspectives"
                            appState.wordCount >= 15 -> "Need ${20 - appState.wordCount} more words"
                            else -> "Need at least 20 words"
                        },
                        style = ERTypography.button.copy(
                            color = if (appState.canSubmit) ERColors.primaryText else ERColors.dimText
                        )
                    )
                }
            }

            // Safety disclaimer
            Row(
                modifier = Modifier.fillMaxWidth().padding(bottom = 24.dp),
                horizontalArrangement = Arrangement.Center,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text("\uD83D\uDEE1\uFE0F", fontSize = 10.sp)
                Spacer(modifier = Modifier.width(4.dp))
                Text(
                    "All content analyzed for safety. Crisis resources provided when needed.",
                    style = ERTypography.caption.copy(color = ERColors.dimText)
                )
            }
        }

    }
}
