# Manifest — at520-scripts-mapped-not-invisible (AT-520, with a gate for its relatives AT-488/AT-502)

**Unit:** AT-520 — `scripts/` is invisible to every routed doc. Filed by the at507 checker
(`qa/issues.jsonl` AT-520, cycle-1 check, 2026-09-18): after at507's `docs/ARCHITECTURE.md` trim,
`scripts/bench_trial.py` was confirmed to have zero hits across `docs/ARCHITECTURE.md`,
`docs/MAP.md`, `docs/SNAPSHOT.md`, `docs/FEATURES.jsonl` and `CLAUDE.md`. The filed issue itself
notes `docs/MAP.md`'s generated Directory map covers `src/autotester/` modules only "by design,
not a regression from this unit" — i.e. `scripts/` was never in scope for that generator, not
recently broken. Two sibling findings (AT-488 `mutation_check.py` unbounded growth, AT-502
`flake_probe.py` rewritten three times in 24h) independently point at the same root cause: no
governance layer — neither the doc generator nor the design-rule checks — has ever looked inside
`scripts/`.

**Contract:** `qa/contracts/living-ledger.md` L1 ("derived, never typed") and L6 (doc routing) —
`docs/MAP.md`'s generated sections are the mechanism both contracts already govern; this unit
extends their coverage rather than inventing a new mechanism.
**Goal task:** none named directly (checker-filed doc-coverage gap, same shape as prior
AT-50x housekeeping units).
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-520 (low, open → fixed here, doc-coverage half). AT-488 and AT-502 are
**not** closed by this unit — see the gate below; I measured their blast radius and am
recommending a scoped follow-up, not building it now. Not flipped by me — `qa/issues.jsonl` is
the checker's write surface (AT-499).

## Step 1 — find the exact seams before touching anything

- `src/autotester/doctor.py` — `check_file_sizes` (:69), `check_function_sizes` (:80),
  `check_file_names` (:94), `check_duplicate_definitions` (:113), `check_docs_routed` (:170),
  `check_generated_fresh` (:130). All of `_python_files`/`_capped_files` (:39, :48) walk only
  `root / "src"` (+ `root / "tests"` for the size cap) — `scripts/` was never in their input set,
  by construction, not oversight.
- `src/autotester/ledger/render.py:20` — `ARCHITECTURE_MAX_LINES = 150` (confirmed at exactly
  144/150 lines this morning per the brief; untouched by this unit).
- `src/autotester/ledger/render.py:62` (`render_map`) — the generator behind `docs/MAP.md`.
  Walked only `root / "src" / "autotester"` for the module table and its `schema/` subfolder for
  the schema table. `apply_map` (:79) is generic over whatever keys `render_map` returns — each
  key becomes one `<!-- generated:NAME -->...<!-- /generated:NAME -->` swap via
  `replace_generated` — so adding a third key needs no change to `apply_map`, `check_generated_fresh`
  (`doctor.py:130`), or the `autotester map` CLI command (`cli.py:67`), all three already generic.
- `docs/MAP.md` — had exactly two generated sections (`map`, `schema`). No `scripts/` mention
  anywhere, confirming the filed issue.

## Step 2 — measure the blast radius before proposing any rule (the brief's central instruction)

Full table, all 13 files in `scripts/` (`wc -l scripts/*.py scripts/*.ps1`):

| File | Lines | > 300 (C2 if extended)? |
|---|---:|---|
| `check_crawl_approval.py` | 61 | no |
| `check_deliverable.py` | 79 | no |
| `check_no_secrets.py` | 98 | no |
| `score_video_issues.py` | 125 | no |
| `onboard_pathlynks.py` | 142 | no |
| `append_decision.ps1` | 144 | no |
| `explore_proof.py` | 181 | no |
| `bench_trial.py` | 184 | no |
| `regression_proof.py` | 199 | no |
| `migrate_url_patterns.py` | 207 | no |
| `run_pathlynks_first_cases.py` | 214 | no |
| `flake_probe.py` | 244 | no |
| `mutation_check.py` | 416 | **yes — already known, AT-488** |

`check_function_sizes` (50-line cap) if extended to `scripts/` — 4 violations via
`ast.walk` over every `*.py`: `bench_trial.py::main` (72 lines, 108–180),
`mutation_check.py::_check_in` (66 lines, 308–374), `onboard_pathlynks.py::_write_knowledge`
(56 lines, 78–134), `run_pathlynks_first_cases.py::main` (67 lines, 143–210).

`check_duplicate_definitions` if extended to `scripts/` — **17 violations**, derived by walking
every top-level `ClassDef`/`FunctionDef` name across the 12 `.py` files and counting collisions:
`main` in 10 files → 9 violations; `build_cases` in 3 files → 2; `make_rubric` in 3 files → 2;
`start_server` in 3 files → 2; `run_and_grade` in 2 files → 1; `scan` in 2 files → 1. All 17 are
the ordinary "every standalone CLI script defines its own `main()`" idiom, not a duplicated
concept — the rule's actual target (the `d:/erp` failure mode of one concept reimplemented in two
modules) is not what any of these 17 are.

**This is exactly the shape the brief warned about (AT-504's false counts, AT-511's 167-line
no-op rule): extending `check_file_sizes`/`check_function_sizes`/`check_duplicate_definitions` to
`scripts/` unmodified would turn `doctor` red over ONE pre-existing file (`mutation_check.py`,
already a known AT-488 signal) and manufacture 17 false positives from a completely legitimate
idiom.** Full derivation script and raw output: `qa/evidence/at520-scripts-mapped-not-invisible/measurement.log`.

## Step 3 — what this unit actually is: (A) built + (B) gated, not conflated

**(A) Built — doc coverage, low risk, additive only:**
`src/autotester/ledger/render.py` — added `_script_one_liner` (new helper: a `.py`'s docstring
first line via the existing `_first_docstring_line`, or a `.ps1`'s first `# name -- doc` header
comment within its first 5 lines, else `"(no description)"`) and extended `render_map` to also
return a third key, `"scripts"`, built by iterating `root / "scripts"` non-recursively for
`*.py`/`*.ps1` (skipping `__pycache__`). `apply_map`, `check_generated_fresh`, and `autotester
map` needed zero changes — all three were already generic over `render_map`'s returned dict.

`docs/MAP.md` — added a `## Scripts` section with `<!-- generated:scripts -->` markers, updated
the file's own **Purpose:**/**Open me when:** header line to mention it and cite AT-520, then
regenerated via `uv run autotester map`. Every one of the 13 files in `scripts/` now has exactly
one row (verified: `grep -c '^| \`scripts/' docs/MAP.md` → 13), closing the filed issue's exact
complaint — `scripts/bench_trial.py` now appears at
`docs/MAP.md` row `| \`scripts/bench_trial.py\` | T-120: the north star made measurable —
first real human-vs-AI trial scorecard. |`.

**(B) Not built — gated:** `qa/gates/at520-scripts-line-cap.md` — the measured blast radius
above, four options (extend-with-fixes-first, extend-with-an-idiom-exemption, don't-extend-govern-
differently, grill-it), and what each blocks (AT-488, AT-502, and the rest of AT-520). Recommends
against extending the three numeric checks to `scripts/` as a mechanical scope-widen; does not
recommend a specific option among the four — that's a decision, not a build.

## Step 4 — test-driven, and mutation-proven not vacuous

`tests/test_ledger.py::make_docs` fixture updated to include `<!-- generated:scripts -->` markers
(matches the real `docs/MAP.md` template — the existing map-staleness test would otherwise break
on this unit's own change, since `apply_map` now requires the marker to exist for the "scripts"
key it produces).

Two new tests (written before the implementation existed, per TDD):
- `test_scripts_section_covers_py_and_ps1_and_doctor_sees_staleness` — a `.py` and a `.ps1` script
  each get their one-job row from `apply_map`; asserts staleness detection round-trips exactly
  like the existing `test_map_is_derived_from_docstrings_and_doctor_sees_staleness`.
- `test_a_ps1_script_with_no_header_comment_gets_a_placeholder` — a `.ps1` with no `# name -- doc`
  header still renders (as `"(no description)"`), never crashes.

```
$ uv run pytest tests/test_ledger.py -v
...
tests\test_ledger.py ........................                            [100%]
24 passed in 1.05s
```

**Mutation proof** (`qa/evidence/at520-scripts-mapped-not-invisible/mutations.json` +
`mutation_run.txt`) — two mutations against `src/autotester/ledger/render.py`, each naming which
new test must die:

```
KILLED  scripts section dropped from render_map's returned dict  (pytest exit 1)
    claims to kill : test_a_ps1_script_with_no_header_comment_gets_a_placeholder, test_scripts_section_covers_py_and_ps1_and_doctor_sees_staleness
    actually failed: test_a_ps1_script_with_no_header_comment_gets_a_placeholder, test_scripts_section_covers_py_and_ps1_and_doctor_sees_staleness
KILLED  ps1 header-comment line is never matched  (pytest exit 1)
    claims to kill : test_scripts_section_covers_py_and_ps1_and_doctor_sees_staleness
    actually failed: test_scripts_section_covers_py_and_ps1_and_doctor_sees_staleness

2/2 mutations killed
```

## How to verify (commands + expected)

```
uv run pytest tests/test_ledger.py         # expect: 24 passed
uv run python scripts/mutation_check.py qa/evidence/at520-scripts-mapped-not-invisible/mutations.json
                                            # expect: 2/2 mutations killed
uv run autotester doctor                   # expect: doctor: clean
uv run ruff check src tests scripts        # expect: All checks passed!
grep -c '^| `scripts/' docs/MAP.md         # expect: 13
uv run pytest                              # full suite — run once, this unit touches src/
```

## Actual outputs (from my own run)

```
$ uv run pytest tests/test_ledger.py
24 passed in 1.05s
$ uv run python scripts/mutation_check.py qa/evidence/at520-scripts-mapped-not-invisible/mutations.json
2/2 mutations killed
$ uv run autotester doctor
doctor: clean
$ uv run ruff check src tests scripts
All checks passed!
$ grep -c '^| `scripts/' docs/MAP.md
13
```

Full-suite run (`uv run pytest`, once, no `-q` doubling), whole-log scanned, not tailed — captured
in `qa/evidence/at520-scripts-mapped-not-invisible/full_suite.log`:

```
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
1 failed, 1485 passed, 2 skipped, 32 xfailed, 1 warning in 720.25s (0:12:00)
```

**The one failure is pre-existing and outside this unit's scope, not caused by this change.**
`test_revised_goal_contract_is_registered` compares `.goal/goal.json`'s live `done_check.cmd`
strings for T-160..T-169 against a hardcoded expectation in
`tests/test_goal_done_checks.py:231` — this is the exact AT-521/AT-522 `-q`-doubling seam,
already documented in `qa/manifests/at521-finish-the-q-sweep.md`. Verified unrelated to my diff:
`.goal/goal.json` shows `M` in `git status` (2 lines changed, matching the brief's note that a
second build subagent is concurrently working that exact file) and `tests/test_goal_done_checks.py`
shows **no** diff against `HEAD` — I did not touch either file, both are outside my declared file
set, and `.goal/goal.json` was already `M` in the git status snapshot at the start of this session,
before this unit began. My own targeted suite (`tests/test_ledger.py`, 24/24) and `doctor`/`ruff`
are the tests that actually exercise this unit's change, and both are green.

## Capability coverage (each claim → its isolating check)

| capability | check | falsifying condition | observed |
|---|---|---|---|
| Every file in `scripts/` gets exactly one row in a routed doc | `grep -c '^| \`scripts/' docs/MAP.md` vs. `ls scripts/*.py scripts/*.ps1 \| wc -l` | counts disagree, or `bench_trial.py` (AT-520's named example) missing | both 13; `bench_trial.py` row present with its real docstring |
| `docs/MAP.md` generation is genuinely derived, not hand-typed (L1) | `uv run autotester doctor` after `git stash` the `.py` change but keep `docs/MAP.md` (manual local check, not re-run here) / the existing `check_generated_fresh` machinery | staleness undetected | mechanism reused verbatim from the `map`/`schema` sections, which the existing `test_map_is_derived_from_docstrings_and_doctor_sees_staleness` already proves catches staleness; the two new tests prove the same for `scripts` |
| The new tests are not vacuous | `scripts/mutation_check.py` against 2 targeted mutations | a mutation survives | 2/2 killed |
| No numeric rule silently widened scope (the brief's hard "don't unilaterally widen" instruction) | `git diff src/autotester/doctor.py` | any diff in this file | **zero diff — `doctor.py` was read for seam-finding only, never edited** |
| `doctor`/`ruff` stay clean | `uv run autotester doctor`, `uv run ruff check src tests scripts` | either goes non-clean | both green |

## Live browser evidence

Not applicable — no UI/browser surface touched. Changed paths: `docs/MAP.md`,
`src/autotester/ledger/render.py`, `tests/test_ledger.py`,
`qa/manifests/at520-scripts-mapped-not-invisible.md`,
`qa/evidence/at520-scripts-mapped-not-invisible/*`, `qa/gates/at520-scripts-line-cap.md`.

## Known limits (disclosed, not claimed)

- **`src/autotester/doctor.py` is untouched by design** — the brief's own hard constraint plus
  Step 2's measurement both argue against unilaterally widening `check_file_sizes`,
  `check_function_sizes`, or `check_duplicate_definitions` to `scripts/`. That decision is
  written up in `qa/gates/at520-scripts-line-cap.md`, unanswered.
- **AT-488 (`mutation_check.py` growth) and AT-502 (`flake_probe.py` churn) are NOT closed by
  this unit.** This unit only closes AT-520's doc-visibility half. The gate names both as blocked
  on the same open question.
- **The gate's four options are not ranked to a single recommendation** — Option 3 (don't extend
  numeric caps, govern `scripts/` differently) is closest to what the measurement supports, but
  the brief asked me to let the measurement decide, not to also make the governance-design call
  Umesh should make.
- **`.ps1` docstring extraction is a narrow heuristic** (first `# ... -- ...` line in the first 5
  lines) — it works for the one `.ps1` file that exists today (`append_decision.ps1`) because
  that file already follows this header convention, and the new test proves the no-header
  fallback doesn't crash, but it is not a general PowerShell comment-based-help parser.

## Status: checked-PASS

Cycle 1, `qa/verdicts/at520-scripts-mapped-not-invisible.md` (commit `c3bde8d`), pushed per D-007.
PASS.

**The checker closed the one hole this manifest admitted to.** The manifest claimed
`check_generated_fresh` would police the new `scripts` section but said it had not re-run to prove
it. The checker did exactly that, in a scratch copy exported with `git archive` **outside the bound
tree**: it added an untracked script, then edited an existing script's docstring, and confirmed
`doctor` reddens in both cases and goes clean on restore. Without that, the new section could have
generated once and then rotted silently — which is precisely how the hand-maintained `## Status`
section in AT-507 came to be false.

It also verified the "zero changes needed elsewhere" claim was **true rather than lucky**: it read
`apply_map` (`ledger/render.py:100`), `check_generated_fresh` (`doctor.py:129`) and the `map` CLI
command (`cli.py:68`), confirmed none of them hardcodes `"map"`/`"schema"`, and grepped `src/` for
any other consumer of `render_map`/`apply_map` to be sure none was missed.

**A number of mine was wrong, and it was heading into a gate.** I told the checker that `scripts/`
had **7** distinct colliding definition names. It is **6**. I verified the correction myself rather
than accept it: `check_duplicate_definitions` skips any name beginning with `_`
(`doctor.py`, `not node.name.startswith("_")`), so `_NoCacheHandler` — which my recount included —
is invisible to the rule that would do the flagging. The manifest's own **17** (extra definitions,
not distinct names) was right all along. Both numbers describe the same corpus counted two ways, and
the gate must not carry the ambiguity into a human decision.

Two findings filed, neither blocking:

- **AT-525** (low) — the mutation proof is thin. 2/2 killed, but it does not isolate the new loop's
  non-recursive walk or its suffix filter. The checker judged this a finding rather than a failure,
  which is the right call for coverage depth on a passing unit.
- **AT-526** (medium) — the concurrency hazard from the previous unit, filed after independent
  confirmation rather than on my say-so.

**On the gate, the checker made a process critique I accept.** It ruled the unranked four-option
gate acceptable in principle — this is a genuine governance-design call for Umesh — but noted that
this manifest's own *Known limits* already leans toward Option 3 while the **gate document itself
withholds that lean**. That is the wrong way round: if the pair has a view, the human should see it
in the document he is asked to decide from, not buried in a manifest. I am not editing the gate to
add a recommendation unilaterally, because the checker ruled the unranked form acceptable and
changing it now would be me overriding a verdict I just accepted — but it is recorded here, and
`qa/gates/at520-scripts-line-cap.md` should carry the pair's lean when it is next touched.

`AT-488` and `AT-502` correctly remain **open**, still blocked on that gate. No scope creep.

