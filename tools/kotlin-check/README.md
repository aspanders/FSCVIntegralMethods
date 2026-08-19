# Engine check — compile and verify the conversion code without an Android SDK

The photo→beads engine is the part of BeadSnap most likely to be quietly wrong
and least likely to be caught by looking at it: CIEDE2000, linear-light
averaging, greedy palette selection, a white-balance pass, and a dirty-rect
cache that has to give exactly the same answer as recomputing everything.

It also barely touches Android. `ColorMath`, `ImageConverter`, `PhotoStudio`,
`BitmapLoader` and the two model files use about six `android.graphics` classes
between them, so stubbing those (see `stubs/`) is enough to compile the real
sources with a plain `kotlinc` and then **run** them on real pixels.

```sh
./check.sh                      # needs kotlinc on PATH, a JDK, python3 + numpy
KOTLINC=/opt/kotlinc/bin/kotlinc ./check.sh
```

## What it establishes

| | |
|---|---|
| **It compiles** | the engine type-checks against the stubs |
| **`Harness.kt`** | runs conversions over a fixture and dumps every board as text |
| **`Cross.kt`** | `PhotoStudio` (live preview) and `ImageConverter` (committed pattern) produce identical boards across 24 configurations — 2 board shapes × 3 sizes × masked/unmasked × 2 white balances, with brightness, contrast, saturation and chroma lift all off their defaults |
| **incremental == full** | six brush strokes applied incrementally give a board identical to reaching the same mask from scratch. This is the correctness property the whole real-time design rests on: if the dirty-rect logic ever drops a cell, this diff catches it |
| **`compare.py`** | an *independent* Python implementation of the same maths agrees bead for bead |
| **`Bench.kt`** | how long a slider move and a brush stroke actually cost |

`compare.py` is deliberately a separate implementation (it shares only
`tools/library/pipeline_test.py`'s colour primitives, which are themselves
checked against the published CIEDE2000 reference dataset). Two implementations
agreeing is evidence; one implementation checking itself is not.

## The fixture

`prepare_fixture.py` generates it — a hue sweep crossed with a luma ramp, five
flat patches, and an off-centre ellipse mask whose edge crosses cells at every
angle so partially-masked cells are exercised. Synthetic on purpose: the check
runs in a fresh clone with no photo to ship, and it is deterministic, so a
failure is a real regression rather than a different picture.

Point it at a real photo instead by writing your own `photo.argb` (little-endian
ARGB, 288×384) and `mask.u8` (one byte per pixel, non-zero = keep).

## What it does NOT cover

Compose UI. `PhotoTuneScreen`, the editor and the navigation need the real
Android toolchain — Material3 and the Compose compiler plugin only ship from
Google's Maven. Those still get their first real check from `./gradlew`.

## Benchmark caveat

`Bench.kt` runs on a desktop JVM, not a phone. Treat the numbers as ratios
(incremental vs full rebuild) rather than as device timings; a mid-range phone
is several times slower.
