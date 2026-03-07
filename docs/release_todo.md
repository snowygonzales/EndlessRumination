# Pre-Release Checklist — Endless Rumination v1.0.0 (On-Device)

Last updated: 2026-03-07
Target: iOS-only worldwide release, on-device inference (no backend, no ads)
Current build: v1.0.0 build 22, branch `experiment/on-device-inference`
Min iOS: 18.0

---

## Critical Blockers — ALL DONE

- [x] C1. Privacy policy rewritten for on-device architecture
- [x] C2. Terms of Service updated for on-device model
- [x] C3. ATS override removed
- [x] C4. Onboarding privacy claims now accurate (no ads = "No tracking" is true)
- [x] Ads removed entirely (GoogleMobileAds, ATT, SKAdNetwork, IDFA all stripped)

---

## High Priority

- [x] H1. Unsupported device screen for <6GB RAM devices
- [x] H2. Model download retry mechanism
- [ ] H3. iPad support — **deferred to v1.1** (iPhone-only for v1.0, iPads run in compatibility mode)
- [ ] H4. Increased Memory Limit entitlement — **MANUAL: enable in Apple Developer Portal, then add to entitlements file**

---

## Medium Priority

### M1. App Store Review Notes (MANUAL)
- [ ] Write App Review Notes in App Store Connect explaining:
  - App downloads a 2.1 GB AI model on first launch
  - All AI processing happens on-device (no network calls for content generation)
  - No ads, no tracking, no analytics
  - AI consent dialog gates first use
  - Content safety: input blocklist + output blocklist + safety preamble in prompts
  - Report/flag button on all AI-generated content
  - Not a mental health tool — medical disclaimer shown prominently

### M2. App Privacy Nutrition Labels (MANUAL)
- [ ] Complete privacy questionnaire in App Store Connect:
  - Data Not Collected: Select all categories (no tracking, no analytics, no ads, no accounts)
  - This is the cleanest possible privacy label

### M3. Age Rating Questionnaire (MANUAL)
- [ ] Select content descriptors in App Store Connect:
  - No violence, no mature themes, no gambling
  - "Infrequent/Mild" for Medical/Treatment Information
  - Consider "17+" due to mental health content sensitivity

### M4. Store Listing (MANUAL)
- [ ] Write and upload to App Store Connect:
  - App description (emphasize privacy, on-device AI, zero data collection)
  - Subtitle (max 30 chars, e.g., "Private AI Perspectives")
  - Keywords (max 100 chars)
  - Promotional text
- [ ] Upload screenshots for required device sizes:
  - 6.7" (iPhone 15 Pro Max / 16 Pro Max)
  - 6.5" (iPhone 15 Plus / 14 Pro Max)

### M5. IAP Review Screenshots (MANUAL)
- [ ] Upload screenshots for each of the 5 IAP products in App Store Connect:
  - `com.endlessrumination.pro.monthly` (subscription)
  - `com.endlessrumination.pack.strategists`
  - `com.endlessrumination.pack.revolutionaries`
  - `com.endlessrumination.pack.philosophers`
  - `com.endlessrumination.pack.creators`

### Code-Level Items — ALL DONE
- [x] M6. Subscription management deep link in ShopView
- [x] M7. Storage space check before model download

---

## Low Priority (nice to have)

### L1. Privacy Manifest (PrivacyInfo.xcprivacy)
- [ ] Create PrivacyInfo.xcprivacy declaring:
  - `NSPrivacyAccessedAPICategoryUserDefaults` (UserDefaults usage)
  - `NSPrivacyAccessedAPICategoryDiskSpace` (disk space check)

### L2. Accessibility
- [ ] Add accessibility labels to key UI elements
- [ ] Test with VoiceOver enabled
- [ ] Ensure Dynamic Type works for body text

### L3. UIRequiredDeviceCapabilities
- [ ] Consider adding `UIRequiredDeviceCapabilities` → `metal` in Info.plist

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

### Unsupported iPhones (iOS 18 but <6GB RAM — app installs but shows unsupported screen)

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

### Supported iPads (iPadOS 18 + 6GB+ RAM) — deferred to v1.1

| Device | Chip | RAM | Status |
|--------|------|-----|--------|
| iPad Pro 11" 2nd gen (2020) | A12Z | 6 GB | Compatible (runs in iPhone mode) |
| iPad Pro 12.9" 4th gen (2020) | A12Z | 6 GB | Compatible (runs in iPhone mode) |
| iPad Pro 11" 3rd+ gen (M1/M2/M4) | M-series | 8-16 GB | Compatible (runs in iPhone mode) |
| iPad Air 5th gen+ (M1/M2) | M-series | 8 GB | Compatible (runs in iPhone mode) |
| iPad mini 7th gen (2024) | A17 Pro | 8 GB | Compatible (runs in iPhone mode) |

---

## GDPR / Privacy Compliance — Excellent Position

- All AI inference runs locally on the device
- No user content transmitted to any server
- No user accounts, no backend database, no server logs
- No advertising SDKs, no tracking frameworks, no analytics
- No IDFA access, no ATT prompt needed
- Only third-party data processing: Apple StoreKit (payments) and HuggingFace (one-time model download)
- **Privacy label: "Data Not Collected"** — the cleanest possible App Store privacy label

### Data Subject Rights
- **Right to erasure:** Delete the app to remove all local data
- **Right to access:** All data is local on user's device
- **Right to portability:** N/A (no data collected)
- **Data Protection Officer:** Not required (no systematic large-scale processing)

---

## Post-Submission

- [ ] Monitor TestFlight crash reports during beta testing
- [ ] Test on at least one 6 GB device (iPhone 14) and one 8 GB device
- [ ] Test full offline flow (airplane mode after model downloaded)
- [ ] Test model download on cellular vs Wi-Fi
- [ ] Respond to any App Review feedback within 24 hours
