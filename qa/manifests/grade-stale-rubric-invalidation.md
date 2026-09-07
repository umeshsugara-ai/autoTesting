# Manifest — grade-stale-rubric-invalidation
**Contract:** qa/contracts/run-case-pipeline.md
**Goal task:** none (issue-fix unit)
**Date:** 2026-09-07
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-059

## What changed
All in `src/autotester/stages/run_case_pipeline.py`; no schema change — the fix rides on the
`Provenance` envelope `schema/base.py::Artifact` already carries.

- New `claim_of(case)` — the one sentence a default rubric grades against, extracted so the
  generator and the staleness check can never compute it differently.
- New `_rubric_for_claim(claim, case_id, rubric_id)` — builds a rubric from an explicit claim
  and **stamps `provenance=Provenance(produced_by=GENERATOR, inputs=[case_id], note=claim)`**.
  Recording the claim is what makes staleness detectable at all.
- `default_rubric(case, rubric_id)` — unchanged signature and output text; now just
  `_rubric_for_claim(claim_of(case), …)`.
- New `is_stale_default(rubric, case)` — True only when the rubric was produced by this
  generator, its recorded claim differs from the case's current one, **and** its criteria and
  no_fire still match exactly what the generator would have produced for that recorded claim.
- `run_and_grade_case` — `if rubric is None or is_stale_default(rubric, case):` regenerate and
  save. One line changed.
- `tests/test_run_case_pipeline.py` — 4 new tests (9 total in the file).

## How it was found
Found live while proving the new UI add-a-case flow (`ui-add-case`). A case created with
`rationale="added by hand from the UI"` persisted a rubric whose claim was literally that
string; the grader duly hunted for a "UI addition step" and FAILed a case whose screenshot
plainly showed the sign-in page it had asked for. Correcting the rationale did **not** help:
`Case.compute_id()` deliberately excludes `rationale`, so the corrected case had the same id,
resolved to the same `rub_<case_id>` file, and kept grading against the stale claim. Deleting
`projects/erp/rubrics/rub_case_27256e2a2b8d.json` by hand was the only recovery.

## The judgement call: what must NOT be overwritten
A rubric is a grading contract. Regenerating one a human tuned would silently destroy their
work and change what "PASS" means, so `is_stale_default` is conservative on both edges:

1. **No provenance, or provenance from any other producer → never touched.** This includes
   every rubric written before this stamping existed: they are genuinely indistinguishable
   from hand-written ones, so they keep their claim. Honest limitation, stated rather than
   hidden — the self-healing applies to rubrics generated from this change forward. (The one
   pre-existing stale rubric in the repo, `erp`'s, was already deleted by hand during
   `ui-add-case`; no other project has one.)
2. **Generator provenance, stale claim, but criteria no longer match what the generator would
   have produced for its own recorded claim → never touched**, because a human has edited it
   since. `tests/test_run_case_pipeline.py`'s pre-existing
   `test_run_and_grade_case_reuses_an_existing_rubric_instead_of_overwriting_it` builds exactly
   this shape (generate, then hand-edit the criterion) and still passes unchanged.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → expected: exit 0, all tests pass
- `docker compose exec autotester uv run pytest -q tests/test_run_case_pipeline.py` → expected: exit 0, 9 passed
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: exit 0
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- Real end-to-end, reproducing the original incident: seed `projects/erp`'s rubric from a case
  carrying `rationale="added by hand from the UI"`, then `POST /projects/erp/run` → expected:
  the persisted rubric's claim has self-healed to the case's title, and the verdict is a real
  PASS — where previously the run graded against the stale claim and FAILed until the file was
  deleted by hand.

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q tests/test_run_case_pipeline.py
.........                                                                [100%]

$ docker compose exec autotester uv run pytest -q
(full suite: all pass, 1 skip, no failures)

$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!

$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

Real end-to-end against the live app, after `docker compose restart autotester`:

```
1. seeded the exact broken state
   poisoned claim: The evidence is consistent with: added by hand from the UI. …

2. POST /projects/erp/run  -> 303
   claim now : The evidence is consistent with: the case 'Sign-in page loads and shows the lo…

   verdict: RESULT: PASS | Criteria 1/1 met.
   note: "The login page loaded and displayed the expected sign-in form fields correctly."
```

The stale claim self-healed on the next run, with no manual file deletion.

## Status: ready-for-check
