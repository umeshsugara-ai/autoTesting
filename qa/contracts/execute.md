# Contract — EXECUTE stage (T-040, T-045)

**Covers:** goal tasks T-040, T-045. **Owner:** /checker. **Criticality:** MEDIUM — the stage
every later regression run depends on, but not itself user-facing yet.
**Depends on:** `core-invariants.md` (all), `browser-and-secrets.md` (B1-B9, all already built).

## Purpose

Run one `Case`'s steps against a real, already-started `BrowserSession` and produce a
`RawResult` — what happened, evidence-first, with **no PASS/FAIL judgement**. Judgement is
`grade.py`'s job (T-041), given only the rubric and this stage's evidence. This is the "executor
only observes" line in the T-040 goal task note, made literal.

## Criteria

### E1 — No judgement, only observation
`stages/execute.py::run_case` never assigns PASS/FAIL/INCONCLUSIVE. Its only outputs are the
three `Outcome` values: `COMPLETED` (every step ran without raising), `ERRORED` (an exception
mid-step), `BLOCKED_HITL` (a step needed a secret the project does not have — see E3). An
`Action.ASSERT` step is executed as evidence capture (screenshot + current URL) only; the stage
never compares the captured evidence against `Step.expected` itself.

### E2 — Every step composes existing session primitives
`run_case` dispatches each `Step.action` to a `BrowserSession` method
(`goto`/`click`/`fill`/`select_option`/`upload`/`wait_for`) — it never touches
`session.page` directly for a mutating action. New `BrowserSession` methods added for this unit
follow the existing pattern: one action, evidence recorded via `_record`, secret-safe (any value
that looks like `{{SECRET:KEY}}` goes through `SecretStore.resolve`, never logged raw). A
screenshot is captured after every step, labeled with the step's order and action, so a human or
`grade.py` can review the run frame by frame.

### E3 — A missing secret blocks for a human, it does not fail the run
If resolving a step's `{{SECRET:KEY}}` value raises `MissingSecret` (the project declared the key
but `.env` has no value — the OTP/2FA case B8 anticipates), `run_case` returns
`Outcome.BLOCKED_HITL` with `hitl_prompt` naming what is needed, not `ERRORED`. Any other
exception (selector not found, navigation refused, timeout, …) is `ERRORED` with `error` naming
the exception type and message — never an unhandled traceback out of `run_case`.

### E4 — RawResult is complete and persisted
The returned `RawResult` carries `case_id`, `outcome`, `duration_s`, and every `Evidence` the
session recorded (already redacted/masked per B4/B7 — `run_case` does not re-implement masking).
`ProjectStore.save_result(run_id, result)` writes it to
`projects/<slug>/runs/<run_id>/<case_id>.json`; `ProjectStore.save_run(run)` writes the `Run`
envelope to `.../runs/<run_id>/run.json`. Both round-trip through `read_json`/`write_json` (C6 —
no new file format).

### E5 — write_policy is respected
`run_case` performs exactly the actions in `case.steps` — it never invents an extra click,
submit, or navigation. A `write_policy=READ_ONLY` project is protected by never running a case
whose steps were authored to mutate data, which is an EXPAND-stage (T-070) and human-review
(T-065) concern, not this stage's; `run_case` itself has no branch on `write_policy` because it
has no way to add or remove actions from what the case already specifies.

## No-fire list

- Vision/LLM-based judgement of `visual_signal` (belongs to `grade.py`, T-041).
- The agent fallback path (write→run→read→edit a generated script) — that is T-080; this unit is
  the script-first / direct-steps path only.
- `EvidenceKind.DB` / read-only Mongo assertions — that is T-045's own follow-on once
  `PATHLYNKS_MONGO_URI` is declared as a `SecretRef`; T-040 does not need it to close.
- Retrying a step automatically on transient failure (no retry logic required yet).
- CI/scheduled triggers (`Trigger.CI`/`SCHEDULE`) — `Run.trigger` exists in the schema already;
  wiring a trigger source is a later phase.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-040 (execute stage), the follow-on named in
  `browser-and-secrets.md`'s amendment log ("belongs to a future `execute` contract, not B1-B9").
- 2026-09-04 · routine · recorded the `at044-entry-case-profile-isolation` fix (AT-045, ledger
  F-030): `run_case` now calls the new `BrowserSession.settle()` (networkidle + 500ms grace,
  both independently exception-suppressed) after a CLICK step, before its screenshot, so
  evidence capture sees the post-transition state rather than mid-transition. E2 ("composes
  existing session primitives") and E5 ("never invents an extra click/submit/navigation") both
  hold unchanged — `settle()` is a passive wait called through `session.settle()`, not a new
  step. Checker-PASSed cycle 1 (`qa/verdicts/at044-entry-case-profile-isolation.md`). Residual
  evidence-timing flakiness for pathlynks live reruns is tracked separately as AT-046 (open,
  medium) — not fixed by this amendment. Found by sweep: shipped with zero contract-side trace
  until now (AT-048).
