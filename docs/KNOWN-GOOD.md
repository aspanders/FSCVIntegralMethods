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

---

# The last ten categories — 2026-09-03

The ten categories nothing had ever looked at: circles, gems, hearts, icons,
mandalas, rainbows, snowflakes, sports, stars, sweets. Every pattern in each
was rendered at thumbnail size with its name under it and judged on one
question — *can you tell what it is, and is it good to look at?*

Six categories needed work. The fixes are in this commit; the rest is recorded
here because it is real and not yet done.

## Fixed: circles — the whole `Radial` family was a dither field

All ten `* Radial *` boards were a polar chessboard whose tiles shrank to one
bead in the outer rings. Half of every colour run is a pale colour, so what
shipped was a scatter of dark beads on white. `Twilight Radial 7` had no disc
left in it at all.

Two things were wrong and both had to be fixed:

* rings thinner than ~2.4 pegs alternate colour every bead. `bands` is now
  clamped from the board size instead of trusted from the caller;
* the pair was `ids[0]`/`ids[-1]`, and seven of the ten runs open on white or
  cream. A chessboard whose light squares are the colour of the board is not a
  chessboard. It now takes `ids[1]`.

Renamed `Checker`, which is what it draws. Category speckle went from a family
of unusable boards to 1.0% overall.

Still weak, not fixed: `Mint Target 13` reads as a broken X rather than a
target, and `Sunset Star 5` reads as an X rather than a star.

## Fixed: icons — five pictograms did not depict their subject

At 5x7 there are not enough columns to hold the parts of a picture apart, and
`_frame` scales whatever ink it gets up to fill the board, so a cramped bitmap
is not a small problem.

| icon | shipped as | now |
|---|---|---|
| Smile | a box with two dots | a face (knockout only) |
| Star | a stick figure | a five-point star |
| Sun | a beetle | a disc with eight rays |
| Bang | a plain bar | an exclamation mark (knockout only) |
| Arrow | a dagger | an arrow |
| Cross | an hourglass | an X |

The pictograms are 9x9 now. Two of them — Smile and Bang — carry their meaning
in their *holes*, and a solid board has to be one connected piece, so the
pipeline welded those holes shut. They are emitted knocked out of a slab only,
where they are the clearest icons in the set. Added Moon, Drop and Cloud, which
are single blobs and survive every style.

Two structural bugs surfaced while doing it:

* the sweep was style-major and `_emit` stops at the target, so the fourth
  style tier was always truncated away. **Not one " Shadow" pattern has ever
  shipped**, and the cut landed mid-tier, which is why the library had a Star
  but no Star Small and a Smile Knockout but no Star Knockout. Three styles
  now, with the pool sized to the target.
* one font pixel is a whole number of beads, so a 9-row pictogram has exactly
  one size that fits a 28-peg board. Asking for a "Small" one produced the same
  board again and the duplicate filter dropped whichever came second. Tall
  bitmaps get solid and knockout only.
* an 11-row bitmap plus the knockout border needs 26 of the 26 usable pegs, and
  when nothing fits `_frame` returns a **bare board**. That is how Star
  Knockout came out as a blank orange square, and it counted as a pattern.

Colour is now pinned for the pictograms. The rotating list had handed out a
brown cloud and a navy raindrop.

## Fixed: hearts — four designs whose subject was invisible

* `Banner Heart` — the banner was cream on a backgroundless board. Invisible.
  Now cheddar with caramel tails.
* `Winged Heart` — same trap, white feathers. Now three shades of blue.
* `Two Hearts`, `Three Hearts`, `Heart Trio Row` — the only designs in the
  category made of separate pieces, and a backgroundless board must be one
  connected piece, so the pipeline welded them: Two Hearts shipped as one heart
  with a pink stripe down it, Heart Trio Row as a single wavy bar. They now sit
  on a cream board, which is what lets them stay separate.
* `Monogram Heart 2/3/4` — the heart's top notch bit the digit's top row, and a
  bitten "2" reads as a smiley face. Monograms are letters now, placed only
  where the glyph clears the mask completely.

## Fixed: rainbows — Fan and Spiral

`Spiral` ran its arm out to r=16 on an 11-unit board, so the outer third was
cropped into the corners, and it drew with a 2.4-unit brush while advancing
1.9 units per turn, so each turn painted over the one before. The brush is
derived from the measured radial gain now and the arm fits the board.

`Fan` drew `bands*2` wedges over a spectrum of 6 or 7, so the colours repeated
partway round — a colour wheel with a mistake in it. One wedge per colour now,
pulled inside the board, base levelled.

Still muddy, not fixed: `Arc 8 Fine`, `Chevron 6 Fine`, `Double 5 Wide`,
`Ring 3 Bold` and `Target 8 Fine` draw their bands from brown and maroon. They
are clean, they just do not say "rainbow".

## Fixed: snowflakes — 197 patterns named after a build artifact

Every flake was titled `Snowflake <n>`: 1, 10, 938, 1002. The candidate pool is
~15,000 boards and ~200 survive the distinctness filter, so the shipped numbers
were the *candidate* indices. They are named from what each flake is made of
now — `Fern Hex Flake 12`, `Plate Star Flake 3` — twelve families, renamed
after the filter runs so **every id is unchanged**.

The ice colour came from a 7-cycle and the sky from a 5-cycle, which landed on
pairs like sky_blue-on-teal at 2.5:1. A snowflake is a tracery, not a slab, so
the pair now has to clear 4.5:1.

## Passed, no changes needed

* **gems** (118) — clean and genuinely attractive. The caveat stands from the
  earlier pass: about seven in ten share one inverted-triangle brilliant-cut
  silhouette, which is most of the 259 same-silhouette collisions.
* **mandalas** (181) — the strongest category in the library. Radially
  symmetric, colourful, unambiguous.
* **circles** apart from the two named above, **hearts** apart from the four,
  **rainbows** apart from the muddy five.

## Failed, and still failing

Named here so they are not lost. None is fixed in this commit.

* **stars** — `Star Grid s5` and `5pt V Star w2` read as **barcodes**.
  `Star Wreath 5` is unidentifiable. `Starburst 8` (14% bbox density) and the
  `n/2 Star Polygon` family read as rings, not stars.
* **sports** — the `Tennis Racket` strings are the 51%-dither crosshatch;
  `Ice Skate` and `Ski` are unidentifiable.
* **sweets** — `Pretzel` is 46% dither and reads as wire; `Marshmallow` and
  `Truffle Outline` are shapeless.
* **icons**, remaining — the Knockout variants of glyphs with enclosed counters
  (0, 2, 3, 6, 8, 9, W, O, U) read as generic rectangles. Inherent to knocking
  a counter out of a slab; the solid and Small variants of those glyphs are
  fine, so nothing is lost.

## Coverage after this pass

All 24 categories have now been looked at pattern by pattern. What is still
open is carried in the earlier sections of this file: flowers (task 17), the
17 dither patterns, `fish/Angelfish`, `bugs/Snail`, the 7 near-blank space
boards, threeD, and the same-silhouette count.

## Second round: the failures named above, fixed

Everything in "Failed, and still failing" was rendered full size rather than as
a thumbnail, which changed two of the calls: `Starburst 8` and `Tennis Racket`
are fine and were wrongly listed, and `5/2`, `6/2`, `7/3` and `8/3 Star
Polygon` are good — only the shallow ones fail. The rest were real.

**stars**

* `{7/2}` and `{9/2} Star Polygon` read as cogs. k/n sets the point angle and
  below ~0.3 the chords barely skip a vertex, so the family is now chosen by
  that ratio; `{13/5}` and `{14/5}` take their place.
* `5pt V Star w2` and the whole internal-pattern family were striped with
  `white`, which the background remover then took away, so the star fell apart
  into loose bars. Both halves are ink now, and the minimum stripe is 3 beads.
* `Star Wreath` satellites were 2-bead blobs. They are big enough to have
  points of their own now.
* `Star Grid` had two problems at once: tile stars too small to have points,
  and — once they were big enough — the one-connected-piece rule welding their
  points into a scaffold. They sit on a night-sky board now and stay separate.

**sports**

* `Ice Skate` was a rounded slab over a bar: a clipboard. It has an ankle now —
  a tall cuff stepping in to a foot — with the blade on two posts and the toe
  turned up.
* `Ski` was a bar beside a pole, which reads as a thermometer next to a golf
  club. Crossed skis with the tips kicking outward is the shape people read as
  skiing.

**sweets**

* `Truffle` was a disc with an ellipse across its top: a cooking pot. It sits
  in a fluted paper cup now, which is what names it.
* `Marshmallow` was a tall white cylinder — a drinking glass. Squat, pink, with
  a toasted top.
* `Pretzel` was three rings that never met. Three overlapping rings in a
  triangle gives the three holes that make a pretzel a pretzel.

The recurring lesson in both rounds: **a design made of separate pieces cannot
be backgroundless.** Three Hearts, Heart Trio Row, Star Grid and the striped
stars all failed the same way, and all four are fixed by giving them a board
rather than by redrawing them.

Library v55, 2351 patterns, 100% distinct, 25 regression checks passing.

---

# Margins: nothing sits on the outermost peg — 2026-09-03

*"Ensure that the letters and the hearts do not touch the edges."*

Measured first. The letters were already clear at every size, minimum three
pegs of margin at full size and one after reduction. The hearts were not:
`Banner Heart` ran off both sides, 89 of the other 91 sat exactly **one** bead
in, and **181 of the 184 reduced hearts touched all four edges**.

The cause is in the reducer, not in the hearts. `scaling.reduce_grid` scales
the whole board — margin included — so a design one bead in from the edge came
out at 0.52 with 0.52 of a bead of margin, which rounds to none. It was not a
hearts problem at all: **2062 of the library's 4674 reduced boards** ran into
the edge.

Three changes:

* **`scaling.MARGIN = 1`.** A backgroundless subject is now resampled onto a
  board one peg smaller on each side and centred on the real one. The inner
  size comes from a single scale factor rather than per-axis, because shrinking
  each axis independently stretches anything that is not square, and a squashed
  heart is worse than a cramped one. A pattern *with* a background keeps its
  full board: that design **is** the board, and an empty ring round it would
  read as a mistake.
* **`scaling.MIN_BEADS = 12`.** The inset costs a ring of pegs, and for the
  thinnest subject in the library — `Number 1 Small`, a one-bead stem — that
  ring was the difference between a glyph and eight beads. Those fall back to
  the full board rather than lose the variant. Exactly one pattern takes the
  fallback.
* **`HEART_SPAN` 0.94 → 0.86**, so the heart itself has two pegs of clearance
  at full size and still has one after reduction. `Banner Heart`'s banner and
  `Winged Heart`'s outermost feather were pulled in to match, and the three
  boxed arrangements — which are not allowed an inset — had their clearance
  built into the drawing instead.

Result, measured the same way:

| | before | after |
|---|---|---|
| hearts touching, full size | 1 | 0 |
| hearts touching, reduced | 181 of 184 | 0 |
| letters touching, any size | 0 | 0 |
| library reduced boards touching | 2062 of 4674 | 695 of 4666 |

The 695 that remain are every one of them a pattern with a background, where a
full board is the design. **No backgroundless board in the library touches an
edge at any size.**

Checks 21 and 21b hold both halves of that, so it cannot come back.

## A measurement error worth recording

The first pass at this reported that all 282 icon variants touched all four
edges, which was wrong and would have sent the fix in the wrong direction. The
compact row encoding uses `.` for an empty peg and `0` for the FIRST PALETTE
COLOUR; the script treated `0` as empty. Every board whose first palette entry
was its outline therefore measured as edge-to-edge ink. The letters were fine
all along — it was only the hearts, and the reducer.

---

# Borders that had closed over what they outlined — 2026-09-03

*"The pretzels look like a slug or some animal. For all categories and all
images, ensure that the borders on both sides of a volume don't touch each
other. If there is a border, black or otherwise, it should contain color
between at all points."*

## What was actually wrong

`_outline` draws a one-bead dark edge round a subject. It already refused to
outline a strand that erodes to nothing, which handles a limb thin in *two*
dimensions. The failure is one-dimensional and it slipped straight through: a
limb three beads **across** but only three beads **long** has a solid centre,
so all eight beads round that centre qualify as edge and the whole limb goes
dark bar one. Repeat that over a pretzel drawn from three overlapping rings and
you get a black amoeba.

Compounding it, the outline colour was allowed to be a colour the subject was
already using. In the species tables the *accent* draws the legs, fins, stripes
and head — and for most bugs and fish the accent is `black`, the same colour
the outline is drawn in. Legs, markings and edge became one mass.

Measured across the library, on backgroundless subjects that carry both an ink
colour and a fill:

| | before | after |
|---|---|---|
| the ink is half the subject or more | 116 | 33 |
| two borders meeting with no colour between | 127 | 43 |
| worst case | `fish/Angelfish` at **99.2% black**, one cream bead | none above 70% |

## Four changes

* **`_outline` second pass.** The rule, stated plainly and enforced along both
  axes: if outlining would leave a whole row or column run of the subject with
  nothing but border in it, the middle bead of that run keeps its colour. Two
  borders can then never meet with nothing between them.
* **`_ink_for`.** The outline is drawn in the first dark tone the subject is not
  already using. A bee whose stripes are black, outlined in black, is one black
  shape.
* **`MAX_OUTLINE_SHARE = 0.45`.** Some subjects are simply too small to carry an
  outline. Past this the border has stopped describing the shape and started
  replacing it, so it is dropped entirely — a plain coloured silhouette reads
  better than a black one. This is what fixed the pretzel.
* **Fins take the body colour.** An Angelfish is a 5-bead body between a dorsal
  and a ventral fin nearly twice its height. Painting the fins in the marking
  colour made the fish 74% black before the outline was even drawn. A real
  fish's fins are the colour of the fish; the accent is for bands, spots and
  the eye. `Angelfish` and `Barb` also had silver bodies, which is invisible on
  a pale board, and now have colour.

## What still reads dark, and why that is right

Ten subjects in the outlined categories are more than half ink: a bat, a bomb,
Steamboat Willie, `Sword Outline` and `Flag Outline` (line art by design), and
the "Long" bug variants, whose extra legs are drawn in the species accent —
a cricket's legs really are black. All were rendered and checked by eye. The 43
still matching the "two borders touching" scan are the hollow `* Outline` style
variants, where the two sides of a thin shape come close with background
between them rather than nothing; they were rendered too and they are fine.

## The checks

Check 22 drives `_outline` directly on blocks chosen to hit each case, rather
than scanning the shipped library — the shipped answer depends on every species
colour and every framing decision as well, and a test that depends on all of
those tells you nothing about which one broke. 22b holds the share bound, 22c
holds the colour-collision rule, and 23 scans the library for a subject that is
mostly its own outline, with the bar set where a genuinely black bat passes and
a swallowed fish cannot.

Library v55, 2379 patterns, 100% distinct, 31 regression checks passing.
