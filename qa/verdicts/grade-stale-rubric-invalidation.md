# Verdict — grade-stale-rubric-invalidation

**Contract:** qa/contracts/run-case-pipeline.md
**Manifest:** qa/manifests/grade-stale-rubric-invalidation.md
**Cycle checked:** 1
**Date:** 2026-09-07
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`, no builder context
**Dual check:** no (primary verdict)

## VERDICT: PASS

**SCOREBOARD:** 4/4 criteria met, 3/3 no-fire boundaries hold

---

## What I re-ran myself (nothing below is the maker's pasted output)

All in the project's own container, `docker compose exec -T autotester …`:

| Command | My result |
|---|---|
| `uv run pytest -q tests/test_run_case_pipeline.py` | `.........` — 9 passed, exit 0 |
| `uv run pytest -q` | `309 passed, 1 skipped, 1 warning in 7.38s`, exit 0 |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 |
| `uv run autotester doctor` | `doctor: clean`, exit 0 |

Plus **two checker-authored probes** (written by me from the contract, not read from the
maker's tests), executed in the same container against the real modules.

The manifest's 5th verify item — the live `POST /projects/erp/run` reproduction — I did **not**
re-execute: it mutates `projects/erp/` runtime data and spends a real judge provider call, and
the dispatch scoped it to inspection. I inspected the artifact it left instead
(`projects/erp/rubrics/rub_case_27256e2a2b8d.json`) and it corroborates the claim exactly:
`provenance.produced_by = "stages.run_case_pipeline.default_rubric"`, `provenance.note` = the
title-fallback claim, and that note equals `claim_of(case_27256e2a2b8d)` today — i.e. the file
self-healed and is now non-stale. Stated plainly so this is not mistaken for a re-run. No
criterion below depends on that live run; the behaviour it demonstrates is independently proven
by probe 1 (B1/B3) and by the on-disk state.

---

## Probe 1 — I attacked the overwrite guard myself

`is_stale_default` returning True on a human's rubric is the one unrecoverable failure of this
unit, so I did not take the maker's four tests as coverage. I constructed **12 independent
false-positive attacks** plus 3 inverse cases and ran them against the real
`autotester.stages.run_case_pipeline`:

```
P0 compute_id excludes rationale+title: True  case_71eca4d8390f == case_71eca4d8390f
OK   A1  hand-written, no provenance                       -> False (expected False)
OK   A2  FORGED produced_by == GENERATOR, note=None, human criteria -> False
OK   A3  FORGED produced_by + note, human criteria          -> False
OK   A4  generated then criteria text edited                -> False
OK   A4b generated then evidence_required flipped           -> False
OK   A4c generated then extra criterion appended            -> False
OK   A5  generated then no_fire appended                    -> False
OK   A5b generated then no_fire cleared                     -> False
OK   A6  generated, provenance.note = None                  -> False
OK   A7  provenance produced_by = "human"                   -> False
OK   A8  generated, note forged to the CURRENT claim        -> False
OK   B1  genuinely stale generated rubric                   -> True  (expected True)
OK   B2  unchanged claim (churn guard)                      -> False (expected False)
OK   B3  rationale cleared -> title fallback, still stale   -> True  (expected True)
```

Every one of the dispatch's named attacks is covered: hand-written with no provenance (A1),
hand-written with a **forged** `produced_by` equal to the generator constant (A2, A3),
generator-produced then edited in `criteria` (A4, and I added A4b/A4c the maker's tests do not
cover), generator-produced then edited **only** in `no_fire` (A5, A5b — also not in the maker's
tests), generator-produced with `provenance.note` absent/None (A6). **Zero false positives.**

The guard's structure is what makes this hold rather than luck: a forged `produced_by` is not
enough, because line 82–83 rebuilds `_rubric_for_claim(recorded, …)` and demands the stored
`criteria` **and** `no_fire` match that reconstruction byte-for-byte. A human's rubric cannot
survive that comparison unless it is byte-identical to generator output for its own recorded
claim — in which case there is nothing of the human's to destroy.

## Probe 2 — the precondition the whole bug rests on, verified in the schema

`src/autotester/schema/case.py:38-45`, read directly, not asserted:

```python
def compute_id(self) -> str:
    payload = {"project": …, "flow_id": …, "case_class": …, "steps": […]}
```

`rationale` and `title` are both absent. Confirmed at runtime (P0 above): two cases differing in
**both** rationale and title hash to the same `case_71eca4d8390f`, therefore to the same
`rub_<case_id>` file, therefore to the same rubric — which is exactly why AT-059 had no
invalidation path. The maker's own `assert old.id == new.id` precondition is real.

## Probe 3 — blast radius on the 4 real projects

I loaded every rubric file on disk and asked the shipped guard whether the **next** ordinary run
would rewrite it:

| File | `produced_by` | Would be rewritten next run |
|---|---|---|
| `projects/erp/rubrics/rub_case_27256e2a2b8d.json` | GENERATOR (stamped) | **False** — recorded note == current claim |
| `projects/pathlynks/rubrics/rub_case_35b17ccece2d.json` | `null` | **False** |
| `projects/pathlynks/rubrics/rub_case_a5ea57c0961a.json` | `null` | **False** |
| `projects/pathlynks/rubrics/rub_case_b1cb019ebb56.json` | `null` | **False** |
| `projects/vidysea-erp/rubrics/rub_case_7ba94f4da443.json` | `null` | **False** |

`projects/regression-demo/` has no `rubrics/` directory. **The manifest's claim that no existing
rubric would be rewritten is confirmed on every file that exists.** I did not modify any of them.

Callers: `grep -rn run_and_grade_case src scripts` returns exactly one non-definition caller —
`src/autotester/ui/routes_runs.py:56,94`. No script calls it, matching the contract's no-fire
deferral. The churn question is settled by B2 above (unchanged claim → `False` at line 80, before
any reconstruction) and by the maker's `test_an_unchanged_generated_rubric_is_left_alone`, which I
re-ran. `case.rubric_ref` still wins for every rubric that is not generator-stamped (A1/A7), and
nothing in the repo assigns `rubric_ref` at all — see AT-064 below.

---

## Criterion-by-criterion

### RP1 — Every case is gradeable, with no hand-written Python — **MET**
`run_and_grade_case` still builds and persists `default_rubric` when `load_rubric` returns None
(`run_case_pipeline.py:97-100`), and still reuses the persisted one on subsequent calls — now
qualified by `is_stale_default`, which my probe shows returns `False` for an unchanged claim, so
reuse is preserved. Evidence: `test_run_and_grade_case_builds_and_persists_a_default_rubric_when_none_exists`
and `test_an_unchanged_generated_rubric_is_left_alone`, both re-run by me; probe B2.

### RP2 — The default rubric is honest, not a rubber stamp — **MET**
The criterion text is **byte-unchanged** by this unit — `git diff` shows the f-string moved from
`default_rubric` into `_rubric_for_claim` with no edit to its content. It is still grounded in
`case.rationale`, still falls back to `title` when rationale is empty (`claim_of`, line 30), still
pins criterion id `"c1"` with the explicit do-not-invent instruction that avoids `grade.md` G3's
self-consistency downgrade. Evidence: the two `default_rubric` tests, re-run; the diff itself.

### RP3 — Persistence is idempotent and reuses `ProjectPaths.rubrics_dir` — **MET**
No change to `ProjectStore.save_rubric`/`load_rubric`, no new file format, no new top-level
directory. The added `provenance` key is not a format change: `Rubric` inherits it from
`schema/base.py::Artifact`, which has carried `provenance: Provenance | None` all along. I proved
backward compatibility rather than assuming it — probe 3 `model_validate`d all 5 on-disk rubrics,
including the 4 written before stamping existed, with `extra="forbid"` in force. `doctor: clean`.

### RP4 — Never grades on stale or wrong evidence — **MET**
`git status` confirms the only modified source file is `run_case_pipeline.py`; `execute.py` and
`grade.py` are untouched. The stage still calls `run_case` then `grade` with no evidence-capture
or judgment logic of its own — the addition sits entirely in the rubric lookup/creation step
between them, which is precisely where RP4 permits it. And this unit *strengthens* RP4's spirit:
grading against a claim the case no longer makes was exactly "grading on stale evidence."

### No-fire boundaries — all 3 hold
The 3 scripts are untouched (`git status`); no AI-authored rubric generation was added (the
generator is still the plain rationale template); `execute.py`/`grade.py` unchanged.

---

## Issues addressed

**AT-059 → `fixed`.** The unit closes it, and I am satisfied it should be closed rather than left
partly open. The dispatch asked me to say so plainly, so: the live failure mode — a corrected
rationale still grading against the old claim with hand-deletion as the only recovery — is gone
for every rubric this system generates from now on, and cannot recur, because the claim is now
recorded on the artifact and compared on every run. That is a complete fix of the mechanism the
ledger entry describes ("load_rubric should regenerate when the stored claim no longer matches").

Where I disagree with the manifest is its *reasoning*, not its conclusion. The manifest calls the
4 pre-existing unstamped rubrics "genuinely indistinguishable from hand-written ones." That is
**factually wrong**, and I checked rather than took it: all 4 carry `_rubric_for_claim`'s exact
output — one criterion with id `c1`, the exact template sentence, and the exact one-element
`no_fire` list — while every hand-written rubric in the repo differs in shape
(`run_pathlynks_first_cases.py:91` uses criterion id `landed`; `regression_proof.py:93` and
`bench_trial.py:83` use `no_fire=["visual styling"]`). Shape alone does distinguish them. So the
limitation is a **choice**, not a forced consequence — and it is the right choice: a
template-matching heuristic at runtime would reintroduce precisely the overwrite-on-a-guess risk
this unit exists to eliminate, for 4 files that are all non-stale today. Filed as AT-065 with a
human-reviewed one-off migration as the fix direction, so the residual is queued work rather than
a paragraph in a manifest nobody re-reads. It does not keep AT-059 open.

## New issues written

- **AT-065** (medium) — the 4 unstamped rubrics are distinguishable but cannot self-heal;
  AT-059's failure mode stays latent for those cases. Corrects the manifest's stated rationale.
- **AT-063** (low) — a human edit confined to `feedback_format` is discarded on regeneration:
  line 83 compares only `criteria` and `no_fire`. Reproduced (probe B4 → `True`). Not a FAIL:
  regeneration is correct in that scenario, no criterion covers `feedback_format`, and nothing in
  the codebase ever sets it, so it is reachable only by hand-editing JSON.
- **AT-064** (low) — a generator-stamped rubric shared by two cases via `case.rubric_ref` would be
  rewritten with the pointing case's claim; `is_stale_default` never checks `rubric.case_id ==
  case.id`. Reproduced (probe B6 → `True`). Unreachable today — nothing anywhere assigns
  `rubric_ref` — so it is filed ahead of the first writer, not charged against this unit.

None of the three is a criterion violation and none is severe enough to burn a fix cycle; each is
reproducible on demand from the probes above.

## Commits I made

The maker's source changes were **uncommitted** when I began (`git status` showed
`src/autotester/stages/run_case_pipeline.py` and `tests/test_run_case_pipeline.py` modified,
manifest untracked) — the same gap as AT-055. Per this session's lesson I committed them myself
with a narrow pathspec covering exactly the source, the tests and the manifest, plus this verdict
and the ledger. No `projects/` runtime data and no `.work/` was committed.

---

## Returned block

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 3/3 no-fire boundaries hold
FAILURES: none
ISSUES-WRITTEN: AT-063, AT-064, AT-065 (AT-059 -> fixed)
EXPLANATION: All four verify commands reproduce in-container (9/9 file tests, 309 passed 1
skipped full suite, ruff clean, doctor clean). I attacked the overwrite guard with 12
checker-authored false-positive cases -- hand-written with no provenance, forged produced_by with
and without a note, generator-output edited in criteria, in evidence_required, by an appended
criterion, and in no_fire alone -- and it returned False on every one, while returning True for a
genuinely stale rubric and False for an unchanged claim. I verified in schema/case.py:38-45 that
compute_id excludes both rationale and title, which is the precondition the bug rests on, and I
ran the shipped guard over all 5 rubric files in the 4 real projects: none would be rewritten by
the next run, as the manifest claims. Three low/medium issues filed, none blocking; the manifest's
"indistinguishable from hand-written" rationale is wrong on the facts (AT-065) but its conclusion
is the safe one, so AT-059 closes here.
```
