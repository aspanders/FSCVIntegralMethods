# BeadSnap Privacy Policy

**Effective date:** July 15, 2026
**Developer:** Pegboard Studio ("we," "us," "our")
**App:** BeadSnap (iOS and Android)
**Contact:** andersjasp@gmail.com

## In plain English

BeadSnap does not collect, store, or transmit any personal information. Every
pattern you create stays on your device. Photos you convert are processed
entirely on your device and are never uploaded anywhere. If you choose to use
the optional AI pattern generator, your text prompt is sent directly from your
device to Anthropic using your own API key — we never see it. If you leave a
tip, Apple or Google handles the payment; we never see your payment details.
There are no accounts, no ads, and no analytics or tracking of any kind.

The rest of this policy explains that in full detail.

## 1. Introduction

This policy describes how BeadSnap ("the App") handles information when you
use it on iOS or Android. BeadSnap is a fuse-bead pattern design app that lets
you draw patterns by hand, convert photos into bead patterns, generate
patterns with AI, and browse a built-in library of designs.

We built BeadSnap to work entirely on your device. This policy exists to be
transparent about the few places data does leave your device — all of which
are optional features you choose to use.

## 2. Information We Do Not Collect

We do not collect, and the App does not transmit to us:

- Your name, email address, or any contact information
- Your location
- Device identifiers, advertising IDs, or analytics identifiers
- Usage statistics, crash reports, or telemetry of any kind
- Your photos, camera captures, or the patterns you create
- Any account or profile information — BeadSnap has no sign-up, no login,
  and no user accounts

We operate no backend servers for BeadSnap. There is nowhere for this data to
go, because we never built a place to send it.

## 3. Information Stored On Your Device

Everything BeadSnap creates or remembers is stored locally, in storage areas
that are private to the App and sandboxed by iOS or Android:

- **Patterns you create or import**, saved as files in the App's private
  storage
- **App preferences**, such as whether you've completed onboarding, how many
  times you've opened the App (used only to time the optional tip-jar
  prompt), and your editor settings
- **Your Anthropic API key**, if you choose to add one — stored using the
  platform's secure credential storage (the iOS Keychain, or Android's
  EncryptedSharedPreferences backed by the Android Keystore), and never
  included in any backup or transmitted to us

BeadSnap does not use iCloud, Google Drive, or any other cloud backup for
this data. On Android, the App explicitly disables system auto-backup for
its data. Uninstalling the App permanently deletes everything it stored.

## 4. Camera and Photo Access

BeadSnap requests access to your camera and photo library only when you
choose to convert a photo into a bead pattern.

- **Photo library:** when you pick a photo, the App reads it only to display
  a preview and generate a converted pattern. The photo file itself is never
  copied, uploaded, or sent anywhere.
- **Camera:** when you take a photo within the App, the capture is written
  to a private, app-only location — never to your device's public photo
  gallery or Photos library — and is deleted automatically once you finish
  or cancel the conversion.

You can revoke camera or photo permission at any time in your device's
system settings; BeadSnap's photo-from-library and photo-conversion features
simply won't be available until you grant it again.

## 5. Background Removal (On-Device Processing)

When you use the "Remove background" option during photo conversion,
BeadSnap identifies the subject of your photo using on-device machine
learning:

- **iOS** uses Apple's Vision framework, running entirely on your device.
- **Android** uses Google's ML Kit Subject Segmentation, also running
  entirely on your device (the underlying model may be delivered via Google
  Play services, but no image data is ever sent to Google or to us).

No photo, mask, or derived image data ever leaves your device for this
feature. The manual "Remove" / "Add back" brush you use to fine-tune the
result also operates entirely locally.

## 6. AI Pattern Generation (Optional, Third-Party)

BeadSnap's AI Studio lets you generate a bead pattern from a text
description. This feature is entirely optional and requires you to provide
your own Anthropic API key.

If you use this feature:

- Your API key is stored only on your device (see Section 3) and is never
  sent to us.
- The text prompt you type, and — if you ask BeadSnap to refine a pattern —
  a compact description of that pattern's colors and layout, are sent
  directly from your device to Anthropic's API (`api.anthropic.com`) using
  your key.
- This exchange happens directly between your device and Anthropic. We do
  not see, log, or store any part of it.
- Anthropic's handling of this data is governed by Anthropic's own privacy
  policy, available at
  [anthropic.com/legal/privacy](https://www.anthropic.com/legal/privacy).

If you never open AI Studio or never add an API key, none of this applies to
you — no data is sent to Anthropic and this feature performs no network
activity.

## 7. In-App Purchases (Tip Jar)

BeadSnap is free with no ads. After a number of uses, it may show an
optional prompt inviting you to leave a tip; you can also open the tip jar
any time from the Library screen. Tips are entirely voluntary and unlock no
additional features or content.

Tip purchases are processed by Apple's In-App Purchase system (iOS) or
Google Play Billing (Android). We never receive, see, or store your payment
card details, billing address, or other payment information — that data is
handled entirely by Apple or Google under their own privacy policies:

- Apple: [apple.com/legal/privacy](https://www.apple.com/legal/privacy/)
- Google: [policies.google.com/privacy](https://policies.google.com/privacy)

## 8. Children's Privacy

BeadSnap does not collect personal information from anyone, including
children. The App has no account creation, no chat or social features, and
no way for a child (or anyone) to enter or transmit personal information
through the App, aside from the optional AI Studio prompt text described in
Section 6, which a parent or guardian controls by choosing whether to add an
API key.

We do not knowingly collect personal information from children under 13 (or
the relevant age in your region), and because the App collects no personal
information from any user, this is true regardless of age.

## 9. Data Security

Because BeadSnap does not operate servers or collect personal information,
there is no central database of user data to secure. Data that exists —
your patterns and, if you choose to add one, your API key — is protected by
the security features built into iOS and Android: app sandboxing, and, for
your API key specifically, the platform's dedicated secure credential
storage (Keychain / Android Keystore–backed encrypted storage).

## 10. Third-Party Services

BeadSnap uses the following third-party services, each limited to the
purpose described:

| Service | Purpose | Data involved |
|---|---|---|
| Anthropic API | Optional AI pattern generation | Your prompt text, sent directly from your device using your own API key — only if you use AI Studio |
| Apple In-App Purchase / Google Play Billing | Processing optional tip payments | Handled entirely by Apple/Google; we never receive payment details |
| Google ML Kit (on-device) | Background removal on Android | None transmitted — processing is entirely on-device |
| Apple Vision framework (on-device) | Background removal on iOS | None transmitted — processing is entirely on-device |

BeadSnap contains no advertising SDKs, no analytics SDKs, and no
cross-app or cross-site tracking of any kind.

## 11. Your Choices and Controls

- **Permissions:** you can grant or revoke camera and photo access at any
  time in your device's system settings.
- **AI features:** you can remove your Anthropic API key at any time from
  AI Studio's settings; doing so disables AI generation entirely.
- **Your data:** since everything is stored locally, uninstalling the App
  deletes all patterns, preferences, and any stored API key immediately and
  completely. There is no account to delete because none exists.
- **Tip prompts:** you can dismiss the tip-jar prompt permanently at any
  time from the prompt itself.

## 12. Changes to This Policy

If we make material changes to this policy, we will update the "Effective
date" above and, where required by the App Store or Google Play, note the
change in the App's release notes. We encourage you to review this page
periodically.

## 13. Contact Us

Questions about this policy or how BeadSnap handles data can be sent to:

**andersjasp@gmail.com**

---

*This policy applies to the BeadSnap app on iOS and Android. It does not
apply to any other product or service.*
