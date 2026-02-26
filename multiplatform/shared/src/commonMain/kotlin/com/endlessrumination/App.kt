package com.endlessrumination

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp

@Composable
fun App() {
    var backendStatus by remember { mutableStateOf("Checking...") }
    val apiClient = remember { ApiClient() }

    LaunchedEffect(Unit) {
        backendStatus = try {
            val health = apiClient.healthCheck("https://backend-production-5537.up.railway.app")
            "${health.app}: ${health.status}"
        } catch (e: Exception) {
            "Offline: ${e.message?.take(40)}"
        }
    }

    MaterialTheme(
        colorScheme = darkColorScheme(
            background = Color(0xFF0A0A0C),
            surface = Color(0xFF1A1A20),
            onBackground = Color(0xFFF0ECE4),
            onSurface = Color(0xFF8A8690),
            primary = Color(0xFFE8653A)
        )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .background(MaterialTheme.colorScheme.background),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Text(
                text = "∞",
                fontSize = 64.sp,
                color = Color(0xFFE8653A),
                fontWeight = FontWeight.Light
            )
            Spacer(modifier = Modifier.height(16.dp))
            Text(
                text = "Endless Rumination",
                fontSize = 28.sp,
                color = Color(0xFFF0ECE4),
                fontWeight = FontWeight.Bold
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = "Scroll your worries",
                fontSize = 16.sp,
                color = Color(0xFF8A8690)
            )
            Spacer(modifier = Modifier.height(24.dp))
            Text(
                text = "Running on ${getPlatformName()}",
                fontSize = 14.sp,
                color = Color(0xFF4A4650)
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "Backend: $backendStatus",
                fontSize = 14.sp,
                color = if (backendStatus.contains("ok")) Color(0xFF3ECF8E) else Color(0xFF8A8690)
            )
        }
    }
}
