# Manifest — at496-the-ledger-never-loses-a-row

**Unit:** AT-496 — the shared `qa/issues.jsonl` silently loses committed rows and reverts committed
statuses when two maker loops commit it from stale copies. A guard in `doctor`, plus the repair of
the two losses that already happened.
**Contract:** `qa/contracts/core-invariants.md` (C10: a maker/checker commit names the qa/ files its
handshake writes — the ledger is one of them, and a write that drops another loop's row breaks it)
**Goal task:** none (issue-driven; filed by the at494 checker)
**Date:** 2026-09-18
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-496 (medium, open -> fixed). Related, not closed here: AT-475 (rows living
only in the working tree) — that is the *uncommitted* half; this is the *committed-then-dropped* half.

## The measurement first

`git log -S` over the last 40 commits that touched `qa/issues.jsonl`, comparing every committed
version against HEAD:

```
rows at HEAD: 488 | ids ever committed (last 40 ledger commits): 489
LOST ids: ['AT-494']
STATUS REGRESSIONS: 1
   AT-401: was fixed at 9b5cbc5, now open
```

Both losses share one mechanism, and both came from a checker doing the right thing the wrong way:
`9b5cbc5` (the at401 checker) appended AT-494 and flipped AT-401 to `fixed`; `1688da3` (the at494
checker, about thirty minutes later) built its commit from a **stale** blob of the ledger and wrote
it back, dropping the row and the flip. Nothing noticed, because the verdicts were correct and only
the ledger was wrong. The at494 checker saw the discrepancy and filed it rather than hand-editing the
contested file, which is why this is a unit and not a silent overwrite.

## What changed

- `src/autotester/doctor.py` — new `check_qa_issue_rows(root)` (registered in `run()` between
  `check_ledger` and `check_generated_fresh`), plus the private `_passed(root, name)`:
  - **`ledger-row-lost`** — an issue id named on a manifest's `**Issues addressed:**` line or a
    verdict's `ISSUES-WRITTEN` line that has no row in `qa/issues.jsonl` at all. The handshake files
    are the surviving record, so they are what makes a dropped row visible.
  - **`ledger-row-stale`** — an issue a PASSed unit's manifest claims to have fixed (the
    `AT-x (low, open -> fixed)` form) that is still `open` in the ledger. A `NOT fixed` note is
    excluded: a manifest may name issues it filed and deliberately left open
    (`at227-first-paint-modal` does exactly that with AT-335, and reading it as a fix claim made that
    unit's PASS look stale).
  - No git history is read — the check is tree-only, so it runs in a worktree or a sandbox copy.
- `qa/issues.jsonl` (commit `67a61ec`) — **the maker's repair, which cycle 1 FAILED on. Read this
  before the rest.** What it actually did, corrected:
  - AT-494's row: re-appended from `9b5cbc5` with `status` set to `fixed` and `fixed_date` added.
  - AT-401: rebuilt from **HEAD's** row with `status`/`fixed_date` set — NOT copied from `9b5cbc5`.
    HEAD's row had already lost `fixed_by`, so the rebuilt row lost it too:
    `"fixed_by": "cf34933 (checker PASS cycle 1, qa/verdicts/at401-flake-probe-runs-are-bounded.md)"`.
    The cycle-1 manifest called this "restored verbatim, not re-judged". **That claim was false**, and
    the field loss is the very failure class this unit exists to catch, reproduced inside its own fix.
  - Cycle 2 does **not** touch the ledger again. The verdict names the remedy as "/checker
    byte-restores AT-401 (including `fixed_by`)", and `qa/issues.jsonl` is the checker's write
    surface — the second half of AT-499 is that the maker wrote it at all. Doing it again, better,
    would repeat the finding. The row therefore still lacks `fixed_by` as this cycle goes to check;
    the byte-exact source is `git show 9b5cbc5:qa/issues.jsonl`.
- `tests/test_doctor.py` — six new tests plus a `_qa` helper and a `ROW` fixture: a manifest-named
  missing row, a verdict-named missing row, a PASSed-but-open row, a correctly-fixed row, a FAILed
  unit's open row, a `NOT fixed` mention, and a project with no `qa/` at all.

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_doctor.py` → `19 passed`
- `uv run autotester doctor` → `doctor: clean` (it printed `3 violation(s)` before the repair — the
  two losses, seen from three artifacts; that is the guard working)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at496-the-ledger-never-loses-a-row/mutations.json` → `5/5 mutations killed`, exit 0
- Re-measure the losses independently: `git show 9b5cbc5:qa/issues.jsonl` holds one `"id": "AT-494"`
  row; the same file at `1688da3` holds none.

## Actual outputs (from maker's own run)

```
$ uv run autotester doctor          # BEFORE the repair, with the new check in place
ledger-row-stale: qa/manifests/at401-flake-probe-runs-are-bounded.md - AT-401 is still `open` although this unit PASSed
ledger-row-lost:  qa/manifests/at494-probe-output-is-a-file-not-a-pipe.md - AT-494 is named here but has no row in qa/issues.jsonl
ledger-row-lost:  qa/verdicts/at401-flake-probe-runs-are-bounded.md - AT-494 is named here but has no row in qa/issues.jsonl
3 violation(s)

$ uv run autotester doctor          # AFTER
doctor: clean
$ uv run pytest -q -o addopts= tests/test_doctor.py
19 passed in 3.71s
$ uv run ruff check src tests scripts
All checks passed!          # cycle 2; cycle 1 pasted this while the tree had an E501 (AT-498)
```

**Cycle 2 — what changed since the FAIL** (`qa/verdicts/at496-the-ledger-never-loses-a-row.md`,
Cycle checked: 1):

> `[C7] manifest pastes ruff check -> All checks passed!, which does not reproduce (1 E501 error
> introduced by this unit's own new test at tests/test_doctor.py:208)`

`tests/test_doctor.py:207-209` — the docstring is rewrapped to three lines, all ≤ 100 chars. Re-run:
`All checks passed!`, `19 passed`, `doctor: clean`.

> `[C7 / ledger single-writer] the maker (not /checker) wrote qa/issues.jsonl in 67a61ec, and the
> AT-401 restoration silently dropped the fixed_by field present in the claimed source (9b5cbc5),
> contradicting the manifest's "restored verbatim, not re-judged" claim`

The claim is corrected in "What changed" above, with the dropped field quoted in full. The row itself
is deliberately left for the checker to byte-restore, because re-editing it would repeat the half of
the finding that is about the actor rather than the bytes.

## Capability coverage (each new claim -> its isolating falsification)

`qa/evidence/at496-the-ledger-never-loses-a-row/mutations.{json,out}`; every edit is one hunk in
`src/autotester/doctor.py`. Ids below are in `tests/test_doctor.py`.

| capability | check | falsifying edit | observed |
|---|---|---|---|
| a named issue with no row is reported | `test_an_issue_a_manifest_names...`, `test_an_issue_a_verdict_wrote...` | the `Violation("ledger-row-lost", ...)` rule string -> `"ledger-row-fine"` | `KILLED` |
| a PASSed unit's still-open issue is reported | `test_a_passed_unit_whose_issue_is_still_open...` | `Violation("ledger-row-stale", ...)` -> `"ledger-row-ok"` | `KILLED` |
| only a PASS triggers the stale check | `test_a_failed_or_unchecked_unit_leaves_its_issue_open` | `verdict.exists() and "VERDICT: PASS" in ...` -> `or` | `KILLED` |
| a `NOT fixed` note is not a fix claim | `test_an_issue_a_manifest_says_it_did_NOT_fix_stays_open` | drop `and "not fixed" not in note.lower()` | `KILLED` |
| a fixed row is not reported | `test_a_passed_unit_whose_issue_is_fixed_is_not_flagged` | drop `if status_of.get(issue) == "open"` | `KILLED` |

`5/5 mutations killed`.

**Two rows survived the first run, and both were real test gaps that were fixed in the tests:** the
verdict-side test asserted only on the message text, so renaming the rule string sailed through; and
nothing covered the `NOT fixed` exclusion at all — the very false positive the real repo surfaced
(`at227-first-paint-modal` / AT-335) while this check was being written.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/doctor.py`,
`tests/test_doctor.py`, `qa/issues.jsonl`.

## Known limits (disclosed, not claimed)

- **The guard detects, it does not prevent.** Two loops can still race; the next `doctor` run (or a
  checker's verify) now names the loss. A real fix is an append-only write path, or
  `qa/issues.jsonl merge=union` in `.gitattributes` — a design decision, not this unit's.
- **Only ids ON the marker line are read.** An issue discussed in prose but absent from
  `**Issues addressed:**` / `ISSUES-WRITTEN` is invisible to the check.
- **`ledger-row-stale` trusts the manifest's arrow**, so a manifest claiming a fix it did not make
  produces a violation against the ledger rather than against the manifest. The checker judges that
  claim; this only reports the disagreement.
- **The maker edited `qa/issues.jsonl`, which is the checker's write surface — cycle 1's second
  failure (AT-499, high).** The cycle-1 checker judged AT-494's `status: fixed` faithful (the 1688da3
  checker had already written that instruction twice) but the AT-401 rebuild unfaithful, and the
  actor wrong in both cases. Cycle 2 accepts both points: nothing in the ledger is touched here.
- **Known blind spot in the guard, filed not fixed: AT-500 (medium).** Both regexes end at a word
  boundary after the digits, so letter-suffixed ids (`AT-297b`, `AT-298b` — the live dual-checker
  convention) are invisible to the check. Enumerated debt, left for its own unit rather than widened
  here mid-fix-cycle.
- **AT-501 (low), also from cycle 1:** the `merge=union` prevention this manifest proposes would not
  have prevented *this* incident, which was a stale sequential write in one tree with no merge at
  all. Recorded so a later unit does not build the wrong mechanism.
- **`git log -S` over 40 commits** is the measured window; an older loss would not show.

## Status: ready-for-check
