"""AT-500 falsification against the REAL repo, not a fixture.

Copy qa/ to a temp tree, drop the live AT-298b row, and ask the guard.
Before the widening it said nothing at all; after it, the loss is named.
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")
from autotester import doctor  # noqa: E402

REPO = Path("d:/autoTesting")
TARGET = "AT-298b"


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        (root / "qa").mkdir(parents=True)
        for kind in ("manifests", "verdicts"):
            shutil.copytree(REPO / "qa" / kind, root / "qa" / kind)
        src = (REPO / "qa" / "issues.jsonl").read_text(encoding="utf-8").splitlines()

        intact = [ln for ln in src if ln.strip()]
        dropped = [ln for ln in intact if json.loads(ln).get("id") != TARGET]
        print(f"rows intact: {len(intact)} -> rows after dropping {TARGET}: {len(dropped)}")

        for label, rows in (("INTACT", intact), (f"{TARGET} DROPPED", dropped)):
            (root / "qa" / "issues.jsonl").write_text("\n".join(rows) + "\n", encoding="utf-8")
            found = [v for v in doctor.check_qa_issue_rows(root) if TARGET in v.detail]
            print(f"\n{label}: {len(found)} violation(s) naming {TARGET}")
            for v in found:
                print(f"  {v.rule}: {v.location} - {v.detail}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
