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
- `render.py` : renders any pattern (or the whole `patterns.json`) to PNG the way
  the app does, for eyeballing quality. `canvas.py` holds the shape primitives.

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
cd tools/library
python build_manifest.py            # auto-increments the version
git add ../../library && git commit -m "Library update" && git push
```

The `patternsUrl` in the manifest points at the raw GitHub file on the app's
branch. Point it elsewhere (GitHub Pages, a CDN) with `--raw-base` if you host
the library somewhere else.

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

Ten content categories, 100 patterns each, plus the `threeD` specialty:

`geometric mandalas hearts stars flowers rainbows space emoji gems icons threeD`

(plus `custom` for user designs, which never appears in the published library).

- The nine parametric categories come from `gen_library.py`.
- **icons** comes from `gen_icons.py` (letters, digits, symbols).
- **threeD** comes from `gen_3d.py`; each carries a `buildGuide` and
  `assemblyGuide` the app shows on an Instructions sheet.
- Add your own real creations to any category with the photo tool above.
