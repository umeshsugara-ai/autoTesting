"""Read and append `docs/FEATURES.jsonl`. The only write path to the ledger.

Built on `store.filestore`'s generic JSONL primitives (C3: one concept, one
place for "how a file gets read or written") plus the one rule specific to
this collection: rows are history, so a repeated id is a defect, not a merge.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from autotester.schema.enums import FeatureEventKind, UserValue
from autotester.schema.ledger import AUTO_REASON, FeatureEvent
from autotester.store.filestore import append_jsonl as _append_jsonl
from autotester.store.filestore import read_jsonl as _read_jsonl


def load_events(path: Path) -> list[FeatureEvent]:
    """Every row, in file order. A malformed row raises with its line number;
    so does a repeated id — this collection is history, never a merge target."""
    events = _read_jsonl(path, FeatureEvent)
    seen: set[str] = set()
    for number, event in enumerate(events, start=1):
        if event.id in seen:
            raise ValueError(f"{path}:{number}: duplicate id {event.id} (rows are append-only)")
        seen.add(event.id)
    return events


def next_id(events: list[FeatureEvent]) -> str:
    highest = max((int(e.id.split("-")[1]) for e in events), default=0)
    return f"F-{highest + 1:03d}"


def append_event(path: Path, event: FeatureEvent) -> FeatureEvent:
    """Append one validated row. Never rewrites existing lines."""
    existing = load_events(path)
    if any(e.id == event.id for e in existing):
        raise ValueError(f"{event.id} already exists in {path}")
    _append_jsonl(path, event)
    return event


def latest_by_feature(events: list[FeatureEvent]) -> dict[str, FeatureEvent]:
    """The most recent row per feature — descriptions drift, so read the latest."""
    latest: dict[str, FeatureEvent] = {}
    for event in events:
        latest[event.feature] = event
    return latest


def retired(events: list[FeatureEvent]) -> list[FeatureEvent]:
    return [e for e in latest_by_feature(events).values() if e.event is FeatureEventKind.RETIRED]


def live(events: list[FeatureEvent]) -> list[FeatureEvent]:
    return [
        e for e in latest_by_feature(events).values()
        if e.event in (FeatureEventKind.LIVE, FeatureEventKind.UPDATED)
    ]


def new_event(
    events: list[FeatureEvent],
    *,
    feature: str,
    title: str,
    event: FeatureEventKind,
    description: str,
    user_value: UserValue = UserValue.NORMAL,
    reason: str | None = None,
    unit: str | None = None,
    verdict_ref: str | None = None,
    supersedes: str | None = None,
    on: date | None = None,
) -> FeatureEvent:
    """Build a row with the next id. `reason` defaults to the auto-stamp for non-retirements."""
    return FeatureEvent(
        id=next_id(events),
        feature=feature,
        title=title,
        event=event,
        date=on or date.today(),
        unit=unit,
        verdict_ref=verdict_ref,
        reason=(reason or AUTO_REASON).strip(),
        user_value=user_value,
        description=description,
        supersedes=supersedes,
    )


def raise_weight(path: Path, feature: str, value: UserValue) -> FeatureEvent:
    """Re-weight a feature after shipping (S2 amendment). Raising to high asks once."""
    events = load_events(path)
    current = latest_by_feature(events).get(feature)
    if current is None:
        raise ValueError(f"unknown feature '{feature}'")
    row = new_event(
        events,
        feature=feature,
        title=current.title,
        event=FeatureEventKind.UPDATED,
        description=current.description,
        user_value=value,
        reason=AUTO_REASON,
        unit=current.unit,
    )
    return append_event(path, row)


def check_rows_on_pass(events: list[FeatureEvent], goal_tasks: list[dict]) -> list[str]:
    """L3: every closed goal task with user_value high must have a live/updated row."""
    shipped = (FeatureEventKind.LIVE, FeatureEventKind.UPDATED)
    covered = {e.unit for e in events if e.event in shipped}
    missing = []
    for task in goal_tasks:
        closed_high = task.get("status") == "done" and task.get("user_value") == "high"
        if closed_high and task["id"] not in covered:
            missing.append(task["id"])
    return missing


def load_goal_tasks(goal_path: Path) -> list[dict]:
    if not goal_path.exists():
        return []
    return json.loads(goal_path.read_text(encoding="utf-8")).get("tasks", [])
