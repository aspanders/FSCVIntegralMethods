# Known-good releases

The point of this file is to make "go back to the version that worked" a
lookup rather than an argument. Each entry is a commit that was **built,
installed on a real device, and accepted by Google Play** — not one that merely
compiled.

Add an entry only after a build has actually shipped. A version that was built
but never confirmed on hardware does not belong here; that is exactly the
ambiguity this file exists to remove.

---

## v1.6.3 — versionCode 19 — commit `5c20c62`

**Confirmed working on a physical Android device, and accepted by Play.**

To return to it:

```bash
git diff 5c20c62 -- BeadSnapAndroid/      # what changed since
git checkout 5c20c62 -- BeadSnapAndroid/  # take the Android app back wholesale
```

What it contains:

- Photo conversion no longer squashes portrait photos. `subjectCrop` grew the
  subject box to the board's aspect ratio and then clamped each edge into the
  photo separately, which silently undid the ratio. Measured against the
  shipped code, a 288x384 photo produced a 288x384 crop for a square board — a
  33% horizontal squash, on every portrait photo, because fitting to the
  subject is on by default.
- A Crop tab: drag to move, pinch to resize, locked to the board's shape by
  `ImageConverter.fitAspect`, which is the single place that shape is enforced.
- Colour count moved to the Colour tab, floor lowered from 4 to 2.
- My Creations replaces the AI studio in the bottom bar; the studio is reached
  from Create and has its own back button.
- Create and onboarding scroll, and stay centred while the content fits.
- Play Billing 8.0.0 — the floor Google requires from 31 Aug 2026, deliberately
  not newer.
- Six device-only Android faults fixed: an OOM crash loop on library load, a
  library that silently stopped updating forever, two OkHttp callbacks that
  could hang for the life of the process, tips that were never reconciled and
  so auto-refunded after three days, and a tip button that failed silently.
- iOS: colour maths, photo studio, AI service, crop tab and scroll fixes.

181 harness checks pass at this commit (`tools/kotlin-check/check.sh`).

---

## Version codes already consumed on Play

Play burns a versionCode the moment a bundle carrying it is **uploaded**, to
any track, whether or not it is ever rolled out. Re-using one is rejected at
upload time, after the build.

Known burned: **14, 17, 19** (and any later upload — append as you go).

`scripts/build-release.ps1` reads `.uploaded-version-codes` in the repo root
(gitignored, one number per line) and refuses to build a burned code, so the
failure happens in one second instead of after a full build and an upload.

---

## A note on diagnosing a blocked release

Time was lost chasing "100% of devices no longer supported" through the app
when the app could not have caused it. Worth remembering:

- The manifest and dependency set were **byte-identical** between the version
  that uploaded cleanly and the ones that did not. Check that first — 
  `git show <commit>:BeadSnapAndroid/app/src/main/AndroidManifest.xml | sha256sum`
  settles in seconds whether the app can possibly be implicated.
- Nothing in an app excludes a phone **and** a TV **and** a Chromebook **and**
  an Android XR device simultaneously. A uniform -100% across every category is
  not a feature, ABI or minSdk exclusion; those are selective.
- Play's own wording lists "a missing app bundle" as a cause, and a release
  with no bundle shows a blank download size. Check the App bundles table on
  the release page before theorising about the manifest.
- The authoritative answer is the per-device **reason** behind "Check changes
  to your supported devices", plus Setup → Advanced settings → Device exclusion
  rules. Get that before changing any code.
