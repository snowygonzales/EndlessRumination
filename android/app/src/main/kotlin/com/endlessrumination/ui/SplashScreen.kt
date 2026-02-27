package com.endlessrumination.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppScreen
import com.endlessrumination.AppState
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography

@Composable
fun SplashScreen(appState: AppState) {
    Column(
        modifier = Modifier.fillMaxSize().background(ERColors.background),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        // Logo
        Box(
            modifier = Modifier
                .size(80.dp)
                .background(ERColors.logoGradient, RoundedCornerShape(20.dp)),
            contentAlignment = Alignment.Center
        ) {
            Text(
                text = "\u221E",
                style = TextStyle(fontSize = 36.sp, color = ERColors.primaryText, fontWeight = FontWeight.Light)
            )
        }

        Spacer(modifier = Modifier.height(24.dp))

        // Title
        Text(
            text = "Endless Rumination",
            style = ERTypography.appTitle.copy(brush = ERColors.titleGradient),
            textAlign = TextAlign.Center
        )

        Spacer(modifier = Modifier.height(8.dp))

        // Tagline
        Text(
            text = "SCROLL YOUR WORRIES",
            style = TextStyle(
                fontSize = 15.sp,
                fontWeight = FontWeight.Light,
                letterSpacing = 3.sp,
                color = ERColors.secondaryText
            )
        )

        Spacer(modifier = Modifier.height(40.dp))

        // Begin button
        Button(
            onClick = { appState.currentScreen = AppScreen.INPUT },
            modifier = Modifier
                .fillMaxWidth()
                .padding(horizontal = 48.dp)
                .height(56.dp),
            shape = RoundedCornerShape(28.dp),
            colors = ButtonDefaults.buttonColors(
                containerColor = ERColors.primaryText,
                contentColor = ERColors.background
            )
        ) {
            Text(
                text = "Begin",
                style = ERTypography.button.copy(color = ERColors.background)
            )
        }
    }
}
