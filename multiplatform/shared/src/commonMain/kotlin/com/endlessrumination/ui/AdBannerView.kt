package com.endlessrumination.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.theme.ERColors

@Composable
fun AdBannerView(appState: AppState) {
    Box(
        modifier = Modifier
            .fillMaxWidth()
            .height(50.dp)
            .background(ERColors.inputBackground)
    ) {
        // Top border
        Box(
            modifier = Modifier
                .fillMaxWidth()
                .height(1.dp)
                .background(ERColors.border)
        )

        Row(
            modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
            horizontalArrangement = Arrangement.Center,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                "mindfulness app \u2014 download free",
                fontSize = 11.sp,
                color = ERColors.dimText,
                letterSpacing = 1.sp
            )
            Spacer(modifier = Modifier.width(12.dp))
            Text(
                "Remove",
                fontSize = 11.sp,
                fontWeight = FontWeight.SemiBold,
                color = ERColors.accentGold,
                modifier = Modifier.clickable { appState.showPaywall = true }
            )
        }

        // AD label
        Text(
            "AD",
            fontSize = 8.sp,
            color = ERColors.dimText,
            modifier = Modifier.align(Alignment.TopEnd).padding(end = 8.dp, top = 4.dp)
        )
    }
}
