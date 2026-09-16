"""Is the maker-checker loop alive, and if it stopped, was that on purpose?

AT-368: `qa/.last-tick` jumped 2026-09-11 straight to 2026-09-16 — 4.85 days,
with 94 open ledger rows and no `qa/.paused`. Nobody noticed, because the only
instrument was a human grepping timestamps out of a prose log after the fact.
The session-start hook does print the last tick's age, but it prints it when a
session opens, and the whole shape of this outage was that no session opened.

So this module does not try to keep the loop alive — nothing in this repo runs
while the app is closed, and pretending otherwise would be the kind of guard
that cannot fail (AT-218). It makes the silence **legible afterwards**: the gaps
are enumerated, measured, and classified, so "the loop slept" becomes a number
this repo can state rather than a thing somebody happens to spot.

Deliberately NOT wired into `autotester doctor`. Doctor is in the adapter's
verify chain, so a stale loop would fail every unit's verification — a liveness
signal that breaks the build is worse than the silence it replaces.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from itertools import pairwise
from pathlib import Path

from autotester.core.paths import repo_root

# A tick line starts with its ISO stamp. The rest of the line is free prose and is
# not parsed: the log has carried both `<iso> · STATE · text` and `<iso> STATE text`
# over its life, and a reader that insists on one of them silently drops the other.
_STAMP = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2}))")

DEFAULT_GAP_HOURS = 6.0
"""Well above the loop's own cadence (60 s between units, a 2 h sweep) and well
below a working day, so an overnight pause in a one-human project is not noise."""


@dataclass(frozen=True)
class Gap:
    """One stretch where no tick was stamped."""

    start: datetime
    end: datetime
    explained: bool
    """True only for the OPEN gap when `qa/.paused` exists right now. A closed gap
    can never be explained by this tool — see `LoopStatus.retro_blind`."""

    @property
    def hours(self) -> float:
        return (self.end - self.start).total_seconds() / 3600.0

    def __str__(self) -> str:
        kind = "paused" if self.explained else "SLEEP"
        return (f"{kind} {self.hours:.1f}h  {self.start.isoformat()} -> "
                f"{self.end.isoformat()}")


@dataclass(frozen=True)
class LoopStatus:
    """What the tick log says about this project's loop."""

    ticks: int
    last_tick: datetime | None
    paused: str | None
    gaps: tuple[Gap, ...]
    threshold_hours: float
    open_end: datetime | None = None
    """The `now` the open gap was measured against, if there is an open gap."""

    @property
    def unexplained(self) -> tuple[Gap, ...]:
        return tuple(gap for gap in self.gaps if not gap.explained)

    @property
    def asleep_now(self) -> bool:
        """The loop is silent RIGHT NOW and nothing on disk explains it.

        Only the open gap counts. A historical gap says the loop once slept; this
        says it is sleeping, which is the thing worth an exit code."""
        if self.open_end is None:
            return False
        return any(gap.end == self.open_end and not gap.explained for gap in self.gaps)

    @property
    def retro_blind(self) -> bool:
        """A closed gap can never be proven deliberate, and this is not a bug here.

        `/maker pause` writes `qa/.paused` and `/maker resume` DELETES it, so a
        finished pause leaves no trace on disk at all. Every historical gap
        therefore reads as `SLEEP` whether it was a sleep or an approved stop.
        Fixing that means making resume append a durable line — a change to the
        maker skill, which lives outside this repo, so it is stated here rather
        than silently papered over."""
        return any(not gap.explained and gap.end != self.open_end for gap in self.gaps)


def read_ticks(path: Path) -> list[datetime]:
    """Every tick stamp in `qa/.last-tick`, oldest first, timezone-aware.

    Mixed offsets are normal in this log (`+00:00` and `+05:30` both appear), so
    everything is converted to UTC — comparing a naive to an aware datetime
    raises, and comparing two different offsets without converting silently
    mis-measures every gap that spans them."""
    if not path.exists():
        return []
    stamps = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _STAMP.match(line.strip())
        if match is None:
            continue
        text = match.group(1).replace("Z", "+00:00")
        try:
            stamps.append(datetime.fromisoformat(text).astimezone(UTC))
        except ValueError:
            continue
    return sorted(stamps)


def find_gaps(
    ticks: list[datetime], now: datetime, *, threshold_hours: float = DEFAULT_GAP_HOURS,
    paused: bool = False,
) -> tuple[tuple[Gap, ...], datetime | None]:
    """Stretches of at least `threshold_hours` with no tick, plus the open gap's end.

    The gap between the last tick and `now` counts. It is the one that matters
    most — a loop that died an hour ago is the loop that is dead — and it is the
    one a log-only reader cannot see at all."""
    if not ticks:
        return (), None
    span = timedelta(hours=threshold_hours)
    gaps = [
        Gap(start=earlier, end=later, explained=False)
        for earlier, later in pairwise(ticks)
        if later - earlier >= span
    ]
    open_end = None
    if now - ticks[-1] >= span:
        open_end = now
        gaps.append(Gap(start=ticks[-1], end=now, explained=paused))
    return tuple(gaps), open_end


def report_lines(report: LoopStatus) -> list[tuple[str, str]]:
    """`(text, level)` rows for a caller to print. Levels: ok · warn · bad · plain.

    The rendering lives here rather than in `cli.py` so the wording is testable
    without a terminal — the disclosure line below is the substance of what this
    unit promises, and a string only a CLI can produce is a string no test reads."""
    if report.last_tick is None:
        return [("loop-status: no ticks recorded", "warn")]

    rows = [(f"ticks: {report.ticks} · last: {report.last_tick.isoformat()}", "plain")]
    if report.paused is not None:
        rows.append((f"paused: {report.paused}", "warn"))
    rows.extend((f"  {gap}", "warn" if gap.explained else "bad") for gap in report.gaps)
    if report.retro_blind:
        rows.append((
            "note: a finished pause deletes qa/.paused, so a CLOSED gap can never be proven "
            "deliberate — historical gaps read as SLEEP either way (AT-368).", "warn"))
    if not report.gaps:
        rows.append(("loop-status: no gaps", "ok"))
    return rows


def status(root: Path | None = None, *, now: datetime | None = None,
           threshold_hours: float = DEFAULT_GAP_HOURS) -> LoopStatus:
    """Read this project's tick log and report on it. Never writes anything."""
    base = root or repo_root()
    paused_file = base / "qa" / ".paused"
    paused = paused_file.read_text(encoding="utf-8").strip() if paused_file.exists() else None

    ticks = read_ticks(base / "qa" / ".last-tick")
    gaps, open_end = find_gaps(
        ticks, now or datetime.now(UTC),
        threshold_hours=threshold_hours, paused=paused is not None,
    )
    return LoopStatus(
        ticks=len(ticks), last_tick=ticks[-1] if ticks else None, paused=paused,
        gaps=gaps, threshold_hours=threshold_hours, open_end=open_end,
    )
