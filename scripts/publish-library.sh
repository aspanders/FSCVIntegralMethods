#!/usr/bin/env bash
# Publish a new pattern library to everyone who already has the app.
#
# The library is fetched over the air from a hosted manifest, so new patterns do
# NOT need an app-store release: rebuild, bump the version, push the two files,
# and installed copies pick them up on their next launch. A store release is
# only needed when app CODE changes.
#
#   scripts/publish-library.sh            # build, verify, commit — stops before pushing
#   scripts/publish-library.sh --push     # …and push
#   scripts/publish-library.sh --dry-run  # build and verify only, touch no git
#
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

PUSH=0
DRY=0
for arg in "$@"; do
  case "$arg" in
    --push)    PUSH=1 ;;
    --dry-run) DRY=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
OLD_VERSION="$(python3 -c "import json;print(json.load(open('library/manifest.json'))['version'])")"
OLD_COUNT="$(python3 -c "import json;print(json.load(open('library/manifest.json'))['count'])")"

echo "==> rebuilding the library (was v$OLD_VERSION, $OLD_COUNT patterns)"
python3 tools/library/build_manifest.py

echo "==> regression checks"
python3 tools/library/test_regressions.py

NEW_VERSION="$(python3 -c "import json;print(json.load(open('library/manifest.json'))['version'])")"
NEW_COUNT="$(python3 -c "import json;print(json.load(open('library/manifest.json'))['count'])")"

# The bundled copies inside each app were just refreshed too, so the constants
# that say which version is bundled have to move with them. Leaving them behind
# is not a bug - a fresh install would simply re-download a library it already
# had - but it is a pointless download, and the two drift further apart every
# publish.
echo "==> bundled-version constants -> $NEW_VERSION"
python3 - "$OLD_VERSION" "$NEW_VERSION" <<'PY'
import re, sys
old, new = sys.argv[1], sys.argv[2]
for path, pattern in [
    ("BeadSnapAndroid/app/src/main/kotlin/com/beadsnap/app/services/RemoteLibraryService.kt",
     r"(BUNDLED_LIBRARY_VERSION = )\d+"),
    ("BeadSnap/BeadSnap/Services/RemoteLibraryService.swift",
     r"(bundledLibraryVersion = )\d+"),
]:
    src = open(path).read()
    updated, n = re.subn(pattern, lambda m: m.group(1) + new, src)
    if n != 1:
        raise SystemExit(f"expected exactly one version constant in {path}, found {n}")
    open(path, "w").write(updated)
    print(f"    {path}")
PY

echo
echo "    v$OLD_VERSION ($OLD_COUNT patterns)  ->  v$NEW_VERSION ($NEW_COUNT patterns)"
echo

if [ "$DRY" = "1" ]; then
  echo "==> --dry-run: leaving git alone. 'git checkout -- .' to discard."
  exit 0
fi

git add library \
        BeadSnapAndroid/app/src/main/assets/library.json \
        BeadSnapAndroid/app/src/main/kotlin/com/beadsnap/app/services/RemoteLibraryService.kt \
        BeadSnap/BeadSnap/Resources/library.json \
        BeadSnap/BeadSnap/Services/RemoteLibraryService.swift

if git diff --cached --quiet; then
  echo "nothing changed - the library is already current."
  exit 0
fi

git commit -q -m "Pattern library v$NEW_VERSION ($NEW_COUNT patterns)"
echo "==> committed on $BRANCH"

if [ "$PUSH" = "1" ]; then
  for i in 1 2 3 4; do
    git push -u origin "$BRANCH" && break || sleep $((2 ** i))
  done
  echo
  echo "Live. Installed apps will pick up v$NEW_VERSION on their next launch."
  echo "Check it is really reachable:"
  echo "  curl -s https://raw.githubusercontent.com/aspanders/FSCVIntegralMethods/$BRANCH/library/manifest.json | head -c 200"
else
  echo
  echo "Not pushed. Review with 'git show', then:"
  echo "  git push -u origin $BRANCH"
fi
