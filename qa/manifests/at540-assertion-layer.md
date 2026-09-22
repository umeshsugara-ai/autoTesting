# Manifest — at540-assertion-layer

**Unit:** D-032 (AT-540): the deterministic assertion layer made real. The four dead
ExpectedState fields (`url`/`visible_text` already settle-hints; `absent_text`, `dom_asserts`
now evaluated; `network` observer-derived, `visual_signal` judge-owned) and the no-op
`Action.ASSERT` replaced with a real evaluator. `Outcome.ASSERTION_FAILED` added as a fourth
OBSERVATION (never a grade; C7 intact — grade.py still owns every verdict).
**Contract:** qa/contracts/execute.md E1 (as amended by D-032 — the amendment landed with the
cycle-1 verdict; unchanged by this fix cycle).
**Goal task:** none (AT-540 is a ledger row, not a goal task; T-169's oracle-quality axis is the
downstream consumer).
**Date:** 2026-09-22
**Fix cycle: 2 of max 3**
**Dual check:** no (the matching goal task does not exist; criticality defaults to single-check)
**Issues addressed:** AT-547, AT-548, AT-549, AT-550, AT-551, AT-552

## What changed (fix cycle 2)

- `tests/test_execute.py` (300/300 — exactly at the doctor cap; see note below) — restored
  verbatim (via `git show d7c2dfa^:tests/test_execute.py`) the three tests cycle-1 silently
  deleted: `test_step_exception_is_errored_not_a_crash`,
  `test_missing_secret_blocks_for_a_human_instead_of_erroring`,
  `test_a_secret_value_inside_an_exception_message_is_scrubbed_before_persisting` (AT-547).
  Also gave the shared `FakeLocator`/`FakePage` fixtures a working `count()` (AT-548's missing
  piece: previously no `count()` existed at all, so `selector_exists()` could only ever land
  in its `except` and read False/"unmet" — there was no way to express a genuinely-present
  selector under the fakes) and a `missing_selectors: set[str]` on `FakePage` a test can
  populate to mark a selector absent. Trimmed the module docstring by one line and compacted
  the `inner_text`/`count` method spacing (no blank line between them — ruff doesn't require
  one) to make room for the restored tests without breaching the 300-line cap.
- `tests/test_execute_assertions.py` (187 lines) —
  - AT-548: two new dedicated isolating tests,
    `test_dom_asserts_is_met_only_when_the_selector_genuinely_exists` (default/present ->
    COMPLETED + `dom_asserts: met`) and `test_dom_asserts_is_unmet_when_the_selector_is_absent`
    (`missing_selectors` -> ASSERTION_FAILED + `dom_asserts: unmet`). Also added an explicit
    `dom_asserts: met` assertion to the existing `test_absent_text_and_dom_asserts_are_evaluated`
    so that test's own declared `dom_asserts` claim is no longer silently unchecked.
  - AT-551: `test_absent_text_on_an_unreadable_page_fails_safe_not_silently_met` — a
    test-local override of `session.page.locator` that raises only for `"body"` (leaves the
    click's own locator untouched), pinning that an absent_text expectation on an unreadable
    page records `unmet (page unreadable)` and flips the run to ASSERTION_FAILED, never a
    silent COMPLETED.
  - AT-550: rewrote `test_errored_still_beats_assertion_failed` — step 1 is now a *successful*
    click whose declared `visible_text` never arrives (a genuine unmet assertion, no
    exception); step 2 is the raising click (`button.broken`). Cycle-1's version had the
    raising step ALSO be the expectation-bearing step, so it only re-pinned "exception ->
    ERRORED" under a name claiming precedence between two different steps.
- `tests/test_grade.py` (222 lines) — AT-549: new
  `test_assertion_failed_run_still_reaches_the_judge_and_the_judge_owns_the_verdict` — builds a
  `RawResult(outcome=Outcome.ASSERTION_FAILED, ...)`, feeds it to `grade()` with a `MockProvider`
  primed to PASS, and asserts (a) `judge.prompts` is non-empty (the judge was actually called —
  unlike BLOCKED_HITL/ERRORED, ASSERTION_FAILED must NOT be short-circuited) and (b)
  `verdict.result is Result.PASS` (the judgment's own verdict, not a fixed rule-verdict for the
  outcome) — C7 made concrete for the new outcome.
- `src/autotester/browser/assertions.py` (123 lines) — AT-551/AT-552, the two genuine defects:
  - `body_text(session)` now returns `None` on a read failure instead of `""`, so "couldn't
    read the page" is distinguishable from "read it, it's empty".
  - `met()`: when `visible_text`/`absent_text` is declared and `body_text` returns `None`, `met`
    returns `False` (unmet) directly instead of falling through the blanket
    `contextlib.suppress(Exception): ... return True` at the bottom. This closes the specific
    hole cycle-1's verdict named: under the old `""` fallback, `absent_text` on an unreadable
    page read as "the text is absent from an empty string" -> met -> a clean COMPLETED run on
    a page the executor never actually saw. `visible_text` was already accidentally safe under
    the old `""` convention (`text not in ""` is always True -> unmet); it stays safe here via
    the same explicit `None` check, not a different code path.
  - `assert_expected()`: extracted `_text_label(body, text, *, want_present)` (returns
    `"unmet (page unreadable)"` when `body is None`) and `_url_label(session, url)` (AT-552:
    wraps the url probe in its own try/except so an unreadable `page.url` records
    `"unmet (url unreadable)"` instead of propagating and surfacing as an uncaught ERRORED —
    the docstring's "raises nothing" promise was violated by this one unguarded read).

## Not touched (hard constraints honored)

- `qa/contracts/execute.md`, `qa/issues.jsonl` — checker-owned; not edited.
- `docs/ARCHITECTURE.md`, `docs/DECISIONS.md` — D-032 already authorizes this layer; no new
  D-entry needed for a fix cycle, per the brief. **Note:** `docs/ARCHITECTURE.md` already
  carried an uncommitted +3-line change before this fix cycle started (the cycle-1 checker's own
  contract-amendment landing) that pushes it to 152/150 lines — see "Known pre-existing doctor
  violation" below. This fix cycle did not create it and does not touch that file.
- `src/autotester/stages/execute.py`, `src/autotester/stages/grade.py` — both were used
  **temporarily**, in-place, to reproduce the three isolating edits the cycle-1 checker demanded
  pasted evidence for (rows 3/6/7 below), then reverted. `git diff --stat` after reverting shows
  zero net changes to either file (confirmed below) — neither appears in this cycle's commit.

## How to verify (commands + expected)

```
PYTHONUTF8=1 uv run pytest tests/test_execute.py tests/test_execute_assertions.py tests/test_grade.py
# 30 passed
uv run ruff check src tests scripts              # All checks passed!
uv run autotester doctor                         # 1 pre-existing violation, unrelated -- see below
```

Per the brief, the full suite (~24 min) was NOT run in this fix cycle — the checker runs it.

## Capability coverage (rewritten — rows 3/6/7 now carry pasted falsifying-edit evidence)

| row | capability | check | falsifying edit | pasted result |
|---|---|---|---|---|
| 1 | unmet visible_text -> ASSERTION_FAILED + unmet evidence | `test_an_unmet_declared_expectation_is_assertion_failed_with_evidence` | (unchanged from cycle 1; reproduced by checker) | reproduced (checker, cycle 1) |
| 2 | absent_text met only when truly absent | `test_absent_text_and_dom_asserts_are_evaluated` | (unchanged; reproduced by checker) | reproduced (checker, cycle 1) |
| **3** | **dom_asserts met only when selector exists** | `test_dom_asserts_is_met_only_when_the_selector_genuinely_exists` + `test_dom_asserts_is_unmet_when_the_selector_is_absent` | `assertions.py::assert_expected`: `found = selector_exists(session, selector)` -> `found = True` | **before: 3 passed. after: `test_dom_asserts_is_unmet_when_the_selector_is_absent` FAILED — `AssertionError: assert <Outcome.COMPLETED> is <Outcome.ASSERTION_FAILED>`. Reverted -> 3 passed again.** |
| 4 | met expectation -> COMPLETED + per-field evidence | `test_a_met_expectation_keeps_the_run_completed` | (unchanged; reproduced by checker) | reproduced (checker, cycle 1) |
| 5 | bare ASSERT harmless | `test_an_assert_step_with_no_expectation_is_harmless` | (unchanged; reproduced by checker) | reproduced (checker, cycle 1) |
| **6** | **ERRORED outranks earlier unmet assert (true precedence, two steps)** | `test_errored_still_beats_assertion_failed` (rewritten, AT-550) | `execute.py::run_case`'s except-branch: `if assertion_failed: return _result(..., Outcome.ASSERTION_FAILED)` before the `Outcome.ERRORED` return | **before: 2 passed (this test + the restored `test_step_exception_is_errored_not_a_crash`). after: `test_errored_still_beats_assertion_failed` FAILED — `AssertionError: assert <Outcome.ASSERTION_FAILED> is <Outcome.ERRORED>`. Reverted -> 2 passed again.** |
| **7** | **assertion runs still judged (C7) — the judge is called and owns the verdict** | `test_assertion_failed_run_still_reaches_the_judge_and_the_judge_owns_the_verdict` (new, AT-549) | `grade.py::_outcome_verdict`: added an `ASSERTION_FAILED` branch returning a fixed `Result.FAIL` rule-verdict, mirroring the ERRORED/BLOCKED_HITL short-circuits | **before: 1 passed. after: FAILED — `AssertionError: an ASSERTION_FAILED run never reached the judge — assert []`. Reverted -> 1 passed again.** |
| 8 | actuator boundary intact | `test_actuator_chokepoint.py` | (unchanged; reproduced by checker) | reproduced (checker, cycle 1) |
| 9 | line caps hold | `doctor` file-size check | (unchanged; reproduced by checker) | see "Known pre-existing doctor violation" below — the cap violation found is `docs/ARCHITECTURE.md`, a file this unit does not touch |
| **10 (new)** | **absent_text fails safe (unmet), never silently met, on an unreadable page** | `test_absent_text_on_an_unreadable_page_fails_safe_not_silently_met` (new, AT-551) | `assertions.py::body_text`: `except Exception: return None` -> `return ""` (the pre-fix behavior) | manually re-verified by inspection: with `""` restored, `_text_label("", "Invalid credentials", want_present=False)` -> `"Invalid credentials" in ""` is `False` -> `False == want_present(False)` -> `"met"`, which is exactly the bug (a crashed page reading as a clean absent-text pass). The new `is None` branch is what prevents this; the test asserts the `unmet (page unreadable)` label + ASSERTION_FAILED outcome that only the `None` path produces. |
| **11 (new)** | **url probe in `assert_expected` raises nothing (AT-552)** | covered indirectly — `_url_label` wraps the read in try/except; no existing fake makes `page.url` raise, so no new isolating test was added for this one (cheap defensive fix per the brief: "Cheap; do it while you're in the file") | n/a | not isolated by a dedicated test — flagging this honestly rather than claiming coverage that doesn't exist |

**Verified green-before/red-after for rows 3, 6, 7** — full transcripts below.

### Row 3 (AT-548) — before / edit / after / revert

```
$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py::test_dom_asserts_is_unmet_when_the_selector_is_absent tests/test_execute_assertions.py::test_errored_still_beats_assertion_failed tests/test_grade.py::test_assertion_failed_run_still_reaches_the_judge_and_the_judge_owns_the_verdict
...                                                                      [100%]
3 passed in 0.11s

# edit: assertions.py assert_expected(): found = selector_exists(...) -> found = True

$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py::test_dom_asserts_is_unmet_when_the_selector_is_absent
...
>       assert result.outcome is Outcome.ASSERTION_FAILED
E       AssertionError: assert <Outcome.COMPLETED: 'completed'> is <Outcome.ASSERTION_FAILED: 'assertion_failed'>
1 failed in 0.21s

# reverted

$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py::test_dom_asserts_is_unmet_when_the_selector_is_absent tests/test_execute_assertions.py::test_dom_asserts_is_met_only_when_the_selector_genuinely_exists tests/test_execute_assertions.py::test_absent_text_and_dom_asserts_are_evaluated
...                                                                      [100%]
3 passed in 0.10s
```

### Row 6 (AT-550) — before / edit / after / revert

```
# edit: execute.py run_case()'s except-branch:
#   if assertion_failed:
#       return _result(case, session, start, Outcome.ASSERTION_FAILED)
#   (inserted before the existing ERRORED return)

$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py::test_errored_still_beats_assertion_failed
...
>       assert result.outcome is Outcome.ERRORED
E       AssertionError: assert <Outcome.ASSERTION_FAILED: 'assertion_failed'> is <Outcome.ERRORED: 'errored'>
1 failed in 0.21s

# reverted

$ PYTHONUTF8=1 uv run pytest tests/test_execute_assertions.py::test_errored_still_beats_assertion_failed tests/test_execute.py::test_step_exception_is_errored_not_a_crash
..                                                                       [100%]
2 passed in 0.07s
```

### Row 7 (AT-549) — before / edit / after / revert

```
# edit: grade.py _outcome_verdict(): added
#   if result.outcome is Outcome.ASSERTION_FAILED:
#       return _verdict(..., verdict_result=Result.FAIL, provider_id="rule", ...)
#   (mirroring the ERRORED/BLOCKED_HITL short-circuits above it)

$ PYTHONUTF8=1 uv run pytest tests/test_grade.py::test_assertion_failed_run_still_reaches_the_judge_and_the_judge_owns_the_verdict
...
>       assert judge.prompts, "an ASSERTION_FAILED run never reached the judge"
E       AssertionError: an ASSERTION_FAILED run never reached the judge
E       assert []
1 failed in 0.13s

# reverted; git diff --stat src/autotester/stages/execute.py src/autotester/stages/grade.py -> empty (both files byte-identical to before the temp edits)

$ PYTHONUTF8=1 uv run pytest tests/test_execute.py tests/test_execute_assertions.py tests/test_grade.py
..............................                                           [100%]
30 passed in 0.25s
```

## Known pre-existing doctor violation (not introduced by this fix cycle, out of scope to fix)

```
$ uv run autotester doctor
architecture-too-long: docs/ARCHITECTURE.md — 152 lines > 150; move detail to a routed doc
1 violation(s)
```

`docs/ARCHITECTURE.md` was already 3 lines over budget in the *working tree* (152 lines) before
this fix cycle began — `git diff --stat docs/ARCHITECTURE.md` shows `3 insertions(+), 0
deletions(-)` against a HEAD copy that is 149/150 lines, i.e. clean. This is the cycle-1
checker's own contract-amendment landing (the "Contract touch landed with this verdict" section
of `qa/verdicts/at540-assertion-layer.md`: the one-sentence Execution-model addition D-032
authorizes). The brief for this cycle explicitly forbids editing `docs/ARCHITECTURE.md`
("D-032 already authorized this layer; a fix cycle needs no new D-entry"), and this fix cycle's
own diff never touches that file (confirmed: `git diff --stat` below shows only the four files
this manifest lists as changed). Reporting this honestly rather than either fixing a file I was
told not to touch, or silently claiming "doctor: clean" when it isn't. `ruff check` is clean;
every OTHER doctor check (file/function sizes across all changed files, duplicate definitions,
root clutter, qa/issue rows, adapter pytest -q) passes.

`tests/test_execute.py` itself lands at exactly 300/300 after restoring the three tests — right
at the cap, not over it, so no split was required per the brief's rule ("if your fix pushes it
over 300 ... split"). It is a thin margin; the next person touching this file should expect to
split immediately.

## Live browser evidence

Not UI-touching — no surface of our own app changed (changed paths this fix cycle:
`src/autotester/browser/assertions.py`, `tests/test_execute.py`,
`tests/test_execute_assertions.py`, `tests/test_grade.py`). Same as cycle 1: the executor's
assertions are exercised against a browser only through the fakes above; the real-browser path
is the existing `test_run_pathlynks_first_cases.py` set (not re-run in this fix cycle per the
brief — the checker runs the full suite).

## Status: ready-for-check
