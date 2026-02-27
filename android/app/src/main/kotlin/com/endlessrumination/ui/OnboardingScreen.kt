package com.endlessrumination.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography

@Composable
fun OnboardingScreen(appState: AppState) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(ERColors.background.copy(alpha = 0.95f)),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(horizontal = 24.dp)
        ) {
            // Logo
            Box(
                modifier = Modifier
                    .size(48.dp)
                    .clip(RoundedCornerShape(14.dp))
                    .background(
                        Brush.linearGradient(
                            listOf(ERColors.accentWarm, ERColors.accentGold)
                        )
                    ),
                contentAlignment = Alignment.Center
            ) {
                Text("\u221E", fontSize = 24.sp, color = Color.White)
            }

            Spacer(modifier = Modifier.height(20.dp))

            // Title
            Text(
                "How It Works",
                style = ERTypography.serifHeadline(),
                color = ERColors.primaryText
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Separator
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp)
                    .height(1.dp)
                    .background(ERColors.dimText.copy(alpha = 0.3f))
            )

            Spacer(modifier = Modifier.height(24.dp))

            // Steps
            Column(
                modifier = Modifier.padding(horizontal = 8.dp),
                verticalArrangement = Arrangement.spacedBy(20.dp)
            ) {
                StepRow(
                    emoji = "\uD83D\uDCDD",
                    title = "Write what\u2019s on your mind",
                    subtitle = "Any worry, decision, or thought"
                )

                StepRow(
                    emoji = "\uD83C\uDFAD",
                    title = "Get fresh perspectives",
                    subtitle = "AI personas react \u2014 comedian, stoic, therapist, your dog..."
                )

                StepRow(
                    emoji = "\u2191",
                    title = "Swipe through & let go",
                    subtitle = "Each take fades forever.\nNo overthinking \u2014 just new angles."
                )
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Separator
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(horizontal = 20.dp)
                    .height(1.dp)
                    .background(ERColors.dimText.copy(alpha = 0.3f))
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Got it button
            Box(
                modifier = Modifier
                    .background(ERColors.primaryText, RoundedCornerShape(50))
                    .clickable { appState.dismissOnboarding() }
                    .padding(horizontal = 48.dp, vertical = 14.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    "Got it",
                    fontSize = 15.sp,
                    fontWeight = FontWeight.Medium,
                    color = ERColors.background
                )
            }
        }
    }
}

@Composable
private fun StepRow(emoji: String, title: String, subtitle: String) {
    Row(
        horizontalArrangement = Arrangement.spacedBy(14.dp),
        modifier = Modifier.fillMaxWidth()
    ) {
        Text(
            emoji,
            fontSize = 22.sp,
            modifier = Modifier.width(32.dp),
            textAlign = TextAlign.Center
        )

        Column(verticalArrangement = Arrangement.spacedBy(3.dp)) {
            Text(
                title,
                fontSize = 14.sp,
                fontWeight = FontWeight.SemiBold,
                color = ERColors.primaryText
            )
            Text(
                subtitle,
                fontSize = 12.sp,
                color = ERColors.secondaryText,
                lineHeight = 16.sp
            )
        }
    }
}
