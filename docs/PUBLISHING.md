# BeadSnap — Publishing Guide (Apple first, then Google Play)

Both apps are **free** with a **tip jar** (in-app purchases). Keep versions in
lockstep: `scripts/bump-version.sh <version>` updates both platforms.

Current version: **1.0.0** (iOS build 1 / Android versionCode 1).

---

## 0. One-time account setup

| | Apple | Google |
|---|---|---|
| Program | Apple Developer Program | Google Play Console |
| Cost | $99 USD / year | $25 USD one-time |
| Sign up | developer.apple.com/programs | play.google.com/console |
| Verification | ~24–48 h (D-U-N-S needed only for organizations) | ~24–48 h |

## 1. Privacy policy (required by BOTH stores)

The apps use Camera + Photos and store an optional user-supplied Anthropic API
key on-device (iOS Keychain / Android EncryptedSharedPreferences). Nothing is
collected or transmitted to us.

- Host the policy at a public URL (GitHub Pages or a public Gist raw URL).
- iOS references it in App Store Connect → App Privacy; a placeholder also
  exists in `BeadSnap/BeadSnap/Resources/Info.plist` (`BeadSnapPrivacyPolicyURL`)
  — update it to the real URL.
- Must state: no data collected; camera/photos processed on-device only;
  API key stored locally; tips processed by Apple/Google (we never see
  payment details).

## 2. Tip jar IAP products (create in BOTH consoles before submitting)

Product IDs are identical on both stores (referenced in
`TipJarManager.swift` / `TipJarManager.kt`):

| Product ID | Type | Suggested price | Display name |
|---|---|---|---|
| `tip_small` | Consumable | $1.99 | Small tip 🍬 |
| `tip_medium` | Consumable | $4.99 | Nice tip ☕️ |
| `tip_large` | Consumable | $9.99 | Amazing tip 🧁 |

- **App Store Connect** → Your app → Features → In-App Purchases → “+” →
  Consumable. Fill display name, price tier, review screenshot (the Tip Jar
  sheet), and a review note: “Voluntary tips; no content is unlocked.”
- **Play Console** → Monetize → Products → In-app products → Create.
  Same IDs, same prices.
- The app degrades gracefully if products aren’t configured (the sheet shows
  a loading state), but submit with products **live** so reviewers can see them.
- Declare “contains in-app purchases” in both listings (checked automatically
  once products exist).

## 3. App Store (Apple) — submission checklist

1. **Xcode setup**: open `BeadSnap/BeadSnap.xcodeproj`, set your Team,
   bundle ID (e.g. `com.yourname.beadsnap`), and enable the
   **In-App Purchase** capability.
2. **App icon**: fill `Assets.xcassets/AppIcon` (1024×1024 master required).
3. **Archive**: Product → Archive → Distribute App → App Store Connect.
4. **App Store Connect**:
   - My Apps → “+” → New App (iOS, name *BeadSnap*, your bundle ID).
   - Pricing: **Free**, all territories (tips do NOT require a paid app).
   - App Privacy: “Data Not Collected” for every category.
   - Age rating questionnaire → 4+.
   - Screenshots: 6.7" iPhone (1290×2796) and 12.9" iPad (2048×2732),
     2–10 each. Capture in Simulator (`Cmd+S`).
   - Copy from `store/listing.md`.
5. **TestFlight** (recommended): internal testing needs no review; verify
   camera, photo import, AI generation, tip purchase (sandbox account).
6. **Submit for review.** First review is typically 1–3 days. IAP review
   happens alongside the app.

Common first-submission rejections to pre-empt:
- IAP products not attached to the version → attach all three tips.
- Privacy policy URL unreachable → test in an incognito browser.
- “App is a demo/minimal” — not a risk here; mention the 25 built-in
  patterns, photo conversion, and editor in review notes.
- Camera/photo permission strings must match actual use (already set in
  Info.plist).

## 4. Google Play — submission checklist

Follow the interactive guide (published earlier) plus these tip-jar deltas:

1. Keystore: `keytool -genkey -v -keystore ~/beadsnap-release.jks -alias beadsnap -keyalg RSA -keysize 2048 -validity 10000` — **back it up**; never commit it.
2. Signing config in `BeadSnapAndroid/app/build.gradle.kts` (use env vars).
3. Build: `cd BeadSnapAndroid && ./gradlew bundleRelease`
   → `app/build/outputs/bundle/release/app-release.aab`.
4. Play Console: Create app → **Free** → declarations.
   - Data safety: no data collected/shared.
   - Content rating (IARC) → Everyone.
   - Create the three in-app products (section 2).
   - Store listing copy from `store/listing.md`.
5. Internal testing track first, then promote to Production.
6. First production review: up to 7 days.

> Play requires the app to be **Free** to be installable without payment;
> a Free listing can never be switched to Paid later (Paid→Free is allowed).
> BeadSnap is intended to stay free — this is a one-way door we are
> deliberately walking through.

## 5. Release cadence (both stores)

1. `scripts/bump-version.sh 1.1.0`
2. Test: `cd BeadSnapAndroid && ./gradlew test` (+ manual pass on device/sim).
3. Commit, tag `v1.1.0`, push.
4. iOS: Archive → upload → submit. Android: `bundleRelease` → upload to
   Production with release notes.
5. Keep release notes identical across stores.
