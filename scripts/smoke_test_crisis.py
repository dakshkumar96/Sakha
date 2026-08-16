"""Offline crisis-detector test over knowledge/taxonomy/crisis_fixture_set.jsonl.

No server required — this exercises the lexicon directly, so it can run in
CI or before starting the backend.

Usage:
    python scripts/smoke_test_crisis.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from backend.engines import crisis_detector  # noqa: E402

FIXTURES = ROOT / "knowledge" / "taxonomy" / "crisis_fixture_set.jsonl"

# Under-detection on a real crisis is the dangerous direction; over-detection
# on ordinary distress is merely annoying. Report them separately.
_ORDER = {"NONE": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}


def main() -> None:
    if not FIXTURES.exists():
        print(f"ERROR: {FIXTURES} not found")
        sys.exit(1)

    cases = [
        json.loads(line)
        for line in FIXTURES.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    passed = 0
    under: list[str] = []
    over: list[str] = []

    for case in cases:
        result = crisis_detector.detect(case["text"])
        expected = case["expect_level"]
        got = result.level

        if got == expected:
            passed += 1
            status = "PASS"
        elif _ORDER[got] < _ORDER[expected]:
            under.append(f"{case['text'][:52]!r}: expected {expected}, got {got}")
            status = "UNDER"
        else:
            over.append(f"{case['text'][:52]!r}: expected {expected}, got {got}")
            status = "OVER"

        if status != "PASS":
            print(f"[{status}] ({case['lang']}) {case['text'][:56]!r} "
                  f"expected={expected} got={got} flags={sorted(result.flags)}")

    print()
    print(f"{passed}/{len(cases)} fixtures matched exactly")

    if under:
        print(f"\nUNDER-DETECTED ({len(under)}) — this is the dangerous direction:")
        for line in under:
            print(f"  - {line}")
    if over:
        print(f"\nOVER-DETECTED ({len(over)}) — safe-fails to care, but check for noise:")
        for line in over:
            print(f"  - {line}")

    # Language routing check on the helpline text itself.
    hi = crisis_detector.detect("आज रात मैं जान दे दूँगा")
    en = crisis_detector.detect("I have a plan to end my life tonight")
    lang_ok = hi.lang == "hi" and en.lang == "en"
    print(f"\n[{'PASS' if lang_ok else 'FAIL'}] helpline language routing "
          f"(devanagari->hi={hi.lang}, english->en={en.lang})")

    # Under-detection fails the build. Over-detection is reported, not fatal.
    if under or not lang_ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
