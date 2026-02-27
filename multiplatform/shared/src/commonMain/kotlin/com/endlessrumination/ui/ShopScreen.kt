package com.endlessrumination.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.model.Lens
import com.endlessrumination.model.VoicePack
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography
import androidx.compose.ui.text.style.TextAlign
import kotlinx.coroutines.launch

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun ShopScreen(appState: AppState) {
    var selectedPack by remember { mutableStateOf<VoicePack?>(null) }
    val scope = rememberCoroutineScope()

    val currentPack = selectedPack
    if (currentPack != null) {
        PackDetailScreen(
            pack = currentPack,
            appState = appState,
            onBack = { selectedPack = null }
        )
        return
    }

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
                // Back button
                Text(
                    "\u2190 Back",
                    fontSize = 14.sp,
                    color = ERColors.secondaryText,
                    modifier = Modifier
                        .align(Alignment.CenterStart)
                        .clickable { appState.showShop = false }
                )

                // Title
                Text(
                    "PERSPECTIVE SHOP",
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
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 24.dp)
                    .padding(top = 12.dp),
                verticalArrangement = Arrangement.spacedBy(20.dp)
            ) {
                // Pro subscription card (only for free tier)
                if (!appState.isPro) {
                    ProCard(appState)
                }

                // Free perspectives section
                FreeLensesSection()

                // Voice packs section
                VoicePacksSection(appState, onPackTap = { selectedPack = it })

                // Products not loaded notice
                if (!appState.productsLoaded) {
                    Text(
                        "Products loading\u2026 Prices may be unavailable.",
                        fontSize = 11.sp,
                        color = ERColors.dimText,
                        textAlign = TextAlign.Center,
                        modifier = Modifier.fillMaxWidth()
                    )
                }

                // Coming soon
                ComingSoonCard()

                // Restore purchases
                Text(
                    "Restore Purchases",
                    fontSize = 14.sp,
                    color = ERColors.secondaryText,
                    textAlign = TextAlign.Center,
                    modifier = Modifier
                        .fillMaxWidth()
                        .clickable {
                            scope.launch { appState.restorePurchases() }
                        }
                )

                Spacer(modifier = Modifier.height(40.dp))
            }
        }
    }
}

@Composable
private fun ProCard(appState: AppState) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(
                brush = androidx.compose.ui.graphics.Brush.linearGradient(
                    listOf(Color(0xFF1A1510), Color(0xFF1A1A20), Color(0xFF15101A))
                )
            )
            .clickable {
                appState.showShop = false
                appState.showPaywall = true
            }
    ) {
        Column {
            // Shimmer top bar
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .height(2.dp)
                    .background(
                        brush = androidx.compose.ui.graphics.Brush.horizontalGradient(
                            listOf(Color.Transparent, ERColors.accentGold.copy(alpha = 0.4f), Color.Transparent)
                        )
                    )
            )

            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(20.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Row(
                        horizontalArrangement = Arrangement.spacedBy(8.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("\u221E", fontSize = 20.sp, color = ERColors.primaryText)
                        Text(
                            "Go Pro",
                            style = ERTypography.serifTitle(),
                            color = ERColors.primaryText
                        )
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        "No ads \u00B7 Unlimited daily takes \u00B7 Save history",
                        fontSize = 12.sp,
                        color = ERColors.secondaryText
                    )
                }

                Text(
                    appState.getProPrice(),
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = ERColors.background,
                    modifier = Modifier
                        .background(ERColors.proGradient, RoundedCornerShape(50))
                        .padding(horizontal = 16.dp, vertical = 10.dp)
                )
            }
        }

    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun FreeLensesSection() {
    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Text(
                "Free Perspectives",
                fontSize = 13.sp,
                fontWeight = FontWeight.SemiBold,
                color = ERColors.primaryText
            )
            Text(
                "${Lens.all.size} included",
                fontSize = 11.sp,
                color = ERColors.dimText
            )
        }

        // Flow layout for lens chips
        FlowRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            for (lens in Lens.all) {
                Row(
                    modifier = Modifier
                        .background(Color.White.copy(alpha = 0.04f), RoundedCornerShape(50))
                        .padding(horizontal = 10.dp, vertical = 4.dp),
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(lens.emoji, fontSize = 11.sp)
                    Text(lens.name, fontSize = 11.sp, color = ERColors.secondaryText)
                }
            }
        }
    }
}

@Composable
private fun VoicePacksSection(appState: AppState, onPackTap: (VoicePack) -> Unit) {
    Column(verticalArrangement = Arrangement.spacedBy(14.dp)) {
        Text(
            "Voice Packs",
            fontSize = 13.sp,
            fontWeight = FontWeight.SemiBold,
            color = ERColors.primaryText
        )

        for (pack in VoicePack.all) {
            PackCardView(
                pack = pack,
                isOwned = appState.ownedPackIDs.contains(pack.productID),
                price = appState.getPackPrice(pack.productID),
                onTap = { onPackTap(pack) }
            )
        }
    }
}

@OptIn(ExperimentalLayoutApi::class)
@Composable
private fun PackCardView(pack: VoicePack, isOwned: Boolean, price: String = "$4.99", onTap: () -> Unit) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(20.dp))
            .background(pack.bgGradient)
            .clickable(onClick = onTap)
            .padding(18.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.Top
        ) {
            Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                Text(pack.icon, fontSize = 28.sp)
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    pack.name,
                    style = ERTypography.serifHeadline(),
                    color = ERColors.primaryText
                )
                Text(
                    pack.subtitle,
                    fontSize = 11.sp,
                    color = ERColors.secondaryText
                )
            }

            if (isOwned) {
                Text(
                    "\u2713 Owned",
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = ERColors.accentGreen,
                    modifier = Modifier
                        .background(ERColors.accentGreen.copy(alpha = 0.15f), RoundedCornerShape(50))
                        .padding(horizontal = 14.dp, vertical = 6.dp)
                )
            } else {
                Text(
                    price,
                    fontSize = 13.sp,
                    fontWeight = FontWeight.Bold,
                    color = pack.color,
                    modifier = Modifier
                        .background(pack.color.copy(alpha = 0.15f), RoundedCornerShape(50))
                        .padding(horizontal = 14.dp, vertical = 6.dp)
                )
            }
        }

        // Voice chips flow
        FlowRow(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)
        ) {
            for (voice in pack.voices) {
                Row(
                    modifier = Modifier
                        .background(Color.White.copy(alpha = 0.04f), RoundedCornerShape(50))
                        .padding(horizontal = 8.dp, vertical = 3.dp),
                    horizontalArrangement = Arrangement.spacedBy(4.dp),
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(voice.emoji, fontSize = 11.sp)
                    Text(voice.name, fontSize = 11.sp, color = ERColors.secondaryText)
                }
            }
        }
    }
}

@Composable
private fun ComingSoonCard() {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 28.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Text(
            "COMING SOON",
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium,
            fontFamily = FontFamily.Monospace,
            letterSpacing = 2.sp,
            color = ERColors.dimText
        )
        Text(
            "The Scientists \u00B7 The Leaders \u00B7 The Writers",
            fontSize = 12.sp,
            color = ERColors.secondaryText
        )
    }
}

