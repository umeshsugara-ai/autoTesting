"""Does the AT-511 stop-condition change alter the ids actually read?

Line-classification counts are the wrong measure: a line only matters if it sits
inside a marker block. This compares the id SET per artifact, shipped vs proposed,
in both directions, and flags any id that has no ledger row (the false-accusation
direction).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "src")
from autotester.ledger import checks  # noqa: E402

REPO = Path("d:/autoTesting")
MARKERS = (("manifests", "**Issues addressed:**"), ("verdicts", "ISSUES-WRITTEN"))

NEW_FIELD = re.compile(r"^[\s>#*_-]*[A-Z][A-Z -]*(\([^)]*\))?\s*:")


def proposed_lines(body: str, marker: str) -> list[str]:
    lines, out = body.splitlines(), []
    for n, line in enumerate(lines):
        if not checks._is_marker_line(line, marker):
            continue
        out.append(line)
        for follow in lines[n + 1:]:
            stripped = follow.lstrip()
            if (not follow.strip() or stripped.startswith("#") or stripped.startswith("```")
                    or NEW_FIELD.match(follow) or checks._is_marker_line(follow, marker)):
                break
            out.append(follow)
    return out


def ids(lines: list[str]) -> set[str]:
    return {i for line in lines for i in re.findall(rf"\b{checks.ISSUE_ID}\b", line)}


rows = {json.loads(line)["id"] for line in
        (REPO / "qa" / "issues.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()}

dropped: list[tuple[str, set[str]]] = []
added: list[tuple[str, set[str]]] = []
for kind, marker in MARKERS:
    for path in sorted((REPO / "qa" / kind).glob("*.md")):
        body = path.read_text(encoding="utf-8", errors="replace")
        old = ids(checks._marker_lines(body, marker))
        new = ids(proposed_lines(body, marker))
        where = f"{kind}/{path.name}"
        if old - new:
            dropped.append((where, old - new))
        if new - old:
            added.append((where, new - old))

print(f"artifacts whose id set SHRINKS: {len(dropped)}")
for where, gone in dropped:
    flag = " <- NO LEDGER ROW" if any(i not in rows for i in gone) else ""
    print(f"  {where}: {sorted(gone)}{flag}")
print(f"\nartifacts whose id set GROWS: {len(added)}")
for where, gain in added:
    flag = " <- NO LEDGER ROW (would be a NEW violation)" if any(i not in rows for i in gain) else ""
    print(f"  {where}: {sorted(gain)}{flag}")
