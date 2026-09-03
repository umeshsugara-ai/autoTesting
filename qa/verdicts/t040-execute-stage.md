# Verdict — t040-execute-stage

**Date:** 2026-09-03
**Cycle checked: 1**
**Contract:** qa/contracts/execute.md (E1-E5, new this cycle) + qa/contracts/core-invariants.md (C1-C8) + qa/contracts/browser-and-secrets.md (B1-B9, dependency, already PASSed)

## New-contract skepticism pass (required — this contract and this code were written the same cycle)

Read `qa/contracts/execute.md` before reading any code. Its central design claim: `run_case`
deliberately never compares captured evidence against `Step.expected` for `ASSERT` steps — it
only takes a screenshot — deferring all PASS/FAIL judgement to a future `grade.py` (T-041).

Verdict on the contract itself: **sound, not a weakening dressed up as an architecture decision.**
`core-invariants.md` C7 already states, project-wide and pre-existing this cycle, "the executor
never grades itself: `RawResult` records observation, `Verdict` records judgement, and they are
produced by different components." E1 is not inventing a new looser rule to let this unit pass —
it is restating an invariant that already bound this unit before any code existed. Confirmed by
reading `src/autotester/schema/flowspec.py:71-82`: `Step.expected: ExpectedState` exists on the
schema already, and `grep -rn "expected" src/autotester/stages/execute.py` returns nothing —
the field is deliberately untouched, not silently dropped. A contract written to match code it
also introduces would be suspect if it *loosened* a standing rule to fit; here it *narrows* scope
to exactly what C7 already required. No criteria-weakening gap found.

The no-fire list's other exclusions (vision/LLM judgement, agent-fallback path, `EvidenceKind.DB`,
retry logic, CI triggers) are all genuinely out of T-040/T-045's stated scope per the goal task and
`browser-and-secrets.md`'s own amendment log, which named the Mongo/DB case as a future
`execute`-contract follow-on before this cycle existed. Not self-serving carve-outs.

## Mode A check — every command re-run myself, not trusted from the manifest

- `uv run pytest tests/test_execute.py -q` → `......` (6 passed), matches claim.
- `uv run pytest -q` → 72-dot band + 31-dot band = 103 passed, exit 0. Matches manifest's "103
  tests (was 97 before this unit: +6)".
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 139 (≤150, C2 holds). Confirmed the file's concept→file table
  carries a row for `stages/execute.py::run_case` and the Status line moved execute from Next to
  Built, Next now names `grade.py` — matches the manifest's described diff.
- `grep -n "taskkill\|pkill\|killall" src/autotester/browser/session.py` → no output (exit 1 from
  grep = no match = B9 still holds).
- `uv run autotester ledger relitigation "T-040 stages/execute.py: script-first runner producing
  RawResult + Evidence"` → "no gate — no retired features (rule)", matches the manifest's
  relitigation-gate claim.

## E1 — PASS

Read `src/autotester/stages/execute.py` in full (79 lines). `run_case` returns only
`Outcome.COMPLETED` / `ERRORED` / `BLOCKED_HITL` — no PASS/FAIL/INCONCLUSIVE symbol exists in the
module. `Action.ASSERT` maps to `lambda session, step: None` in the `_ACTIONS` table (line 43);
the subsequent `session.screenshot(...)` call after every step (line 53) fires for ASSERT the same
as any other action — evidence-only, no comparison, as designed. `Step.expected` is never read
(confirmed above).

## E2 — PASS

`run_case` dispatches every step through `_ACTIONS[step.action](session, step)` — a table of
calls to `BrowserSession` methods (`goto`/`click`/`fill`/`select_option`/`upload`/`wait_for`);
`session.page` never appears in `stages/execute.py`. Read `src/autotester/browser/session.py:155-175`:
the three new methods (`select_option`, `upload`, `wait_for`) follow the existing `click`/`fill`
pattern exactly — one `self.page.locator(...)` call, then `self._record(...)` for evidence. `fill`
(pre-existing, unchanged) still owns the only secret-resolution path (`self.secrets.resolve` at
line 142) via `PLACEHOLDER_RE`; the new methods don't introduce a second path, so B2's placeholder
discipline isn't duplicated or bypassed. A screenshot is captured after every step in `run_case`,
labeled `step<NN>-<action>` — confirmed in `test_completed_run_composes_session_methods_and_screenshots_every_step`,
which asserts 5 screenshots for 5 steps including the ASSERT.

## E3 — PASS

`run_case` catches `MissingSecret` first → `Outcome.BLOCKED_HITL` with `hitl_prompt=str(exc)`;
any other `Exception` → `Outcome.ERRORED` with `error=f"{type(exc).__name__}: {exc}"`; the
`except Exception` clause is second so an unrelated exception can't masquerade as blocked. Read
`src/autotester/browser/secrets.py:130,167`: `MissingSecret`'s message names only the declared key
string — there is no value to leak because the key has none loaded, so `hitl_prompt` cannot carry a
credential. `test_step_exception_is_errored_not_a_crash` and
`test_missing_secret_blocks_for_a_human_instead_of_erroring` both pass and assert the correct branch
is taken, including that a later step never runs after a mid-step exception.

## E4 — PASS

`RawResult` (schema/run.py:38-49) carries `case_id`, `outcome`, `duration_s`, `error`,
`hitl_prompt`, `evidence: list[Evidence]` — all populated by `_result()` in execute.py, including
`evidence=list(session.state.evidence)`, i.e. whatever the session already recorded (masked at
source per B4/B7 — `run_case` does no re-masking of its own, matching the criterion's "does not
re-implement masking"). `ProjectStore.save_run`/`save_result` (project_store.py:62-69) are thin
wrappers over `write_json` writing to `runs/<run_id>/run.json` and `runs/<run_id>/<case_id>.json`
respectively — no new file format, C6 holds. `load_results` on an unknown run returns `[]` (not an
exception) — verified by `test_load_results_for_an_unknown_run_is_empty_not_an_error`, which
passed on my own re-run.

## E5 — PASS (by construction, as the manifest claims — verified, not assumed)

`run_case`'s only actions are exactly `case.steps` in `case.steps` order (the `for step in
sorted(case.steps, ...)` loop, dispatch table, no other browser call anywhere in the function
body) — confirmed by reading the full 79-line file; there is no code path that adds a click,
submit, or navigation beyond what the case specifies, and no `write_policy` read anywhere in
`stages/execute.py` or `browser/session.py`'s new methods. The criterion is honest about what it
does NOT claim (no branch on `write_policy` — deferred to T-070/T-065 per the no-fire list), which
matches what the code actually does rather than overclaiming enforcement it doesn't perform.

## C1-C8 — hold

`uv run pytest -q` (schema/core/store tests included) passes; `uv run autotester doctor` clean
(C2/C3/C4 — no `*_v2.py`-style file, `stages/` is a genuinely new package with a stated reason in
the manifest, not a duplicate concept); `git ls-files | grep -E "\.env$"` — not re-run this cycle
since no `.env`-adjacent file was touched (manifest correctly notes this, and `browser-and-secrets.md`
already carries this check for its own units); ruff clean; no vendor SDK import in
`src/autotester/stages/` (`grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/`
returns nothing, checked). `RawResult` inherits `schema.base.Artifact` per C1 (confirmed:
`class RawResult(Artifact)`, schema/run.py:38). All 8 invariants hold.

## Issue ledger

No issues addressed (correctly — this is a new unit, manifest states "Issues addressed: none").
No new issues found; nothing to write to `qa/issues.jsonl`.

## Goal task T-040

`.goal/goal.json` T-040: deps `T-010`, `T-020` both `status: "done"` — dependency gate satisfied.
`done_check` is `uv run pytest tests/test_execute.py -q`, which passes (6/6). Task status is
`pending` going into this check, correctly not self-closed by the manifest — flipping it to `done`
is this verdict's job per the checker/goal wiring, done below since this is a PASS.

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 8/8 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: All five execute.md criteria (E1-E5) are evidenced directly in the 79-line
stages/execute.py and the three new BrowserSession methods, re-verified by independently
re-running every command in the manifest (103/103 tests, ruff clean, doctor clean,
ARCHITECTURE.md 139 lines, no taskkill/pkill, relitigation gate clear) rather than trusting the
pasted output. The one design claim flagged for extra scrutiny — ASSERT steps are evidence-only,
with PASS/FAIL judgement deferred entirely to a future grade.py — was checked against
core-invariants.md C7, which already required exactly this separation before this cycle's code
existed; E1 restates a standing invariant rather than inventing a looser one to fit the code, so
this is a sound architectural boundary, not a self-certified weakening. No issues found.
```
