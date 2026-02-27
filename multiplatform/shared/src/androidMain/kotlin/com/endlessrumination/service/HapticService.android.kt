package com.endlessrumination.service

import android.content.Context
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager

actual object HapticService {
    private var context: Context? = null

    fun init(context: Context) {
        this.context = context.applicationContext
    }

    private fun vibrate(durationMs: Long, amplitude: Int) {
        val ctx = context ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            val vibratorManager = ctx.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager
            vibratorManager?.defaultVibrator?.vibrate(
                VibrationEffect.createOneShot(durationMs, amplitude)
            )
        } else if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            @Suppress("DEPRECATION")
            val vibrator = ctx.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
            vibrator?.vibrate(VibrationEffect.createOneShot(durationMs, amplitude))
        }
    }

    actual fun light() {
        vibrate(10, 40)
    }

    actual fun medium() {
        vibrate(20, 120)
    }

    actual fun selection() {
        vibrate(5, 20)
    }
}
