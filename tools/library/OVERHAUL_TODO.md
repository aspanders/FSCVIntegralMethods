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
