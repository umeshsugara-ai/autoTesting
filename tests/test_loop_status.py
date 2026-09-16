"""Loop liveness. AT-368: the maker loop was dead 4.85 days and nothing said so.

The instrument cannot keep the loop alive — nothing in this repo runs while the
app is closed — so what is tested here is that the silence becomes *legible*:
every gap enumerated, measured, and honestly classified, including the one thing
the tool genuinely cannot know.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from autotester.loop_status import (
    DEFAULT_GAP_HOURS,
    find_gaps,
    read_ticks,
    report_lines,
    status,
)


def _at(day: int, hour: int = 0, offset: str = "+00:00") -> str:
    return f"2026-09-{day:02d}T{hour:02d}:00:00{offset}"


def _tick_log(tmp_path: Path, lines: list[str]) -> Path:
    qa = tmp_path / "qa"
    qa.mkdir(parents=True, exist_ok=True)
    (qa / ".last-tick").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return tmp_path


# -- read_ticks: the log is prose with a stamp on the front --------------------

def test_both_tick_line_shapes_the_log_has_ever_used_are_read(tmp_path: Path) -> None:
    """The log carries `<iso> · STATE · text` from older ticks and `<iso> STATE text`
    from newer ones. A reader that insists on one shape silently drops half the
    history — and a gap computed from half a history is worse than no gap."""
    root = _tick_log(tmp_path, [
        f"{_at(11, 9)} · ADVANCED · closed at161, ledger flipped",
        f"{_at(11, 10)} ADVANCED at169 built and dispatched",
    ])

    assert len(read_ticks(root / "qa" / ".last-tick")) == 2


def test_a_gap_spanning_two_offsets_is_measured_by_real_elapsed_time(
    tmp_path: Path,
) -> None:
    """Both `+00:00` and `+05:30` appear in the real log, and a gap that spans the
    switch must be measured in real elapsed time: these two stamps look 6 hours
    apart on their faces and are 30 minutes apart in fact, so nothing is reported."""
    root = _tick_log(tmp_path, [
        f"{_at(11, 9, '+00:00')} ADVANCED first",
        f"{_at(11, 15, '+05:30')} ADVANCED second",
    ])
    ticks = read_ticks(root / "qa" / ".last-tick")

    assert (ticks[1] - ticks[0]) == timedelta(minutes=30)
    gaps, _ = find_gaps(ticks, ticks[-1], threshold_hours=DEFAULT_GAP_HOURS)
    assert gaps == ()


def test_every_reported_stamp_is_rendered_in_one_timezone(tmp_path: Path) -> None:
    """What `.astimezone(UTC)` is actually load-bearing for — and it is NOT the
    arithmetic above, which is correct either way because `fromisoformat` already
    returns aware datetimes and Python subtracts those correctly across offsets.
    I learned that by sabotage: dropping the normalisation left all 14 tests green,
    so the claim it was protecting the measurement was vacuous (AT-218's class).

    What it really protects is the READING: a report mixing `+00:00` and `+05:30`
    rows asks a human to do offset arithmetic in their head to see which outage
    was longer, which is how a 5-day gap gets skimmed past."""
    root = _tick_log(tmp_path, [
        f"{_at(11, 9, '+00:00')} ADVANCED first",
        f"{_at(16, 15, '+05:30')} ADVANCED much later",
    ])
    rendered = "\n".join(text for text, _ in report_lines(
        status(root, now=datetime(2026, 9, 16, 12, tzinfo=UTC))))

    assert "+05:30" not in rendered, "a second offset in the output is the defect"
    assert "+00:00" in rendered


def test_prose_lines_with_no_stamp_are_skipped_not_guessed_at(tmp_path: Path) -> None:
    """Tick notes wrap onto their own lines. A wrapped line is not a tick, and
    inventing a timestamp for one would invent a tick that never happened."""
    root = _tick_log(tmp_path, [
        f"{_at(11, 9)} ADVANCED something",
        "  ...continued prose about what the checker said, no stamp here",
        "",
        f"{_at(11, 10)} ADVANCED something else",
    ])

    assert len(read_ticks(root / "qa" / ".last-tick")) == 2


def test_a_missing_tick_log_is_empty_not_an_error(tmp_path: Path) -> None:
    assert read_ticks(tmp_path / "qa" / ".last-tick") == []


# -- the outage AT-368 was actually filed about --------------------------------

def test_the_real_outage_is_reported_with_its_real_duration(tmp_path: Path) -> None:
    """The exact shape of AT-368: 2026-09-11 straight to 2026-09-16, no pause file."""
    root = _tick_log(tmp_path, [
        f"{_at(11, 9)} ADVANCED at161 closed",
        f"{_at(16, 5)} ADVANCED woke up five days later",
    ])
    report = status(root, now=datetime(2026, 9, 16, 6, tzinfo=UTC))

    assert len(report.gaps) == 1
    gap = report.gaps[0]
    assert 115 < gap.hours < 117, "4.85 days"
    assert gap.explained is False
    assert str(gap).startswith("SLEEP")


def test_an_open_gap_is_counted_against_now_not_only_against_the_next_tick(
    tmp_path: Path,
) -> None:
    """The gap that matters most is the one with no closing tick — a loop that
    died an hour ago is the loop that is dead — and it is precisely the one a
    reader of the log alone cannot see, because nothing was written."""
    root = _tick_log(tmp_path, [f"{_at(16, 5)} ADVANCED last thing it ever did"])
    report = status(root, now=datetime(2026, 9, 16, 20, tzinfo=UTC))

    assert len(report.gaps) == 1
    assert report.gaps[0].hours == 15.0
    assert report.asleep_now is True


def test_a_healthy_loop_reports_nothing(tmp_path: Path) -> None:
    """The check must be able to come back clean, or it is an alarm that is
    always on and will be ignored like one."""
    root = _tick_log(tmp_path, [
        f"{_at(16, 5)} ADVANCED one",
        f"{_at(16, 6)} ADVANCED two",
    ])
    report = status(root, now=datetime(2026, 9, 16, 7, tzinfo=UTC))

    assert report.gaps == ()
    assert report.asleep_now is False
    assert report.ticks == 2


# -- paused is not asleep ------------------------------------------------------

def test_a_current_pause_explains_the_open_gap(tmp_path: Path) -> None:
    """AT-368's `expected` names this as the whole point: a deliberate stop must
    be distinguishable from a dead loop."""
    root = _tick_log(tmp_path, [f"{_at(11, 9)} PAUSED umesh said baad me dekhenge"])
    (root / "qa" / ".paused").write_text(
        "umesh 2026-09-11T09:30:00+00:00 — baad me dekhenge\n", encoding="utf-8")
    report = status(root, now=datetime(2026, 9, 16, 6, tzinfo=UTC))

    assert report.paused is not None
    assert len(report.gaps) == 1
    assert report.gaps[0].explained is True
    assert report.asleep_now is False, "a pause the user asked for is not an outage"
    assert str(report.gaps[0]).startswith("paused")


def test_a_closed_gap_is_never_credited_to_the_current_pause(tmp_path: Path) -> None:
    """The trap: `qa/.paused` describes NOW. Letting it explain a gap that closed
    days ago would let one pause retroactively excuse every past outage in the
    log -- a guard that cannot fail, which is the AT-218 class."""
    root = _tick_log(tmp_path, [
        f"{_at(11, 9)} ADVANCED before the outage",
        f"{_at(16, 5)} ADVANCED after the outage",
    ])
    (root / "qa" / ".paused").write_text("umesh 2026-09-16 — pausing now\n", encoding="utf-8")
    report = status(root, now=datetime(2026, 9, 16, 6, tzinfo=UTC))

    closed = [gap for gap in report.gaps if gap.end != report.open_end]
    assert len(closed) == 1
    assert closed[0].explained is False, "the old outage is still an outage"


def test_the_tool_says_out_loud_what_it_cannot_know(tmp_path: Path) -> None:
    """`/maker resume` DELETES `qa/.paused`, so a finished pause leaves no trace
    and a closed gap can never be proven deliberate. Disclosing that is the
    honest move; silently reporting every historical gap as a SLEEP without
    saying why would overstate what the evidence supports."""
    root = _tick_log(tmp_path, [
        f"{_at(11, 9)} ADVANCED before",
        f"{_at(16, 5)} ADVANCED after",
    ])
    report = status(root, now=datetime(2026, 9, 16, 6, tzinfo=UTC))

    assert report.retro_blind is True


def test_retro_blind_is_false_when_there_is_nothing_to_be_blind_about(
    tmp_path: Path,
) -> None:
    """The disclosure must not fire on a loop with no history to misread."""
    root = _tick_log(tmp_path, [f"{_at(16, 5)} ADVANCED only tick"])
    report = status(root, now=datetime(2026, 9, 16, 20, tzinfo=UTC))

    assert report.gaps != (), "there IS an open gap"
    assert report.retro_blind is False, "but no CLOSED one to be blind about"


# -- what a human is actually shown --------------------------------------------

def test_the_disclosure_is_printed_not_merely_available_on_the_object(
    tmp_path: Path,
) -> None:
    """`retro_blind` being True is worth nothing if the line never reaches a
    reader. This is the AT-366 lesson applied to this unit: a structured field
    nothing renders is the same silence one layer up."""
    root = _tick_log(tmp_path, [
        f"{_at(11, 9)} ADVANCED before",
        f"{_at(16, 5)} ADVANCED after",
    ])
    rendered = "\n".join(text for text, _ in report_lines(
        status(root, now=datetime(2026, 9, 16, 6, tzinfo=UTC))))

    assert "SLEEP 116." in rendered, "the outage, with its duration"
    assert "can never be proven deliberate" in rendered, "the limit, stated"


def test_a_clean_loop_says_so_rather_than_printing_nothing(tmp_path: Path) -> None:
    """Silence from a health check reads as 'not run', not as 'healthy'."""
    root = _tick_log(tmp_path, [f"{_at(16, 5)} ADVANCED one", f"{_at(16, 6)} ADVANCED two"])
    rendered = "\n".join(text for text, _ in report_lines(
        status(root, now=datetime(2026, 9, 16, 7, tzinfo=UTC))))

    assert "no gaps" in rendered


def test_an_empty_log_is_reported_as_unknown_not_as_healthy(tmp_path: Path) -> None:
    """A project with no ticks at all must not render as a clean loop — that is
    the reading that would let a never-started loop pass for a running one."""
    (tmp_path / "qa").mkdir()
    rendered = [text for text, _ in report_lines(
        status(tmp_path, now=datetime(2026, 9, 16, 7, tzinfo=UTC)))]

    assert rendered == ["loop-status: no ticks recorded"]
