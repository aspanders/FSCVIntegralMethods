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

---

# Audit findings, 2026-09-02

## Library: 254 same-silhouette collisions

`tools/library/audit.py` gained a `shape_collisions` check and it found what
the existing checks could not: the near-duplicate test compares COLOURED cells,
so two identical outlines in different palettes sail past it.

In the representational categories - where the outline IS the picture - 254
pairs of different subjects are drawn as the same shape:

    trees      Oak == Cherry Young == Apple Tree Young   100%
    flowers    Sunflower == Chrysanthemum                 99%
    flowers    Carnation == Peony                         99%
    animals    Bear == Panda (all four poses)             99%
    birds      Eagle == Robin Wings Out                   98%
    bugs       Ladybug Slender == Chafer Slender          97%
    threeD     Gift Box == Creeper Head                  100%

Colour is the only thing telling these apart on a board. The check is scoped to
REPRESENTATIONAL categories on purpose: in hearts, stars and the knockout icons
a shared outline is the design - a heart of stripes and a heart of waves are
both meant to be heart-shaped - and flagging those buried the real finding
under thousands of expected matches when the check was first written.

## Flowers (task 17): better than its description, but a quarter are wrong

The note said "still reads as abstract radial motifs". Looking at the rendered
category, that is no longer true - most read clearly as flowers, with stems and
leaves. What is true is that roughly a quarter of them are the wrong subject:

    Tulip              renders as a house with a window
    Bluebell           renders as a conifer
    Foxglove           renders as a conifer, 96% identical to Bluebell
    Hyacinth/Lavender  two near-identical striped cones
    Bouquet            a hollow ring, reads as a wreath
    Clover, Snowdrop   32% bounding-box density, read as empty

## Two false alarms worth recording

Both cost time and both were caught by rendering the thing rather than trusting
a number:

- The "Knockout" icons looked like 39 identical solid rectangles under a check
  that treated any non-empty cell as filled. They are fine: the glyph is
  knocked out in a SECOND COLOUR, so the board is full but the picture is
  there.
- The first shape-collision pass reported 31,448 pairs library-wide. Nearly all
  were "Framed" designs and full-board fills, where the whole tile is occupied
  and only colour differs. Occupancy comparison is meaningless for those.

## iOS parity

Present on both: colour maths, image conversion, photo studio, AI service,
pattern store, photo project store, remote library, tip jar, background
removal, secure key storage, crop tab, My Creations.

CORRECTION - onboarding. The line above originally read "Onboarding: no iOS
equivalent at all". That was wrong. iOS has a full four-page onboarding with
the same copy, the same Back/Skip/Next/Get Started controls and @AppStorage
persistence; it is simply defined inside Views/Home/CameraView.swift, which is
why a search for an Onboarding *file* found nothing. Checking for a file is not
checking for a feature.

Still Android-only:

    Photos / Projects   PhotoProjectStore exists on iOS with NO UI to reach it
    BitmapLoader        no single EXIF-aware, size-bounded decode path; the
                        orientation handling is spread across CameraView,
                        ImageConverter, PhotoStudio and BackgroundRemover

The Photos gap is the significant one: photo projects are created and stored on
iOS and there is no screen that lists them, so re-deriving a pattern from a
kept photo is impossible there.

## The finding that matters most: five files were not in the iOS build

Xcode referenced 28 Swift files; 32 were on disk. These five compiled nowhere
and shipped nowhere, while sitting in the repo looking finished:

    Services/ColorMath.swift          the entire colour science
    Services/PhotoStudio.swift        the live photo studio
    Services/PhotoProjectStore.swift  photo projects
    Views/Create/PhotoTuneView.swift  the tune screen, including the crop tab
    Views/Creations/MyCreationsView.swift

So every piece of iOS work from this session was outside the build, and since
ContentView now references MyCreationsView, the target could not compile at
all. All five are added to the project and to the Sources build phase.

parity.py gained check_ios_target, which walks the Swift files on disk and
fails unless each one appears in the project AND in the Sources build phase.
The existing paired-file check could never have caught this: it asks whether a
file EXISTS, and existence is not membership. Verified by removing ColorMath
from the Sources phase and watching the check fail.

Nothing on the Android side is affected - versionCode 19 stands as recorded.


---

# Adversarial QC, continued — 2026-09-03

## Dither: 17 patterns that are noise, not designs

New `MAX_DITHER` check in audit.py, at 35% isolated beads. Above the existing
15% "speckled" line a pattern is worth looking at; above 35% it is not a
pattern at all.

    Diag Stripes w1     100%   784 beads, EVERY one differing from all four neighbours
    Diag Heart w1       100%   359 beads, the same
    Wide Chevron p10     93%
    Chevron p7           89%
    Tennis Racket        51%   the strings are a one-bead crosshatch

The library mean is 4.1%, so these are extreme outliers. 13 patterns sit above
50% and 37 above 25%, together 15,368 beads of near-pure noise. Every one of
them passes every other check in the file: distinct, connected, well formed,
correct at all three sizes. They are simply miserable to build and read as dirt
on the board.

Mostly geometric (14 of the worst 37), and all of them are the finest
variant of a family that is fine at coarser settings - Chevron p5 upward is a
proper chevron, p2 is dither. The fix is to stop generating the finest
variants, which is a change to the generators and a library republish rather
than an app change.

## Snail is broken

`bugs / Snail` is a horizontal oval filled with a chaotic three-colour scatter.
No spiral, no body, no eyestalks - it reads as a pizza. Confirmed by dumping
the cells, not by squinting at a thumbnail.

Slug, next to it, is fine: eyestalks and an elongated body. It looked like a
bowl in the contact sheet purely because the tile was small - a reminder that
the thumbnail is for finding candidates, not for judging them.

## Trees: the "Young" variants are one traced outline

Oak, Apple Tree Young and Cherry Young share a byte-identical canopy and trunk
silhouette. Apple Tree Young is that oak with red beads scattered in; Cherry
Young is the same oak in blush and pink. Defensible for cherry blossom,
thinner for apple. It is the clearest instance of the 254 silhouette
collisions already recorded above.

Also in trees: `Mushroom` is not a tree, and `Cactus` is a stretch. Both are
fine patterns in the wrong category.

## What the pass has NOT covered

Reviewed by eye: flowers, birds, animals, trees, bugs. Rendered but not yet
read: vehicles, fish, food. Never rendered: circles, emoji, gems, geometric,
hearts, holidays, icons, mandalas, rainbows, snowflakes, space, sports, stars,
sweets, threeD, videogame.

The metrics cover all 24 categories; the eyes do not. Anything above is a
finding, not a clean bill of health for the rest.


---

# Visual pass over the remaining categories — 2026-09-03

Fourteen categories now reviewed by eye against the rendered contact sheets,
not just by metric. New defects, each confirmed by dumping the cells rather
than by squinting at a thumbnail.

## Broken patterns

    fish / Angelfish     palette is [cream, black] and the board is a solid
                         black silhouette with EXACTLY ONE cream bead - the
                         eye. No fins, no detail. A black blob.
    bugs / Snail         a chaotic three-colour scatter in an oval; reads as
                         a pizza (recorded earlier)

## space: 7 patterns are a background with a few dots on it

    Comet 1, Comet 2                      93% of the board is one colour
    Constellation 1, 2, 4, 5, 6           90-93%

676 to 841 beads to produce a blue square with five dots. They pass the
connectivity and distinctness checks; they are simply not worth building.
The category also has no background discipline at all - navy, cyan, pink,
yellow, cream, lavender and grey all appear, so the category does not read as
a set.

## threeD is the weakest category in the library

Eight patterns. Four are flagged "tiny" (28-39 beads). Two of the remaining
four - Gift Box and Creeper Head - are the same cross-shaped net. Three large
fold-out nets sit beside five small objects with no visual coherence.

## vehicles: one template, repeated

Rows of car, bus, taxi, van, truck, ambulance and tractor are the same box on
the same wheels, which is what the earlier collision numbers were pointing at
(Taxi == Car Big Wheels 95.5%). The bicycles read as spectacles - two rings
joined by a blob - and three or four vehicles are not identifiable at all.

## Smaller findings

    geometric   the dither finding confirmed by eye; also a "pattern" that is
                four solid colour quadrants and nothing else
    emoji       a few faces are pale-on-pale (cream outline on cream fill) so
                the features barely read
    holidays    turkey and one bowl-like subject do not read; several outline
                variants are very sparse
    food        grapes and bread are weak; the outline variants are thin
    videogame   good throughout, including the Steamboat Willie set

## Coverage, stated honestly

Reviewed by eye (14): flowers, birds, animals, trees, bugs, geometric, emoji,
space, threeD, holidays, vehicles, fish, food, videogame.

NOT reviewed by eye (10): circles, gems, hearts, icons, mandalas, rainbows,
snowflakes, sports, stars, sweets. Most are abstract fill families where the
metrics carry more signal than a thumbnail does, and icons was checked by
dumping cells instead - but none of them has had a human-equivalent look, and
this list should not be read as a pass.

---

# Copyright audit — 2026-09-03

Not legal advice; I am not a lawyer. This is an engineering review of what the
library depicts, and what it would be prudent to change.

## Removed: four recognisable characters

Each was checked by rendering it, not by reading its name, and each is
unmistakable once drawn:

    threeD/Creeper Head    the Minecraft creeper's square eyes and frown, on a
                           cube net, tagged "minecraft", with build notes
                           calling for "the classic frown"   (Mojang/Microsoft)
    videogame/Power Mushroom  red cap, cream spots, EYES on the stem - the
                           Super Mario super mushroom              (Nintendo)
    videogame/Ghost Sprite magenta, wavy skirt, blue-pupil eyes - a Pac-Man
                           ghost                              (Bandai Namco)
    videogame/Alien Sprite the Space Invaders invader                 (Taito)

All four rights holders are known to enforce. The three sprites are gone
outright; nothing is lost, because holidays already ships a proper Ghost and
space already ships an Alien. The creeper's cube NET was worth keeping, so it
survives as Monster Cube - purple, with a plain grin.

## Changed: the tetrominoes

Polyominoes are mathematics and belong to nobody. What starts to look like
trade dress is the named set in its familiar colour-to-shape mapping, which is
what shipped: T purple, L orange, S green, O yellow. Renamed to Block Tee, Ell,
Zigzag and Square, and recoloured to teal, plum, sky blue and rust.

## Kept, deliberately: Steamboat Willie

The 1928 short entered the United States public domain on 1 January 2024. The
art is held to that depiction - black and white, pie-cut eyes, no gloves - and
the patterns are titled after the SHORT, never after the character, because the
name remains a live trademark. gen_willie.py carries that reasoning at the top
of the file. This is the one place in the library where a famous figure is
drawn on purpose, and the basis is written down.

## The check that keeps it out

Regression 20 scans every shipped title and tag against a list of franchise
terms. Verified by adding a "minecraft" tag to a pattern and watching it fail.

It is a name check, not an image check - it would not have caught a creeper
drawn under a different title, and nothing automatic can. The rule for the
videogame category is written at the top of VG_ITEMS: draw the generic object a
game might contain - a sword, a key, a potion, a chest - never a specific
character. If a player could name the game it came from, it does not belong.

Library rebuilt to version 54.
