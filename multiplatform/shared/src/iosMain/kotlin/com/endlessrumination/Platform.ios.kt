package com.endlessrumination

import platform.UIKit.UIDevice

actual fun getPlatformName(): String =
    UIDevice.currentDevice.systemName() + " " + UIDevice.currentDevice.systemVersion

actual fun getBaseUrl(): String = "https://backend-production-5537.up.railway.app"
