# Verdict — at540-assertion-layer

**Date:** 2026-09-22 · **Checker:** /checker Mode A, fresh subagent (claude) · **Bound root:** D:/autoTesting
**Cycle checked: 1** (manifest Fix cycle: 1 of max 3) · **Dual check:** no (single check)

## VERDICT: FAIL

**SCOREBOARD:** 5/5 criteria met (E1–E5, E1 judged as amended by D-032), 1 invariant holds in code
with a caveat (C7 holds in `grade.py` — read-verified — but is unisolated for the new outcome, row 7
below).

```
VERDICT: FAIL
SCOREBOARD: 5/5 criteria met, 1/1 applicable invariants hold in code (C7 caveat: unisolated by any test)
FAILURES:
- [capability row 3 — dom_asserts] sev: high · the named check contains NO dom_asserts assertion; the falsifying edit (`found = True` in browser/assertions.py) SURVIVED (1 passed after) · add a dom_asserts assertion (met path needs FakeLocator.count(); today dom_asserts can only ever read "unmet" under fakes) · issue: AT-548
- [capability row 7 — C7] sev: high · no test anywhere constructs Outcome.ASSERTION_FAILED for grade(); the judge-refusal edit in grade.py::_outcome_verdict SURVIVED (tests/test_grade.py 12 passed after) · add a grade-side test: an ASSERTION_FAILED run reaches the judge and its verdict comes from the judgment · issue: AT-549
- [capability row 6 — ERRORED precedence] sev: high · the fake raises on button.broken inside the handler, so the expectation-bearing step and the exception are the SAME step; the exception-masking edit SURVIVED (1 passed after) — the test re-pins only "exception → ERRORED" (the very test this unit deleted) under a name claiming precedence · make step 1 a successful click whose declared expectation never arrives, step 2 the raising click · issue: AT-550
- [diff scope 4c] sev: high · three existing tests deleted from tests/test_execute.py, not moved anywhere: test_step_exception_is_errored_not_a_crash, test_missing_secret_blocks_for_a_human_instead_of_erroring (E3's two pins), test_a_secret_value_inside_an_exception_message_is_scrubbed_before_persisting (AT-341) — verbatim bodies re-run green against the post-change tree (3 passed), so this is pure coverage loss · restore them · issue: AT-547
CAPABILITY-COVERAGE: 6/9 rows reproduced; 3 rows' falsifying edits SURVIVED (rows 3, 6, 7) — unenumerated claims; 0 UNVERIFIED
LIVE-BROWSER: not-applicable (changed paths are src/autotester/{schema/enums.py, browser/{session.py, assertions.py}, stages/{execute.py, grade.py}} + tests — no UI surface of our own app changed; manifest claim verified against git diff --name-only df529f2..d7c2dfa)
ISSUES-WRITTEN: AT-547, AT-548, AT-549, AT-550, AT-551, AT-552 (AT-540 flipped open → fixed by this check)
EXECUTOR: claude-sonnet-subagent (manifest carries no Executor line; checker: claude)
EXPLANATION: The D-032 behaviour itself is real and verified — I re-ran every verify command (5+27+62 pytest groups, ruff, doctor: all green; the combined 9-file run reproduces the claimed 96 passed) and reproduced 6 of 9 capability rows in throwaway worktree copies, each green-before / red-after with the named assertion firing (row 1: outcome COMPLETED vs ASSERTION_FAILED; row 2: the absent_text assertion; row 4: met_asserts 1 == 2; row 5: bare ASSERT now fails; row 8: chokepoint fired on the planted .page line; row 9: doctor file-too-long 302 > 300, exit 1). The unit fails on its own evidence table: three of its nine claimed capabilities are not isolated by any test — the falsifying edits survived — and the diff silently deleted three existing tests. This is the assertion layer's own first check: an oracle layer whose dom_asserts/precedence/C7-for-assertions rows have no teeth is exactly the "assessed < claimed" pattern this pair exists to catch.
```

## What I re-ran (all in the bound tree, 2026-09-22)

- `uv run pytest tests/test_execute_assertions.py` → 5 passed
- `uv run pytest tests/test_execute.py tests/test_grade.py tests/test_run_case_pipeline.py` → 27 passed
- `uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py tests/test_actuator_chokepoint.py tests/test_schema.py` → 62 passed
- Combined 9-file run incl. `tests/test_execute_new_actions.py` → **96 passed** (reproduces the manifest's claimed number)
- `uv run ruff check src tests scripts` → All checks passed! · `uv run autotester doctor` → doctor: clean
- Deleted-test bodies re-run verbatim in a clean throwaway copy → 3 passed (E3/AT-341 behaviour holds; deletion is coverage-only)

## Capability-coverage rows (each in its own worktree copy at HEAD, green-before → edit → red-after)

| row | before (copy) | edit (single hunk, file from What-changed) | after | verdict |
|---|---|---|---|---|
| 1 unmet visible_text → ASSERTION_FAILED | 1 passed | execute.py: `if _assertions_unmet(...)` → `if False and ...` | RED at `assert result.outcome is Outcome.ASSERTION_FAILED` (COMPLETED) | reproduced |
| 2 absent_text met only when truly absent | 1 passed | assertions.py: inverted absent_text label | RED at `assert any("absent_text: unmet" ...)` | reproduced |
| 3 dom_asserts met only when selector exists | 1 passed | assertions.py: `found = selector_exists(...)` → `found = True` | **1 passed — edit SURVIVED** | unisolated (AT-548) |
| 4 met expectation → COMPLETED + per-field evidence | 1 passed | assertions.py: deleted the url evidence block | RED at `assert len(met_asserts) == 2` (1 == 2) | reproduced |
| 5 bare ASSERT harmless | 1 passed | execute.py: unmet-check also fires for bare ASSERT | RED at `assert result.outcome is Outcome.COMPLETED` | reproduced |
| 6 ERRORED outranks earlier unmet assert | 1 passed | execute.py: except-branch returns ASSERTION_FAILED when an earlier unmet assert exists | **1 passed — edit SURVIVED** | unisolated (AT-550) |
| 7 assertion runs still judged (C7) | 12 passed | grade.py: ASSERTION_FAILED refusal inserted into _outcome_verdict | **12 passed — edit SURVIVED** | unisolated (AT-549) |
| 8 actuator boundary intact | 2 passed | execute.py: one planted `.page.` line | RED — chokepoint named the offender `stages\execute.py:26` | reproduced |
| 9 line caps hold | doctor: clean | session.py: +3 filler lines | RED — `file-too-long: ... 302 lines > 300`, exit 1 | reproduced |

The three surviving rows are unenumerated claims per the protocol and each fails the unit on its own.

## Diff-scope review (4c)

Unit commits: d7c2dfa (code + D-032) and cd3acd5 (tick stamp). Base df529f2. Findings:

- **Deleted:** the three tests named in AT-547 above (manifest says "split" — they were dropped, not moved). This is the 4c failure.
- **No function/class/export/config-key deletions** in src: enums.py compaction is docstring prose only; grade.py's `_outcome_verdict` extraction moved the two outcome branches verbatim; session.py's `_poll_for_expected` survives; execute.py's `lambda: None` ASSERT is the unit's target.
- **Touched-but-unlisted in "What changed":** docs/MAP.md (+1 generated map row for the new module), docs/SNAPSHOT.md (regeneration + F-044/T-122 ledger-text refresh), qa/.last-tick (tick stamp), qa/delegation/at119-vocab-ollama-deepseek-v4.1-flash.log (+12 delegation-log appends). All additive generated/bookkeeping surfaces, no behavioural content — recorded here, not failed: the manifest should have listed them.

## Non-blocking notes (ledger rows AT-551, AT-552)

- The unit introduced a UTF-8 BOM + mojibake em-dash in tests/test_execute.py's docstring and 4 new mojibake lines in DECISIONS.md's D-032 entry (pattern pre-existing: 6 lines before → 10 after). Cosmetic; ruff/pytest green.
- `assert_expected`'s "raises nothing" promise is violated by its unsuppressed url probe (browser/assertions.py:59) — an edge-case exception surfaces as ERRORED instead of a recorded unmet assert.
- D-032's Result text says a no-expected ASSERT "records `assert: nothing expected` DOM evidence"; the implementation records nothing (the manifest discloses this deviation and the test pins it). Judged as a disclosed deviation from the decision's detail, not a contract violation — the contract line I wrote says "stays harmless".
- Manifest line-count claims are off in places (execute.py 138→actual 156; test_execute.py 193→247; assertions.py 80→92; grade.py 205 ✓; session.py 299 ✓). Caps hold regardless (doctor clean).

## Contract touch landed with this verdict (checker-owned, authorized by D-032)

- `qa/contracts/execute.md` — E1 superseded per D-032 (four observations incl. ASSERTION_FAILED; ASSERT evaluates declared expectations and records per-field evidence; C7 restated) + amendment-log entry citing D-032 and this FAIL's coverage findings.
- `docs/ARCHITECTURE.md` — the one-sentence Execution-model addition D-032 authorizes ("deterministic assertions are evidence… the grader still owns every verdict").

The amendment is the mechanical fold-in of an already-human-approved decision (D-032, Umesh 2026-09-22, appended to DECISIONS.md before the code was written) — decided away from this verdict; nothing was softened to pass a failing artifact, and no criterion was weakened: the E1 rewrite preserves and restates the no-grading boundary C7 holds.

## Fix directions for cycle 2

1. Restore the three deleted tests (AT-547).
2. Pin dom_asserts: assert the dom_asserts evidence label in test_absent_text_and_dom_asserts_are_evaluated (give FakeLocator a `count()` so a met path is expressible) (AT-548).
3. Pin C7 for the new outcome: a test_grade.py test with `Outcome.ASSERTION_FAILED` asserting the judge is called and the verdict is the judgment's (AT-549).
4. Fix test_errored_still_beats_assertion_failed: step 1 a successful click with a never-arriving expectation, step 2 the raising click (AT-550).
5. (Low) strip the BOM + mojibake (AT-551); suppress the url probe like its siblings (AT-552).