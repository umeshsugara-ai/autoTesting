"""`.goal/goal.json`'s criticality vocabulary must match the classifier's.

AT-116 (checker-found): the shared classifier keys its ordering off the
lowercase set below and falls back to `"low"` for anything it does not
recognise — case-sensitively. This project wrote `"HIGH"`, `"CRITICAL"`,
`"NORMAL"` … from the day the file was created, so **every** task's declared
floor was silently discarded and 41 of 44 rows derived `low`. Nothing failed;
the field simply never did anything.

That is the failure mode this test exists for: a config value that is read,
not rejected, and quietly ignored. It cannot be caught by the classifier
(which has no way to know `"HIGH"` was meant to be `"high"`) so it is pinned
here, on the data.
"""

from __future__ import annotations

import json
from pathlib import Path

GOAL = Path(__file__).resolve().parents[1] / ".goal" / "goal.json"

# Mirrors `goal/scripts/criticality.py::_ORDER`. Duplicated deliberately: that
# file is a shared AIOS skill outside this repo, so importing it would make this
# project's test suite depend on a path it does not own.
CLASSIFIER_VOCABULARY = {"low", "medium", "high", "critical"}


def tasks() -> list[dict]:
    return json.loads(GOAL.read_text(encoding="utf-8"))["tasks"]


def test_every_base_criticality_is_a_value_the_classifier_recognises() -> None:
    """The whole of AT-116 in one assertion. A value outside this set is not a
    validation error anywhere — it is silently downgraded to the lowest floor."""
    unknown = {
        t["id"]: t["base_criticality"]
        for t in tasks()
        if t.get("base_criticality") not in CLASSIFIER_VOCABULARY
    }
    assert not unknown, (
        "these tasks declare a criticality the classifier will silently ignore, "
        f"downgrading them to 'low': {unknown}"
    )


def test_the_highest_risk_pending_work_actually_derives_critical() -> None:
    """The consequence that made AT-116 worth fixing rather than noting: a
    `critical` task gets a DUAL check (two blind checkers, both must pass).
    While the vocabulary mismatch stood, T-145 — an autonomous crawler pointed
    at a live production ERP — derived `low` and would have got a single one."""
    by_id = {t["id"]: t for t in tasks()}
    for task_id in ("T-145", "T-154"):
        assert by_id[task_id].get("criticality") == "critical", (
            f"{task_id} derives {by_id[task_id].get('criticality')!r}, not 'critical' — "
            "it would be dispatched to a single checker"
        )
