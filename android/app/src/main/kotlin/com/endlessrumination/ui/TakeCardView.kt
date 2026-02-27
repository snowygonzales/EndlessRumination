package com.endlessrumination.ui

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.endlessrumination.model.Lens
import com.endlessrumination.model.Take
import com.endlessrumination.theme.ERColors
import com.endlessrumination.theme.ERTypography

@Composable
fun TakeCardView(take: Take) {
    val display = Lens.displayInfo(take.lensIndex)

    Column(modifier = Modifier.fillMaxWidth()) {
        // Badge row
        Row(
            horizontalArrangement = Arrangement.spacedBy(6.dp),
            modifier = Modifier.padding(bottom = 16.dp)
        ) {
            // Voice name badge
            Row(
                modifier = Modifier
                    .background(display.bgColor, RoundedCornerShape(50))
                    .padding(horizontal = 14.dp, vertical = 6.dp),
                horizontalArrangement = Arrangement.spacedBy(4.dp)
            ) {
                Text(display.emoji, fontSize = 12.sp)
                Text(
                    display.name.uppercase(),
                    fontSize = 12.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 2.sp,
                    color = display.color
                )
            }

            // "WISE" badge
            if (take.wise || take.isPackVoice) {
                Row(
                    modifier = Modifier
                        .background(ERColors.accentGold.copy(alpha = 0.12f), RoundedCornerShape(50))
                        .padding(horizontal = 10.dp, vertical = 5.dp),
                    horizontalArrangement = Arrangement.spacedBy(4.dp)
                ) {
                    Text("\u2728", fontSize = 9.sp)
                    Text(
                        "WISE",
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        letterSpacing = 1.5.sp,
                        color = ERColors.accentGold
                    )
                }
            }

            // Pack name badge
            val packName = take.packName
            if (packName != null) {
                Text(
                    packName.uppercase(),
                    fontSize = 9.sp,
                    fontWeight = FontWeight.Bold,
                    letterSpacing = 1.5.sp,
                    color = display.color.copy(alpha = 0.7f),
                    modifier = Modifier
                        .background(display.color.copy(alpha = 0.08f), RoundedCornerShape(50))
                        .padding(horizontal = 8.dp, vertical = 4.dp)
                )
            }
        }

        // Headline
        Text(
            text = take.headline,
            style = ERTypography.headline.copy(color = ERColors.primaryText, lineHeight = 28.sp),
            modifier = Modifier.padding(bottom = 16.dp)
        )

        // Body (scrollable)
        Column(
            modifier = Modifier
                .weight(1f)
                .verticalScroll(rememberScrollState())
        ) {
            Text(
                text = take.body,
                style = ERTypography.body.copy(color = ERColors.secondaryText, lineHeight = 20.sp)
            )

            if (!take.wise) {
                Spacer(modifier = Modifier.height(16.dp))
                Text(
                    text = "Quick take \u00B7 Powered by Haiku",
                    fontSize = 10.sp,
                    color = ERColors.dimText
                )
            }
        }
    }
}
