package com.endlessrumination.service

import platform.UIKit.UIImpactFeedbackGenerator
import platform.UIKit.UIImpactFeedbackStyle
import platform.UIKit.UISelectionFeedbackGenerator

actual object HapticService {
    private val lightGenerator = UIImpactFeedbackGenerator(style = UIImpactFeedbackStyle.UIImpactFeedbackStyleLight)
    private val mediumGenerator = UIImpactFeedbackGenerator(style = UIImpactFeedbackStyle.UIImpactFeedbackStyleMedium)
    private val selectionGenerator = UISelectionFeedbackGenerator()

    actual fun light() {
        lightGenerator.prepare()
        lightGenerator.impactOccurred()
    }

    actual fun medium() {
        mediumGenerator.prepare()
        mediumGenerator.impactOccurred()
    }

    actual fun selection() {
        selectionGenerator.prepare()
        selectionGenerator.selectionChanged()
    }
}
