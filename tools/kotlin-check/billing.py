#!/usr/bin/env python3
"""Check the tip jar for the mistakes that cost real money, silently.

There is no billing emulator here and the stubs do nothing, so compiling
TipJarManager proves only that the call sites match the v9 signatures - not
that the flow WORKS. Both faults found in review compiled perfectly:

  * launchBillingFlow reports failure by RETURN VALUE, and the return value was
    thrown away. When checkout did not open, the tip button was dead - no
    dialog, no message, no state change, nothing in the log.

  * queryPurchasesAsync was never called at all. A consumable that is bought
    but never consumed is refunded automatically after three days, so a tip
    paid while the app was killed mid-checkout came back to the user as a
    refund and we never even said thank you.

Neither is visible to a type checker and neither can be reached from a unit
test without injecting a fake BillingClient through production code. What CAN
be checked cheaply is that the code that fixes them is still there, which is
what this does - the same trick parity.py plays on the AI request.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
AND = os.path.join(REPO, "BeadSnapAndroid", "app", "src", "main", "kotlin", "com", "beadsnap", "app")

MANAGER = os.path.join(AND, "services", "TipJarManager.kt")
SHEET = os.path.join(AND, "ui", "tipjar", "TipJarSheet.kt")
MAIN = os.path.join(AND, "MainActivity.kt")


def strip_comments(src: str) -> str:
    """A rule quoted in a comment is documentation, not code."""
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return "\n".join(l for l in src.split("\n") if not l.strip().startswith(("//", "*")))


def main() -> int:
    for p in (MANAGER, SHEET, MAIN):
        if not os.path.exists(p):
            print(f"  MISSING {p}")
            return 1

    mgr = strip_comments(open(MANAGER).read())
    sheet = strip_comments(open(SHEET).read())
    main_act = strip_comments(open(MAIN).read())

    checks = [
        (
            "an undelivered tip is reconciled, not left to auto-refund",
            "queryPurchasesAsync" in mgr,
        ),
        (
            "reconciliation runs on launch, not only when the sheet opens",
            re.search(r"tipJar\.connect\(\)", main_act) is not None,
        ),
        (
            "launchBillingFlow's result is used, not discarded",
            re.search(r"=\s*billingClient\.launchBillingFlow\(", mgr) is not None,
        ),
        (
            "a tip cannot be launched before the client is ready",
            re.search(r"if\s*\(!billingClient\.isReady\)", mgr) is not None,
        ),
        (
            "a purchase result that is not OK is reported",
            re.search(r"else\s*->\s*_lastError\.value", mgr) is not None,
        ),
        (
            "backing out is not reported as a failure",
            "USER_CANCELED" in mgr,
        ),
        (
            "the same purchase token is never consumed twice",
            re.search(r"consuming\.add\(", mgr) is not None,
        ),
        (
            "the sheet shows what went wrong",
            "lastError" in sheet,
        ),
        (
            "a pending tip is not thanked for as if it were paid",
            "PurchaseState.PENDING" in mgr and "pendingTip" in sheet,
        ),
    ]

    bad = [name for name, ok in checks if not ok]
    for name, ok in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
