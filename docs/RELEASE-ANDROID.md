# Shipping an Android update to Google Play

For the **one-time** setup — creating the Play account, the store listing, the
six tip-jar products, the data-safety and content-rating forms — see
[PUBLISHING.md](PUBLISHING.md). This file is the repeatable part: getting a new
build from Android Studio into Production.

Everything below assumes the release you are about to ship is
**versionCode 14 / versionName 1.5.0**, which is what is currently in
`BeadSnapAndroid/app/build.gradle.kts`.

---

## 0. Before you open Android Studio

### 0.1 Get the code

```bash
git fetch origin claude/fuse-bead-converter-app-706h2s
git checkout claude/fuse-bead-converter-app-706h2s
git pull
```

### 0.2 The keystore is not in the repo, and the build knows it

`BeadSnapAndroid/keystore.properties` is gitignored and holds the path and
passwords for your upload key. Without it, a release build produces an
**unsigned** `.aab` that Play Console rejects with an unhelpful error — so
`app/build.gradle.kts` deliberately hard-fails any release task instead:

> Cannot build a release variant: BeadSnapAndroid/keystore.properties is
> missing…

If you see that, copy the template and fill it in:

```bash
cp BeadSnapAndroid/keystore.properties.template BeadSnapAndroid/keystore.properties
```

```properties
storeFile=/absolute/path/to/beadsnap-release.jks
storePassword=…
keyAlias=beadsnap
keyPassword=…
```

Keep the `.jks` **outside** the repo. If you lose it you cannot update the app
under the same listing ever again, short of asking Google to reset your upload
key. Back it up somewhere you would still have after losing this machine.

### 0.3 One thing that is easy to get wrong: the library update URL

The app fetches pattern-library updates over the air, and the URL is a raw
GitHub link that hardcodes **this branch**:

- `RemoteLibraryService.kt` → `manifestUrl`
- `library/manifest.json` → `patternsUrl`

```
https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/claude/fuse-bead-converter-app-706h2s/library/…
```

The already-published 1.4.0 has the same URL baked in. **If you merge this
branch to `main` and delete it, over-the-air library updates break for every
installed copy of the app, old and new.** The bundled library still works
offline, so nobody is left with an empty app — they just stop getting new
patterns.

Pick one before you ship:

- **Keep the branch alive.** Nothing to do.
- **Move to `main`.** Change both URLs to `.../main/library/…`, rebuild the
  manifest with `python3 tools/library/build_manifest.py --raw-base
  https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/main`, then
  merge. Installed 1.4.0 copies keep pointing at the old branch, so keep the
  branch until they have updated.

### 0.4 Java 17

The project compiles at `JavaVersion.VERSION_17` with Gradle 8.11.1 and
AGP 8.7.3. Android Studio's embedded JDK is 17+ on any recent version; if you
have pointed it elsewhere, check **Settings → Build, Execution, Deployment →
Build Tools → Gradle → Gradle JDK**.

---

## 1. Open and sync

1. Android Studio → **Open** → select the **`BeadSnapAndroid`** folder
   (not the repository root — the Gradle project lives one level down).
2. Wait for **Gradle sync** to finish. First sync downloads Gradle 8.11.1 and
   the dependencies, including Play Billing 9.1.0; give it a few minutes.
3. If sync fails with `Task 'prepareKotlinBuildScriptModel' not found`, the
   cause is almost always a missing `android.useAndroidX=true` — it is in
   `gradle.properties`, so check you opened the right folder.

## 2. Run the tests

```bash
cd BeadSnapAndroid && ./gradlew test
```

Or **Gradle panel → BeadSnapAndroid → app → Tasks → verification → test**.
These are JVM unit tests (pattern model, seed patterns, colour maths, tip
prompt logic); they need no device.

## 3. Build the signed bundle

Signing is already wired through `keystore.properties`, so **do not** use
**Build → Generate Signed App Bundle**. That wizard asks for the keystore
again and configures a second, competing signing path. Just run the release
task and the `.aab` comes out signed:

- **Gradle panel → app → Tasks → build → `bundleRelease`**, or
- Terminal: `cd BeadSnapAndroid && ./gradlew bundleRelease`

Output:

```
BeadSnapAndroid/app/build/outputs/bundle/release/app-release.aab
```

Release builds run R8 with `isMinifyEnabled` and `isShrinkResources` on, so
this is slower than a debug build and is the only build that can surface
minification bugs. That is why step 4 matters.

## 4. Test the release build on a real device

R8 problems and billing problems both only appear in a signed release build,
and **this release changed the billing code** (Play Billing 7 → 9.1.0). Do not
skip this.

1. **Build → Generate Signed APK** *or* `./gradlew assembleRelease`, then
   `adb install -r app/build/outputs/apk/release/app-release.apk`.
2. Add your Google account under **Play Console → Setup → License testing** so
   purchases are free and refunded automatically.
3. Open the tip jar. Check that:
   - the six tiers appear **with prices** — an empty sheet means
     `queryProductDetailsAsync` came back unhappy, which is exactly the call
     whose signature changed in Billing 8;
   - a tip completes and the thank-you appears;
   - tipping a second time works — tips are consumables and are consumed on
     purchase.
4. Check the pattern library loads and a pattern opens at Small / Medium /
   Large.

## 5. Upload to Play Console

1. [play.google.com/console](https://play.google.com/console) → **BeadSnap**.
2. **Test and release → Testing → Internal testing → Create new release.**
   Go through internal testing first even when you are confident: it is
   instant, it costs nothing, and it is the only way to see the bundle
   processed exactly as Production will process it.
3. **Upload** `app-release.aab`. Play will show it as versionCode 14.
4. Release name: `1.5.0 (14)`. Release notes — paste the text from
   [§7](#7-release-notes) below.
5. **Next → Save → Review release → Start rollout to Internal testing.**
6. Install from the internal-testing link on a device that already has the
   Play build, so you also exercise the **upgrade** path — pattern projects and
   the tip state live in local storage and must survive.

## 6. Promote to Production

1. **Test and release → Production → Create new release**.
2. **Add from library** → pick the bundle you already uploaded, rather than
   uploading the `.aab` a second time.
3. Same release notes.
4. **Start rollout to Production.** Consider a **staged rollout** (20%) for a
   release that touches billing; you can halt it if crash rate moves.
5. Review takes anywhere from a few hours to a few days for an update.

### Confirming the billing warning is gone

The Play Billing deprecation notice lives under **Policy → App content**, or on
the Play Console home dashboard. It clears once a bundle using Billing 8+ is
live on **every** track you publish to — including any old internal or closed
track still serving an ancient build. If the warning persists after Production
goes live, look for a stale build on another track and either update or
deactivate it.

You can verify what Play detected: **Release → App bundle explorer** → pick the
version → **Downloads / Details**, which lists the SDKs found in the bundle.

## 7. Release notes

Play caps release notes at 500 characters per language.

```
Every pattern now comes in three sizes — pick Small, Medium or Large when you
open it, and each one is a complete design rather than a crop.

The pattern library has been redrawn: species now have their own colours (no
more orange zebras), flowers actually look like flowers, and squashed,
unrecognisable variants are gone. New line-drawing versions of many patterns.

Plus three Steamboat Willie designs, and the usual fixes under the hood.
```

## 8. After it is live

- Tag the release: `git tag v1.5.0 && git push origin v1.5.0`.
- Watch **Quality → Android vitals** for a day or two; a billing regression
  shows up as ANRs or crashes in the tip flow.
- iOS is **not** in lockstep — `Info.plist` is still at 1.0.5 (build 6) while
  Android is at 1.5.0 (14). `scripts/bump-version.sh` assumes they move
  together; it will need a manual reconcile before the next iOS submission.

---

## Troubleshooting

| Symptom | Cause |
|---|---|
| `Cannot build a release variant: keystore.properties is missing` | Step 0.2. This is the guard working, not a bug. |
| Play rejects the bundle: "not signed" | You built with `assembleDebug`/`bundleDebug`, or `keystore.properties` points at a `.jks` that is not there. |
| "Version code 14 has already been used" | Someone uploaded a 14 already. Bump to 15 in `app/build.gradle.kts` and rebuild — version codes are permanently consumed even by deleted drafts. |
| Tip sheet is empty in the release build | The six product IDs in `TipJarManager.kt` must exist and be **active** in Play Console, and your test account must be a licence tester. |
| Billing warning still showing after rollout | An older build is still live on some other track. See §6. |
| Library never updates over the air | The branch in the raw-GitHub URL was deleted. See §0.3. |
