package com.endlessrumination.ui

import androidx.compose.animation.animateContentSize
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.model.VoicePack
import com.endlessrumination.model.VoicePackVoice
import com.endlessrumination.service.PurchaseUiState
import com.endlessrumination.service.rememberActivityProvider
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography
import kotlinx.coroutines.launch

@Composable
fun PackDetailScreen(pack: VoicePack, appState: AppState, onBack: () -> Unit) {
    val isOwned = appState.ownedPackIDs.contains(pack.productID)
    val scope = rememberCoroutineScope()
    val activityProvider = rememberActivityProvider()

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(ERColors.background)
    ) {
        Column(modifier = Modifier.fillMaxSize()) {
            // Top bar
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 16.dp)
            ) {
                Text(
                    "\u2190 Back",
                    fontSize = 14.sp,
                    color = ERColors.secondaryText,
                    modifier = Modifier
                        .align(Alignment.CenterStart)
                        .clickable(onClick = onBack)
                )

                Text(
                    "${pack.voices.size} VOICES",
                    fontSize = 10.sp,
                    fontWeight = FontWeight.Medium,
                    fontFamily = FontFamily.Monospace,
                    letterSpacing = 2.sp,
                    color = ERColors.dimText,
                    modifier = Modifier.align(Alignment.Center)
                )
            }

            // Scrollable content
            Column(
                modifier = Modifier
                    .weight(1f)
                    .verticalScroll(rememberScrollState())
            ) {
                // Pack header
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 24.dp),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    verticalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text(pack.icon, fontSize = 44.sp)
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        pack.name,
                        style = ERTypography.serifTitle(),
                        color = ERColors.primaryText
                    )
                    Text(
                        pack.subtitle,
                        fontSize = 12.sp,
                        color = ERColors.secondaryText
                    )
                }

                // Voices list
                Column(
                    modifier = Modifier
                        .padding(horizontal = 24.dp)
                        .padding(bottom = 20.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    for (voice in pack.voices) {
                        VoicePreviewCard(voice = voice, packColor = pack.color)
                    }
                }
            }

            // Purchase bar
            PurchaseBar(
                pack = pack,
                isOwned = isOwned,
                isPurchasing = appState.purchaseState == PurchaseUiState.PURCHASING,
                price = appState.getPackPrice(pack.productID),
                errorMessage = appState.purchaseErrorMessage,
                onPurchase = {
                    scope.launch { appState.purchasePack(pack.productID, activityProvider) }
                }
            )
        }
    }
}

@Composable
private fun VoicePreviewCard(voice: VoicePackVoice, packColor: Color) {
    var isExpanded by remember { mutableStateOf(false) }
    val chevronRotation by animateFloatAsState(
        targetValue = if (isExpanded) 180f else 0f,
        animationSpec = tween(250)
    )

    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Color.White.copy(alpha = 0.03f))
            .animateContentSize(animationSpec = tween(250))
    ) {
        // Header row
        Row(
            modifier = Modifier
                .fillMaxWidth()
                .clickable { isExpanded = !isExpanded }
                .padding(14.dp),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(voice.emoji, fontSize = 24.sp)

            Column(
                modifier = Modifier.weight(1f),
                verticalArrangement = Arrangement.spacedBy(1.dp)
            ) {
                Text(
                    voice.name,
                    fontSize = 14.sp,
                    fontWeight = FontWeight.SemiBold,
                    color = ERColors.primaryText
                )
                Text(
                    voice.years,
                    fontSize = 11.sp,
                    color = ERColors.dimText
                )
            }

            Text(
                "\u25BC",
                fontSize = 11.sp,
                color = packColor,
                modifier = Modifier.rotate(chevronRotation)
            )
        }

        // Expanded content
        if (isExpanded) {
            Column(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 14.dp)
                    .padding(bottom = 14.dp),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                // Divider
                Box(
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(1.dp)
                        .background(Color.White.copy(alpha = 0.04f))
                )

                // Description
                Text(
                    voice.desc,
                    fontSize = 12.sp,
                    color = ERColors.secondaryText,
                    lineHeight = 16.sp
                )

                // Sample take
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .clip(RoundedCornerShape(12.dp))
                        .background(Color.White.copy(alpha = 0.02f))
                        .padding(14.dp),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    Text(
                        "SAMPLE TAKE",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Medium,
                        fontFamily = FontFamily.Monospace,
                        letterSpacing = 2.sp,
                        color = ERColors.dimText
                    )
                    Text(
                        voice.sampleHeadline,
                        style = ERTypography.serifHeadline(),
                        color = ERColors.primaryText,
                        lineHeight = 26.sp
                    )
                    Text(
                        voice.sampleBody,
                        fontSize = 11.5.sp,
                        fontWeight = FontWeight.Light,
                        color = ERColors.secondaryText,
                        lineHeight = 16.5.sp
                    )
                }
            }
        }
    }
}

@Composable
private fun PurchaseBar(
    pack: VoicePack,
    isOwned: Boolean,
    isPurchasing: Boolean = false,
    price: String = "$4.99",
    errorMessage: String? = null,
    onPurchase: () -> Unit
) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .background(ERColors.background)
    ) {
        // Top divider
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(Color.White.copy(alpha = 0.04f))
        )

        // Error message
        errorMessage?.let { msg ->
            Text(
                msg,
                fontSize = 12.sp,
                color = ERColors.accentRed,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 6.dp),
                textAlign = androidx.compose.ui.text.style.TextAlign.Center
            )
        }

        val buttonModifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 24.dp, vertical = 12.dp)
            .clip(RoundedCornerShape(14.dp))
        val bgModifier = if (isOwned) {
            buttonModifier.background(ERColors.accentGreen.copy(alpha = 0.12f))
        } else {
            buttonModifier.background(
                brush = androidx.compose.ui.graphics.Brush.linearGradient(
                    listOf(pack.color, pack.color.copy(alpha = 0.6f))
                )
            )
        }
        val finalModifier = bgModifier
            .then(if (!isOwned && !isPurchasing) Modifier.clickable(onClick = onPurchase) else Modifier)
            .padding(vertical = 16.dp)

        Box(
            modifier = finalModifier,
            contentAlignment = Alignment.Center
        ) {
            when {
                isOwned -> Text(
                    "\u2713 Purchased \u2014 Voices Active",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color = ERColors.accentGreen
                )
                isPurchasing -> CircularProgressIndicator(
                    modifier = Modifier.size(22.dp),
                    color = Color.White,
                    strokeWidth = 2.dp
                )
                else -> Text(
                    "Unlock ${pack.voices.size} Voices \u2014 $price",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color.White
                )
            }
        }
    }
}
