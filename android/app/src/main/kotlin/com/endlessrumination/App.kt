package com.endlessrumination

import androidx.compose.animation.*
import androidx.compose.animation.core.tween
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.DisposableEffect
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Modifier
import androidx.lifecycle.viewmodel.compose.viewModel
import com.endlessrumination.service.BillingService
import com.endlessrumination.theme.ERColors
import com.endlessrumination.ui.*

@Composable
fun App() {
    val appState: AppState = viewModel()

    // Initialize billing service
    LaunchedEffect(Unit) {
        val billing = BillingService(appState)
        appState.billingService = billing
        billing.initialize()
        val loadResult = billing.loadProducts()
        appState.productsLoaded = loadResult is com.endlessrumination.service.BillingResult.Success
        billing.checkEntitlements()
    }

    // Dispose billing on exit
    DisposableEffect(Unit) {
        onDispose {
            appState.billingService?.dispose()
        }
    }

    MaterialTheme(
        colorScheme = darkColorScheme(
            background = ERColors.background,
            surface = ERColors.inputBackground,
            onBackground = ERColors.primaryText,
            onSurface = ERColors.secondaryText,
            primary = ERColors.accentWarm
        )
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(ERColors.background)
                .safeDrawingPadding()
        ) {
            // Main screen content with animated transitions
            AnimatedContent(
                targetState = appState.currentScreen,
                transitionSpec = {
                    when {
                        // Splash → Input: slide in from right
                        initialState == AppScreen.SPLASH && targetState == AppScreen.INPUT ->
                            slideInHorizontally(tween(400)) { it } + fadeIn(tween(400)) togetherWith
                                    slideOutHorizontally(tween(400)) { -it } + fadeOut(tween(400))
                        // Input → Loading: fade
                        initialState == AppScreen.INPUT && targetState == AppScreen.LOADING ->
                            fadeIn(tween(300)) togetherWith fadeOut(tween(300))
                        // Loading → Takes: fade
                        initialState == AppScreen.LOADING && targetState == AppScreen.TAKES ->
                            fadeIn(tween(300)) togetherWith fadeOut(tween(300))
                        // Takes → Input (back): slide in from left
                        initialState == AppScreen.TAKES && targetState == AppScreen.INPUT ->
                            slideInHorizontally(tween(400)) { -it } + fadeIn(tween(400)) togetherWith
                                    slideOutHorizontally(tween(400)) { it } + fadeOut(tween(400))
                        // Default: crossfade
                        else -> fadeIn(tween(300)) togetherWith fadeOut(tween(300))
                    }
                },
                label = "screen_transition"
            ) { screen ->
                when (screen) {
                    AppScreen.SPLASH -> SplashScreen(appState)
                    AppScreen.INPUT -> ProblemInputScreen(appState)
                    AppScreen.LOADING -> LoadingScreen(appState)
                    AppScreen.TAKES -> TakesScreen(appState)
                }
            }

            // Full-screen overlays
            if (appState.showSafetyOverlay) {
                SafetyOverlayScreen(appState)
            }

            if (appState.showInstructionOverlay && appState.currentScreen == AppScreen.TAKES) {
                InstructionOverlayScreen(appState)
            }

            // One-time onboarding overlay (shown after first "Begin" tap)
            AnimatedVisibility(
                visible = appState.showOnboarding && appState.currentScreen == AppScreen.INPUT,
                enter = fadeIn(tween(300)),
                exit = fadeOut(tween(250))
            ) {
                OnboardingScreen(appState)
            }

            // AI consent dialog (shown before first submission)
            AnimatedVisibility(
                visible = appState.showAIConsent,
                enter = fadeIn(tween(300)),
                exit = fadeOut(tween(250))
            ) {
                AIConsentScreen(appState)
            }

            // Full-screen modals
            AnimatedVisibility(
                visible = appState.showShop,
                enter = slideInVertically(tween(300)) { it } + fadeIn(tween(300)),
                exit = slideOutVertically(tween(300)) { it } + fadeOut(tween(300))
            ) {
                ShopScreen(appState)
            }

            AnimatedVisibility(
                visible = appState.showPaywall,
                enter = slideInVertically(tween(300)) { it } + fadeIn(tween(300)),
                exit = slideOutVertically(tween(300)) { it } + fadeOut(tween(300))
            ) {
                ProUpgradeScreen(appState)
            }
        }
    }
}
