"""A behaviour fingerprint for the record checks, over the real qa/ corpus.

Run before and after the split; the two files must be byte-identical. Exercising
them over a DAMAGED copy as well as the live tree matters: on the live tree both
checks return nothing, and "nothing == nothing" would prove nothing at all.

    python at506_fingerprint.py <out.txt>
"""
from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")

REPO = Path("d:/autoTesting")
DROP = ["AT-298b", "AT-297b", "AT-494", "AT-401", "AT-500"]


def checks():
    """Import wherever they live now — the point of the fingerprint is that the
    behaviour does not move even though the definitions do."""
    try:
        from autotester.ledger import checks as mod  # after the split
    except ImportError:
        from autotester import doctor as mod  # before it
    return mod.check_qa_issue_rows, mod.check_ledger


def dump(fn, root: Path, label: str) -> list[str]:
    rows = sorted(f"{v.rule}|{v.location}|{v.detail}" for v in fn(root))
    return [f"--- {label}: {len(rows)} ---", *rows]


def main(out: Path) -> int:
    check_rows, check_ledger = checks()
    lines: list[str] = []
    lines += dump(check_rows, REPO, "live tree, check_qa_issue_rows")
    lines += dump(check_ledger, REPO, "live tree, check_ledger")

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "repo"
        (root / "qa").mkdir(parents=True)
        for kind in ("manifests", "verdicts"):
            shutil.copytree(REPO / "qa" / kind, root / "qa" / kind)
        kept = [ln for ln in (REPO / "qa" / "issues.jsonl").read_text(encoding="utf-8").splitlines()
                if ln.strip() and json.loads(ln).get("id") not in DROP]
        (root / "qa" / "issues.jsonl").write_text("\n".join(kept) + "\n", encoding="utf-8")
        lines += dump(check_rows, root, f"damaged copy ({len(DROP)} rows dropped)")

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[:4]))
    print(f"... {len(lines)} lines -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
