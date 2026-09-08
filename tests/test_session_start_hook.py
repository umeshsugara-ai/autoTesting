"""The session-start hook's ARCHITECTURE excerpt (D-008 / D-010 / D-019).

This hook injects the project's ground truth into every session. It has now
silently regressed **twice** to a filter that matches nothing in this repo
(AT-015, then AT-097 when a "byte-identical to the template" sync reverted the
authorized fix without recording it), and each time every session ran with an
empty ground-truth block until a sweep happened to notice.

Nothing tested it. These tests read the REAL `.ps1` on disk — not a copy — so a
third revert fails here instead of going unnoticed for days. They are pure
Python (no PowerShell), so they run in the Linux container like everything else.

**AT-106/AT-107 (checker-found, and the reason this file grew a path test):** the
first version of these tests hardcoded the architecture path, so all six passed
green while the hook was injecting NOTHING — it looks for `ARCHITECTURE.md` at
the repo root, and this project keeps it in `docs/`, so the whole filter block
below has never once executed. That is the same "testing a fiction" flaw the
filter tests were written to avoid, one axis over. The path is now parsed out of
the `.ps1` too, and `test_the_hook_reads_the_file_the_project_actually_has`
xfails STRICTLY: it fails loudly the moment the path is corrected, so nobody can
fix the hook and leave a stale xfail behind.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
HOOK = REPO / ".claude" / "hooks" / "lab-session-start.ps1"
ARCHITECTURE = REPO / "docs" / "ARCHITECTURE.md"

# D-008: the generic Lab Protocol template keys its allowlist to NUMBERED
# headings. This repo's ARCHITECTURE.md has always used named ones.
_TEMPLATE_NUMBERED_FILTER = r"^## (1|2|3|6)"
_EXCLUDED_HEADING = "## Directory map and schema summary"
_AUTHORIZED_CAP = 150


def hook_source() -> str:
    return HOOK.read_text(encoding="utf-8")


def hook_code() -> str:
    """The hook with comment lines stripped. The docs/comments in this file
    deliberately QUOTE the bad filter to explain the regression; only its use
    as live code is the defect."""
    return chr(10).join(
        line for line in hook_source().splitlines() if not line.lstrip().startswith("#")
    )


_FILTER_RE = re.compile(r"\$inKeep = \(\$line -notmatch '\^## (.+?)'\)")
_CAP_RE = re.compile(r"\$keep\.Count -ge (\d+)")


def excluded_pattern() -> str:
    """The heading the hook drops, READ OUT OF THE HOOK rather than hardcoded.

    This is what makes the behavioural tests below real: if the filter is
    reverted to the template's numbered allowlist, this match fails and every
    test that depends on it fails with it — instead of quietly going on to
    simulate a filter the hook no longer contains."""
    match = _FILTER_RE.search(hook_code())
    assert match is not None, (
        "the hook's section filter is not the authorized 'keep everything except one "
        "generated section' form (D-008/D-019). Live code line was: "
        + next((ln.strip() for ln in hook_code().splitlines() if "$inKeep =" in ln), "<absent>")
    )
    return match.group(1)


_ARCHPATH_RE = re.compile(r'\$archPath = Join-Path \$root "([^"]+)"')


def architecture_path_from_hook() -> Path:
    """The architecture file the hook ACTUALLY opens, read out of the hook.

    Hardcoding this is what let AT-097's fix look green while the repaired
    filter was unreachable dead code."""
    match = _ARCHPATH_RE.search(hook_code())
    assert match is not None, "the hook no longer computes an $archPath at all"
    return REPO / match.group(1).replace("\\", "/")


def test_the_hook_reads_the_file_the_project_actually_has() -> None:
    """AT-106 (D-020): the hook looked for ARCHITECTURE.md at the repo ROOT for
    this repo's entire history, while the file has always been in docs/ — so the
    excerpt block never executed once and the empty ground-truth block predates
    every decision that argued about the filter's contents. This assertion was a
    strict xfail until the gate was answered; it is live now."""
    resolved = architecture_path_from_hook()
    assert resolved.exists(), f"the hook opens {resolved}, which does not exist"
    assert resolved == ARCHITECTURE, f"the hook opens {resolved}, not the project's {ARCHITECTURE}"


def hook_cap() -> int:
    caps = [int(m) for m in _CAP_RE.findall(hook_code())]
    assert caps, "no excerpt cap found in the hook at all"
    return min(caps)


def test_the_hook_exists_where_the_protocol_expects_it() -> None:
    assert HOOK.exists(), f"enforcement path missing: {HOOK}"


def test_the_numbered_heading_filter_is_not_back() -> None:
    """The exact regression AT-015 and AT-097 both were. It matches zero
    headings in this repo, so the injected block is empty and nobody is told."""
    assert _TEMPLATE_NUMBERED_FILTER not in hook_code(), (
        "the template's numbered-heading allowlist is back in lab-session-start.ps1 — "
        "it matches no heading in this repo, so every session start injects an empty "
        "ARCHITECTURE block (AT-015, AT-097). See D-008/D-010/D-019."
    )


def test_the_excerpt_cap_is_the_authorized_one() -> None:
    """D-010 raised the cap to 150 because the broadened filter needs more than
    100 lines to reach Design rules, Commands and Status (AT-029)."""
    caps = [int(m) for m in re.findall(r"\$keep\.Count -ge (\d+)", hook_code())]
    assert caps, "no excerpt cap found in the hook at all"
    assert all(cap >= _AUTHORIZED_CAP for cap in caps), (
        f"excerpt cap reverted to {caps} — D-010 authorizes {_AUTHORIZED_CAP}; below it the "
        "excerpt truncates before Design rules / Commands / Status (AT-029)."
    )


def apply_filter(lines: list[str], cap: int | None = None) -> list[str]:
    """The hook's filter, in Python — but driven by the pattern and cap parsed
    out of the real `.ps1`, so it can never drift into testing a fiction."""
    excluded = re.compile("## " + excluded_pattern())
    cap = hook_cap() if cap is None else cap
    keep: list[str] = []
    in_keep = False
    for line in lines:
        if line.startswith("## "):
            in_keep = excluded.match(line) is None
        elif line.startswith("# "):
            in_keep = False
        if in_keep or line.startswith("# "):
            keep.append(line)
        if len(keep) >= cap:
            break
    return keep


def test_every_named_section_survives_the_filter() -> None:
    lines = ARCHITECTURE.read_text(encoding="utf-8").splitlines()
    headings = [ln for ln in lines if ln.startswith("## ")]
    kept = apply_filter(lines)
    kept_headings = [ln for ln in kept if ln.startswith("## ")]

    expected = [h for h in headings if not h.startswith(_EXCLUDED_HEADING)]
    assert kept_headings == expected, (
        "the injected ground truth is missing sections: "
        f"expected {expected}, kept {kept_headings}"
    )


def test_the_generated_directory_map_is_the_only_thing_dropped() -> None:
    """It is regenerated into docs/MAP.md; carrying it in every session start
    would spend the cap on content that is mechanically derivable."""
    lines = ARCHITECTURE.read_text(encoding="utf-8").splitlines()
    kept = apply_filter(lines)
    assert not any(ln.startswith(_EXCLUDED_HEADING) for ln in kept)
    assert _EXCLUDED_HEADING.startswith("## " + excluded_pattern())


def test_the_excerpt_is_not_effectively_empty() -> None:
    """The failure both regressions actually produced: one line, the title.
    A filter can be present, well-formed and still match nothing."""
    lines = ARCHITECTURE.read_text(encoding="utf-8").splitlines()
    kept = apply_filter(lines)
    assert len(kept) > 100, (
        f"the ground-truth excerpt is {len(kept)} lines — that is the AT-015/AT-097 failure: "
        "a filter that runs, produces no error, and injects nothing."
    )
