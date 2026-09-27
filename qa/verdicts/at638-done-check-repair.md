# Verdict — at638-done-check-repair

**Date:** 2026-09-27
**Cycle checked:** 1
**Manifest:** `qa/manifests/at638-done-check-repair.md` (commits `194db834` fix, `dd106737` manifest)
**Contract:** none dedicated — judged directly against `ISS-at638-remainder-2` (high) and `AT-647`
(medium).
**Environment:** worktree `D:/autoTesting/.worktrees/at638-done-check-repair`, branch
`wave/at638-done-check-repair`, HEAD `5b73ca89` (master already merged in). Bare `uv run pytest`
(no CLI `-q`, AT-503). Falsifications done in `git archive HEAD` throwaway copies under
`D:/autoTesting/.work/`, never the bound tree.

## VERDICT: PASS

**SCOREBOARD:** both claimed issues genuinely fixed; all four capability-coverage falsifications
independently reproduced; full suite re-run by me, not taken on the manifest's word.

## What I re-ran myself

| Command | My result | Manifest claim |
|---|---|---|
| `uv run pytest tests/test_goal_done_checks.py tests/test_goal_contract_registration.py tests/test_goal_done_check_shapes.py -v` | **10 passed** | 10 passed ✓ |
| `uv run pytest tests/test_browser_scroll_reach_at408_416.py -v` | **2 passed** | 2 passed ✓ |
| `uv run ruff check src tests scripts` | `All checks passed!` | ✓ |
| `uv run autotester doctor` | `1 violation(s)` — `stale-generated: docs/SNAPSHOT.md` | ✓ (same violation, same file) |
| `uv run pytest` (full suite, background, ~19 min) | **1 failed, 2070 passed, 6 skipped, 14 xfailed, 15 warnings in 1141.01s (0:19:01)** | 1 failed, 2070 passed, 6 skipped, 14 xfailed, 15 warnings in 1157.37s ✓ (same shape, my run 16s faster) |

**Note on my own near-miss:** I ran the full suite as `uv run pytest 2>&1 | tee <log>`, and the
background-task completion notice reported "exit code 0" — that is `tee`'s exit code, not
pytest's, exactly the masking this project's `qa/adapter.json` warns about and has been bitten by
at least three times before. I did not trust it: I read the failure list itself, which correctly
shows `1 failed`. Recorded so it isn't repeated by the next reader of this verdict.

**The one failure, independently confirmed as the pre-named flake:** `tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`,
`AssertionError: run_once killed pytest but left its real grandchild running`. This is AT-627
(open, low, filed 2026-09-27, unrelated feature area), whose own ledger text describes exactly this
failure mode (a grandchild process not scheduled in time under load to write its pid file before
`run_once`'s 10s timeout fires). Not caused by this unit's diff (which touches only
`.goal/goal.json`, `.goal/dashboard.html`, and two `tests/` files under `test_goal_*`). Zero
`test_goal_done_checks.py` / `test_goal_contract_registration.py` failures anywhere in the log.

## 1. The waiver mechanism — ruling

**The waiver key is NOT newly invented by this unit.** I checked this independently before
accepting the dispatch's framing: `git log --all -S'"waiver"' -- .goal/goal.json` shows exactly one
commit, `194db834` (this unit) — so T-190 is the **first real task on disk** to carry one. But the
*mechanism* — `waiver_of`, `_waiver_offenders`, the 20-character hollow-waiver floor, and the
composition test guarding against silently deleting the exemption — was built and
checker-**PASSed** on 2026-09-08 (`qa/verdicts/at154-at157-fail-closed.md`, cycle 1, C7/C9), months
before this unit. That verdict explicitly deliberated the tradeoff this dispatch asked me to
re-litigate ("a waiver is a sentence someone had to write and anyone can grep; a false negative is
nothing at all") and chose the fail-closed allowlist plus a written waiver over widening what
commands are accepted. This unit's contribution is exercising that pre-existing escape hatch for
the first time on real data, plus one docstring correction (`test_the_waiver_rule_actually_rejects_a_hollow_waiver`, which used to say truthfully "no task on disk carries a waiver" and now
correctly names T-190 as the first).

Confirmed independently: `grep -rn "waiver" src/autotester/` returns **nothing** —
`src/autotester/ledger/checks.py:285-287`'s `check_goal_pytest_q` reads only `done_check["type"]`
and `done_check["cmd"]`. There is also no Pydantic model for `done_check` anywhere in
`src/autotester/schema/` — `.goal/goal.json`'s `done_check` is an unvalidated raw dict, not a
schema-checked shape, so "is `waiver` schema-legal under `extra=\"forbid\"`" is moot: there is no
schema to violate. That absence of a `done_check` schema model is itself a small, pre-existing gap
against this repo's own "every domain shape is a Pydantic model" rule, but it long predates this
unit and is not something AT-638 introduced or was asked to fix.

**So: can any future task self-service-exempt itself with one sentence, no linked issue, no
expiry?** Yes — and that is a known, already-reviewed property of this mechanism, not a hole this
unit dug. The `test_a_waived_task_is_exempt_and_an_unwaived_one_is_not` composition test (unchanged
by this unit) proves a waiver exempts *only* its own task. There is genuinely no requirement for a
linked issue id or an expiry date — I looked for one and found none — but that is a pre-existing
design choice from AT-154/157, reviewed and PASSed once already, not new risk introduced by AT-638.
**Judged on the instance**, not the mechanism: T-190's waiver is well-founded — I independently
confirmed `schema/user_persona.py` does not exist anywhere in the repo, and
`qa/contracts/persona-ux-advisory.md`'s Plan-gate items 3 and 4 ("Where `UXReport`/`UXFinding`
files are stored" / "Where `UserPersona` is stored") are exactly the undecided items the manifest
names — guessing a node id here would be exactly the AT-647 failure mode recurring. **Ruling: the
mechanism is legitimate pre-reviewed infrastructure, correctly applied to a genuinely unbuilt task.
Not a finding against this unit.**

## 2. The deleted magic-number assertion — independently falsified, not weakened

I did not accept the manifest's own falsification table on trust. In a throwaway `git archive`
copy I ran two mutations of my own the manifest did not try:

- **Mutated a T-160..T-184 row** (changed T-165's `done_check.cmd` filename) → still **RED**,
  `AssertionError: assert {...} == {...}` — `actual == expected` catches it with zero help from the
  literal count.
- **Added a bogus 82nd task without touching `progress.total`** → still **RED**,
  `AssertionError: assert 81 == 82` on `progress["total"] == len(data["tasks"])` — the retained
  self-consistency invariant catches it.

Both directions the literal `== 70` used to (partially) cover are still caught by the two
assertions that remain. **Not a weakened test** — a redundant magic number was correctly identified
and removed; the AT-100/AT-115 "assertion that stopped measuring anything specific" concern this
project already has a lineage for.

## 3. T-185's repaired check — semantic match, not just existence

`tests/test_browser_scroll_reach_at408_416.py` (85 lines) is a real-browser test exercising
`visual_text`/`reachOf` against an `at416_card.html` fixture, asserting sentinels are reachable
**before any scroll** and that the **same set** is reported **after** scrolling — i.e. it tests the
AT-408/AT-416 scroll-invariance bug directly. T-185's own `note` field in `.goal/goal.json` reads
"AT-416/AT-408/AT-379; gate at416-clip-vs-reach-direction answer B (D-048)" — an exact match to
what the repointed file's docstring says it covers. This is not resolution-proves-existence
(AT-218's generalised limit); it is the correct test for this task's own stated bug numbers.

## 4. Recurrence guard scope (done-only) — verified accurate, gap correctly disclosed

Independently re-derived the guard's own logic against `.goal/goal.json` (not trusting the
manifest's count): **19** pending tasks reference a file that does not yet exist on disk, and
**zero** done tasks do — the exact IDs match the manifest's list exactly
(T-125, T-151..T-155, T-165, T-166..T-169, T-171, T-174, T-176..T-181). Zero false positives today,
confirmed. The maker's own manifest discloses, rather than hides, that the PENDING half of the
AT-647 class (a task whose check names a file that will *never* exist, filed before it goes done)
is not covered by a static `done_check` scan and needs a checker-side `pytest --collect-only`
gate — real scope, correctly deferred rather than built out-of-band. **I filed this as a new ledger
row, `AT-649` (low), in `qa/issues.jsonl`,** rather than leaving it inside a per-unit manifest where
it would likely be lost — not charged against this unit, which was not asked to build it.

## 5. The new file — precedent confirmed real

`tests/test_goal_contract_registration.py` (90 lines) houses only the one moved test plus its
imports; it duplicates no helper logic (`GOAL`, `REPO_ROOT` imported, not redefined).
`tests/test_goal_done_checks.py` was 300 lines before this unit (doctor's own cap) and ends at 277
after the split. The cited precedent is real: `tests/test_goal_done_check_shapes.py`'s own
docstring says verbatim "Split from test_goal_done_checks.py once that file passed doctor's
300-line cap" — `git log` confirms that file was split off in the `AT-161`/`AT-359` era, well
before this unit. This is a genuine split, not a second home for the same concept.

**One gap I found that the dispatch did not flag, and fixed:** the split left `C9`'s own `Verify`
line in `qa/contracts/core-invariants.md` stale — it named only
`tests/test_goal_criticality_vocabulary.py tests/test_goal_done_checks.py`, which no longer runs
`test_revised_goal_contract_is_registered` at all (confirmed: `uv run pytest` on exactly that
Verify command collects zero mentions of it). C9's own text had stopped matching what it verifies —
the self-referential kind of contract drift this project cares most about. **Amended** (this
verdict, checker-owned, no enforcement-path file touched, tightening only) to add
`tests/test_goal_contract_registration.py` to the Verify line, with a changelog entry.

## 6. `.goal/goal.json` edit scope and the `monitor.py` claim — both confirmed

`git show 194db834 -- .goal/goal.json` touches only the `progress` block and three tasks'
`done_check` fields (T-160, T-185, T-190) — **no task's `status` changed**. `progress.done` was
genuinely stale (56 vs. 57 actually-done tasks; `pending` 25 vs. 24 actual) before this unit's edit,
confirmed by counting `status == "done"` directly. The claim that `goal_store.recompute_progress`
and `render_dashboard.write_dashboard` were used (not `monitor.py`'s `run()`) is verified against
the actual functions: they live in the shared `/goal` skill at
`D:/ai_os/.claude/skills/goal/scripts/{goal_store,render_dashboard,monitor}.py` (outside this repo),
and `monitor.py:98` really does call `goal_store.register_product(data["product"],
data["project_path"], data["status"])` — confirming that calling `run()` from this worktree would
have pointed the shared, cross-project goal registry at the worktree's own path. Avoiding it was
the correct call. `dashboard.html` now shows `70%` / `57/81`, matching the corrected block.

## 7. Full suite — see table above. Confirmed genuinely green apart from the pre-authorized flake.

## 8. Capability-coverage table — all four rows independently reproduced

Using fresh `git archive HEAD` copies (never the bound tree), run via
`D:/autoTesting/.venv/Scripts/python.exe -m pytest` directly:

| Falsification | My result |
|---|---|
| Delete T-190's `done_check.waiver` | RED: `AssertionError: ... carry no waiver: ['T-190']` — matches manifest exactly |
| Mutate a T-160..T-184 `done_check.cmd` (my own choice: T-165, not the manifest's `== 70` revert) | RED: `actual == expected` catches it |
| Add a task without updating `progress.total` (my own choice, stronger than the manifest's row) | RED: `progress["total"] == len(data["tasks"])` catches it |
| Point a DONE task (T-186) at a nonexistent file | RED: `AssertionError: ...{'T-186': [...]}` — matches manifest exactly |

## Contract maintenance

- Amended `qa/contracts/core-invariants.md` C9's Verify line (stale after the AT-638 split) — see
  §5 above and the file's own changelog entry, dated 2026-09-27, checker-authored, tightening only.
- No other criterion needed amendment.

## Issue ledger

- `ISS-at638-remainder-2`: `open` → **`fixed`**, `fixed_date`/`verified_date` 2026-09-27,
  `regression_check` set, note appended (byte-preserving, not re-serialized).
- `AT-647`: `open` → **`fixed`**, same treatment.
- **New:** `AT-649` (low) filed — the disclosed, deferred PENDING-half gap from §4 above, so it is
  tracked canonically rather than only inside this unit's manifest.

## Not in the dispatch's list, found by me

1. C9's stale `Verify` line (§5) — repaired.
2. `qa/gates/at638-four-contract-files-authorization.md` is a **separate, still-OPEN** human gate
   blocking `ISS-at638-remainder-1` (contract authorization for T-166/T-167/T-168/T-171) — it is
   about a *different* issue from the same original `at638-remainder` filing and does **not** block
   or relate to this unit's two issues (`-2` and `AT-647`). Noted so it is not confused with this
   PASS.
3. `test_revised_goal_contract_is_registered` (moved, unchanged) is 69 lines — over this project's
   documented "function ≤ 50 lines" guideline. Not a finding against this unit: the function's body
   is unchanged from before the split (only its file and two comments changed), `autotester doctor`
   has no function-length check to violate, and shrinking a moved, otherwise-untouched function was
   not in scope.

## Commands run (this check)

```
uv run pytest tests/test_goal_done_checks.py tests/test_goal_contract_registration.py tests/test_goal_done_check_shapes.py -v
uv run pytest tests/test_browser_scroll_reach_at408_416.py -v
uv run ruff check src tests scripts
uv run autotester doctor
uv run pytest   # full suite, background, 1141.01s
# plus falsifications in git-archive throwaway copies under D:/autoTesting/.work/
```
