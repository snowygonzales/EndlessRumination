# TestFlight Readiness Checklist

## 1. Apple Developer Account ✅
- [x] Enroll in Apple Developer Program ($99/year) at [developer.apple.com](https://developer.apple.com/programs/enroll/)
- [x] Wait for enrollment approval (usually 24-48 hours)
- [x] Note your **Team ID** from Membership details

## 2. Xcode Signing Configuration ✅
- [x] Open `ios/project.yml` and set `DEVELOPMENT_TEAM` to your Team ID
- [x] Run `xcodegen generate` to regenerate the project
- [x] Open project in Xcode → Signing & Capabilities → confirm "Automatically manage signing" is checked
- [x] Select your team from the dropdown
- [x] Verify bundle ID `com.endlessrumination.EndlessRumination` is available

## 3. App Icon ✅
- [x] Create a 1024×1024 app icon (single size, Xcode auto-generates all variants)
- [x] Place in `ios/EndlessRumination/Assets.xcassets/AppIcon.appiconset/appicon.png`
- [x] Update the corresponding `Contents.json` to reference the file

## 4. Backend Deployment ✅
- [x] Deploy FastAPI backend to Railway
- [x] Set environment variables: `ANTHROPIC_API_KEY`, `DATABASE_URL`, `JWT_SECRET`
- [x] Update `ios/EndlessRumination/Services/APIClient.swift` — release `baseURL` points to Railway
- [x] Health check verified: `curl https://backend-production-5537.up.railway.app/health`
- [x] Monetization model: Free (5 lenses, Sonnet/Haiku hybrid) / Pro $9.99/mo (all 20 Sonnet)
- **Production URL**: `https://backend-production-5537.up.railway.app`
- **Railway project**: https://railway.com/project/30951286-357e-4529-a21c-bb527d62eb13

## 5. App Store Connect Setup ✅
- [x] Log in to [App Store Connect](https://appstoreconnect.apple.com)
- [x] Create a new app: **Endless Rumination**
- [x] Select iOS platform, your bundle ID, and SKU (`endlessrumination001`)
- [x] Fill in required metadata:
  - [x] App name, subtitle, category (Health & Fitness)
  - [x] Description, keywords, support URL
  - [x] Screenshots (6.7" + 6.5" resized from simulator)
  - [x] Age rating questionnaire
  - [x] Encryption declaration (None)

## 6. Privacy Policy ✅
- [x] Created privacy policy at `docs/privacy-policy.md`
- [x] Discloses: data collected (problem text sent to API), third-party services (Anthropic Claude API)
- [x] Add the URL to App Store Connect under "App Privacy"
- [x] Complete the App Privacy questionnaire in App Store Connect
- **Privacy Policy URL**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md

## 7. Archive & Upload ✅
- [x] `xcodegen generate` with iPad orientations fix
- [x] Registered physical device for provisioning profiles
- [x] In Xcode: Product → Archive (generic iOS device)
- [x] In Organizer: Distribute App → App Store Connect → Upload
- [x] Build processed successfully

## 8. TestFlight ✅
- [x] Build appeared in App Store Connect → TestFlight tab
- [x] Internal testing — app installed and verified on physical device
- [x] App runs, delivers perspectives, icon displays correctly
- [ ] External testers (optional): create group, submit for Beta App Review

## 9. Remaining for App Store Release
- [x] Set up StoreKit 2 subscription products in App Store Connect ($9.99/mo Pro tier)
- [x] Configure StoreKit testing in Xcode for local subscription testing
- [ ] Integrate ads SDK for free tier (AdMob or similar)
- [ ] Add crash reporting (Firebase Crashlytics or native Xcode Organizer)
- [ ] Proper App Store screenshots from physical device
- [ ] Submit for full App Store Review

## Build Pipeline
```bash
# From ios/ directory:
xcodegen generate
xcodebuild -project EndlessRumination.xcodeproj -scheme EndlessRumination \
  -destination 'generic/platform=iOS' -configuration Release \
  archive -archivePath build/EndlessRumination.xcarchive -allowProvisioningUpdates
# Then: open build/EndlessRumination.xcarchive → Distribute App → App Store Connect → Upload
```

## Cost Summary
| Item | Cost |
|------|------|
| Apple Developer Program | $99/year |
| Backend hosting (Railway) | ~$5-15/month |
| Anthropic API — free user submission | ~$0.013 (2 Sonnet + 3 Haiku + safety) |
| Anthropic API — Pro user submission | ~$0.12 (20 Sonnet + safety) |
| Anthropic API — per voice pack (marginal) | ~$0.025 (5 Sonnet) |
| TestFlight | Free (included with dev program) |

## Quick Reference
- **Team ID**: R6N5B4SDWH
- **Bundle ID**: `com.endlessrumination.EndlessRumination`
- **Minimum iOS**: 17.0
- **Xcode**: 16.0+
- **Version**: 0.0.1 (build 3)
- **Privacy Policy URL**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md
- **Support URL**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/support.md
