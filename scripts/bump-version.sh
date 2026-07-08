#!/usr/bin/env bash
# Bump BeadSnap's version on BOTH platforms in lockstep.
# Usage: scripts/bump-version.sh 1.1.0
set -euo pipefail

VERSION="${1:?usage: bump-version.sh <semver, e.g. 1.1.0>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

GRADLE="$ROOT/BeadSnapAndroid/app/build.gradle.kts"
PLIST="$ROOT/BeadSnap/BeadSnap/Resources/Info.plist"

# Android: versionName = semver, versionCode monotonically increments
OLD_CODE=$(grep -o 'versionCode = [0-9]*' "$GRADLE" | grep -o '[0-9]*')
NEW_CODE=$((OLD_CODE + 1))
sed -i.bak "s/versionCode = $OLD_CODE/versionCode = $NEW_CODE/" "$GRADLE"
sed -i.bak "s/versionName = \"[^\"]*\"/versionName = \"$VERSION\"/" "$GRADLE"
rm -f "$GRADLE.bak"

# iOS: CFBundleShortVersionString = semver, CFBundleVersion = same build number
python3 - "$PLIST" "$VERSION" "$NEW_CODE" <<'EOF'
import re, sys
path, version, build = sys.argv[1], sys.argv[2], sys.argv[3]
src = open(path).read()
src = re.sub(
    r"(<key>CFBundleShortVersionString</key>\s*<string>)[^<]*(</string>)",
    rf"\g<1>{version}\g<2>", src)
src = re.sub(
    r"(<key>CFBundleVersion</key>\s*<string>)[^<]*(</string>)",
    rf"\g<1>{build}\g<2>", src)
open(path, "w").write(src)
EOF

echo "Bumped both platforms to $VERSION (build/versionCode $NEW_CODE)"
echo "  Android: $GRADLE"
echo "  iOS:     $PLIST"
echo "Next: commit, tag v$VERSION, then archive (iOS) / bundleRelease (Android)."
