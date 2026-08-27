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

### 0.3 The library update URL (already handled — read once)

The app fetches pattern-library updates over the air. That used to be a single
raw-GitHub URL pinned to this feature branch, in both `RemoteLibraryService`
and the generated `manifest.json` — so deleting the branch after a merge would
have cut off pattern updates for every installed copy, with no fix short of
shipping a new build.

Both apps now try a **list** of sources in order:

1. `https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/main`
2. `https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/claude/fuse-bead-converter-app-706h2s`

The first that answers wins; a 404 falls through. `main` has no `library/`
directory yet, so today source 2 serves everybody. Merge this branch to `main`
and source 1 starts winning on its own, with no app update needed. The
patterns file is fetched as a **sibling of the manifest that actually
answered**, not from the absolute `patternsUrl` recorded inside it, so moving
the library does not require regenerating anything.

`LibrarySourcesTest` pins this behaviour.

> The **already-published 1.4.0** still has the single old URL compiled in, so
> keep the feature branch until your users have moved to 1.5.0.

### 0.4 Java, and why `gradlew` fails in a terminal

The project compiles at `JavaVersion.VERSION_17` with Gradle 8.11.1 and
AGP 8.7.3. Android Studio ships its own JDK and does **not** put it on your
PATH, so running `gradlew` from a plain terminal usually fails with:

> ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.

That is not a broken install. Two ways round it, either is fine:

**Run the tasks from inside the IDE.** The Gradle tool window (elephant icon)
→ **app → Tasks** → `verification/test` and `build/bundleRelease`. The IDE
already knows where its JDK is, so there is nothing to configure. This is the
path of least resistance and the rest of this guide notes the task names as
well as the command lines.

**Or export JAVA_HOME.** Point it at Android Studio's bundled runtime — `jbr`
on any recent version:

```powershell
# Windows PowerShell, this session only
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"

# …or permanently, then reopen the terminal
[Environment]::SetEnvironmentVariable("JAVA_HOME", "C:\Program Files\Android\Android Studio\jbr", "User")
```

```bash
# macOS
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
```

If that path does not exist, **Settings → Build, Execution, Deployment → Build
Tools → Gradle → Gradle JDK** shows the one the IDE is actually using.

### 0.5 Windows notes

- Use `.\gradlew` (PowerShell) rather than `./gradlew`.
- `scripts/publish-library.sh` is a bash script and will not run in PowerShell.
  Use Git Bash — which ships with Git for Windows — or WSL. It is only needed
  for publishing patterns without a store release (§8), not for a build.

---

## 1. Open and sync

1. Android Studio → **Open** → select the **`BeadSnapAndroid`** folder
   (not the repository root — the Gradle project lives one level down).
2. Wait for **Gradle sync** to finish. First sync downloads Gradle 8.11.1 and
   the dependencies, including Play Billing 9.1.0; give it a few minutes.
3. If sync fails with `Task 'prepareKotlinBuildScriptModel' not found`, the
   cause is almost always a missing `android.useAndroidX=true` — it is in
   `gradle.properties`, so check you opened the right folder.

## 1b. Pulling a change while you are mid-release

Fixes land on the branch during a release more often than you would like. The
loop is short:

```powershell
git pull
```

Then, in Android Studio:

1. If the yellow **"Gradle files have changed"** banner appears, click **Sync
   Now**. It only appears when `build.gradle.kts`, `libs.versions.toml` or the
   wrapper changed — a pure Kotlin change needs no sync.
2. **Build → Clean Project** is *not* normally needed. Gradle tracks inputs
   properly. Reach for it only if a build fails in a way that makes no sense
   against the source you are looking at.
3. Re-run whichever step you were on:

```powershell
.\gradlew test              # if the change touched logic
.\gradlew assembleRelease   # to re-test on a device
.\gradlew bundleRelease     # to rebuild the upload artifact
```

Two things that catch people out:

- **`git pull` will refuse if you have local edits** to a file the pull wants to
  change. `git stash`, pull, `git stash pop`. Your `keystore.properties` is
  gitignored and is never involved.
- **Reinstalling over an existing build keeps the app's data**, which is what you
  want — it exercises the upgrade path. `adb install -r` does this. Only
  uninstall first when you specifically want to test a *fresh* install.

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

## 8. Shipping new patterns *without* a store release

New patterns do not need a Play release. The library is fetched over the air,
so this is the whole flow:

```bash
scripts/publish-library.sh --push
```

It rebuilds the library, runs the 19 regression checks, bumps the version and
the bundled-version constants in both apps, commits, and pushes. Installed apps
pick it up on their next launch and show a "Pattern library updated" notice.

Drop `--push` to stop at the commit and review first, or use `--dry-run` to
build and verify without touching git.

A store release is only needed when app **code** changes. Refreshing the
bundled copy of the library — so first-run offline users get the new patterns
too — happens automatically as part of the same script.

## 9. After it is live

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
| Library never updates over the air | Every source in `LibrarySources.BASES` is unreachable, or the hosted version is not greater than `BUNDLED_LIBRARY_VERSION`. See §0.3 and §8. |
