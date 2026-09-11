"""Shared data + spec builder for the mutation-instrument tests.

Both halves of the split suite drive the same synthetic project, so it lives in
one place (C1). The `mutation_repo` FIXTURE lives in `conftest.py` instead — a
fixture that is imported shadows the test's own parameter name.
"""

from __future__ import annotations

MODULE = '''def classify(value):
    if value > 10:
        return "big"
    return "small"
'''

TESTS = '''import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from mod import classify


def test_big_values_are_big():
    assert classify(50) == "big"


def test_small_values_are_small():
    assert classify(1) == "small"


def test_zz_runs_last():
    assert classify(999) == "big"
'''


def spec(**overrides) -> dict:
    """One mutation that genuinely breaks `classify`, with overrides for the
    attack cases. `kills` names the test that should notice."""
    mutation = {
        "name": "threshold broken", "file": "scripts/mod.py",
        "old": "if value > 10:", "new": "if value > 0:",
        "kills": ["test_small_values_are_small"],
    }
    mutation.update(overrides.pop("mutation", {}))
    return {"tests": "tests/test_mod.py", "mutations": [mutation], **overrides}
