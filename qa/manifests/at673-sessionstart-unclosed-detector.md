# AT-673 — the session-start hook's handshake signals read phrases, not fields

**Gate:** `qa/gates/at673-sessionstart-unclosed-detector.md`, answered **option A** by Umesh
("theek kr, isme permission ka wait mat krr"). The gate's governing warning: *a partial fix here
is worse than no fix — anchoring only the visibly-wrong pattern makes the spurious `1` disappear,
which removes the one symptom that motivates fixing the silent half. Whichever option you pick, it
has to cover `:14`, `:16`, `:18` and `:21` together.* All four sites are covered below.

## Status: ready-for-check

**Fix cycle:** 1

## DISCLOSED DEBT — read before judging (a declaration, not an attempt to route around)

`qa/hooks/*` is an **enforcement path**. Per the Lab Protocol it needs an authorizing
`docs/DECISIONS.md` entry carrying `Approved-by: Umesh`, and **that entry does not exist.** The
append is classifier-blocked for both seats (the checker's attempt was refused as Instruction
Poisoning; I have not attempted it and will not route around it). The code below therefore lands
**ahead of its authorization**, knowingly and in writing rather than silently. Whether it stays
landed until the entry can be appended is Umesh's call, not mine and not the checker's.

## The defect, and why its evidence is a trap

Four reads at `:14/:16/:18/:21` matched a **phrase** anywhere in a file instead of reading the
**field**. Two opposite failures, one root:

- **Over-report.** `Status: ready-for-check` matched a manifest's *superseded cycle-1 history*.
  Manifests keep old cycles (LS6), so a first-match read returns a closed unit's earlier state as
  current. `t182-viewport-locale` was stuck as an unclosed PASS permanently.
- **Under-report.** The same first-match read hit a cycle-1 `checked-PASS` line and never reached
  the later `## Status (cycle 2): ready-for-check`, so a genuine dangling handshake was invisible.
  `at483-orphaned-running-crawl` was in exactly that state.

**The headline number does not move: `PASS not closed out: 1` before, `1` after.** The SET
inverts — one wrong entry out, one right entry in. A capability row claiming `1 -> 0` or "count
corrected" would pass against both implementations (AT-697 shape A), so no row below asserts a
count on the real tree. Every row is a synthetic `qa/` tree holding exactly ONE manifest, where
the count *is* the set.

## What changed

- `qa/hooks/mc-sessionstart.ps1:4-28` — new `Get-ManifestStatus`: reads the Status **field** over
  the six spellings measured on disk across 263 manifests (234 `## Status:`, 20 `**Status:**`,
  9 bare `Status:`, plus `## Status` as a bare heading with the value on a later line,
  `- **Status: x**`, and `## Status (cycle 2): x`). **LAST field wins.** An earlier attempt that
  anchored to `^## Status:` would have silently skipped ~37 manifests — worse than the bug.
  Result: **0 of 263 unreadable.**
- `qa/hooks/mc-sessionstart.ps1:30-50` — new `Get-CycleNumber`: same discipline for
  `Fix cycle` / `Cycle checked` / `Fix cycle judged`. A `^`-anchored read scored **45 of 280
  verdicts** as `-1` because they write the field mid-line after a separator
  (`**Date:** … · **Cycle checked:** 2 · **Commit:** …`), which silently reclassified those units
  as *awaiting a check*. The field may now begin at line start **or just after a separator**.
  Unreadable verdicts: **53 → 10**, and all 10 are correct rejections (6 have no field at all —
  sweeps and live checks, which have no cycle; `RECOVERY (post-STALL)` is non-numeric; two are
  prose about the field; one is a `.b` dual-check file with no manifest of its own). Of manifests
  currently at `ready-for-check`, **0** have an unreadable verdict cycle.
- `qa/hooks/mc-sessionstart.ps1:70-80` — the four sites now call the two readers.
- `tests/test_mc_sessionstart_unclosed.py` (new) — four behavioural cases against the real `.ps1`
  in synthetic trees, plus one portable static case. A new file because
  `tests/test_mc_sessionstart_loop_status.py` is at 273/300 and this is a different unit;
  `tests/test_session_start_hook.py` is the precedent for splitting hook tests by concern.
- `qa/manifests/at483-orphaned-running-crawl.md` — flipped to `checked-PASS` (cycle 2, verdict
  `Cycle checked: 2`, `VERDICT: PASS` at :151, all verified here rather than taken on report).
  This is the under-reported unit the fix exposed. With it closed the hook reaches a **true zero**,
  while the pre-fix hook still prints `1` — its false positive.

## Two of my own errors, caught by measuring rather than by reasoning

1. **An inline-code strip I added was dead code.** I justified it by `sweep-2026-09-24.md`, which
   quotes the field inside a code span while describing a *different* file, and wrote a row
   claiming the strip excluded it. The row **passed under sabotage**. The real excluder is the
   separator boundary: a backtick is neither line start nor a separator. Measured across all 543
   manifests and verdicts, the strip changed **0** answers. Removed, and the row rewritten to
   claim what is actually true, with the falsification switched to deleting the boundary — which
   is the original AT-673 defect itself.
2. **The first draft of that same row was vacuous** for a second, independent reason: with the
   fixture's manifest at `Fix cycle: 2`, a wrongly-swallowed `1` is below 2 either way, so both
   implementations returned `(1, 0)`. The fixture, not the code, decided the outcome. Set to 1,
   where a swallowed `1` satisfies `vc >= mc` and flips the unit to an unclosed PASS.

## Capability coverage — every row falsified, restored from a saved copy, never `git checkout`

| Capability | Test | Falsifying edit | Result |
|---|---|---|---|
| A closed unit that keeps superseded cycle history is NOT reported (over-report half) | `test_a_closed_unit_that_keeps_its_superseded_history_is_not_reported` | `Get-ManifestStatus`: `break` after the first field | `assert (0, 1) == (0, 0)` — FAILED |
| A cycle-2 PASS whose manifest was never flipped IS reported (under-report half) | `test_a_pass_verdict_whose_manifest_was_never_flipped_is_reported` | same `break` | FAILED — the unit vanishes from the set |
| A cycle number written mid-line after a separator is read (45 of 280 verdicts) | `test_a_cycle_number_written_mid_line_after_a_separator_is_read` | re-anchor `Get-CycleNumber` to `^` | FAILED — `(1, 0)` instead of `(0, 1)` |
| A cycle number quoted inside backticks is not read as this file's value | `test_a_cycle_number_quoted_inside_backticks_is_not_read_as_this_files_value` | delete the separator boundary — the original defect | `assert (0, 1) == (1, 0)` — FAILED |
| The loop reads through both field readers, no phrase fallback at any of the four sites | `test_the_hook_reads_status_and_cycle_through_the_two_field_readers` | restore the `Status: ready-for-check` phrase read at `:70` | FAILED |

Restored each time from `.work/at673-hook-good.ps1`. `git checkout -- <path>` is not used in this
repo's falsification loop: on AT-701 it destroyed an uncommitted production fix, after which three
artifacts agreed with each other and none with the tree.

## How to verify

```
uv run pytest                          # full suite, unpiped (AT-692); result appended below
uv run ruff check src tests scripts    # All checks passed!
uv run autotester doctor               # doctor: clean
uv run pytest tests/test_mc_sessionstart_unclosed.py -p no:cacheprovider   # 5 passed
```

Set-inversion evidence on the real tree, reproducible:

```
OLD set (1): t182-viewport-locale            <- false positive
NEW set (1): at483-orphaned-running-crawl    <- the one it was missing
baseline hook (.work/at673-hook-before.ps1): PASS not closed out: 1
fixed hook, after the at483 close-out:       PASS not closed out: 0
```

Prior whole-suite baseline on `9b142654`: 2167 passed, 6 skipped, 14 xfailed, exit 0 (peer, unpiped).
