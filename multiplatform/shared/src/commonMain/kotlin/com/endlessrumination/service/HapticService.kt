package com.endlessrumination.service

/**
 * Cross-platform haptic feedback service.
 *
 * Provides light, medium, and selection haptic patterns.
 * - iOS: UIImpactFeedbackGenerator / UISelectionFeedbackGenerator
 * - Android: View.performHapticFeedback via HapticFeedbackConstants
 */
expect object HapticService {
    /** Light impact — used for swipe gestures. */
    fun light()

    /** Medium impact — used for button taps like submit. */
    fun medium()

    /** Selection tick — used for text input changes. */
    fun selection()
}
