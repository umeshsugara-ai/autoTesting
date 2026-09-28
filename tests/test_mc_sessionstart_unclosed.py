"""AT-673 (gate `at673-sessionstart-unclosed-detector`, option A): the session-start
hook's "PASS not closed out" and "Checks pending" signals must read the Status and
cycle FIELDS, not the phrases.

Why the obvious evidence is a trap: on the real tree at the time of the fix the
headline number did not move -- `PASS not closed out: 1` before, `1` after. What
inverted was the SET. The old phrase read flagged `t182-viewport-locale`, whose
manifest merely *keeps its superseded cycle-1 history*, and MISSED
`at483-orphaned-running-crawl`, a genuine cycle-2 PASS never flipped. One wrong
entry out, one right entry in, count unchanged. A test asserting a count on the
real tree would therefore have passed against both implementations.

So each case here is its own synthetic `qa/` tree holding exactly ONE manifest.
With one candidate, the count IS the set, and every assertion below is falsified
by reverting the corresponding read in `qa/hooks/mc-sessionstart.ps1`.

The four shapes are the ones measured on disk (263 manifests / 280 verdicts), not
invented: superseded history, a last-field `## Status (cycle 2):`, a cycle field
written mid-line after a separator (45 of 280 verdicts), and a cycle field quoted
inside backticks while describing a different file (`sweep-2026-09-24.md`).
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / "qa" / "hooks" / "mc-sessionstart.ps1"

_PWSH = shutil.which("powershell") or shutil.which("pwsh")
windows_only = pytest.mark.skipif(
    not (sys.platform == "win32" and _PWSH),
    reason="the hook is PowerShell; behavioural cases need a real shell",
)

_PASS_VERDICT = "VERDICT: PASS\n"


def _tree(root: Path, slug: str, manifest: str, verdict: str | None) -> None:
    (root / "qa" / "manifests").mkdir(parents=True, exist_ok=True)
    (root / "qa" / "verdicts").mkdir(parents=True, exist_ok=True)
    (root / "qa" / "manifests" / f"{slug}.md").write_text(manifest, encoding="utf-8")
    if verdict is not None:
        (root / "qa" / "verdicts" / f"{slug}.md").write_text(verdict, encoding="utf-8")


def _signals(root: Path) -> tuple[int, int]:
    """Run the real hook against `root` and return (checks_pending, unclosed)."""
    out = subprocess.run(
        [_PWSH, "-NoProfile", "-File", str(HOOK)],
        cwd=root, capture_output=True, text=True, timeout=120,
    ).stdout
    pending = re.search(r"Checks pending: (\d+)", out)
    unclosed = re.search(r"PASS not closed out: (\d+)", out)
    assert pending and unclosed, f"hook printed no signal line:\n{out}"
    return int(pending.group(1)), int(unclosed.group(1))


@windows_only
def test_a_closed_unit_that_keeps_its_superseded_history_is_not_reported(tmp_path):
    """The t182 shape: cycle 1 said ready-for-check, cycle 2 closed it. The LAST
    Status field is the current one. Falsify: make Get-ManifestStatus keep the
    FIRST field (or match the bare phrase) -- this unit reappears as unclosed."""
    _tree(
        tmp_path, "t182-shape",
        "## Status: ready-for-check\n\nFix cycle: 1\n\n"
        "## Status (cycle 2): checked-PASS (verdict ..., cycle 2)\n",
        "**Cycle checked:** 2\n\n" + _PASS_VERDICT,
    )
    assert _signals(tmp_path) == (0, 0)


@windows_only
def test_a_pass_verdict_whose_manifest_was_never_flipped_is_reported(tmp_path):
    """The at483 shape, and the half the old read MISSED: cycle 1 closed PASS,
    then cycle 2 reopened and its PASS was never closed out. A first-match read
    sees line 1's `checked-PASS` and stays silent. Falsify: keep the FIRST field."""
    _tree(
        tmp_path, "at483-shape",
        "## Status: checked-PASS (cycle 1, verdict ...)\n\n"
        "## Status (cycle 2): ready-for-check\n\nFix cycle: 2\n",
        "**Cycle checked:** 2\n\n" + _PASS_VERDICT,
    )
    assert _signals(tmp_path) == (0, 1)


@windows_only
def test_a_cycle_number_written_mid_line_after_a_separator_is_read(tmp_path):
    """45 of 280 verdicts write `... - **Cycle checked:** 2 - **Commit:** ...`.
    A `^`-anchored read scores them -1, which is BELOW the manifest's cycle, so
    the unit is misreported as still awaiting a check instead of as an unclosed
    PASS. Falsify: re-anchor Get-CycleNumber to `^` -- (1, 0) instead of (0, 1)."""
    _tree(
        tmp_path, "midline-shape",
        "## Status: ready-for-check\n\n**Date:** x - **Fix cycle:** 2 - **Head:** abc\n",
        "**Date:** 2026-09-26 - **Cycle checked:** 2 - **Commit:** abc\n\n" + _PASS_VERDICT,
    )
    assert _signals(tmp_path) == (0, 1)


@windows_only
def test_a_cycle_number_quoted_inside_backticks_is_not_read_as_this_files_value(tmp_path):
    r"""`sweep-2026-09-24.md` quotes `Cycle checked: 1` inside a code span while
    describing a DIFFERENT file. The read must not swallow that: the field has to
    BEGIN at line start or just after a separator, and a backtick is neither. With
    no real field the verdict scores -1, below the manifest's cycle, so the unit is
    PENDING and never an unclosed PASS.

    The manifest cycle is 1, not 2, ON PURPOSE. At 2 this case is vacuous -- a
    swallowed `1` sits below 2 either way, so both implementations return (1, 0)
    and the fixture, not the code, decides the outcome (AT-697 shape A; the first
    draft of this test had exactly that defect and passed under sabotage). At 1 a
    swallowed `1` satisfies `vc >= mc` and the unit flips to an unclosed PASS.

    Falsify: delete the `(?:^|[^\w\s`])` boundary from Get-CycleNumber, which is
    the original AT-673 defect -- (0, 1) instead of (1, 0)."""
    _tree(
        tmp_path, "backtick-shape",
        "## Status: ready-for-check\n\nFix cycle: 1\n",
        "The sweep grepped `Cycle checked: 1` in another verdict.\n\n" + _PASS_VERDICT,
    )
    assert _signals(tmp_path) == (1, 0)


@windows_only
def test_the_highest_cycle_wins_when_a_verdict_lists_its_newest_first(tmp_path):
    r"""AT-713 (cycle 2, authorized by D-056): verdicts order their history the
    OPPOSITE way to manifests -- newest on top. LS6's last-field-wins is a rule
    about MANIFESTS, which append new cycles BELOW; applied to a verdict it reads
    the OLDEST cycle as current. Measured over all 280 verdicts: 40 carry more
    than one cycle value, 39 ascend and exactly one descends
    (`at700-setup-vs-subject.md`, read as 1 when it is 2). Cycle numbers only ever
    increase, so MAX is correct under BOTH orderings.

    The manifest here is at `ready-for-check`, NOT `checked-PASS`, on purpose. The
    hook skips a closed manifest at `:95` (`if ($status -notmatch 'ready-for-check')
    { continue }`) before it ever reads a cycle, so a closed fixture scores (0, 0)
    under BOTH implementations and proves nothing -- the first draft of this test
    was exactly that and passed under sabotage (AT-697 shape A, the third instance
    in this one unit). At `ready-for-check` the cycle comparison is what decides.

    The verdict states cycle 2 on top with a preserved cycle-1 FAIL below. Under
    MAX the verdict scores 2, which is not below the manifest's 2, so the PASS is
    reached and the dangling handshake is reported. Under last-wins it scores 1,
    below 2, so the unit is misreported as merely awaiting its check and the
    unclosed PASS stays invisible -- the AT-483 failure the whole unit exists to
    catch.

    Falsify: restore the bare `$n = [int]...` assignment in place of the `-gt`
    guard -- (1, 0) instead of (0, 1)."""
    _tree(
        tmp_path, "newest-on-top",
        "## Status: ready-for-check\n\n**Fix cycle:** 2\n",
        "## Cycle checked: 2 -- commit `abc1234`\n\nVERDICT: PASS\n\n"
        "## Cycle checked: 1 -- commit `def5678` -- FAIL (preserved)\n",
    )
    assert _signals(tmp_path) == (0, 1)


@windows_only
def test_a_cycle_named_after_a_bare_word_is_prose_about_another_file(tmp_path):
    r"""AT-714 (cycle 2, same waiver): the old boundary admitted a BARE SPACE, so
    ordinary prose counted. Measured on disk, 24 hits sit after a plain word --
    `manifest Fix cycle: 1 of 3`, `manifest's Fix cycle: 1 of 3` -- each one
    describing ANOTHER file's value. Under last-wins that was often harmless
    because the numbers happened to agree; under MAX it is actively harmful, which
    is why AT-713 and AT-714 had to land in the same cycle rather than separately.

    The real file this reproduces is `sweep-2026-09-22b.md`, whose table cell
    `FAIL at Cycle checked: 3 of max 3` describes a DIFFERENT unit and was read as
    the sweep's own cycle 3.

    The manifest is at cycle 1 on purpose, by the same AT-697 shape-A reasoning as
    the backtick case: a swallowed 3 must be able to satisfy `vc >= mc` and flip
    the unit to an unclosed PASS, or the fixture decides the outcome instead of
    the code.

    Falsify: put `\s` back inside the boundary class. Observed `(0, 0)`, not the
    `(0, 1)` first predicted -- worse than expected and recorded as measured. The
    swallowed 3 clears `vc >= mc`, so the unit passes the pending test, but this
    fixture's verdict carries no `VERDICT: PASS` line, so it is not counted
    unclosed either. A unit awaiting its check vanishes from BOTH signals and is
    simply invisible, which is the failure direction C12 does not permit."""
    _tree(
        tmp_path, "prose-shape",
        "## Status: ready-for-check\n\nFix cycle: 1\n",
        "| AT-549 | medium | STALLED (manifest :230, FAIL at Cycle checked: 3 of max 3) |\n",
    )
    assert _signals(tmp_path) == (1, 0)


@windows_only
def test_a_quoted_heading_is_not_readable_through_the_heading_allowance(tmp_path):
    r"""The defect cycle 2 introduced in itself, kept as a regression.

    Cycle 1 measured an inline-code strip as changing 0 answers and removed it as
    dead code -- correct at the time, because under the OLD boundary a backtick
    immediately before the field already excluded a quoted value. It does not
    survive MAX. A quoted HEADING -- ``## Cycle checked: 2`` written inside a code
    span while describing a different file -- puts a `#` between the backtick and
    the field, and `#` is itself a legal separator, so the quote gets re-admitted
    through the heading allowance that AT-714 deliberately kept.

    This was found by running the hook against this unit's OWN verdict, whose
    `:96` carries exactly that shape: it reported an unclosed PASS that does not
    exist. Measured over all 546 manifests and verdicts the strip changes exactly
    one answer -- that file, 2 -> 1 -- so it is both narrow and necessary.

    Here the manifest is at cycle 2 with a cycle-1 PASS verdict that merely QUOTES
    a cycle-2 heading. The unit is awaiting its cycle-2 check and must be reported
    pending, never as a closed-out PASS.

    Falsify: delete the ``[regex]::Replace($line, '`[^`]*`', ' ')`` strip --
    (0, 1) instead of (1, 0)."""
    _tree(
        tmp_path, "quoted-heading",
        "## Status: ready-for-check\n\n**Fix cycle:** 2\n",
        "**Cycle checked:** 1\n\nThe old read misread `## Cycle checked: 2` here.\n\n"
        + _PASS_VERDICT,
    )
    assert _signals(tmp_path) == (1, 0)


def test_the_hook_reads_status_and_cycle_through_the_two_field_readers():
    """Static, portable half (no PowerShell needed): the loop must not fall back
    to a bare phrase/regex read at the four sites gate at673 named together."""
    src = HOOK.read_text(encoding="utf-8")
    body = src.split("$pending = @(); $unclosed = @()", 1)[1]
    assert "Get-ManifestStatus $m.FullName" in body
    assert "Get-CycleNumber $m.FullName 'Fix cycle'" in body
    assert "Get-CycleNumber $v 'Cycle checked|Fix cycle judged'" in body
    assert "'Status: ready-for-check'" not in body, "phrase read reintroduced"
