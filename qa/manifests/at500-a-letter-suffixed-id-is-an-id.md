# Manifest — at500-a-letter-suffixed-id-is-an-id

**Unit:** AT-500 — `check_qa_issue_rows`, the ledger-loss guard shipped by AT-496 one commit
earlier, cannot see letter-suffixed issue ids (`AT-297b`, `AT-298b`, `AT-299b`), which is the live
convention for a second checker's duplicate row. A guard blind to a whole class of id reports
"clean" over exactly the losses it exists to catch.
**Contract:** `qa/contracts/core-invariants.md` (C10: a maker/checker commit names the qa/ files its
handshake writes — the ledger is one of them, and a row silently dropped breaks it)
**Goal task:** none (issue-driven; filed by the at496 cycle-1 checker as disclosed debt)
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-500 (medium, open -> fixed)

## The measurement first

The convention is real and in use — these are counts from the live tree, not a hypothetical:

```
$ grep -o '"id": "AT-[0-9]*[a-z]"' qa/issues.jsonl | sort -u
"id": "AT-297b"   (status: verified)
"id": "AT-298b"   (status: fixed)
"id": "AT-299b"   (status: open)

on manifest `**Issues addressed:**` lines:  AT-298b (at298-migration-host-guard.md)
                                           AT-297b (t135-coverage-merge-expand.md)
on verdict `ISSUES-WRITTEN` lines:          AT-297b, AT-298b, AT-299b
```

Both regexes ended at `\b` immediately after the digits. `\bAT-\d+\b` does not match a shorter
prefix of `AT-297b` — **it does not match at all**, because there is no word boundary between `7`
and `b`. So a suffixed id was not mis-read; it was invisible on both sides of the comparison at
once, which is why the blindness is silent rather than noisy.

**Falsified against the real repo, not a fixture** (`qa/evidence/.../probe_before.py`,
`probe_after.py`, both run over a temp copy of the live `qa/manifests`, `qa/verdicts` and
`qa/issues.jsonl` — nothing in the working tree was modified, no stash, no checkout):

```
PRE-FIX guard, AT-298b row deleted:  0 violation(s) naming it
  (0 violations in total — the loss is simply invisible)

POST-FIX guard, AT-298b row deleted: 2 violation(s)
  ledger-row-lost: qa/manifests/at298-migration-host-guard.md - AT-298b ... has no row
  ledger-row-lost: qa/verdicts/t135-coverage-merge-expand.b.md  - AT-298b ... has no row

POST-FIX guard, row INTACT:          0 violation(s)   <- no false positive
```

## What changed

- `src/autotester/doctor.py` — one new module constant and three call sites that now read it:
  - **`ISSUE_ID = r"AT-\d+[a-z]?"`** (:170), with the reason for the suffix in its docstring. One
    concept in one place: the id was previously spelled out three times in three regexes, which is
    precisely how two of them could have been widened and the third left behind.
  - `status_of` (:196) — the id read out of the **ledger**.
  - `named` (:202) — the ids read off a manifest/verdict **marker line**.
  - `claimed` (:212) — the ids a PASSed manifest claims to have **fixed**. Its trailing `\b` after
    the capture group was dropped, because `[a-z]?` is greedy and `\s*\(` already anchors the end.
  - No behaviour change for plain ids: every pre-existing test passes untouched.
- `tests/test_doctor.py` — two new tests, each parametrized over `AT-900` and `AT-900b` so the plain
  id is a control on the same assertion rather than a separate one that could drift:
  - `test_a_letter_suffixed_id_is_an_id_too` — a named id with no row is reported.
  - `test_a_letter_suffixed_id_is_read_on_both_sides_of_the_comparison` — widening only one side
    would turn every suffixed row into a **phantom loss**, so the test pins that a row that exists
    is reported `ledger-row-stale`, never `ledger-row-lost`.

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_doctor.py` → `23 passed`
- `uv run autotester doctor` → `doctor: clean` (the widening reports nothing new against the three
  live suffixed rows — that is the false-positive check, and it is the part most likely to be wrong)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at500-a-letter-suffixed-id-is-an-id/mutations.json`
  → `5/5 mutations killed`, exit 0
- Re-run the real-repo falsification yourself:
  `uv run python qa/evidence/at500-a-letter-suffixed-id-is-an-id/probe_before.py` then
  `probe_after.py`. `probe_before.py` needs `doctor_before.py` beside it — regenerate with
  `git show a0155f2:src/autotester/doctor.py > qa/evidence/at500-a-letter-suffixed-id-is-an-id/doctor_before.py`.
  Expected: `0` violations before, `2` after, `0` after with the row intact.

## Actual outputs (from maker's own run)

```
$ uv run pytest -q -o addopts= tests/test_doctor.py
23 passed in 0.86s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run python scripts/mutation_check.py qa/evidence/at500-.../mutations.json
5/5 mutations killed            # exit 0, first run, no test strengthened after the fact
$ uv run pytest -q               # the adapter's verify command, whole suite
EXIT=0                           # see the note below: this command prints NO summary line
```

**Read this before checking the suite output.** `qa/adapter.json`'s verify command is
`uv run pytest -q`, and `pyproject.toml:62` already sets `addopts = "-q"`. The two combine into
`-qq`, at which level pytest **suppresses the final `N passed in Xs` line entirely.** I wasted two
full runs grepping for "passed" and finding nothing before noticing. The suite's result is
carried only by the exit code and the progress dots (`[100%]`, no `F`/`E`). Use
`uv run pytest -q -o addopts=` when you want a readable count — that is why the per-file command
in "How to verify" above carries `-o addopts=`. The same `-q`-doubling is already documented in
`tests/test_flake_probe_runner.py` for `flake_probe`'s own subprocess, which is where I
eventually recognised it.

## Capability coverage (each new claim -> its isolating falsification)

`qa/evidence/at500-a-letter-suffixed-id-is-an-id/mutations.{json,out}`; every edit is one hunk in
`src/autotester/doctor.py`. Ids below are in `tests/test_doctor.py`.

| capability | check | falsifying edit | observed |
|---|---|---|---|
| a suffixed id is an id at all | `test_a_letter_suffixed_id_is_an_id_too[AT-900b]` | `ISSUE_ID` -> `r"AT-\d+"` | `KILLED` |
| a PLAIN id still is one | `..._is_an_id_too[AT-900]`, `..._manifest_names...`, `..._still_open...` | `[a-z]?` -> `[a-z]` (suffix mandatory) | `KILLED` |
| the LEDGER side reads the suffix | `..._read_on_both_sides...[AT-900b]` | `status_of` regex reverted to `(AT-\d+)` | `KILLED` |
| the HANDSHAKE side reads the suffix | `..._is_an_id_too[AT-900b]` | `named` regex reverted to `\bAT-\d+\b` | `KILLED` |
| the fix-CLAIM side reads the suffix | `..._read_on_both_sides...[AT-900b]` | `claimed` regex reverted to `\b(AT-\d+)\b` | `KILLED` |

`5/5 mutations killed`. The last three rows exist because the interesting failure here is not
"forgot to widen" but **"widened two of three"** — a half-widened guard reports a row that is
sitting in front of it as lost, which is worse than the blindness it replaced. Each of the three
call sites is reverted on its own so no single test can cover for another.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/doctor.py`,
`tests/test_doctor.py`, `qa/evidence/at500-a-letter-suffixed-id-is-an-id/*`.

## Known limits (disclosed, not claimed)

- **Only `[a-z]?` — one lowercase letter.** `AT-029s` and `AT-015s` appear in prose in `qa/` and are
  covered by that, but a two-letter or uppercase suffix would not be. I did not widen further
  because every id actually filed under the convention is single-lowercase, and a looser pattern
  starts matching prose.
- **The ids that are mentioned but have no row are still invisible where it matters least.**
  `AT-466a/b`, `AT-480a/b`, `AT-290a/b`, `AT-294b`, `AT-295b` appear in `qa/` prose with no ledger
  row. I checked before shipping: none of them sits on a `**Issues addressed:**` or `ISSUE-WRITTEN`
  marker line, which is why `doctor` stays clean. If one is ever moved onto a marker line it will be
  reported as lost, and that is the correct behaviour, not a false positive.
- **AT-501 is untouched and still open.** This unit makes the detector see more; it does not make
  the stale-write race impossible. That prevention decision is still open, and the at496 checker
  already recorded that the `merge=union` idea would not have prevented the incident that started
  this.
- **The adapter's own verify command is unreadable, and that is not this unit's to fix.**
  `uv run pytest -q` resolves to `-qq` and prints no pass/fail summary, so every manifest in this
  repo that pastes a count for it either used `-o addopts=` or is quoting something the command
  does not emit. Worth a row in `qa/issues.jsonl` — **filed by the checker, not by me**, because
  the ledger is the checker's write surface (AT-499's lesson, one unit ago).
- **The `probe_before.py` evidence depends on a regenerated `doctor_before.py`** (gitignored-size
  copy of HEAD's module, not committed). The regeneration command is in "How to verify"; the probe
  is reproducible, but not self-contained from the repo alone.

## Status: ready-for-check
