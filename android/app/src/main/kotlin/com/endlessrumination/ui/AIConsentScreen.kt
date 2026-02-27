package com.endlessrumination.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.withStyle
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography

@Composable
fun AIConsentScreen(appState: AppState) {
    val context = LocalContext.current

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
            // Icon
            Text("\uD83E\uDDE0", fontSize = 28.sp)

            Spacer(modifier = Modifier.height(20.dp))

            // Title
            Text(
                "AI Data Processing",
                style = ERTypography.serifHeadline(),
                color = ERColors.primaryText
            )

            Spacer(modifier = Modifier.height(12.dp))

            // Description
            Text(
                buildAnnotatedString {
                    append("Your problem text is sent to ")
                    withStyle(SpanStyle(fontWeight = FontWeight.Bold)) {
                        append("Anthropic\u2019s Claude AI")
                    }
                    append(" to generate perspectives. Anthropic does not use your data to train their models.")
                },
                fontSize = 14.sp,
                color = ERColors.secondaryText,
                textAlign = TextAlign.Center,
                lineHeight = 20.sp,
                modifier = Modifier.padding(horizontal = 8.dp)
            )

            Spacer(modifier = Modifier.height(20.dp))

            // Links
            Text(
                "Privacy Policy",
                fontSize = 13.sp,
                color = ERColors.accentCool,
                modifier = Modifier.clickable {
                    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md")))
                }
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                "Terms of Service",
                fontSize = 13.sp,
                color = ERColors.accentCool,
                modifier = Modifier.clickable {
                    context.startActivity(Intent(Intent.ACTION_VIEW, Uri.parse("https://github.com/snowygonzales/EndlessRumination/blob/master/docs/terms-of-service.md")))
                }
            )

            Spacer(modifier = Modifier.height(32.dp))

            // Consent button
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(14.dp))
                    .background(ERColors.warmGradient)
                    .clickable { appState.consentToAI() }
                    .padding(vertical = 16.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    "I Agree",
                    style = ERTypography.button.copy(color = Color.White)
                )
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Decline text
            Text(
                "You must agree to use the app.",
                fontSize = 11.sp,
                color = ERColors.dimText
            )
        }
    }
}
