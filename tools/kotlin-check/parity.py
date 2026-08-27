#!/usr/bin/env python3
"""Check that the Android and iOS colour maths have not drifted apart.

The two platforms must pick the same bead for the same pixel, or the same photo
produces two different patterns. There is no Swift toolchain in the development
container and no way to run BeadSnap/Services/ColorMath.swift here, so the next
best thing is to prove the port is a faithful TRANSCRIPTION: every numeric
constant in one file appears in the other, and every function does too.

That catches the failure mode a transcription actually has - a mistyped
coefficient, a dropped term, a function ported in name only - which no amount of
reading catches reliably. It does not catch a wrong ALGORITHM written
consistently in both, which is what tools/kotlin-check/compare.py is for on the
Kotlin side.

Differences that are genuinely expected are listed in ALLOWED below, each with a
reason. Anything else fails, so a future edit to one file and not the other
cannot pass quietly.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

KT = os.path.join(REPO, "BeadSnapAndroid", "app", "src", "main", "kotlin",
                  "com", "beadsnap", "app", "services", "ColorMath.kt")
SWIFT = os.path.join(REPO, "BeadSnap", "BeadSnap", "Services", "ColorMath.swift")

# Constants that legitimately appear on one side only.
ALLOWED = {
    "180.0": "Swift converts degrees by hand; Kotlin calls Math.toDegrees/toRadians",
}

# Helpers that exist on one platform because its standard library lacks the
# other's. Anything not listed here must exist on both.
ALLOWED_FUNCS = {
    "rad": "Swift has no Math.toRadians, so the conversion is a local helper",
}

# Kotlin writes Float literals with an f suffix - 0.04045f - and Swift does not.
# The suffix is stripped so the two sides compare as the same number.
NUMBER = re.compile(r"(?<![\w.])(\d+\.\d+|\d{3,})[fFdD]?(?![\w.])")
FUNC_KT = re.compile(r"\bfun\s+([A-Za-z][A-Za-z0-9]*)\s*\(")
FUNC_SWIFT = re.compile(r"\bfunc\s+([A-Za-z][A-Za-z0-9]*)\s*[(<]")


def strip_comments(src: str) -> str:
    """Constants quoted in prose are documentation, not behaviour."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return "\n".join(l for l in src.split("\n") if not l.strip().startswith(("//", "*", "/**")))


def numbers(src: str):
    from collections import Counter
    return Counter(NUMBER.findall(strip_comments(src)))


AI_KT = os.path.join(REPO, "BeadSnapAndroid", "app", "src", "main", "kotlin",
                     "com", "beadsnap", "app", "services", "AIPatternService.kt")
AI_SWIFT = os.path.join(REPO, "BeadSnap", "BeadSnap", "Services", "AIPatternService.swift")

# The AI request has to be the same on both platforms or the same words produce
# a different pattern - and one platform can silently keep a setting that made
# the feature unusable. These are the settings that mattered.
AI_MUST_MATCH = [
    ("claude-opus-5", "the model, not a small one - spatial layout is the hard part"),
    ("16000", "max_tokens; 4096 could not finish a default board"),
    ("adaptive", "thinking mode"),
    ("json_schema", "structured output rather than JSON hunted out of prose"),
    ("EDGES meet", "the fusing rule the pattern has to obey to be buildable"),
]

# Things whose PRESENCE means the old broken design is still there.
AI_MUST_BE_GONE = [
    ('"cells": [{"x"', "the per-cell schema that could not fit in max_tokens"),
    ("4096", "the old max_tokens"),
    ("claude-haiku-4-5", "the old model"),
]


def check_ai() -> list:
    """Both AI services must ask for the same thing."""
    problems = []
    for path, label in ((AI_KT, "Android"), (AI_SWIFT, "iOS")):
        if not os.path.exists(path):
            problems.append(f"{label} AIPatternService is missing")
            continue
        src = open(path).read()
        for needle, why in AI_MUST_MATCH:
            if needle not in src:
                problems.append(f"{label} AI service is missing '{needle}' ({why})")
        for needle, why in AI_MUST_BE_GONE:
            if needle in src:
                problems.append(f"{label} AI service still contains '{needle}' ({why})")
    return problems


def main() -> int:
    for p in (KT, SWIFT):
        if not os.path.exists(p):
            print(f"  MISSING {p}")
            return 1

    kt_src = open(KT).read()
    sw_src = open(SWIFT).read()

    kt_n = numbers(kt_src)
    sw_n = numbers(sw_src)

    problems = []

    only_kt = sorted(set(kt_n) - set(sw_n))
    only_sw = sorted(set(sw_n) - set(kt_n))
    for v in only_kt:
        if v not in ALLOWED:
            problems.append(f"constant {v} is in ColorMath.kt but NOT in ColorMath.swift")
    for v in only_sw:
        if v not in ALLOWED:
            problems.append(f"constant {v} is in ColorMath.swift but NOT in ColorMath.kt")

    # Names, lowercased: Kotlin uses EDGE_SNAP_DE, Swift edgeSnapDE.
    def norm(s):
        return s.lower().replace("_", "")

    kt_f = {norm(f) for f in FUNC_KT.findall(kt_src)}
    sw_f = {norm(f) for f in FUNC_SWIFT.findall(sw_src)}
    for f in sorted(kt_f - sw_f):
        if f not in ALLOWED_FUNCS:
            problems.append(f"function {f}() exists on Android but not on iOS")
    for f in sorted(sw_f - kt_f):
        if f not in ALLOWED_FUNCS:
            problems.append(f"function {f}() exists on iOS but not on Android")

    problems += check_ai()

    shared = sorted(set(kt_n) & set(sw_n))
    print(f"  {len(shared)} colour constants match across both platforms")
    print(f"  {len(kt_f & sw_f)} colour functions present on both")
    print(f"  {len(AI_MUST_MATCH)} AI request settings checked on both platforms")

    if problems:
        for p in problems:
            print(f"  FAIL  {p}")
        return 1
    print("  colour maths parity holds")
    return 0


if __name__ == "__main__":
    sys.exit(main())
