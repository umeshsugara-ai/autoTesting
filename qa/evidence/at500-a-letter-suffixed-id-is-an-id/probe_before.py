"""The same probe against the PRE-fix guard (HEAD's doctor.py), loaded by path.

No working-tree mutation: a second maker loop shares this tree, so nothing is
stashed, checked out or reset.
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "src")

BEFORE = Path(__file__).with_name("doctor_before.py")
spec = importlib.util.spec_from_file_location("doctor_before", BEFORE)
assert spec and spec.loader
doctor_before = importlib.util.module_from_spec(spec)
sys.modules["doctor_before"] = doctor_before  # @dataclass resolves via sys.modules
spec.loader.exec_module(doctor_before)

REPO = Path("d:/autoTesting")
TARGET = "AT-298b"

with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "repo"
    (root / "qa").mkdir(parents=True)
    for kind in ("manifests", "verdicts"):
        shutil.copytree(REPO / "qa" / kind, root / "qa" / kind)
    rows = [ln for ln in (REPO / "qa" / "issues.jsonl").read_text(encoding="utf-8").splitlines()
            if ln.strip()]
    dropped = [ln for ln in rows if json.loads(ln).get("id") != TARGET]
    (root / "qa" / "issues.jsonl").write_text("\n".join(dropped) + "\n", encoding="utf-8")

    found = [v for v in doctor_before.check_qa_issue_rows(root) if TARGET in v.detail]
    print(f"PRE-FIX guard, {TARGET} row deleted: {len(found)} violation(s) naming it")
    for v in found:
        print(f"  {v.rule}: {v.location}")
    total = len(doctor_before.check_qa_issue_rows(root))
    print(f"  (it reported {total} violation(s) in total -- the loss is simply invisible)")
