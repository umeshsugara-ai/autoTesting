# AT-673 — the session-start hook's handshake signals read phrases, not fields

**Gate:** `qa/gates/at673-sessionstart-unclosed-detector.md`, answered **option A** by Umesh
("theek kr, isme permission ka wait mat krr"). The gate's governing warning: *a partial fix here
is worse than no fix — anchoring only the visibly-wrong pattern makes the spurious `1` disappear,
which removes the one symptom that motivates fixing the silent half. Whichever option you pick, it
has to cover `:14`, `:16`, `:18` and `:21` together.* All four sites are covered below.

## Status: ready-for-check

**Fix cycle:** 1

**Round cap:** (c) — CAP REACHED, ROUND 2 NOT OPENED. Escalated to HUMAN_GATE
`qa/gates/at673-round-cap.md`.

This seam (the session-start hook and the state it reads) already carries three PASSes:
`at097-session-start-hook-regression`, `at383-sessionstart-loop-status`, `t005-living-ledger`.
This unit is the fourth visit. The non-security cap is 2.

**It is NOT security class, and I am not claiming it is.** The hook prints a directive and reads
manifest/verdict/ledger state. It does not touch tenancy, auth, cross-tenant reads, data writes or
credential handling. It IS an enforcement path, which is adjacent to the class and not in it —
and stretching "enforcement path" into "security class" to escape a cap is precisely the
rationalisation the cap exists to stop. No waiver exists either: option (b) needs a DECISIONS
entry with `Approved-by`, and that append is classifier-blocked for both seats (see DISCLOSED DEBT
above).

**The evidence supports the cap rather than an exception to it.** Within this single unit the seam
produced four defects: two wrong fixes of my own (an anchored Status read that would have silently
skipped ~37 manifests; a `Fix cycle` pattern that broke on `**Fix cycle:** 2`), plus the checker's
AT-713 (last-wins is a manifest rule applied to verdicts, which order history the opposite way)
and AT-714 (the boundary admits a bare space, so prose counts). A seam that yields four defects
while being fixed once is the shape the cap is named for.

**What this changes, concretely:** AT-713/714/715 are correct and I am NOT fixing them in a cycle 2.
That would be round N+1 on a capped seam. They stay open, attributed, and go to Umesh as the
gate's question: accept this round and close, or withdraw it and take the finding as
file-don't-fix. Cycle 1 stands as built; the check in flight is still worth completing, because a
verdict on round 1 is information either way.

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

**Full suite (run unpiped per AT-692, on this unit's tree):**

```
2172 passed, 6 skipped, 14 xfailed, 15 warnings in 1544.86s (0:25:44)
PYTEST_EXIT=0
```

**Disclosure, because the first attempt was not evidence.** An earlier run of the same command was
**killed at 65%** and produced no summary line, so for one tick this manifest promised a result that
did not exist. The block above is the re-run, not the killed one. 2172 against the peer's 2167
baseline on `9b142654` is exactly the five new tests in `tests/test_mc_sessionstart_unclosed.py`.

Prior whole-suite baseline on `9b142654`: 2167 passed, 6 skipped, 14 xfailed, exit 0 (peer, unpiped).
