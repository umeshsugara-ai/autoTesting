# Verdict — at520-scripts-mapped-not-invisible

**Cycle checked:** 1
**Date:** 2026-09-18
**Checked by:** /checker (fresh subagent, bound to `d:/autoTesting`)
**Commit under check:** `9ca9f99` — `feat(map): generate a Scripts section so scripts/ stops being invisible (AT-520)`

## VERDICT: PASS

SCOREBOARD: 5/5 falsification claims hold; contract criteria L1 + L6
(`qa/contracts/living-ledger.md`) evidenced; 0 invariants violated; full suite clean (1486 passed,
2 skipped, 32 xfailed, exit 0, own run).

## What I independently re-derived (not trusted from the manifest)

1. **"Zero changes needed elsewhere" — confirmed true, not accidental.** Read `apply_map`
   (`ledger/render.py:100`), `check_generated_fresh` (`doctor.py:129`) and the `map` CLI command
   (`cli.py:68`): all three iterate `render_map(...)`'s returned dict generically (`for name, body
   in render_map(docs.root).items()`), with no reference to `"map"`/`"schema"` by name anywhere in
   `doctor.py` or `cli.py`. Grepped the whole `src/` tree for `render_map`/`apply_map`/`.map` usage
   — no other consumer hardcodes the old two-key shape. `git diff 9ca9f99~1 9ca9f99 --
   src/autotester/doctor.py` → 0 lines. The generic-over-keys design is real, not a lucky accident.

2. **`check_generated_fresh` genuinely polices the new `scripts` section — the sharpest claim,
   reproduced myself.** Exported the unit commit's tracked files via `git archive 9ca9f99` into a
   scratch dir outside the bound tree (never touched the bound working copy), then, using the
   in-tree `autotester` package pointed at that scratch root:
   - baseline: `check_generated_fresh(scratch_root)` → `[]` (clean)
   - added an untracked `scripts/zzz_new_probe.py` with a docstring, MAP.md left unregenerated →
     `[Violation('stale-generated', 'docs/MAP.md', ...)]` (reddened)
   - restored, then mutated an *existing* script's docstring in place
     (`scripts/check_no_secrets.py`) → reddened again
   - restored → clean again.
   This is exactly the AT-507 hand-maintained-section rot the unit claims to avoid, and it is
   proven, not merely reused-by-claim.

3. **Mutation proof reproduced exactly.** `uv run python scripts/mutation_check.py
   qa/evidence/at520-scripts-mapped-not-invisible/mutations.json` → `2/2 mutations killed`,
   identical to the manifest. Judgment on sufficiency: **two mutations is thin** — neither exercises
   the non-recursive `iterdir()` walk nor the `.py`/`.ps1` suffix filter (a mutation widening either
   to recurse or to admit other file types would survive undetected today). Not a reason to fail —
   the two mutations do isolate the two behaviours the unit actually claims (dict key present, `.ps1`
   header parsed) — but filed as **AT-525** (low) rather than waved through silently.

4. **AT-520's actual finding closed.** `docs/MAP.md` row: `` | `scripts/bench_trial.py` | T-120:
   the north star made measurable — first real human-vs-AI trial scorecard. | `` — matches the
   file's real docstring (confirmed via `head`). `grep -c '^| \`scripts/' docs/MAP.md` → 13,
   matching `scripts/*.py`+`*.ps1` count.

5. **`.ps1` heuristic degrades gracefully.** Read `_script_one_liner` — for a `.ps1` with no
   `# name -- doc` header in its first 5 lines it falls through to `"(no description)"`, never
   raises. Confirmed by the unit's own `test_a_ps1_script_with_no_header_comment_gets_a_placeholder`
   and independently by code reading. Disclosed as narrow (works today only because
   `append_decision.ps1` follows the convention) — accurate disclosure, not overclaiming.

## Diff scope (step 4c)

`git diff 9ca9f99~1 9ca9f99` is purely additive to `render.py` (`_script_one_liner` + a 3rd dict
key), plus the two new tests, the `docs/MAP.md` regeneration, the manifest, the gate, and evidence
files — exactly the "What changed" the manifest declares. No function/class/route/test deleted or
renamed; no file touched outside the declared set.

## On the gate (`qa/gates/at520-scripts-line-cap.md`)

Independently re-derived every number in the gate from `scripts/*.py`, not trusted from the table:

- `check_file_sizes` @ 300: **1 violation** — `mutation_check.py`, confirmed 416 lines. Matches.
- `check_function_sizes` @ 50: **4 violations**, same 4 files/functions the gate names
  (`bench_trial.py::main` 72, `mutation_check.py::_check_in` 66, `onboard_pathlynks.py::_write_knowledge`
  56, `run_pathlynks_first_cases.py::main` 67). Matches exactly.
- `check_duplicate_definitions`: ran the check's own extra-definition-counting logic (first
  occurrence "seen", every later occurrence a violation) over the 12 `.py` files myself:
  **17 violations**, matching the gate's total exactly. **Correction to the counting method stated
  in my own dispatch:** the number of *distinct colliding names* is **6** (`main`, `build_cases`,
  `make_rubric`, `start_server`, `run_and_grade`, `scan`), not 7 — `main` alone accounts for 9 of
  the 17 violations (10 files sharing the name). The manifest's "17" is the correct, defensible
  figure (extra-definition count, which is literally what `check_duplicate_definitions` would
  report); "distinct names" is a different, smaller number and should not be quoted as 7.

**On the gate being unranked:** the gate document itself presents 4 options with no single
recommendation. I find this a defensible call to escalate — the tradeoff is a real governance-design
decision (how to treat CLI-script idioms vs. library code), not a mechanical judgment call the pair
could safely make alone — **but** the manifest's own "Known limits" section already discloses a lean
("Option 3 ... is closest to what the measurement supports") that the gate file itself withholds.
Burying the lean in the manifest rather than stating it in the gate asks Umesh to re-derive an
opinion the pair had already formed. Not a blocker on this unit (the gate is explicitly the "not
built" half, correctly disclosed as unanswered), but worth surfacing plainly rather than silently
accepting the unranked framing as ideal.

## Verify commands (re-run myself, not pasted)

```
uv run pytest tests/test_ledger.py -v      -> 24 passed in 1.37s
uv run python scripts/mutation_check.py qa/evidence/at520-scripts-mapped-not-invisible/mutations.json
                                            -> 2/2 mutations killed
uv run autotester doctor                   -> doctor: clean
uv run ruff check src tests scripts        -> All checks passed!
grep -c '^| `scripts/' docs/MAP.md         -> 13
uv run pytest (full, bare, own run, PYTHONUTF8=1, redirected+whole-log-scanned, never tailed)
                                            -> 1486 passed, 2 skipped, 32 xfailed, 1 warning,
                                               877.58s, exit 0. grep for FAILED/ERROR/^E over the
                                               whole log: no hits.
```
The full-suite failure the manifest disclosed (`test_revised_goal_contract_is_registered`,
pre-existing, outside this unit's file set) is gone in my own run — resolved by the concurrent
AT-521 unit's fix (commit `0fe2b6d`/`db090e1`), which landed mid-run. Confirmed unrelated to this
unit's diff either way: this unit never touches `.goal/goal.json` or `tests/test_goal_done_checks.py`.

## Capability coverage

5/5 rows reproduced by me directly (not merely re-read from the manifest): grep count, the
generated-freshness mechanism (reproduced harder than the manifest itself claimed — see item 2
above, which the manifest explicitly flagged as "not re-run here"), the mutation kill count, the
zero-diff on `doctor.py`, and doctor/ruff green.

## Ledger + contract actions taken this check

- **AT-520** flipped `open -> fixed` (doc-coverage half; AT-488/AT-502 correctly stay open, blocked
  on the still-unanswered gate). **This flip landed via a concurrent commit before I could write
  this verdict — see "Concurrency note" below. I am confirming it as correct, not making it now.**
- **AT-525** (low) filed: mutation coverage for the new `scripts` section is thin (misses the
  non-recursive-walk and suffix-filter behaviours). Same concurrency history as AT-520 — already on
  disk via the same commit, confirmed correct on re-read.
- **AT-526** (medium, process) filed by me just now: the concurrency defect itself (below).
- `qa/contracts/living-ledger.md` L1 amended (routine, additive-only): "two generated sections" ->
  "three", crediting AT-520, with a dated amendment-log entry. No criterion weakened.

## Concurrency note (raised by the orchestrator, addressed)

While I was still mid-check, the concurrently-dispatched `at521-finish-the-q-sweep` checker ran
`git commit --only qa/issues.jsonl` for its own PASS. `--only <path>` restricts which *files* are
committed, not whose *changes* within that file are included — it commits the file's current
on-disk content wholesale. My own in-progress, uncommitted edits to that same shared file (the
AT-520 flip and the AT-525 append, made before this verdict file existed) rode along in that
commit (`0fe2b6d`). I re-read `qa/issues.jsonl` fresh from disk (not from memory) before touching
it again, confirmed both edits landed exactly as I had written them, and did not revert or redo
either — reverting a correct edit to "fix" an authorship mismatch would be strictly worse. Filed
**AT-526** for the process defect itself: two checkers must not hold concurrent uncommitted edits
to the same shared ledger file; remedy is either serializing `qa/issues.jsonl` writes across
concurrent checkers or having each checker diff its staged change against its own intended edit
before committing, rather than trusting path-scoped commit to imply authorship-scoped commit.

CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: docs/MAP.md, src/autotester/ledger/render.py,
tests/test_ledger.py, qa/manifests/at520-scripts-mapped-not-invisible.md,
qa/evidence/at520-scripts-mapped-not-invisible/*, qa/gates/at520-scripts-line-cap.md — no UI surface)
ISSUES-WRITTEN: AT-525, AT-526 (AT-520 flip confirmed, landed via concurrent commit 0fe2b6d)
EXPLANATION: The build half is real and additive: render_map/apply_map/check_generated_fresh/the
map CLI are genuinely generic over render_map's keys (verified by code + grep, zero-line doctor.py
diff), and check_generated_fresh was independently proven — in a throwaway git-archive scratch
copy, never the bound tree — to catch a stale scripts section from both a new file and an edited
docstring. The gated half (numeric caps over scripts/) is correctly not built; every number in the
gate re-derives exactly except a "7 distinct names" framing in my own dispatch, which should read
6. The gate's lack of a stated recommendation is a minor process critique (the manifest already has
a lean it declines to put in the gate itself) but not a defect blocking this unit. Two low/medium
ledger findings filed (thin mutation coverage; a live concurrent-write hazard on qa/issues.jsonl
that already fired once, harmlessly, during this very check).
