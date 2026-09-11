# Contract — core invariants (project-wide)

**Applies to:** every work unit in `d:/autoTesting`. A unit that violates any criterion here
fails its check regardless of what its own feature contract says.
**Owner:** /checker (maker reads only; feedback → `qa/feedback-inbox.md`).
**Source:** approved plan `C:/Users/Lenovo/.claude/plans/great-when-you-really-iridescent-ocean.md`
§3 Design principles, §7 Enforcement, §8 Security.

## Why these exist

The prior project (`d:/erp`) shipped without an upfront schema or system design. It reached 232
top-level entries, 977 source files, duplicated concepts across modules, and a 291-line landmine
document — at which point neither a human engineer nor an agent could hold it in context or take
control of it. Every criterion below is a cheap rule now that was unaffordable there.

## Criteria

### C1 — Schema-first, single source of truth
- Every domain data shape is a Pydantic model under `src/autotester/schema/`, one model family per file.
- No dict-shaped domain object, dataclass, or TypedDict duplicating a schema model exists elsewhere.
- Every artifact model inherits `schema.base.Artifact` (carries `schema_version`, `created_at`, `provenance`).
- Models use `extra="forbid"`, so an unknown key raises at load instead of being silently dropped.
- **Verify:** `uv run pytest tests/test_schema.py -q` exits 0.

### C2 — Readable by a human and an agent
- No file in `src/` or `tests/` exceeds 300 lines; no function exceeds 50 lines.
- Every module has a docstring stating its one job.
- `docs/ARCHITECTURE.md` stays ≤ 150 lines and its concept→file table matches reality.
- **Verify:** `uv run autotester doctor` exits 0.

### C3 — One concept, one place (anti-drift)
- No class or public top-level function name is defined in two modules.
- No file named `*_v2.py`, `*_new.py`, `*_old.py`, `*_copy.py`, `*_final.py`, `*_temp.py`.
- Changes edit existing files in place; a new module requires a stated reason in the manifest.
- **Verify:** `uv run autotester doctor` exits 0 (duplicate-concept + drift-filename rules).

### C4 — Repo root stays clean
- Top-level entries are limited to the declared layout (`src`, `tests`, `docs`, `projects`,
  `profiles`, `qa`, `.goal`, `.work`, config files).
- Scratch, logs, and in-progress evidence live in `.work/` (gitignored), never the repo root.
- **Verify:** `uv run autotester doctor` exits 0 (root-clutter rule).

### C5 — Secrets never reach a model, a log, or an artifact
- `SecretRef` carries a key and its domain scope. No schema model has a field holding a secret value.
- Secret values live only in the **repo-root `.env`** (one file for the whole repo, keys namespaced
  per project and declared in each project's `SecretRef[]`); a project can resolve only the keys it
  declares. Everything in that file is masked from logs, prompts, and artifacts, declared or not.
- Prompts and stored steps carry `{{SECRET:KEY}}` placeholders; substitution happens only at the
  moment of typing into the browser, scoped to that `SecretRef`'s `domains` (which lie within the
  project's `allowed_domains`).
- Every log line and stored artifact passes `core.redact.Redactor.scrub`.
- Any route that accepts a new raw credential value must treat it as secret immediately: before any
  same-request non-secret validator can echo or persist input, its prompt/artifact guard includes
  the union of pre-existing root secrets and all newly submitted values.
- `**/.env`, `profiles/`, `.work/`, and `projects/*/runs/` are gitignored.
- **Verify:** `uv run pytest tests/test_core.py -q` exits 0; `git ls-files | grep -E "\.env$"` returns nothing.

### C6 — Artifacts are human-editable files
- Every stage output is JSON, JSONL, or Markdown on disk under `projects/<slug>/`, valid against its model.
- A human can open, edit, or delete any artifact and the system still loads.
- The UI is a view over these files, never a second source of truth.
- **Verify:** artifact roundtrip tests pass; no database is the primary store.

### C7 — Verification is independent
- A unit is complete only when a check that someone else can re-run passes.
- The executor never grades itself: `RawResult` records observation, `Verdict` records judgement,
  and they are produced by different components.
- **A sabotage must assert that it was applied.** Where a manifest's evidence is "I broke X and N
  tests failed", the harness must establish, before believing any result, that its **anchor
  matched exactly once** and that the **file on disk actually changed**. A patch whose anchor did
  not match applies nothing and reports a green suite — which reads as *"the guard test is
  vacuous"*, the precise opposite of the truth. A sabotage needs its own assertion, not just its
  own patch.
- **A zero-failure sabotage is evidence about the SABOTAGE, not about the tests.** "Anchor matched
  once" + "file changed" are necessary but not sufficient: an anchor can match once inside a
  comment, a docstring, or a line no test exercises, so the patch applies, the file changes, and
  nothing semantically moves. When a sabotage yields 0 failures the harness must report it as
  **INCONCLUSIVE — mutation not shown to change behaviour**, and either strengthen the mutation
  (revert the actual fix hunk, not a nearby string) or state the null result as unproven. It must
  never be reported as "the guard test is vacuous" on that evidence alone.
- **A harness must assert its own BASELINE is green before believing any result.** "Killed" is
  read from a non-zero exit status, so an unrelated red suite — a flake, a broken import, a
  half-applied edit — makes **every** mutation look killed and certifies a vacuous test as sound.
  Printing the baseline is not asserting it. The harness asserts `exit == 0` on the unmutated copy
  first, or none of its results mean anything.
- **A harness must attribute its kill to the test that claims the property.** "Killed" read from a
  non-zero exit status cannot distinguish *"the test named for this fix failed"* from *"an unrelated
  test failed"* from *"the suite failed to collect at all"*. A mutation that breaks the module under
  test exits non-zero and reads KILLED while **no test ran** — measured: a syntax-error mutation
  reported `KILLED  1 error`, with an empty failure list. The harness must assert that the specific
  test(s) it names as defending the mutated behaviour appear in that run's failure list, not merely
  that the exit code moved. A `defends:` label nothing compares against is a comment, not an
  assertion — measured: a committed harness printed `defends: test_a_file_nested_below_the_project_
  is_still_judged_by_it` on four consecutive kills, and no test of that name exists.
- **A unit that ADDS or REWRITES a test must mutation-test it before the manifest is submitted.**
  For each such test, mutate the specific branch it claims to defend and require at least one
  failure, attributed as above. A zero-failure mutation is reported INCONCLUSIVE (clause 2 above),
  never as a pass and never as "the test is vacuous". The maker runs this; the checker still re-runs
  its own. This is a duty on the unit, not a step in `qa/adapter.json` slot-1 — slot-1 runs on every
  unit, most of which add no test, and a step that no-ops on most runs is a step people learn to
  skip.
- **An unreachability claim is INCONCLUSIVE, never a justification, and extraction never
  discharges the mutation duty.** "No mutation can reach this property" is an unfalsifiable
  negative; asserting it stops the search that would refute it, and it has been refuted on the
  first attempt both times it was made here (AT-315, AT-321). A unit MAY extract a property into a
  directly-assertable function — that is cheap and often clearer — but the extraction is an
  addition, not a substitute: the extracted decision must still be exercised end-to-end by at
  least one mutation of its CALLER, or the property is recorded as unproven. A direct unit
  assertion about a pure function is evidence about that function; only the mutation is evidence
  that the caller would notice.
- **An unreachability claim costs one mutation run, not one paragraph.** A manifest that claims no
  mutation can reach a property must paste the mutation it actually **tried** and the run showing
  zero failures, reported as INCONCLUSIVE per clause 2 above. Prose reasoning toward the same
  conclusion is not evidence and is not accepted: the claim has now been made three times in this
  repo (AT-315, AT-321, AT-354) and refuted by a checker on the first attempt every time, and the
  clause above — which already forbids it by name and cites the precedent — did not stop the third.
  A rule that is violated by *not being read* is repaired by making it cost something mechanical, not
  by writing it more firmly. The duty converts a belief into an artifact a checker can judge, and a
  claim submitted without one is treated as an unproven property, not as a justification.
- **Verify:** `uv run pytest -q` exits 0 and the manifest pastes real output, not a summary; a
  sabotage claim in a manifest is re-run by the checker in its own harness, never read; a unit
  adding or rewriting a test pastes its mutation run, with a green asserted baseline and a named
  failing test per mutation; a manifest containing an unreachability claim pastes the attempted
  mutation and its INCONCLUSIVE run alongside it.

### C8 — Provider-agnostic
- All model calls go through `providers.base.Provider`. No stage imports a vendor SDK directly.
- Prompts live in `src/autotester/prompts/*.md` as versioned files, never inline string literals.
- **Verify:** `grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/` returns nothing.

### C9 — A declared control value is honoured or rejected, never silently ignored
- A field that exists to change the system's behaviour (a criticality floor, a `done_check`, an
  approval flag, a gate) must either take effect or fail loudly. A reader that does not recognise
  a value must not substitute a default that is *weaker* than the value written.
- Where the reader is outside this repo and cannot be changed here, this repo pins its own data
  against the reader's actual vocabulary in a test, and files the upstream defect in the ledger.
- Applies to `.goal/goal.json` control fields (`base_criticality`, `done_check`, `approved`) as
  well as to `projects/<slug>/` artifacts.
- **Verify:** `uv run pytest tests/test_goal_criticality_vocabulary.py tests/test_goal_done_checks.py -q`
  exits 0 — one file per control field pinned so far (`base_criticality`, `done_check`). `approved`
  is not yet pinned (AT-156); when it is, its test joins this line.

## No-fire list (do not raise these as findings)

- Style/formatting preferences already satisfied by `ruff`.
- Missing features that are scheduled in a later phase of the plan and not claimed by this unit.
- Absence of tests for code the unit did not touch.
- Suggestions for future work that no criterion requires.
- The `src/` layout differing from the plan's prose `autotester/` — this was a deliberate,
  recorded choice (standard Python packaging); it is not a finding.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · routine · C5: credential file is the repo-root `.env`, keys namespaced + declared per
  project; undeclared values still masked; substitution scoped to the `SecretRef`'s `domains` ·
  why: user instruction 2026-09-03 folded from `qa/feedback-inbox.md` (mirrors browser-and-secrets
  B1 amendment); non-safety-weakening — the gitignore rule `**/.env` already covers the root file,
  and per-project declaration + domain scoping are unchanged.
- 2026-09-08 · routine · added C9: a declared control value is honoured or rejected, never silently
  ignored · why: third occurrence of one shape — AT-100 (a `done_check` of `true` that cannot fail),
  AT-115, and AT-116 (an uppercase criticality vocabulary the shared classifier silently downgraded
  to `low`, disarming every declared floor since the file was created). C1's `extra="forbid"` already
  makes an *unknown key* raise; nothing covered an unknown *value* being quietly replaced by a weaker
  default. Tightening only — it adds a criterion and weakens none, so it applies under the routine
  gate. Ruling on the at116-criticality-vocabulary manifest's open question: `.goal/goal.json` does
  NOT need its own feature contract — one file's vocabulary is too narrow a thing to govern
  separately, and the real invariant is project-wide, so it belongs here.
- 2026-09-08 · routine · added to **C7** the sabotage-assertion clause (an anchor must match
  exactly once and the file must actually change before a sabotage result is believed) · why:
  **five occurrences in two days across three independent agents.** (1) AT-140 cycle 1 — the
  maker's no-op sabotage read as "my test is vacuous" and it nearly rewrote a correct test;
  (2) the `at140` checker hit it from its own side (`max_actions=max_actions` matched twice in the
  file); (3) `at149-at150-path-containment` sabotage T — heredoc quoting mangled the anchor, patch
  applied nothing, suite green; (4) and (5) the checker of that same unit, twice, whose harness
  assertion caught it both times and printed "ANCHOR NOT PRESENT -- harness is lying". Without the
  assertion, (4) would have been reported as "sabotage T: 0 failures, the maker's test is vacuous"
  and a correct fix would have been FAILed. Ruling on the maker's request for a home: **not**
  `consent.md` — a feature contract judges the artifact, not how the maker held the tools, which
  is why AT-131 was correctly refused a home in `ingest.md`; **not** `qa/loop.md` — that file is
  the maker's own, and a rule the maker writes for itself is not a gate. C7 is already the
  criterion about how verification is done ("the executor never grades itself", "the manifest
  pastes real output"), and a sabotage that silently applied nothing is a manifest pasting real
  output from an experiment that never happened. Tightening only — it adds a clause and weakens
  none, so it applies under the routine gate. Verdict:
  `qa/verdicts/at149-at150-path-containment.md`.
- 2026-09-08 · routine · added to **C7** the zero-failure clause (a sabotage that produces no
  failures is INCONCLUSIVE about the tests until the mutation is shown to change behaviour) · why:
  measured during `at151-at152-both-arms` cycle 1, the FIRST unit judged against the clause added
  the day before. The checker's own sabotage U matched its anchor exactly once and changed the
  file on disk — satisfying the clause as written — and produced 0 failures, because the mutated
  string (`"already in the past"` → `"already in the past XXX"`) is on a line no assertion reads.
  Under the previous wording that is a clean "sabotage applied, suite green", which is exactly the
  "the guard test is vacuous" misreading the clause exists to prevent. Re-running with the real
  AT-151 hunk reverted produced the expected failure. The clause I wrote had a hole; this closes
  it. Tightening only — adds a reporting duty, weakens nothing, routine gate. Verdict:
  `qa/verdicts/at151-at152-both-arms.md`.
- 2026-09-08 · routine · C9's **Verify** clause now also names `tests/test_goal_done_checks.py` ·
  why: C9 governs three control fields and its Verify clause tested only the first — that gap was
  AT-141 itself, and leaving the clause naming one file after a second file was written would let
  the same drift recur silently. Ruling on the `at141-at115-done-check-can-fail` manifest's first
  question: **the static predicate is the right instrument, and the maker's reasoning is adopted
  verbatim.** A standing regression test must pin an invariant, and "this check fails today" is not
  one — it inverts the moment the work lands, so a dynamic version would go green exactly when the
  task completes and would thereafter assert nothing. What is invariant is that a `done_check` names
  something specific to its own task. The dynamic direction is not lost: sweep check 4's third
  loop-design question ("can it run a wrong answer to completion — is every `done_check` at least as
  strong as the contract criterion it closes") is where an executed check belongs, and it is the
  sweep's obligation, not `tests/`. Tightening only — it names one more file and weakens nothing, so
  it applies under the routine gate.
- 2026-09-09 · routine · **Edge cases recorded from the cycle-1 check of `at176-at178-render-not-scan`
  (PASS).** No criterion changed. (i) **C7's Verify clause names `uv run pytest -q`, and one member
  of that suite is non-deterministic.**
  `tests/test_explore_live.py::test_the_dialog_page_does_not_trap_the_crawl` asserts
  `status.value in ("aborted_dialog","explored")`; `NodeStatus`'s third terminal value,
  `ABORTED_ERROR`, is what a loaded host produces, and the maker observed exactly that once. The
  checker confirmed it is a flake and not a regression — `git show --stat e2f119f` touches `tests/`
  and `.goal/` only, so no explore code changed — over 7 consecutive clean runs (3 full suites,
  3 isolated runs of the file, and 1 isolated run executed concurrently with a second full suite).
  **The clause is not weakened and slot-1 is not re-scoped:** the failure direction is a false FAIL
  on a busy machine, never a false PASS, so no verdict already given rests on it. Recorded (AT-196)
  so the next maker or checker meeting an unrelated red suite reads this instead of learning to
  re-run until green. (ii) **The generalisation, stated narrowly**, because the maker's version
  ("every live test asserting one exact terminal `NodeStatus`") over-reaches — this test asserts
  membership in a *two*-element set, and the defect is not the arity: **a live test must assert the
  invariant it is named for, not enumerate the outcomes its author happened to observe.** Here "does
  not trap the crawl" is already fully carried by `crawl.finished_at is not None` on the preceding
  line; a node reaching *some* terminal status is the property, and which one is environment.
  (iii) **A sabotage's failure COUNT is a delta, not a suite total, and both are worth stating.**
  Sabotage AY yielded 4 full-suite failures where the manifest reported 3 — the manifest named the
  three newly-catching tests correctly and omitted the pre-existing instance test that already
  caught the same mutation at `3b765a4`. Accurate as a delta, and C7's "pastes real output" is met;
  noted so the next reader compares like with like. Verdict:
  `qa/verdicts/at176-at178-render-not-scan.md`.
- 2026-09-10 · /checker (t161-unified-project-intake cycle 1) · C5 tightened for credential-accepting
  routes: newly submitted values join pre-existing root secrets in the guard before any other field
  can be echoed or persisted. Why: D-025 intentionally adds the first same-request raw-value intake;
  without this timing rule, a pre-guard validator can disclose a value that later guards would have
  caught. B10 carries the feature-level transaction details. No existing C5 protection is weakened.
- 2026-09-11 · routine · **C7 gains the baseline clause: a mutation/sabotage harness must assert its
  own baseline is green before believing any result.** Why: found in the `at300-migration-config-hardening`
  cycle-1 check, in the maker's *own* harness — the one whose whole purpose was to end a four-test
  vacuity streak, and which is otherwise exemplary (it satisfies both existing C7 clauses, works on a
  copy outside the repo, and its four kills reproduced exactly). Its verdict is
  `"KILLED" if code != 0`, and the baseline is **printed but never asserted**. This repo has a
  documented flake (AT-196, `tests/test_explore_live.py`), so a red baseline is not hypothetical here;
  under one, every mutation reads KILLED and a vacuous test is certified sound. That is the same
  failure direction as the two clauses already in C7 — a harness reporting confidently about an
  experiment that did not happen — and it is the one direction that yields a **false PASS** rather
  than a false FAIL. It becomes load-bearing the moment `qa/feedback-inbox.md`'s standing proposal
  (promote mutation into `qa/adapter.json` slot-1) is folded. Tightening only — adds a duty, weakens
  nothing, so it applies under the routine gate. Ledger: **AT-307** (low). Verdict:
  `qa/verdicts/at300-migration-config-hardening.md`.
- 2026-09-11 · routine · **C7 gains two clauses: kill-attribution, and a mutation duty on any unit
  that adds or rewrites a test. This FOLDS the standing `qa/feedback-inbox.md` proposal of
  2026-09-11T04:00.** Why, in two parts. (i) *The fold.* The maker filed a pattern against itself —
  FOUR vacuous tests in one session (T-135 c1/c2/c3 and AT-303), every one found by a checker
  running mutation, none by the maker re-reading its own test — and proposed making mutation a
  required verify step. The evidence for it only got stronger: AT-300 was the first unit to
  mutation-test itself before submitting and it self-caught a *fifth* (M4 SURVIVED on the first
  attempt). A failure mode that recurs five times across three agents and is caught by one cheap
  instrument every single time is exactly what a contract criterion is for. I adopted the **duty**
  and declined the proposed **mechanism**: not `qa/adapter.json` slot-1, because that file is the
  maker's own — and a rule the maker writes for itself is not a gate, the same reasoning that
  refused `qa/loop.md` a home for the sabotage clause on 2026-09-08 — and because slot-1 runs on
  every unit while most add no test. C7 already holds the anchor, zero-failure and baseline clauses;
  this is the fourth member of one family and belongs with them. (ii) *Kill-attribution.* Found in
  the `at306-verification-artifact-integrity` cycle-1 check, in the harness that had just been fixed
  for AT-307. `KILLED` is still `exit != 0`, so I mutated the target into a syntax error: the module
  never imported, pytest exited 2, and the harness printed `KILLED  1 error` with an empty failure
  list — a mutation certified as killed by a suite that never collected. Corroborated by the
  harness's own `defends:` field naming a test that does not exist in the file, printed confidently
  on four consecutive kills. Same failure direction as every other C7 clause — a harness reporting
  about an experiment that did not happen — and the one that yields a **false PASS**. AT-307 closed
  "already red *before* the mutation"; this closes "red for the wrong reason *after* it", which
  becomes load-bearing the moment clause (i) makes the instrument mandatory. Tightening only — adds
  two duties, weakens none, so it applies under the routine gate. Ledger: **AT-311** (medium),
  **AT-312** (low, the harness needs a shared parameterised home now that it is contractual).
  Verdict: `qa/verdicts/at306-verification-artifact-integrity.md`.
- 2026-09-11 · routine · **C7 gains the unreachability clause, and the maker's proposed general rule
  is REFUSED in its general form.** Ruling on a question now in its third session. The maker
  proposed: *"when a property cannot be reached by mutation, extract it until it can be asserted
  directly."* Cycle 2's checker declined it; cycle 3 withdrew it; this entry settles it so it stops
  recurring. **The withdrawal is correct.** The rule is keyed on an unfalsifiable negative, and a
  rule keyed on an unprovable premise licenses the premise: believing "no mutation exists" is
  precisely what stops the search that refutes it. It was refuted on the FIRST attempt both times it
  was asserted in this repo — AT-315 (the `is_kill` clause allegedly unreachable) and AT-321 (the
  same claim restated, killed by one `KeyboardInterrupt` mutation that makes pytest exit 2 INTERRUPTED
  while printing real `FAILED` lines; the checker reproduced it independently at baf56a1: exit 2,
  `failed=['tests/test_mod.py::test_small_values_are_small']`, `no_test_results=False`). Its failure
  direction is also the wrong one: it converts "I could not think of a mutation" into a licence to
  restructure code, and the restructure then reads as proof. **The narrow form IS adopted**, because
  the useful half is real and leaving it unresolved for a fourth session is worse than ruling: an
  unreachability claim is INCONCLUSIVE (the same word C7's zero-failure clause already mandates for a
  zero-failure sabotage — this is that principle applied one level up, to a claim about mutations
  rather than a result of one), extraction is permitted as an ADDITION, and the mutation duty is
  discharged only by a mutation of the caller. This is exactly what `at311-mutation-check` cycle 3
  actually did — it kept `test_an_interrupted_run_with_real_failures_is_not_a_kill` AND the `is_kill`
  table — so the clause codifies the behaviour that was right, not a new burden, and no pending
  verdict turns on it. Tightening only — adds a duty, weakens none, routine gate.
  **Edge case recorded, no criterion changed: C3's text is wider than C3's gate.** C3 says "No class
  or public top-level function name is defined in two modules", unscoped, while its Verify instrument
  `check_duplicate_definitions` (`src/autotester/doctor.py:88`) reads `_python_files()`
  (`doctor.py:38-43`), which globs `src/` only — deliberately, since `check_file_sizes` on line 48
  adds `tests/*.py` and the duplicate rule does not. A checker AST scan of `tests/*.py` at baf56a1
  found **29** duplicated public top-level names, including a duplicated TEST name
  (`test_act_without_a_schema_raises`, `tests/test_providers.py:32` and
  `tests/test_langchain_fallback.py:186`). So the pattern is pre-existing and project-wide, and one
  more instance introduced by cycle 3 (`spec` in `tests/conftest.py:68` duplicating
  `tests/tests_mutation_fixtures.py:35`) was recorded (**AT-326**) rather than charged: inventing an
  enforcement scope against one unit on its last fix cycle would judge it harder than cycles 1 and 2
  were judged, and the checker's one absolute cuts the other way too — a criterion is not
  *strengthened* mid-verdict to fail an artifact any more than it is softened to pass one. The
  text-vs-gate divergence is itself the C9 shape one level up and is filed as **AT-327** for a
  decision (widen the rule and clear the 29, or scope C3's text to `src/` and say why test helpers
  are exempt). Ledger: **AT-324** (medium), **AT-325** (medium), **AT-326** (low), **AT-327**
  (medium), **AT-328** (low). Verdict: `qa/verdicts/at311-mutation-check.md`.
- 2026-09-11 · /checker (contract maintenance, no unit in flight) · **C7 extended** — a separate
  amendment from the same turn's `ui.md` U13 fold, with its own criticality judgement:
  **ROUTINE (a duty added, nothing softened).** Folds the durable fix proposed by
  `qa/debug/at345-346-fold-coverage-cycle3.md` §5 and restated in `qa/gates/at355-guard-shape.md`:
  an unreachability claim must paste the mutation actually attempted and its INCONCLUSIVE run.
  Adopted because the diagnosis's attribution is sound and independently re-derivable — the
  instrument (`scripts/mutation_check.py`) was audited against all five clauses by two checkers and
  holds, and the contract already forbade the move by name citing AT-315/AT-321, so neither is the
  cause; what recurs is the maker reaching "no mutation can reach this" by failing to think of one,
  which is cheaper than the search. A mechanical duty is the only form of the rule that is not
  discharged by prose. Deliberately placed in C7 and **not** in `qa/adapter.json` or `qa/loop.md`,
  for the reason that already declined the 2026-09-11 slot-1 mutation proposal: a rule the maker
  writes for itself is not a gate. Evidence: AT-354 refuted in one line (mutating the strip to
  `category(ch).startswith("M")` kills the test the maker called unkillable).
