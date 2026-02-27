package com.endlessrumination.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.service.PurchaseUiState
import com.endlessrumination.service.rememberActivityProvider
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography
import kotlinx.coroutines.launch

@Composable
fun ProUpgradeScreen(appState: AppState) {
    val scope = rememberCoroutineScope()
    val activityProvider = rememberActivityProvider()
    val isPurchasing = appState.purchaseState == PurchaseUiState.PURCHASING

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(ERColors.background)
    ) {
        Column(
            modifier = Modifier.fillMaxSize()
        ) {
            // Dismiss button
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp, vertical = 16.dp),
                horizontalArrangement = Arrangement.End
            ) {
                Box(
                    modifier = Modifier
                        .size(32.dp)
                        .background(ERColors.inputBackground, CircleShape)
                        .clickable { appState.showPaywall = false },
                    contentAlignment = Alignment.Center
                ) {
                    Text(
                        "\u2715",
                        fontSize = 16.sp,
                        fontWeight = FontWeight.Medium,
                        color = ERColors.secondaryText
                    )
                }
            }

            Spacer(modifier = Modifier.height(32.dp))

            // Title
            Text(
                "Go Pro",
                style = ERTypography.serifLargeTitle(),
                color = ERColors.accentGold,
                modifier = Modifier.fillMaxWidth(),
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                "Unlock the full experience",
                fontSize = 15.sp,
                color = ERColors.secondaryText,
                modifier = Modifier.fillMaxWidth(),
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(40.dp))

            // Benefits
            Column(
                modifier = Modifier.padding(horizontal = 32.dp),
                verticalArrangement = Arrangement.spacedBy(20.dp)
            ) {
                BenefitRow(icon = "\u2728", text = "All 20 perspectives on every problem")
                BenefitRow(icon = "\uD83E\uDDE0", text = "Premium AI for deeper, wiser takes")
                BenefitRow(icon = "\uD83D\uDEAB", text = "No ads")
                BenefitRow(icon = "\uD83D\uDD04", text = "Save your history forever")
            }

            Spacer(modifier = Modifier.height(48.dp))

            // Subscribe button
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 24.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(ERColors.warmGradient)
                    .then(
                        if (!isPurchasing) Modifier.clickable {
                            scope.launch { appState.purchasePro(activityProvider) }
                        } else Modifier
                    )
                    .padding(vertical = 18.dp),
                contentAlignment = Alignment.Center
            ) {
                if (isPurchasing) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(22.dp),
                        color = Color.White,
                        strokeWidth = 2.dp
                    )
                } else {
                    Text(
                        "Subscribe for ${appState.getProPrice()}/month",
                        fontSize = 17.sp,
                        fontWeight = FontWeight.SemiBold,
                        color = Color.White
                    )
                }
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Restore purchases
            Text(
                "Restore Purchases",
                fontSize = 14.sp,
                color = ERColors.secondaryText,
                modifier = Modifier
                    .fillMaxWidth()
                    .clickable {
                        scope.launch { appState.restorePurchases() }
                    },
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.weight(1f))

            // Fine print
            Text(
                "Cancel anytime. Subscription auto-renews monthly.",
                fontSize = 11.sp,
                color = ERColors.dimText,
                textAlign = TextAlign.Center,
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 32.dp)
                    .padding(bottom = 24.dp)
            )
        }
    }
}

@Composable
private fun BenefitRow(icon: String, text: String) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(14.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            icon,
            fontSize = 18.sp,
            modifier = Modifier.width(28.dp)
        )
        Text(
            text,
            fontSize = 15.sp,
            color = ERColors.primaryText
        )
    }
}
