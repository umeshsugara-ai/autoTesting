# Verdict — run-case-pipeline

**Contract:** qa/contracts/run-case-pipeline.md (RP1-RP4)
**Manifest:** qa/manifests/run-case-pipeline.md
**Cycle checked:** 1
**Result: PASS**

## RP1 — every case is gradeable, with no hand-written Python

`run_and_grade_case` (`src/autotester/stages/run_case_pipeline.py:40-56`) never raises for a
rubric-less case: `store.load_rubric(rubric_id)` returning `None` triggers
`default_rubric(...)` + `store.save_rubric(...)` before grading (lines 51-54). Confirmed by my
own independent repro script (not the maker's test suite) — see "Independent reproduction"
below: first call with no prior rubric completed with `Outcome.COMPLETED` / `Result.PASS` and
created `rubrics_dir/rub_<case.id>.json` where none existed before.

## RP2 — the default rubric is honest, not a rubber stamp

`default_rubric` (`run_case_pipeline.py:25-37`): `claim = case.rationale or f"the case
'{case.title}' completes as its steps describe"` — grounded in the case's own rationale, title
only as fallback. Criterion is pinned `id="c1"` with the explicit "do not invent a different
id" instruction, textually mirroring `scripts/regression_proof.py:92-98`'s `make_rubric`
(same `id="c1"`, same "do not invent a different id" phrasing). Verified in
`src/autotester/stages/grade.py:49-64,94-98` (`_inconsistency`) that an unknown
`failure.criterion_id` downgrades the verdict to `Result.INCONCLUSIVE` via the
self-consistency gate — so the pinned-id pattern is not decorative, it's defending against a
real, code-visible failure mode.
`tests/test_run_case_pipeline.py:56-64` cover both the rationale-grounded case and the
title-fallback case; content checked with `"welcome message" in rubric.criteria[0].text` /
`"Homepage loads" in rubric.criteria[0].text` — not merely "a rubric object exists."

## RP3 — persistence is idempotent, reuses `ProjectPaths.rubrics_dir`

`ProjectStore.save_rubric`/`load_rubric` (`src/autotester/store/project_store.py:85-89`) are a
single `write_json`/`read_json` pair against `self.paths.rubrics_dir / f"{id}.json"` — the same
one-file-per-id shape as `save_bench_corpus`/`load_bench_corpus` (lines 143-147) and
`save_run`/`load_run` (92-96) in the same file. `rubrics_dir` already existed in
`core/paths.py:64` (and in the directories-created-at-init list, `core/paths.py:106`) — no new
directory, no new file format (C1/C3/C4 satisfied).

Idempotent reuse verified two ways:
1. `tests/test_run_case_pipeline.py:86-104` — pre-seeds a hand-tuned rubric with distinct text,
   calls `run_and_grade_case`, reloads, asserts the text is unchanged.
2. My own independent repro (below) — same rubric file's raw bytes compared before/after a
   second `run_and_grade_case` call on the same case: byte-identical.

## RP4 — never grades on stale or wrong evidence

`git diff --stat -- src/autotester/stages/execute.py src/autotester/stages/grade.py` against
the working tree is empty — neither file is touched by this unit. `run_and_grade_case` calls
the unmodified `run_case` (imported from `stages.execute`) and `grade` (imported from
`stages.grade`) directly (`run_case_pipeline.py:20-21,49,55`) with no evidence-shaping logic of
its own beyond the rubric lookup/creation step.

## Scope decision (no-fire list)

The manifest's "Deliberate scope decision" section states plainly, up front, that the 3
existing scripts are not refactored to call this function, with a stated reason (each is
already checker-PASSed with a hand-tuned rubric; migrating risks regression for no immediate
benefit) and names the actual first caller (the UI run-trigger, a separate upcoming unit). This
matches the contract's own no-fire list verbatim — not a silently smuggled scope cut.

Note: the working tree also carries unrelated uncommitted changes to
`scripts/run_pathlynks_first_cases.py` (a login-flow timing fix, its own
untracked manifest/verdict pair `pathlynks-login-test-fresh-profile`) — unrelated to this
contract's scope and not evaluated here.

## Independent reproduction (not the maker's test suite)

Wrote and ran `repro_run_case_pipeline.py` (scratchpad, not committed) against a fresh tmp
project `demo2`, a case with `rationale="the checker independently verifies this claim"`, and a
`MockProvider` queued with a PASS `Judgment`:

```
rubric file exists BEFORE first call: False
outcome: completed verdict: PASS
rubric file exists AFTER first call: True
rubric content snapshot 1 len: 630
rubric content unchanged after 2nd call: True
ALL CHECKS PASSED
```

Confirms: a case with no persisted rubric runs and grades without raising; the rubric file
lands on disk under `rubrics_dir`; a second `run_and_grade_case` call on the same case does not
mutate the persisted file (idempotent reuse), independent of the maker's own test fixtures.

## Verification commands re-run myself

```
$ uv run pytest tests/test_run_case_pipeline.py -v
....                                                                      [100%]
4 passed in 0.34s

$ uv run pytest -q
............ (all collected tests) ...s...............s.......           [100%]
(no failures)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

## Verdict

PASS. RP1-RP4 all hold on direct code reading and on my own independent reproduction, not just
re-running the maker's tests. The default rubric is genuinely case-specific (rationale/title
text appears verbatim in the criterion), the pinned `"c1"` id defends against a real,
code-verified failure mode in `grade.py`'s self-consistency check, persistence follows the
established one-file-per-id pattern with no new format, `execute.py`/`grade.py` are untouched,
and the no-fire scope decision (not migrating the 3 existing scripts) is stated plainly rather
than smuggled in.
