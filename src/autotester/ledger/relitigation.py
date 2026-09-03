"""The cyclic-rebuild gate: is this new unit a retired feature coming back?

Principle D-004: rules decide only where certain (an explicit feature id in the
unit text); everything else goes to the judge model with the retired rows'
descriptions and reasons. A keyword miss is never treated as "no match".
"""

from __future__ import annotations

import re

from autotester.core.paths import RepoDocs
from autotester.providers.base import Provider
from autotester.schema.enums import UserValue
from autotester.schema.ledger import FeatureEvent, RelitigationVerdict

_FEATURE_ID_RE = re.compile(r"\bF-\d{3,}\b")
PROMPT_NAME = "relitigation_v1.md"


def _certain_match(unit_text: str, retired_rows: list[FeatureEvent]) -> FeatureEvent | None:
    """Deterministic only on an explicit id — the one case a rule can be sure of."""
    ids = set(_FEATURE_ID_RE.findall(unit_text))
    for row in retired_rows:
        if row.id in ids or (row.supersedes and row.supersedes in ids):
            return row
    return None


def _render_rows(rows: list[FeatureEvent]) -> str:
    lines = []
    for row in rows:
        lines.append(
            f"- {row.id} `{row.feature}` — {row.title} "
            f"(retired {row.date}, value {row.user_value.value})\n"
            f"  description: {row.description}\n  reason: {row.reason}"
        )
    return "\n".join(lines)


def build_prompt(unit_text: str, retired_rows: list[FeatureEvent], docs: RepoDocs) -> str:
    template = (docs.prompts_dir / PROMPT_NAME).read_text(encoding="utf-8")
    return template.replace("{{RETIRED_ROWS}}", _render_rows(retired_rows)).replace(
        "{{UNIT}}", unit_text.strip()
    )


def relitigate(
    unit_text: str,
    retired_rows: list[FeatureEvent],
    judge: Provider,
    docs: RepoDocs | None = None,
) -> RelitigationVerdict:
    """Decide whether building `unit_text` re-delivers a retired feature.

    Returns a verdict whose `gate` is True when a human must confirm. With no
    retired rows there is nothing to relitigate and no model call is made.
    """
    if not retired_rows:
        return RelitigationVerdict(
            same_behaviour=False, justification="no retired features", confidence=1.0,
            decided_by="rule",
        )
    certain = _certain_match(unit_text, retired_rows)
    if certain is not None:
        return RelitigationVerdict(
            same_behaviour=True,
            matched_feature_id=certain.id,
            justification=f"unit names {certain.id} explicitly",
            confidence=1.0,
            decided_by="rule",
        )
    prompt = build_prompt(unit_text, retired_rows, docs or RepoDocs())
    verdict = judge.judge(prompt, RelitigationVerdict)
    return verdict.model_copy(update={"decided_by": "llm"})


def gate_message(verdict: RelitigationVerdict, retired_rows: list[FeatureEvent]) -> str:
    """The HUMAN_GATE text: feature, date, reason, and the three choices."""
    row = next((r for r in retired_rows if r.id == verdict.matched_feature_id), None)
    if row is None:
        return f"HUMAN_GATE: {verdict.justification}"
    weight = "HIGH-value " if row.user_value is UserValue.HIGH else ""
    return (
        f"HUMAN_GATE: {row.id} '{row.title}' ({weight}feature) was retired on {row.date} — "
        f"reason: {row.reason}\n"
        f"  judge: {verdict.justification} (confidence {verdict.confidence:.2f})\n"
        "  choices: rebuild as-is · build differently (state why) · cancel"
    )
