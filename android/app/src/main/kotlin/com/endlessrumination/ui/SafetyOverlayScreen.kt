package com.endlessrumination.ui

import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.AppState
import com.endlessrumination.service.SafetyService
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography

@Composable
fun SafetyOverlayScreen(appState: AppState) {
    val context = LocalContext.current
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(ERColors.background.copy(alpha = 0.95f)),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            modifier = Modifier.padding(horizontal = 40.dp)
        ) {
            // Shield icon circle
            Box(
                modifier = Modifier
                    .size(64.dp)
                    .background(ERColors.accentRed.copy(alpha = 0.15f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Text("\uD83D\uDEE1\uFE0F", fontSize = 28.sp)
            }

            Spacer(modifier = Modifier.height(20.dp))

            Text(
                "We can\u2019t process this",
                style = ERTypography.headline.copy(color = ERColors.primaryText),
                textAlign = TextAlign.Center
            )

            Spacer(modifier = Modifier.height(12.dp))

            Text(
                "Your input was flagged by our safety system. If you\u2019re going through a difficult time, please reach out to a crisis resource.",
                fontSize = 14.sp,
                color = ERColors.secondaryText,
                textAlign = TextAlign.Center,
                lineHeight = 20.sp
            )

            Spacer(modifier = Modifier.height(20.dp))

            // Crisis resources (tappable)
            for (resource in SafetyService.crisisResources) {
                Column(
                    horizontalAlignment = Alignment.CenterHorizontally,
                    modifier = Modifier.clickable {
                        val intent = when (resource.action) {
                            "call" -> Intent(Intent.ACTION_DIAL, Uri.parse("tel:${resource.value}"))
                            "text" -> Intent(Intent.ACTION_SENDTO, Uri.parse("smsto:741741")).apply {
                                putExtra("sms_body", "HOME")
                            }
                            else -> null
                        }
                        intent?.let { context.startActivity(it) }
                    }
                ) {
                    Text(
                        "${resource.name}: ${resource.value}",
                        fontSize = 13.sp,
                        color = ERColors.accentCool,
                        textAlign = TextAlign.Center
                    )
                    Text(
                        resource.description,
                        fontSize = 11.sp,
                        color = ERColors.dimText,
                        textAlign = TextAlign.Center
                    )
                }
                Spacer(modifier = Modifier.height(8.dp))
            }

            Spacer(modifier = Modifier.height(24.dp))

            // Edit button
            Box(
                modifier = Modifier
                    .fillMaxWidth()
                    .background(ERColors.inputBackground, RoundedCornerShape(50))
                    .clickable { appState.showSafetyOverlay = false }
                    .padding(vertical = 14.dp),
                contentAlignment = Alignment.Center
            ) {
                Text(
                    "Edit my input",
                    fontSize = 14.sp,
                    color = ERColors.primaryText
                )
            }
        }
    }
}
