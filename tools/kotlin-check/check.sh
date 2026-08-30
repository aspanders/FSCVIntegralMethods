#!/usr/bin/env bash
# Type-check and VERIFY the app's conversion engine without an Android SDK.
#
# The engine (ColorMath / ImageConverter / PhotoStudio / BitmapLoader) touches
# only a handful of android.graphics classes, so stubbing those is enough to
# compile it with a plain kotlinc and then RUN it on real pixel data. That
# turns "it looks right" into three checkable properties:
#
#   1. it compiles
#   2. it agrees bead-for-bead with an independent Python implementation
#   3. the incremental (brush) path gives the same board as a full rebuild
#
# Requirements: kotlinc on PATH (or KOTLINC=/path/to/kotlinc), a JDK, python3
# with numpy. Compose UI files are NOT covered - they need the real toolchain.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
SRC="$REPO/BeadSnapAndroid/app/src/main/kotlin/com/beadsnap/app"
WORK="${WORK:-/tmp/beadsnap-kcheck}"
KOTLINC="${KOTLINC:-kotlinc}"

COROUTINES="${COROUTINES:-$(dirname "$(dirname "$(command -v "$KOTLINC" || echo /opt/kotlinc/bin/kotlinc)")")/lib/kotlinx-coroutines-core-jvm.jar}"

ENGINE=(
  "$SRC/data/model/BeadColor.kt"
  "$SRC/data/model/FusePattern.kt"
  "$SRC/services/ColorMath.kt"
  "$SRC/services/BitmapLoader.kt"
  "$SRC/services/ImageConverter.kt"
  "$SRC/services/PhotoStudio.kt"
)

mkdir -p "$WORK"
echo "==> fixture"
python3 "$HERE/prepare_fixture.py" "$WORK"

echo "==> compile engine"
"$KOTLINC" -nowarn -d "$WORK/engine" "$HERE"/stubs/*.kt "${ENGINE[@]}"

for main in Harness Cross Bench Decode Crop; do
  echo "==> $main"
  "$KOTLINC" -nowarn -include-runtime -d "$WORK/$main.jar" \
    "$HERE"/stubs/*.kt "$HERE/$main.kt" "${ENGINE[@]}"
  java -Dfixture="$WORK" -jar "$WORK/$main.jar"
done

echo "==> incremental brush vs full rebuild"
if diff -q <(tail -n +2 "$WORK/out_incremental.txt") \
           <(tail -n +2 "$WORK/out_fromscratch.txt") >/dev/null; then
  echo "  IDENTICAL"
else
  echo "  DIFFER - the dirty-rect logic is dropping cells"; exit 1
fi

# Play Billing has no emulator here and no Android SDK, so this is a
# TYPE check, not a behaviour one: stubs/BillingStubs.kt encodes the v8
# signatures from the public API reference, and compiling TipJarManager
# against them proves the call sites match the library the app declares.
# Reverting either v8 migration - the no-argument enablePendingPurchases, or
# treating the queryProductDetailsAsync callback's second argument as a list -
# fails right here.
# The AI pattern service had never been compiled off-device, let alone run, so
# nothing could notice that its default request could not succeed: a 32x32 board
# as per-cell JSON needs ~6,700 output tokens against a max_tokens of 4,096, and
# every ordinary prompt came back truncated. This drives it end to end against
# the okhttp / org.json stubs - what goes on the wire, and what it makes of a
# reply - so the request shape and the validation are checked, not assumed.
echo "==> ai pattern service"
"$KOTLINC" -nowarn -cp "$COROUTINES" -include-runtime -d "$WORK/Ai.jar" \
  "$HERE"/stubs/*.kt "$HERE/Ai.kt" \
  "$SRC/data/model/BeadColor.kt" "$SRC/data/model/FusePattern.kt" \
  "$SRC/services/AIPatternService.kt"
java -cp "$WORK/Ai.jar:$COROUTINES" AiKt

echo "==> play billing call sites (v8 signatures)"
"$KOTLINC" -nowarn -cp "$COROUTINES" -d "$WORK/billing" \
  "$HERE"/stubs/*.kt "$SRC/services/TipJarManager.kt"

# Compiling proves the SIGNATURES match. It cannot prove the flow works, and
# both faults found in the tip jar compiled perfectly - a discarded return value
# and a call that was simply never made. This asserts the fixes are still there.
echo "==> tip jar"
python3 "$HERE/billing.py"

echo "==> python reference"
python3 "$HERE/compare.py" "$WORK"

# No Swift toolchain here, so the iOS colour maths and AI request cannot be
# compiled or run. This proves the port is a faithful TRANSCRIPTION - every
# constant and function present on both sides, and the AI settings that made the
# feature work matching - which is the failure mode a hand port actually has.
echo "==> android / ios parity"
python3 "$HERE/parity.py"

echo "==> library regressions"
python3 "$REPO/tools/library/test_regressions.py"
