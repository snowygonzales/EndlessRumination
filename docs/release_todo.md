# Release Todo — Endless Rumination US Soft Launch

Last updated: 2026-02-28
Current builds: iOS v0.4.0 (build 14, TestFlight) · Android versionCode 6 (Internal Testing, DRAFT)

---

## Pre-Release Code Task

- [ ] Change `ReleaseStatus.DRAFT` → `ReleaseStatus.COMPLETED` in `android/app/build.gradle.kts` when ready for auto-rollout
- [ ] Bump `versionCode` in `android/app/build.gradle.kts` (currently 6) and publish: `./gradlew :app:publishReleaseBundle`

---

## Apple App Store Connect (Manual)

- [ ] **App Privacy Nutrition Labels** — Complete privacy questionnaire
  - Data Used to Track You: Device ID (via AdMob)
  - Data Not Linked to You: Usage Data, Diagnostics
  - Data Not Collected: everything else
- [ ] **Age Rating Questionnaire** — Select content descriptors
  - No violence, no mature themes
  - "Infrequent/Mild" for Medical/Treatment Information
- [ ] **App Review Notes** — Add reviewer context:
  > This app uses Anthropic's Claude AI to generate multiple perspectives on user-described problems. Users must explicitly consent to AI processing before any data is sent. All input is safety-filtered; crisis resources are shown when distress is detected. Content is generated fresh each time and not stored for free-tier users.
- [ ] **IAP Review Screenshots** — Upload screenshots for each of the 5 IAP products
  - `com.endlessrumination.pro.monthly` (subscription)
  - `com.endlessrumination.pack.strategists` (voice pack)
  - `com.endlessrumination.pack.revolutionaries` (voice pack)
  - `com.endlessrumination.pack.philosophers` (voice pack)
  - `com.endlessrumination.pack.creators` (voice pack)
- [ ] **Store Listing** — Write and upload:
  - App description
  - Subtitle (max 30 characters)
  - Keywords (max 100 characters)
  - Promotional text
- [ ] **Screenshots** — Upload for required device sizes:
  - 6.7" (iPhone 15 Pro Max / 16 Pro Max)
  - 6.5" (iPhone 15 Plus / 14 Pro Max)

---

## Google Play Console (Manual)

- [ ] **Data Safety Section** — Complete the data safety form
  - Declare AdMob SDK data collection (advertising ID, device info)
  - Declare AI processing (user text sent to Anthropic API)
  - No account-linked PII collected
- [ ] **IARC Content Rating Questionnaire** — Complete for content rating
  - Expected result: "Everyone" or "Teen"
- [ ] **Store Listing** — Write and upload:
  - Short description (max 80 characters)
  - Full description (max 4000 characters)
  - Feature graphic (1024×500 PNG)
- [ ] **Screenshots** — Upload phone screenshots (min 2, recommended 8)
- [ ] **Set "Contains Ads"** — Mark app as ad-supported in Content Rating section

---

## AdMob Console

- [ ] **Ad Content Filtering** — Review age-appropriate ad categories in AdMob console
  - App ID: `ca-app-pub-5300605522420042`
  - Ensure ad content is appropriate for the app's audience

---

## Notes

- GitHub repo is public — privacy policy and ToS URLs are accessible to reviewers
- Privacy Policy: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md
- Terms of Service: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/terms-of-service.md
- Support: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/support.md
