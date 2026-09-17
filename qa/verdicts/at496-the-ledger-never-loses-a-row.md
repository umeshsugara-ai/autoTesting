# Verdict — at496-the-ledger-never-loses-a-row

**Date:** 2026-09-18
**Cycle checked:** 1
**Checker:** fresh Mode A subagent, no builder context.
**Unit commits:** 385fec1 (guard + tests + evidence + manifest), 67a61ec (ledger repair, `qa/issues.jsonl`
only, two lines).

## What I re-ran myself

- `uv run autotester doctor` (bound tree, HEAD 67a61ec) -> `doctor: clean`. Matches manifest.
- `uv run pytest -q -o addopts= tests/test_doctor.py` -> `19 passed in 1.55s`. Matches manifest.
- `uv run ruff check src tests scripts` -> **`Found 1 error`**: `E501 Line too long (101 > 100)` at
  `tests/test_doctor.py:208`, inside this unit's own new test
  `test_an_issue_a_manifest_says_it_did_NOT_fix_stays_open` (docstring line added by 385fec1 —
  confirmed via `git show 385fec1 -- tests/test_doctor.py`). pyproject.toml:40 sets
  `line-length = 100`; the line measures 101 chars. **Does NOT match the manifest's pasted
  `All checks passed!`.** Filed AT-498.
- `uv run python scripts/mutation_check.py qa/evidence/at496-the-ledger-never-loses-a-row/mutations.json`
  (the project's own sandboxed, baseline-asserting, kill-attributing harness — re-run myself, not
  read) -> **`5/5 mutations killed`**, every kill's actual failure list matches its claimed
  `kills:` list exactly. Matches manifest's capability-coverage table; counts as my step-4b
  reproduction (isolation.sandbox = the project's declared `worktree-copy`/tempdir mechanism).

## Item 1 — the measurement

Independently re-derived from git, not read from the manifest:

- `git show 9b5cbc5:qa/issues.jsonl`: 483 rows, `AT-494` present with `status: open` (just filed,
  not yet fixed), `AT-401` present with `status: fixed`.
- `git show 1688da3:qa/issues.jsonl`: 488 rows, `AT-494` **absent**, `AT-401` reverted to `status: open`.
- `git show HEAD~2 (f8f304d)`: identical to 1688da3's state — 488 rows, same absence/reversion.
- A full window replay (`git log -S`-style, but a full pickaxe/diff walk in Python) over the last 40
  commits touching `qa/issues.jsonl` up to `f8f304d` (the manifest's own measurement point):
  **489 ids ever committed in the window, LOST = ['AT-494'] exactly, STATUS REGRESSIONS = 1
  (AT-401, fixed at 9b5cbc5 -> open at BASE) exactly.** Matches the manifest's numbers precisely.
- **Does the 40-commit window hide anything older?** Checked the AT-N id sequence at the pre-repair
  state for gaps: missing numbers are 54, 234-238, 342-344, 494. Ran `git log -S"\"id\": \"AT-NNN\""`
  across FULL history (not windowed) for every one of those besides 494 — **zero commits ever
  contained any of them.** They are unused/skipped numbers, never committed and then dropped, which
  is a different (benign) phenomenon from AT-494's committed-then-vanished shape. No evidence the
  window hides an older loss.

**Item 1: confirmed accurate, independently re-derived.**

## Item 2 — the maker edited the ledger (be hard on this one)

Field-by-field diff of the two restored rows against their claimed source (9b5cbc5):

- **AT-494**: content identical to 9b5cbc5 except `status: open -> fixed` and `fixed_date: null -> "2026-09-17"`.
  This is NOT the maker inventing a judgement it had no authority to make — it is a **verbatim
  execution of an instruction the 1688da3 checker itself already wrote**, twice: in its own verdict
  (`qa/verdicts/at494-probe-output-is-a-file-not-a-pipe.md` line 128, "restore AT-494's row as
  `fixed`, citing this verdict") and in the AT-496 ledger row's own `expected` field (also
  checker-authored: "restore the AT-494 row ... and keep AT-401/AT-490/AT-491 at status:fixed").
  On the narrow question the manifest itself asks me to rule on ("restoring AT-494 as fixed rather
  than open") — **that specific judgement was already the checker's, not the maker's.** Correct.
- **AT-401**: I diffed this row field-by-field against 9b5cbc5 and it is **not** a faithful
  restoration. `9b5cbc5`'s row carries `"fixed_by": "cf34933 (checker PASS cycle 1,
  qa/verdicts/at401-flake-probe-runs-are-bounded.md)"`; the restored row at HEAD is **missing that
  field entirely**. The manifest's commit message and "Known limits" both assert "Both restored
  from 9b5cbc5, not re-judged" — that claim is **false for AT-401 as executed**. This is a silent
  field-level loss, on the very row this unit exists to repair, committed by the unit's own fix.
- **The write act itself.** Setting aside content correctness, `qa/issues.jsonl` is named in this
  project's own SKILL.md as the checker's exclusive write surface ("the checker is also the single
  writer of ... the `qa/issues.jsonl` ledger"). The 1688da3 checker explicitly chose NOT to
  hand-edit the contested line for exactly this reason ("Rather than hand-edit a contested shared
  line mid-write, I filed AT-496"). One cycle later, the maker did precisely the edit the checker
  had declined to make, with no `/checker` dispatch in between — even though the correct values for
  AT-494 were already on record. The content for AT-494 happened to be right; the actor and the
  fidelity of the AT-401 restoration were not.

**Item 2 verdict: FAIL.** The manifest's "restored verbatim ... not re-judged" claim is contradicted
by evidence (dropped `fixed_by` on AT-401), and the edit was performed by the wrong actor for a
ledger the project's own protocol reserves to `/checker`. Filed **AT-499** (high) naming the exact
diff and the correction (byte-restore AT-401 including `fixed_by`, and have `/checker`, not the
maker, perform ledger repairs the checker's own verdict already specified).

## Item 3 — the guard's false-positive/negative surface

- Ran `check_qa_issue_rows` against the real repo: `doctor: clean`, confirmed.
- Confirmed the manifest's own disclosed gap is real and fixed: `at227-first-paint-modal`'s "NOT
  fixed" mention of AT-335 does not trip `ledger-row-stale` (tested directly and via the mutation
  for that clause: `KILLED`).
- **Found a second, undisclosed gap.** Both of the guard's regexes (`named` extraction:
  `\bAT-\d+\b`; ledger `status_of` extraction: `"id":\s*"(AT-\d+)"...`) require the id to end at a
  digit with a word boundary immediately after. Real ledger ids with a letter suffix — `AT-297b`,
  `AT-298b`, `AT-299b`, an established convention for a second ("checker B") dual-check finding —
  have a digit immediately followed by a letter, so **neither regex can ever match them.**
  Reproduced live: `qa/manifests/at298-migration-host-guard.md` line 9 names `AT-298b (checker B,
  high)` on its own "Issues addressed" line; running the guard's exact `named` regex against that
  line yields `['AT-298']` only — `AT-298b` is invisible. `doctor: clean` today only because none of
  the three live `b`-suffixed rows currently needs catching; if one were lost or reverted the way
  AT-494 was, this guard would say nothing. Filed **AT-500** (medium).
- No false positives found: cross-checked the guard's `status_of` regex against every row in the
  live ledger via independent JSON parsing — 487/490 ids matched by regex (the 3 mismatches are
  exactly the `b`-suffixed ids above, a false negative, not a false positive).

## Item 4 — detect vs. prevent

The manifest honestly discloses "The guard detects, it does not prevent" and proposes
`qa/issues.jsonl merge=union` as a future remedy. I judge that proposed remedy, not just the gap:
**`merge=union` would not have prevented this specific loss.** The 9b5cbc5 -> 1688da3 loss was a
single shared working tree where a second commit was built from a stale in-process read and
overwrote the file — no git merge or rebase ever ran, so a `.gitattributes` merge driver (which
engages only during an actual merge of divergent commits) would never have fired. Also confirmed
`.gitattributes` still carries no `merge=union` entry today despite the C10 amendment log's
2026-09-16 note that the maker adds it "before the first wave." Per the no-fire list ("suggestions
for future work that no criterion requires") I am not failing the unit for lacking prevention — the
manifest never claims to build it — but I am filing **AT-501** (low) both for the missing mechanism
and to correct the mismatch between the proposed remedy and the actual failure mode, so a future
unit doesn't build `merge=union` believing it closes this gap.

## Diff scope (4c)

`git show 385fec1 --stat` / `-- src tests`: exactly `src/autotester/doctor.py`,
`tests/test_doctor.py`, the unit's own `qa/manifests/...md` and
`qa/evidence/at496-.../{mutations.json,mutations.out}` — pure additions, no function/test/export
removed, no other file touched. `git show 67a61ec -- qa/issues.jsonl`: exactly 2 lines changed
(AT-401 status flip, one new AT-494 line) as claimed, though the AT-401 line silently dropped a
field not visible in the one-line diff view (see item 2). No C10 violation: both commits carry only
paths this unit (or the shared ledger it repairs) legitimately touches.

## Capability coverage

5/5 rows reproduced via the project's own sandboxed mutation harness (`scripts/mutation_check.py`),
re-run independently, all kills correctly attributed to their named tests.

## Live browser

Not UI-touching. Changed paths: `src/autotester/doctor.py`, `tests/test_doctor.py`,
`qa/issues.jsonl`. Confirmed.

## Issues addressed

AT-496 (medium): the underlying incident (lost AT-494 row, reverted AT-401 status) is reconciled in
content, and a detection guard now exists — but the repair was executed by the wrong actor and is
itself imperfect (see item 2), so I am leaving **AT-496 open** rather than flagging it fixed; the
correction is now specified in AT-499.

```
VERDICT: FAIL
SCOREBOARD: 2/4 applicable criteria met, 0/0 invariants violated
FAILURES (if any):
- [C7] sev: medium · manifest pastes `ruff check` -> `All checks passed!`, which does not reproduce (1 E501 error introduced by this unit's own new test at tests/test_doctor.py:208) · fix: shorten the docstring line to <=100 chars · issue: ISS-AT-498
- [C7 / ledger single-writer] sev: high · the maker (not /checker) wrote qa/issues.jsonl in 67a61ec, and the AT-401 restoration silently dropped the `fixed_by` field present in the claimed source (9b5cbc5), contradicting the manifest's "restored verbatim, not re-judged" claim · fix: /checker byte-restores AT-401 (including fixed_by) and the manifest's claim is corrected · issue: ISS-AT-499
CAPABILITY-COVERAGE: 5/5 rows reproduced (project's own sandboxed mutation harness, re-run independently)
LIVE-BROWSER: not-applicable (src/autotester/doctor.py, tests/test_doctor.py, qa/issues.jsonl only — no UI paths changed)
ISSUES-WRITTEN: AT-498 (medium, ruff reproducibility), AT-499 (high, ledger single-writer + fidelity loss), AT-500 (medium, guard blind to letter-suffixed ids), AT-501 (low, detect-only + proposed remedy doesn't fit the mechanism)
EXPLANATION: The core measurement (item 1) is independently re-derived and exact: one lost row
(AT-494), one status regression (AT-401), no evidence the 40-commit window hides an older loss. The
new doctor guard is real, correctly registered, mutation-proven 5/5, and doctor is clean. But the
unit fails on its own terms: the manifest's pasted ruff output does not reproduce, and its claim
that the ledger repair "restored from 9b5cbc5, not re-judged" is false for AT-401 (a field was
silently dropped) — the exact failure class (silent ledger loss) this unit exists to prevent,
recurring in miniature inside the unit's own fix, compounded by the wrong actor (maker, not
/checker) performing the write. AT-494's status:fixed value is correctly sourced to the checker's
own prior instruction, so that half of item 2's question is resolved in the maker's favor; AT-401's
is not.
```
