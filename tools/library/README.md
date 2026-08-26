# BeadSnap Pattern Library (developer tools)

The app ships with a bundled seed set and then downloads an updatable library
from `library/manifest.json` on every launch. These tools build that library
and let you add your own patterns from photos.

## Files

- `library/palette.json` : the 55 bead colors (extracted from the app palette).
- `library/patterns.json` : every published pattern (the file the app downloads).
  Uses a compact `rows` encoding (one string per grid row, each char a palette
  index; `.` = empty) so 1,000+ patterns fit in ~1 MB. Both apps expand it back
  to cells on load. See `compact.py`.
- `library/manifest.json` : tiny `{version, count, perCategory, patternsUrl}` the app checks first.
- `library/incoming.json` : your staged photo patterns (created by the photo tool).

The library also ships **bundled** inside each app (Android
`app/src/main/assets/library.json`, iOS `Resources/library.json`) so it shows on
first run offline. `build_manifest.py` keeps those copies identical to
`patterns.json`.

## Generators

- `gen_library.py` : 9 categories x 100 procedural patterns (geometric, mandalas,
  hearts, stars, flowers, rainbows, space, emoji, gems). Real parametric variety,
  rendered as touching "fused" beads.
- `gen_icons.py` : icons (letters, digits, symbols), 100+.
- `gen_3d.py` : threeD builds, each with a `buildGuide` and `assemblyGuide`.
- `gen_seeds.py` : regenerates the tiny in-app `SeedPatterns` (one example per
  category) for both platforms. Run after changing the taxonomy.
- `gen_creatures.py` / `gen_objects.py` / `gen_faces.py` : the silhouette
  categories, built from parametric parts rather than recolours.
- `gen_willie.py` : three hand-drawn Steamboat Willie boards for `videogame`.
  **Read the copyright note at the top of that file before adding to it** -
  only the 1928 public-domain depiction belongs there, and the note also
  explains why there are three of them and not thirty.
- `render.py` : renders any pattern (or the whole `patterns.json`) to PNG the way
  the app does, for eyeballing quality. `canvas.py` holds the shape primitives.

## Quality passes

Every pattern goes through these on its way into `patterns.json`; none of them
live in the app.

- `connectivity.py` : the physical checks. Strips backdrops, welds loose parts
  onto the main piece, widens the one-bead necks that carry weight (and only
  those - a leg or an antenna is meant to be one bead wide), and pulls
  symmetric subjects true about their own mirror line.
- `scaling.py` : the small and medium boards each pattern carries in its
  `sizes` map. Box-majority reduction, then the same weld/widen/mirror repair
  at the smaller size, because a reduced board still has to be buildable.
- `uniqueness.py` / `audit.py` : distinctness. Two boards that render the same
  are one pattern, however differently they were specified.
- `test_regressions.py` : one named test per bug found in a QC pass, so none of
  them can come back. Run it after any change to a generator or a pass.

## How the app updates

1. On launch the app fetches `manifest.json`.
2. If its `version` is higher than the one the app last applied, it downloads
   `patterns.json`, caches it, merges it on top of the bundled seeds, and shows
   a "Pattern library updated" notice.
3. Everything works offline from the cached copy until the next successful check.

So: to push new patterns to everyone who has the app, rebuild the library with a
higher version and commit `library/manifest.json` + `library/patterns.json`.

## Publish an update

```bash
scripts/publish-library.sh --push
```

That rebuilds the library, runs the regression checks, bumps the version and
the bundled-version constants in both apps, commits and pushes. Drop `--push`
to review the commit first; `--dry-run` builds and verifies without touching
git. The manual equivalent is:

```bash
cd tools/library
python build_manifest.py            # auto-increments the version
git add ../../library && git commit -m "Library update" && git push
```

Both apps try a LIST of hosts (`LibrarySources.BASES` on Android, `sources` on
iOS) and take the first that answers, fetching `patterns.json` as a sibling of
whichever `manifest.json` responded. So re-hosting the library is a matter of
adding the new home to the front of those lists in a future app release - the
old host keeps serving everyone who has not updated. `--raw-base` still sets
the absolute `patternsUrl` written into the manifest, which older app versions
rely on.

## Add patterns from your own photos

Photograph a finished bead creation, then:

```bash
pip install pillow      # one time
cd tools/library
python photo_to_pattern.py add ~/photos/my_flower.jpg \
    --title "My Flower" --category flowers --tags flower,red --grid 32 --max-colors 14
python build_manifest.py            # folds it into the library, bumps version
```

Or a whole folder at once with a CSV (`filename,title,category,tags`):

```bash
python photo_to_pattern.py batch ~/photos --csv meta.csv --grid 32
python build_manifest.py
```

The photo tool uses the same LAB nearest-color quantization as the app, so what
you stage looks like what a user would get converting the same photo in-app.

## Categories

Twenty-two content categories, 100 patterns each, plus the `threeD` specialty:

`geometric mandalas hearts stars flowers rainbows space emoji gems icons
animals birds fish bugs food sweets trees vehicles snowflakes holidays
videogame sports threeD`

(plus `custom` for user designs, which never appears in the published library).

- `gen_library.py` produces the first nine parametric categories.
- `gen_library2.py` produces animals, birds, fish, bugs, food, sweets, trees,
  vehicles, snowflakes, holidays, videogame, and sports.
- **icons** comes from `gen_icons.py` (letters, digits, symbols).
- **threeD** comes from `gen_3d.py`; each carries a `buildGuide` and
  `assemblyGuide` the app shows on an Instructions sheet.
- Add your own real creations to any category with the photo tool above.
