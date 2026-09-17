"""Which notes change verdict when the substring test becomes a word-boundary one?

Prints every parenthetical in the live manifests whose "is this a fix claim?"
answer differs between the shipped filter and the proposed one, in both
directions. A change that moves a real claim out is as bad as one that leaves
the false accusation in.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path("d:/autoTesting")
ISSUE_ID = r"AT-\d+[a-z]?"
MARKER = "**Issues addressed:**"

_LEAD = re.compile(r"^[\s>#*_-]*")
NEGATED = re.compile(r"\bnot\b[\w\s-]{0,15}?\bfixed\b", re.IGNORECASE)
FIXED = re.compile(r"\bfixed\b", re.IGNORECASE)


def old(note: str) -> bool:
    return "fixed" in note.lower() and "not fixed" not in note.lower()


def new(note: str) -> bool:
    return bool(FIXED.search(note)) and not NEGATED.search(note)


def main() -> int:
    seen: dict[str, tuple[bool, bool, str]] = {}
    for path in sorted((REPO / "qa" / "manifests").glob("*.md")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if not _LEAD.sub("", line).startswith(MARKER.strip("*")):
                continue
            for issue, note in re.findall(rf"\b({ISSUE_ID})\s*\(([^)]*)\)", line):
                seen.setdefault(note, (old(note), new(note), f"{path.name} {issue}"))

    same = [n for n, (o, w, _) in seen.items() if o == w]
    moved = {n: v for n, v in seen.items() if v[0] != v[1]}
    print(f"distinct notes: {len(seen)} | unchanged verdict: {len(same)} | CHANGED: {len(moved)}")
    for note, (o, w, where) in sorted(moved.items()):
        arrow = "claim -> NOT a claim" if o else "NOT a claim -> claim"
        print(f"  [{arrow}]  ({note})")
        print(f"      first seen: {where}")

    print("\nsynthetic shapes the reviewer reproduced:")
    for note in ("low, unfixed - tracked separately", "low, not-fixed, deferred",
                 "low, prefixed by AT-899", "low, NOT fixed - reasons below",
                 "low, open -> fixed", "medium, open \u2192 fixed", "fixed",
                 "low, not yet fixed", "not a duplicate, open -> fixed"):
        print(f"  old={old(note)!s:<5} new={new(note)!s:<5} ({note})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
