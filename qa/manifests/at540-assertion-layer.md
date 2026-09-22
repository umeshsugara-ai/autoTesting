# Manifest — at540-assertion-layer

**Unit:** D-032 (AT-540): the deterministic assertion layer made real. The four dead
ExpectedState fields (`url`/`visible_text` already settle-hints; `absent_text`, `dom_asserts`
now evaluated; `network` observer-derived, `visual_signal` judge-owned) and the no-op
`Action.ASSERT` replaced with a real evaluator. `Outcome.ASSERTION_FAILED` added as a fourth
OBSERVATION (never a grade; C7 intact — grade.py still owns every verdict).
**Contract:** qa/contracts/execute.md E1 (as amended by D-032 — the amendment itself is the
checker's next contract touch; the code is written against D-032's Result section verbatim).
**Goal task:** none (AT-540 is a ledger row, not a goal task; T-169's oracle-quality axis is the
downstream consumer).
**Date:** 2026-09-22
**Fix cycle:** 1 of max 3
**Dual check:** no (the matching goal task does not exist; criticality defaults to single-check)
**Issues addressed:** AT-540 (high)

## What changed

- `src/autotester/schema/enums.py` — `Outcome.ASSERTION_FAILED` added (docstring states
  observation-not-grade; the enum file compacted to 299/300 lines, no behaviour change).
- `src/autotester/browser/assertions.py` (NEW, 80 lines) — `met(session, expected)` (one probe:
  url substring, visible_text present, absent_text truly absent, dom_asserts selectors exist)
  and `assert_expected(...)` (poll to the settle ceiling, then record one `assert <field>:
  met|unmet (<detail>)` DOM evidence item per evaluated field). Raises nothing. `network` and
  `visual_signal` deliberately NOT evaluated (E1's no-fire line, unchanged).
- `src/autotester/browser/session.py` (299/300) — `assert_expected`/`_met` are the session's
  door to `browser/assertions.py` (the line-cap split; the actuator choke-point test still
  holds — assertions.py is INSIDE `browser/`). `settle`'s history moved to execute.md's
  amendment log where it already lived.
- `src/autotester/stages/execute.py` (138 lines) — `Action.ASSERT` now evaluates the step's
  declared expectation (a bare ASSERT records nothing and stays harmless); after every step
  whose `expected` declares checkable fields, the expectation is evaluated post-settle; any
  unmet assert makes the run's outcome `ASSERTION_FAILED`. An ERRORED exception still wins
  (it explains why the rest never ran).
- `src/autotester/stages/grade.py` (205 lines) — `_outcome_verdict` extracted; an
  ASSERTION_FAILED run still reaches the judge (the recorded unmet asserts travel inside the
  evidence list — the judge weighs recorded facts and may disagree with a wrongly-authored
  expectation: C7's "the grader still owns the verdict" made literal for the new outcome).
- `docs/DECISIONS.md` — D-032 appended FIRST via scripts/append_decision.ps1 (Lab Protocol),
  with `Approved-by`-style authorization chain naming Umesh's 2026-09-22 chat approval.
- `docs/ARCHITECTURE.md` — D-031's corrected section (the previous commit) is the prose
  baseline; the D-032-authorized one-sentence addition lands with the checker's contract
  amendment to keep this unit's file set narrow.
- Tests: `tests/test_execute_assertions.py` (NEW, 5 falsifying tests); `test_execute.py`
  (split to 193/300; the completed-run test's fake page now carries the asserted text and
  asserts the recorded evidence).

## How to verify (commands + expected)

```
uv run pytest tests/test_execute_assertions.py   # 5 pass — the D-032 behaviour
uv run pytest tests/test_execute.py tests/test_grade.py tests/test_run_case_pipeline.py
uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py tests/test_actuator_chokepoint.py tests/test_schema.py
uv run ruff check src tests scripts              # All checks passed!
uv run autotester doctor                         # doctor: clean
```

## Capability coverage (each claim -> its isolating check)

| capability | check | falsifying condition |
|---|---|---|
| unmet visible_text -> ASSERTION_FAILED + unmet evidence | test_an_unmet_declared_expectation... | outcome stays COMPLETED silently |
| absent_text met only when truly absent | test_absent_text_and_dom_asserts... | present text reads as met |
| dom_asserts met only when selector exists | same test (error-banner absent) | selector absence ignored |
| met expectation -> COMPLETED + per-field evidence | test_a_met_expectation_keeps_the_run_completed | met asserts missing from evidence |
| bare ASSERT harmless | test_an_assert_step_with_no_expectation_is_harmless | no-expected ASSERT fails the run |
| ERRORED outranks earlier unmet assert | test_errored_still_beats_assertion_failed | exception masked as assertion outcome |
| assertion runs still judged (C7) | tests/test_grade.py full pass + grade.py:142 comment | judge refused on ASSERTION_FAILED |
| actuator boundary intact | test_actuator_chokepoint.py | .page/playwright outside browser/ |
| line caps hold | doctor: clean (measured below) | any file > 300 |

## Actual outputs (my own run, 2026-09-22)

```
$ uv run pytest tests/test_execute_assertions.py tests/test_execute.py tests/test_grade.py
  tests/test_run_case_pipeline.py tests/test_browser.py tests/test_browser_navigation_secrets.py
  tests/test_secrets.py tests/test_actuator_chokepoint.py tests/test_schema.py
  tests/test_execute_new_actions.py
96 passed in 6.97s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Live browser evidence

Not UI-touching — no surface of our own app changed (changed paths:
src/autotester/{schema/enums.py, browser/{session.py, assertions.py},
stages/{execute.py, grade.py}, tests}). The executor's assertions are exercised against a
browser only through the fakes above; the real-browser path is the existing
test_run_pathlynks_first_cases.py set (re-run green in the 96).

## Status: ready-for-check