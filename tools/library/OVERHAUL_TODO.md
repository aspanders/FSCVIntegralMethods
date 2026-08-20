# Library uniqueness overhaul — progress & remaining work

Goal (from user): every icon in the library must be a **unique fuse-bead
pattern**, not a color-only variant. Target **200 per category**. Run an
**independent per-image audit** (a reviewer agent identifies each icon and
suggests fixes) and revise until it passes.

## Baseline problem (measured)
Of 2,203 patterns, only **687 were structurally unique**; 1,516 were color-only
recolors. Worst: birds 6 unique/100, fish 8, gems/mandalas/bugs/trees 11.

## Machinery built (reusable)
- `uniqueness.py` — color-agnostic `signature` + `dedup` (recolors collapse);
  `colored_signature` for color-defined categories (rainbows).
- `gen_unique.py` — home for the overhauled 200-unique generators.
- `audit_prep.py` — renders each icon as a numbered tile + intended-label
  manifest for one category (batches of 20).
- `icon-audit` workflow — independent reviewer agents view each tile blind,
  guess it, rate clarity 1-5, suggest a fix. (Run per category.)
- `render.numbered_montage` — blind numbered montages for the audit.

## Audit

`python audit.py` measures both halves of this and prints failures;
`python audit.py --montage <category>` renders a contact sheet to eyeball.
Two numbers matter per category: **unique %** (colour-blind distinct designs)
and **exactDup** (byte-identical boards, the indefensible case).

Baseline v9: 2790 patterns, 59.0% distinct, 1145 exact duplicates.
After v11:   2777 patterns, 74.2% distinct,  250 exact duplicates.

## DONE (overhauled, wired, shipped)
| category | unique | notes |
|---|---|---|
| emoji | 200 | combinatorial eyes x mouths, one yellow face (structural only) |
| geometric | 200 | ~40 motif families x structural params |
| mandalas | 200 | interleaved 5/6/8/10/12/16-fold |
| snowflakes | 200 | ornate dendritic + hex plates, exact 6-fold |
| hearts | 133 | internal patterns + monograms + arrangements (silhouette-capped) |
| stars | 120 | n-point, star-polygons, bursts, wreaths, patterned fills |
| gems | 126 | cuts x facets + clusters/rings/pendants |
| birds | 100 | 20 species as PROPORTIONS (neck/leg/beak/tail) x 5 poses |
| fish | 100 | 20 species x body/tail/fin/marking, tail scaled to body |
| bugs | 87 | 20 species x 5 plans (beetle/flier/walker/crawler/spider/snail) |
| trees | 100 | 20 species x crown plan (round/conifer/column/weep/palm/...) |
| circles | 100 | was 36% - every family now varies across all ten runs |

Shared machinery in `gen_creatures.py` worth reusing for the rest:
`_frame` draws on a roomy canvas then centres the ink on the board (no more
clipped tails, no more subjects adrift), `_pick_bg` chooses the background
furthest from the body colour (no more silver fish on grey water), `_outline`
gives every subject a one-bead dark edge.

## STATUS: complete

`python audit.py` is the gate. It measures four things, and the third only
exists because the first two passed while the library was still repetitive:

| measure | what it catches |
|---|---|
| distinct designs | colour-only recolours |
| exact duplicates | the same board shipped twice |
| **lookalike pairs** | boards differing by a handful of beads, which `signature` calls unique |
| near-blank / speckled / tiny | patterns not worth making |

Lookalikes are split into **same-family** (a variant the drawing ignored) and
**cross-family** (two designs that render the same), because the fixes differ.

| | baseline v9 | v29 |
|---|---|---|
| patterns | 2790 | 2722 |
| distinct designs | 59.0% | **100.0%** |
| exact duplicates | 1145 | **0** |
| lookalike pairs | 13536 | **251, all in icons** |
| blank boards | 1 | **0** |

The 251 remaining are letters resembling letters - M and N, O and 0. `icons`
is deliberately exempt: a category defined by COMPLETENESS is worse for
missing D, F, N and 8 than for containing near-neighbours.

## Regression tests

`python test_regressions.py` has one named test per bug below, each stating the
SYMPTOM first. They run against the shipped patterns.json, so a regression in a
generator is caught by the artefact rather than by the code that made it.

## The bugs this pass found

Each of these passed every check that existed at the time.

1. **Auto-fit cancelled every scale variant.** `_frame` scales a subject up to
   fill the board, so a spec asking for 0.76 and one asking for 1.18 both came
   out full-size. "Grapes" and "Grapes Large" were 99.9% identical. Scale is
   now expressed as `fill` where the fitting happens.
2. **Shrinking makes different things converge.** The first fix used 0.54 fill
   for the small variants, and at that size "Wasp Small" and "Firefly Small"
   were 99.7% identical - and 90% of the board was background. 0.72 is the
   floor.
3. **`_emit` only deduped EXACT matches**, so a parameter sweep fine enough to
   fill a category was finer than the eye. It now rejects lookalikes, which is
   why the candidate pools are far larger than the targets.
4. **`family_of` missed sequence suffixes.** "Planet 4" and "Vert Stripes w1"
   each became their own family, which both mislabelled lookalike pairs and
   defeated the interleave - round-robin over 75 one-member families
   reproduces the original order, so space still opened with 16 planets and
   geometric with 14 stripe patterns.
5. **3D nets erased themselves.** `_place` wrote the overlay's transparent
   marker through as a colour, so every face overlay deleted the face under
   it: the dice net was a scatter of pips with no faces, the gift box four
   floating red bars. Nets also had no fold lines, and the lines had to be
   drawn BEFORE the overlay or they clipped the corner pips.
6. **The near-blank measure was wrong.** It compared the dominant colour to
   the PLACED beads, so a one-colour star on an empty board scored 100% - 57
   of 105 flags were that. It measures against the whole board now.
7. **One genuinely blank board** shipped: "Square Grid s4", where the grid
   spacing made the squares meet. `_is_blank` drops those.
8. **The lookalike detector itself was wrong.** `cell_map` numbered colours by
   FIRST APPEARANCE, so the map depended on which colour happened to occupy
   the top-left cell: two boards differing by a single bead, where that bead
   was the first cell, scored 5.6% similar instead of 94%. Indices are ranked
   by cell count now. Fixing it surfaced 34 more lookalikes in space alone,
   plus pairs like "Bear Cub == Panda Cub" that had been passing.
9. **The audit had its own copy of that map**, so the audit and the generators
   disagreed about what a lookalike is. There is one implementation now.

## Machinery worth reusing

- `_frame(draw, spec, bg, fill=)` - draw roomy, scale to the requested share
  of the board, centre the ink.
- `_pick_bg` - background furthest from the subject's colour.
- `_outline` - one-bead dark edge.
- `_run_ops` - shape recipes; `("clip", r)` erases outside a radius, which is
  how ball seams drawn as outside-centred rings stop leaving fragments.
- `uniqueness.select_distinct` / `family_of` - the distinctness backstop and
  the one shared definition of a design family.
- `_interleave` - deals each category round-robin across families.

## Traps worth not repeating

- **Generate specs pose-major.** `_emit` caps at the target, so species-major
  order silently drops the tail of the species list - vehicles shipped with no
  boats, planes or rockets while reporting 100 unique patterns.
- **A variant must change the drawing.** A "Winged" spider is still a spider.
- **Thin appendages fight the auto-scaler** - a one-bead tail widens the
  bounding box and shrinks the whole subject to fit it.
- **`Grid.set` ignores None**, so nothing can be erased by drawing over it.
- **Metrics can be clean while the category reads badly.** Look at the contact
  sheets: `python audit.py --montage <category>`.

## Historical TODO — remaining categories
## TODO — remaining categories (recolour-heavy; unique % from audit.py)

Worst first: sports 12%, holidays 12%, vehicles 13%, food 16%, videogame 18%,
flowers 21%, sweets 24%, rainbows 44%, animals 50%, icons 80%.

sports/food/holidays/videogame also carry 80/85/30/28 EXACT duplicates - the
same board shipped many times over - so they are the first thing a user
scrolling a category actually notices.

One option worth putting to the user before more generator work: cap each
category at its distinct-design count. That drops the library to ~2060
patterns but removes every duplicate immediately, and 2060 real designs is a
better product than 2777 with 717 repeats.

## TODO detail — remaining categories (still 100, recolor-heavy)
Overhaul each in `gen_unique.py`, wire into the right GENERATORS dict
(`gen_library.py` for the first 10, `gen_library2.py` for the rest), then
rebuild + bump version + seeds + commit.

- [ ] **flowers** — flower types (rose/daisy/tulip/sunflower/lotus/poppy/lily/
      cherry-blossom...) x petal counts x arrangements (single/bouquet/wreath/
      in-pot/with-stem). Parametric: ~150+ feasible.
- [ ] **rainbows** — MUST dedup by `colored_signature` (color IS the design).
      arcs/spectrum/ombre/rings/chevron/plaid/sunset x color schemes. ~150+.
- [ ] **space** — planets(banded/ringed/earth) + moons/phases + rockets + UFO
      + comets + constellations + aliens + satellites + sun. Already fairly
      unique (95); expand to ~150.
- [ ] **icons** — already 82 unique; expand the symbol set toward 200 (arrows,
      weather, hands, math, music, tech, zodiac, shapes, tools...).
- [ ] **animals** — cute faces + full-body poses per species; honest ceiling
      likely ~80-120 recognizable. Vary pose/composition, never color.
- [ ] **birds** — species x pose; ~60-100 honest ceiling.
- [ ] **fish** — body x fins x pattern x species; ~120-150 feasible.
- [ ] **bugs** — butterflies (wing patterns) huge + ladybug/bee/spider/snail/
      dragonfly/caterpillar/ant/beetle/moth; ~150 feasible.
- [ ] **food** — fruits/veg/meals distinct subjects; ~80-120 honest ceiling.
- [ ] **sweets** — cupcake/donut/icecream/lollipop/... ; ~60-90 ceiling.
- [ ] **trees** — tree/pine/palm/cactus/bush/... x season; ~60-90 ceiling.
- [ ] **vehicles** — car/truck/bus/train/boat/plane/... distinct; ~60-90.
- [ ] **holidays** — seasonal items; ~60-90 ceiling.
- [ ] **videogame** — retro sprites; ~80-120 feasible.
- [ ] **sports** — balls + equipment; ~50-80 honest ceiling.

Note: several SUBJECT categories cannot reach 200 genuinely-unique
recognizable designs — deliver the honest max (all unique) and record it, do
not pad with near-duplicates.

## TODO — independent audit (was blocked)
The reviewer agents hit the session usage limit. When usage resets, for each
overhauled category run:
1. `python audit_prep.py <cat>`
2. `Workflow` with the `icon-audit` script, args = the category manifest
   (pass as a JSON object; the script also tolerates a JSON string).
3. Revise the weak tiles (clarity <= 3) per the agents' suggestions; re-audit.

## TODO — app logo (user request, do after categories)
A single **3D fuse bead** (the classic ring/tube perler bead) rendered in a
clean modern app-icon style (soft gradient, depth/shadow, rounded-square).
Produce iOS `AppIcon` set + Android adaptive/mipmap icons.

## Rebuild checklist per category
1. write/refine generator in `gen_unique.py`
2. wire it in the correct GENERATORS dict
3. `python gen_seeds.py`
4. `python build_manifest.py --version <n>`  (auto-copies bundled assets)
5. bump `BUNDLED_LIBRARY_VERSION` (Android) / `bundledLibraryVersion` (iOS)
6. verify uniqueness, commit + push
