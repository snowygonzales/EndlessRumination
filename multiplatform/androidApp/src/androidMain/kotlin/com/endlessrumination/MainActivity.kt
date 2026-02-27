package com.endlessrumination

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.endlessrumination.service.BillingService
import com.endlessrumination.service.HapticService
import com.google.android.gms.ads.MobileAds

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Initialize billing context, haptics, and AdMob before Compose renders
        BillingService.init(this)
        HapticService.init(this)
        MobileAds.initialize(this)
        setContent {
            App()
        }
    }
}
