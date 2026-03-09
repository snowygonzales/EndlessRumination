# Screenshot Capture Procedure

Automated capture of App Store listing and IAP review screenshots using `ScreenshotHostView` (DEBUG-only) and `xcrun simctl`.

---

## Prerequisites

1. **Xcode project generated:** `cd ios && xcodegen generate`
2. **Simulator build:** `xcodebuild -scheme EndlessRumination -sdk iphonesimulator -destination 'platform=iOS Simulator,id=<DEVICE_ID>' -configuration Debug build`
3. **ScreenshotHostView.swift** must be up to date with all screen cases

## Simulators

| Device | Size Category | Resolution | Simulator ID |
|--------|--------------|------------|--------------|
| iPhone 17 Pro | 6.5" (maps to 6.7" ASC slot) | 1206x2622 | `8C545099-AF9E-4D62-A716-E0826851F18D` |
| iPhone 17 Pro Max | 6.9" (also usable for 6.7" via resize) | 1320x2868 | `132E1E30-3267-487B-844F-1A40362D485F` |

**Primary simulator:** iPhone 17 Pro Max -- captures at 6.9" native, then resize to 1290x2796 for 6.7".

## Locale Setup (USD Pricing)

The simulator must be set to US English locale so StoreKit price fallbacks display as "$X.XX" instead of the host machine's locale. This only needs to be done once per simulator, but reboot is required.

```bash
# Set US locale (requires simulator reboot)
xcrun simctl spawn <DEVICE_ID> defaults write -g AppleLocale -string "en_US"
xcrun simctl spawn <DEVICE_ID> defaults write -g AppleLanguages -array "en"

# Reboot simulator for locale change to take effect
xcrun simctl shutdown <DEVICE_ID>
sleep 2
xcrun simctl boot <DEVICE_ID>
sleep 5

# Restore Romanian locale when done (optional)
xcrun simctl spawn <DEVICE_ID> defaults write -g AppleLocale -string "ro_RO"
xcrun simctl spawn <DEVICE_ID> defaults write -g AppleLanguages -array "en"
```

## Available Screenshot Screens

Launch argument: `-screenshot-screen <screen-name>`

### App Store Listing Screenshots
| Screen Name | Description |
|-------------|-------------|
| `splash` | Splash screen with app icon and tagline |
| `input` | Problem input (free user, with sample text) |
| `input-pro` | Problem input (Pro user) |
| `takes` | Take 1/5 -- The Comedian |
| `takes-2` | Take 2/5 -- The Stoic |
| `takes-3` | Take 3/5 -- The Therapist |
| `takes-4` | Take 4/5 -- Your Dog |
| `takes-pro` | Take 1/5 -- Pro user (swipe to browse) |
| `shop` | Shop screen |

### IAP Review Screenshots
| Screen Name | Description | Product |
|-------------|-------------|---------|
| `paywall` | Pro subscription paywall | `com.endlessrumination.pro.monthly` |
| `pack-strategists` | Strategists voice pack detail | `com.endlessrumination.pack.strategists` |
| `pack-revolutionaries` | Revolutionaries voice pack detail | `com.endlessrumination.pack.revolutionaries` |
| `pack-philosophers` | Philosophers voice pack detail | `com.endlessrumination.pack.philosophers` |
| `pack-creators` | Creators voice pack detail | `com.endlessrumination.pack.creators` |
| `extra-takes` | Extra takes prompt (take 5/5, free user) | `com.endlessrumination.extra.takes` |

## Capture Procedure

### Full capture (all screens, both sizes)

```bash
PROJ="/Users/bogdanlucaci/Library/CloudStorage/OneDrive-Personal/CodeProjects/Claude/EndlessRumination"
SIM_ID="132E1E30-3267-487B-844F-1A40362D485F"  # iPhone 17 Pro Max
BUNDLE="com.endlessrumination.EndlessRumination"
APP_PATH="$(find ~/Library/Developer/Xcode/DerivedData/EndlessRumination-*/Build/Products/Debug-iphonesimulator/EndlessRumination.app -maxdepth 0 2>/dev/null | head -1)"

# 1. Build for simulator
cd "$PROJ/ios" && xcodegen generate
xcodebuild -scheme EndlessRumination -sdk iphonesimulator \
  -destination "platform=iOS Simulator,id=$SIM_ID" \
  -configuration Debug build

# 2. Boot simulator with US locale
xcrun simctl boot $SIM_ID 2>/dev/null || true
xcrun simctl spawn $SIM_ID defaults write -g AppleLocale -string "en_US"
xcrun simctl spawn $SIM_ID defaults write -g AppleLanguages -array "en"
xcrun simctl shutdown $SIM_ID && sleep 2 && xcrun simctl boot $SIM_ID && sleep 5

# 3. Install the app
xcrun simctl install $SIM_ID "$APP_PATH"

# 4. Capture each screen
capture() {
  local screen=$1 output=$2
  xcrun simctl terminate $SIM_ID $BUNDLE 2>/dev/null || true
  sleep 1
  xcrun simctl launch $SIM_ID $BUNDLE -screenshot-screen "$screen"
  sleep 4
  xcrun simctl io $SIM_ID screenshot "$output"
  echo "Captured: $output"
}

# Store listing screenshots (6.9-inch native)
capture splash       "$PROJ/docs/screenshots/6.9-inch/store/01_splash.png"
capture input        "$PROJ/docs/screenshots/6.9-inch/store/02_input.png"
capture takes        "$PROJ/docs/screenshots/6.9-inch/store/03_takes_comedian.png"
capture takes-3      "$PROJ/docs/screenshots/6.9-inch/store/04_takes_therapist.png"
capture takes-4      "$PROJ/docs/screenshots/6.9-inch/store/05_takes_dog.png"
capture shop         "$PROJ/docs/screenshots/6.9-inch/store/06_shop.png"

# IAP review screenshots (6.9-inch native)
capture paywall              "$PROJ/docs/screenshots/6.9-inch/iap/01_pro_paywall.png"
capture pack-strategists     "$PROJ/docs/screenshots/6.9-inch/iap/02_pack_strategists.png"
capture pack-revolutionaries "$PROJ/docs/screenshots/6.9-inch/iap/03_pack_revolutionaries.png"
capture pack-philosophers    "$PROJ/docs/screenshots/6.9-inch/iap/04_pack_philosophers.png"
capture pack-creators        "$PROJ/docs/screenshots/6.9-inch/iap/05_pack_creators.png"
capture extra-takes          "$PROJ/docs/screenshots/6.9-inch/iap/06_extra_takes.png"

# 5. Generate 6.7-inch versions (resize from 1320x2868 to 1290x2796)
for dir in store iap; do
  for f in "$PROJ/docs/screenshots/6.9-inch/$dir/"*.png; do
    base=$(basename "$f")
    sips -z 2796 1290 "$f" --out "$PROJ/docs/screenshots/6.7-inch/$dir/$base"
  done
done

echo "Done! All screenshots captured."
```

### Single screen capture

```bash
SIM_ID="132E1E30-3267-487B-844F-1A40362D485F"
BUNDLE="com.endlessrumination.EndlessRumination"

# Terminate any running instance, launch with screenshot arg, capture
xcrun simctl terminate $SIM_ID $BUNDLE 2>/dev/null || true
sleep 1
xcrun simctl launch $SIM_ID $BUNDLE -screenshot-screen extra-takes
sleep 4
xcrun simctl io $SIM_ID screenshot /tmp/screenshot.png

# Verify
open /tmp/screenshot.png
```

## Output Directory Structure

```
docs/screenshots/
  6.9-inch/           # Native from iPhone 17 Pro Max (1320x2868)
    store/            # App Store listing screenshots
      01_splash.png
      02_input.png
      03_takes_comedian.png
      04_takes_therapist.png
      05_takes_dog.png
      06_shop.png
    iap/              # IAP review screenshots (one per product)
      01_pro_paywall.png
      02_pack_strategists.png
      03_pack_revolutionaries.png
      04_pack_philosophers.png
      05_pack_creators.png
      06_extra_takes.png
  6.7-inch/           # Resized from 6.9-inch (1290x2796)
    store/            # (same filenames)
    iap/              # (same filenames)
```

## Notes

- **IMPORTANT:** The app must be freshly installed on the simulator (`xcrun simctl install`) after each build. The simulator may cache a stale version otherwise.
- `ScreenshotHostView` is `#if DEBUG` only -- never ships in Release builds.
- Mock data (takes, problem text) is hardcoded in `ScreenshotHostView.mockTakes`.
- StoreKit products are not loaded in screenshot mode, so prices use the locale-formatted fallback. This is why US locale must be set.
- The `sleep 4` after launch gives the app time to render. Increase if screenshots appear blank or mid-animation.
- Pack detail screens render inside a `NavigationStack` to show the nav bar correctly.
