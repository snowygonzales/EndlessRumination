# Pre-Release Checklist — Endless Rumination v1.0.0 (On-Device)

Last updated: 2026-03-07
Target: iOS-only worldwide release, on-device inference (no backend)
Current build: v1.0.0 build 20, branch `experiment/on-device-inference`
Min iOS: 18.0

---

## Critical Blockers (must fix before submission)

### C1. Privacy Policy — Factually Wrong
The current privacy-policy.md describes cloud API architecture that no longer exists:
- [ ] Remove "Problem text is sent to our server for processing"
- [ ] Remove all references to Anthropic's Claude API and Anthropic's servers
- [ ] Remove "Account Information" section (no accounts exist on-device)
- [ ] Remove "hashed password" and "database" references
- [ ] Remove Railway server references
- [ ] Remove Google Play Billing references (iOS-only release)
- [ ] Add "All AI processing happens entirely on your device" language
- [ ] Add model download from HuggingFace disclosure (one-time HTTPS download)
- [ ] Keep AdMob / IDFA / ad tracking disclosures (still accurate)
- [ ] Keep StoreKit / Apple payment processing section
- [ ] Update "Data Retention" to reflect no server storage
- [ ] Update "Security" to reflect on-device processing
- [ ] Update date to current

### C2. Terms of Service — Factually Wrong
- [ ] Remove "using Anthropic's Claude AI" from description
- [ ] Replace with "using an on-device AI model"
- [ ] Remove Android/Google Play references (iOS-only for now)
- [ ] Keep AI-generated content disclaimer
- [ ] Keep mental health disclaimer and crisis resources
- [ ] Keep subscription and voice pack purchase terms
- [ ] Update date to current

### C3. ATS Override — Remove
`NSAllowsArbitraryLoads: true` in project.yml is unnecessary:
- [ ] Remove `NSAllowsArbitraryLoads: true` from project.yml Info.plist properties
- HuggingFace model download uses HTTPS (no exception needed)
- AdMob SDK handles its own ATS exceptions via SKAdNetwork
- Apple reviewers flag blanket ATS overrides

### C4. Onboarding Privacy Claims — Misleading
Privacy page (page 3) claims "No cloud. No servers. No tracking." — contradicts AdMob:
- [ ] Change "No tracking" to accurate language (e.g., "No data tracking" or remove the line)
- [ ] Or clarify: "Your thoughts never leave this device. Ads are served by Google AdMob."
- Keep: "AI runs entirely on your iPhone", "Works offline after setup", "Your thoughts never leave this device"

---

## High Priority (should fix before submission)

### H1. Unsupported Device Screen
4GB devices (iPhone 12, 13, SE 3rd) can install the app, download 2.1 GB, then get an error.
- [ ] Add a graceful screen shown BEFORE model download for unsupported devices
- [ ] Show device RAM, explain minimum requirement (6 GB)
- [ ] DeviceCapability.canRunModel already checks this — wire it into the app flow
- [ ] Consider showing this at first launch, before onboarding

### H2. Model Download Retry
If download fails (network drop, backgrounded, etc.), user is stuck:
- [ ] Add retry button when download fails (currently shows "Download failed" with no action)
- [ ] Consider resume support (URLSession background download)
- [ ] Show error message with actionable guidance

### H3. iPad Support Decision
project.yml `platform: iOS` defaults to iPhone-only. iPads can run in compatibility mode.
- [ ] **Decision needed:** Explicitly support iPad, or keep iPhone-only?
  - If iPhone-only: No code changes needed, iPads run in compatibility mode
  - If iPad: Add `TARGETED_DEVICE_FAMILY: "1,2"`, test portrait layout on iPad screen sizes
- [ ] If supporting iPad: test on iPad simulator (portrait-only is fine for v1.0)

### H4. Increased Memory Limit Entitlement
The 2.0 GB model on 6 GB devices benefits from this entitlement:
- [ ] Enable "Increased Memory Limit" capability in Apple Developer Portal for the App ID
- [ ] Re-download provisioning profile (Xcode automatic signing should handle this)
- [ ] Add `com.apple.developer.kernel.increased-memory-limit` to entitlements file
- Note: App still works without it on 6 GB devices, but this provides safety margin

---

## Medium Priority (recommended before submission)

### M1. App Store Review Notes
Reviewer needs context about the AI model and on-device processing:
- [ ] Write App Review Notes explaining:
  - App downloads a 2.1 GB AI model on first launch
  - All AI processing happens on-device (no network calls for content generation)
  - AI consent dialog gates first use
  - Content safety: input blocklist + output blocklist + safety preamble in prompts
  - Report/flag button on all AI-generated content
  - Not a mental health tool — medical disclaimer shown prominently

### M2. App Privacy Nutrition Labels
- [ ] Complete privacy questionnaire in App Store Connect:
  - Data Used to Track You: Device ID (via AdMob, for free tier only)
  - Data Not Linked to You: Usage Data, Diagnostics
  - Data Not Collected: everything else (no accounts, no server, no content collection)

### M3. Age Rating Questionnaire
- [ ] Select content descriptors in App Store Connect:
  - No violence, no mature themes, no gambling
  - "Infrequent/Mild" for Medical/Treatment Information
  - Consider "17+" due to mental health content sensitivity

### M4. Store Listing
- [ ] Write and upload to App Store Connect:
  - App description (emphasize privacy, on-device AI, no data collection)
  - Subtitle (max 30 chars, e.g., "Private AI Perspectives")
  - Keywords (max 100 chars)
  - Promotional text
- [ ] Upload screenshots for required device sizes:
  - 6.7" (iPhone 15 Pro Max / 16 Pro Max)
  - 6.5" (iPhone 15 Plus / 14 Pro Max)

### M5. IAP Review Screenshots
- [ ] Upload screenshots for each of the 5 IAP products in App Store Connect:
  - `com.endlessrumination.pro.monthly` (subscription)
  - `com.endlessrumination.pack.strategists`
  - `com.endlessrumination.pack.revolutionaries`
  - `com.endlessrumination.pack.philosophers`
  - `com.endlessrumination.pack.creators`

### M6. Subscription Management Deep Link
Apple requires apps to make it easy to manage subscriptions:
- [ ] Add "Manage Subscription" button in ShopView that opens:
  `UIApplication.shared.open(URL(string: "https://apps.apple.com/account/subscriptions")!)`

### M7. Storage Space Check
Model is 2.1 GB — users need adequate free space:
- [ ] Check available disk space before starting download
- [ ] Show storage requirement (e.g., "Requires 2.1 GB of free space") in onboarding
- [ ] Show friendly error if insufficient space

---

## Low Priority (nice to have)

### L1. Privacy Manifest (PrivacyInfo.xcprivacy)
Apple now requires privacy manifests for apps using certain APIs:
- [ ] Create PrivacyInfo.xcprivacy declaring:
  - `NSPrivacyAccessedAPICategoryUserDefaults` (UserDefaults usage)
  - `NSPrivacyAccessedAPICategoryFileTimestamp` (if any file timestamp access)
  - `NSPrivacyAccessedAPICategoryDiskSpace` (disk space check)
- [ ] AdMob SDK should include its own privacy manifest

### L2. Accessibility
- [ ] Add accessibility labels to key UI elements (take cards, lens badges, buttons)
- [ ] Test with VoiceOver enabled
- [ ] Ensure Dynamic Type works for body text

### L3. UIRequiredDeviceCapabilities
Could restrict installation to capable devices at the App Store level:
- [ ] Consider adding `UIRequiredDeviceCapabilities` in Info.plist
  - `metal` — all supported devices have this, but makes intent explicit
  - Note: There is no capability key for minimum RAM, so 4GB devices can still install

---

## Device Compatibility

### Minimum Requirements
- **iOS 18.0** (required by mlx-swift Metal kernels for Gated DeltaNet)
- **6 GB RAM** (2.0 GB 4-bit model + inference overhead)
- **2.1 GB free storage** (one-time model download from HuggingFace)

### Supported iPhones (iOS 18 + 6GB+ RAM)

| Device | Chip | RAM | Status |
|--------|------|-----|--------|
| iPhone 12 Pro | A14 | 6 GB | Supported |
| iPhone 12 Pro Max | A14 | 6 GB | Supported |
| iPhone 13 Pro | A15 | 6 GB | Supported |
| iPhone 13 Pro Max | A15 | 6 GB | Supported |
| iPhone 14 | A15 | 6 GB | Supported (tested) |
| iPhone 14 Plus | A15 | 6 GB | Supported |
| iPhone 14 Pro | A16 | 6 GB | Supported |
| iPhone 14 Pro Max | A16 | 6 GB | Supported |
| iPhone 15 | A16 | 6 GB | Supported |
| iPhone 15 Plus | A16 | 6 GB | Supported |
| iPhone 15 Pro | A17 Pro | 8 GB | Supported |
| iPhone 15 Pro Max | A17 Pro | 8 GB | Supported |
| iPhone 16 | A18 | 8 GB | Supported |
| iPhone 16 Plus | A18 | 8 GB | Supported |
| iPhone 16 Pro | A18 Pro | 8 GB | Supported |
| iPhone 16 Pro Max | A18 Pro | 8 GB | Supported |
| iPhone 16e | A18 | 8 GB | Supported |

### Unsupported iPhones (iOS 18 but <6GB RAM — app installs but cannot run model)

| Device | Chip | RAM | Reason |
|--------|------|-----|--------|
| iPhone XR | A12 | 3 GB | Insufficient RAM |
| iPhone XS / XS Max | A12 | 4 GB | Insufficient RAM |
| iPhone 11 | A13 | 4 GB | Insufficient RAM |
| iPhone 11 Pro / Pro Max | A13 | 4 GB | Insufficient RAM |
| iPhone SE 2nd gen | A13 | 3 GB | Insufficient RAM |
| iPhone 12 | A14 | 4 GB | Insufficient RAM |
| iPhone 12 mini | A14 | 4 GB | Insufficient RAM |
| iPhone 13 | A15 | 4 GB | Insufficient RAM |
| iPhone 13 mini | A15 | 4 GB | Insufficient RAM |
| iPhone SE 3rd gen | A15 | 4 GB | Insufficient RAM |

### Supported iPads (iPadOS 18 + 6GB+ RAM)

| Device | Chip | RAM | Status |
|--------|------|-----|--------|
| iPad Pro 11" 2nd gen (2020) | A12Z | 6 GB | Supported |
| iPad Pro 12.9" 4th gen (2020) | A12Z | 6 GB | Supported |
| iPad Pro 11" 3rd gen (2021) | M1 | 8-16 GB | Supported |
| iPad Pro 12.9" 5th gen (2021) | M1 | 8-16 GB | Supported |
| iPad Pro 11" 4th gen (2022) | M2 | 8-16 GB | Supported |
| iPad Pro 12.9" 6th gen (2022) | M2 | 8-16 GB | Supported |
| iPad Pro 11" (2024) | M4 | 8-16 GB | Supported |
| iPad Pro 13" (2024) | M4 | 8-16 GB | Supported |
| iPad Air 5th gen (2022) | M1 | 8 GB | Supported |
| iPad Air 11" (2024) | M2 | 8 GB | Supported |
| iPad Air 13" (2024) | M2 | 8 GB | Supported |
| iPad mini 7th gen (2024) | A17 Pro | 8 GB | Supported |

Note: iPad Pro 11" 1st gen (2018) / 12.9" 3rd gen (2018) have A12X with 4 GB (base) or 6 GB (1 TB model only) — excluded due to inconsistent RAM across storage tiers.

### Unsupported iPads (iPadOS 18 but <6GB RAM)

| Device | Chip | RAM | Reason |
|--------|------|-----|--------|
| iPad 8th gen | A12 | 3 GB | Insufficient RAM |
| iPad 9th gen | A13 | 3 GB | Insufficient RAM |
| iPad 10th gen | A14 | 4 GB | Insufficient RAM |
| iPad Air 4th gen | A14 | 4 GB | Insufficient RAM |
| iPad mini 6th gen | A15 | 4 GB | Insufficient RAM |

---

## GDPR / Privacy Compliance

### On-Device Processing — Strong Position
- All AI inference runs locally on the device
- No user content (problem text, AI responses) is transmitted to any server
- No user accounts, no backend database, no server logs
- Problem text is processed in memory and never persisted (free tier) or persisted only locally (Pro session history)

### AdMob — Requires Disclosure
- Google AdMob SDK collects device identifiers (IDFA) and ad interaction data
- ATT prompt is implemented (iOS requirement for IDFA access)
- Users can opt out of personalized ads via device settings
- Pro subscribers see no ads (no AdMob data collection for Pro users)
- **GDPR basis:** Consent (ATT prompt) for ad personalization; Legitimate interest for non-personalized ads

### StoreKit — Apple Handles
- All payment processing handled by Apple
- No payment data touches the app or any custom server
- Apple's GDPR compliance applies to payment data

### Data Subject Rights
- **Right to erasure:** No server-side data to delete; app can be uninstalled to remove all local data
- **Right to access:** All data is local on user's device
- **Right to portability:** N/A (no data collected)
- **Data Protection Officer:** Not required (no systematic large-scale processing)

### Recommendations
- [ ] Update Privacy Policy to accurately reflect on-device architecture (see C1 above)
- [ ] Consider adding in-app "Delete All Data" button (clears UserDefaults + any cached model data)
- [ ] Ensure ATT prompt appears before any AdMob initialization (currently implemented)

---

## AdMob Console

- [ ] Review age-appropriate ad categories in AdMob console
  - App ID: `ca-app-pub-5300605522420042`
  - Ensure ad content is appropriate for the app's audience
  - Consider blocking sensitive categories (dating, alcohol, gambling)

---

## Post-Submission

- [ ] Monitor TestFlight crash reports during beta testing
- [ ] Test on at least one 6 GB device (iPhone 14) and one 8 GB device
- [ ] Test full offline flow (airplane mode after model downloaded)
- [ ] Test model download on cellular vs Wi-Fi
- [ ] Respond to any App Review feedback within 24 hours
