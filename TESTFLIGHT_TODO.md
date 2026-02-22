# TestFlight Readiness Checklist

## 1. Apple Developer Account
- [ ] Enroll in Apple Developer Program ($99/year) at [developer.apple.com](https://developer.apple.com/programs/enroll/)
- [ ] Wait for enrollment approval (usually 24-48 hours)
- [ ] Note your **Team ID** from Membership details

## 2. Xcode Signing Configuration
- [ ] Open `ios/project.yml` and set `DEVELOPMENT_TEAM` to your Team ID
- [ ] Run `xcodegen generate` to regenerate the project
- [ ] Open project in Xcode → Signing & Capabilities → confirm "Automatically manage signing" is checked
- [ ] Select your team from the dropdown
- [ ] Verify bundle ID `com.endlessrumination.EndlessRumination` is available (change if taken)

## 3. App Icon ✅
- [x] Create a 1024×1024 app icon (single size, Xcode auto-generates all variants)
- [x] Place in `ios/EndlessRumination/Assets.xcassets/AppIcon.appiconset/appicon.png`
- [x] Update the corresponding `Contents.json` to reference the file

## 4. Backend Deployment ✅
- [x] Deploy FastAPI backend to Railway
- [x] Set environment variables: `ANTHROPIC_API_KEY`, `DATABASE_URL`, `JWT_SECRET`
- [x] Update `ios/EndlessRumination/Services/APIClient.swift` — release `baseURL` points to Railway
- [x] Health check verified: `curl https://backend-production-5537.up.railway.app/health`
- [ ] Estimated API cost: ~$0.12 per problem submission (20 Sonnet takes + 1 safety check)
- **Production URL**: `https://backend-production-5537.up.railway.app`
- **Railway project**: https://railway.com/project/30951286-357e-4529-a21c-bb527d62eb13

## 5. App Store Connect Setup
- [ ] Log in to [App Store Connect](https://appstoreconnect.apple.com)
- [ ] Create a new app: **Endless Rumination**
- [ ] Select iOS platform, your bundle ID, and SKU (e.g., `endlessrumination001`)
- [ ] Fill in required metadata:
  - [ ] App name, subtitle, category (Health & Fitness or Lifestyle)
  - [ ] Description, keywords, support URL
  - [ ] Screenshots (6.7" iPhone 15 Pro Max + 6.5" iPhone 11 Pro Max minimum)
  - [ ] Age rating questionnaire (likely 17+ due to mental health content)

## 6. Privacy Policy ✅
- [x] Created privacy policy at `docs/privacy-policy.md`
- [x] Discloses: data collected (problem text sent to API), third-party services (Anthropic Claude API)
- [ ] Add the URL to App Store Connect under "App Privacy"
- [ ] Complete the App Privacy questionnaire in App Store Connect
- **Privacy Policy URL**: https://github.com/snowygonzales/EndlessRumination/blob/master/docs/privacy-policy.md

## 7. Archive & Upload
```bash
# From ios/ directory:
xcodegen generate
```
- [ ] In Xcode: Product → Archive (select "Any iOS Device" as destination)
- [ ] In Organizer window: click "Distribute App" → App Store Connect → Upload
- [ ] Wait for processing (5-30 minutes, you'll get an email)

## 8. TestFlight Configuration
- [ ] In App Store Connect → TestFlight tab, your build should appear after processing
- [ ] Add **internal testers** (up to 100, must be App Store Connect users)
- [ ] For **external testers** (up to 10,000):
  - [ ] Create a test group
  - [ ] Fill in beta test info (what to test, contact email)
  - [ ] Submit for **Beta App Review** (usually 24-48 hours first time)
- [ ] Share the TestFlight invite link with testers

## 9. Optional but Recommended
- [ ] Add a launch screen or splash animation (current `SplashView` works as initial screen)
- [ ] Add crash reporting (Firebase Crashlytics or native Xcode Organizer)
- [ ] Test on physical device before uploading
- [ ] Set up StoreKit 2 subscription products in App Store Connect (for Pro tier)
- [ ] Configure StoreKit testing in Xcode for local subscription testing

## Cost Summary
| Item | Cost |
|------|------|
| Apple Developer Program | $99/year |
| Backend hosting (Railway/Render) | ~$5-15/month |
| Anthropic API (per submission) | ~$0.12 |
| TestFlight | Free (included with dev program) |

## Quick Reference
- **Team ID location**: developer.apple.com → Account → Membership
- **Bundle ID**: `com.endlessrumination.EndlessRumination`
- **Minimum iOS**: 17.0
- **Xcode**: 16.0+
