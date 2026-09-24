# Verdict — t172-run-trace

**Cycle checked:** 1
**Checker:** fresh, read-only, Mode A + Mode D
**Date:** 2026-09-25

## VERDICT: FAIL

## What I re-ran

- Diff: `git -C <wt> merge-base HEAD master` -> `a953bc5cb86243c8d467a064ad1068ac3cf58296`; full
  `git diff <base>..HEAD --stat` and content diff. Every touched file matches the manifest's "What
  changed"; no deletions/renames of existing functions/exports/tests/config keys outside what the
  manifest describes.
- Throwaway copy at `%TEMP%\claude\...\scratchpad\t172-copy` (outside the worktree), `uv sync` fresh.
- Targeted verify, re-run in the copy:
  - `uv run pytest tests/test_run_trace.py tests/test_orchestrate.py tests/test_orchestrate_runners.py tests/test_providers.py tests/test_ui_report.py tests/test_ui_report_no_runs.py` -> **43 passed**
  - `uv run ruff check src tests scripts` -> **All checks passed!**
  - `uv run autotester doctor` -> **doctor: clean**
  - Full `uv run pytest` (whole suite): **environment-deferred** (RAM ~1.8GB free ceiling per instructions) — targeted suite above covers the unit.
- 8-row capability coverage, each reproduced in the copy (baseline green -> single-hunk edit ->
  red-for-the-named-reason -> revert -> green), all single-hunk edits to files listed in "What
  changed" (no CONTRACT_MISMATCH).
- My own adversarial RT6 wiring probe (below) — the reason for the FAIL.
- Live browser check (Mode D) via playwright MCP against a real `uvicorn` server.

## FAILURES

**1. sev: critical — RT6 / core-invariants C5 (credential boundary): the real/default wiring never
redacts anything.**

`core/trace.py:26`:
```python
self._redactor = redactor or Redactor({})
```
`stages/orchestrate.py:76` (the *only* production call site that builds a `TraceWriter` —
`StageContext.__post_init__`):
```python
self.trace = TraceWriter(self.store.paths.run_trace(self.run_id), self.run_id)
```
No `redactor=` is ever passed here, so every trace this unit's own orchestrator wiring produces is
written with an **empty** `Redactor({})` — `scrub()` has no values to replace and `assert_clean()`
iterates an empty list, so it can never raise. Nothing else added by this diff closes the gap:
`orchestrate_runners.make_ingest_runner` only does `provider.trace = ctx.trace` (no redactor);
`ingest.py`/`grade.py`/`expand.py`/`analyze_video.py` only pass `prompt_file`/`fed_id`, never a
redactor. A real `Redactor` carrying actual `.env` values only ever comes from
`SecretStore.redactor()` (`browser/secrets.py:222`), used elsewhere at `stages/execute.py:101` and
`stages/explore.py:230` — this pattern is never reused for the trace writer anywhere in this diff.

**I reproduced this concretely** (script: adversarial probe below) using the exact wiring this unit
ships (`StageContext` built with no `trace=` kwarg, then `provider.trace = ctx.trace` exactly as
`make_ingest_runner` does it): a secret value embedded in `fed_id` (the same fixture shape the
unit's own RT6a test uses, `f"case-{secret_value}"`) landed **raw, unredacted, on disk** in
`trace.jsonl`.

The unit's own two RT6 tests do not catch this because both manually construct
`TraceWriter(..., redactor=Redactor({...}))` — a populated redactor supplied by the test, never
built from the real wiring path. They prove the *mechanism* (scrub-then-assert_clean) works when
given real secret values; they never prove the *wiring* ever gives it any. Nothing in the manifest
discloses this as a known residual/deferred item — it's presented as covered.

**Fix direction:** `StageContext` (or whichever caller eventually drives a real run) must build its
`TraceWriter` from the project's actual `SecretStore.redactor()` — e.g. accept a `secrets:
SecretStore | None` on `StageContext` and pass `redactor=secrets.redactor()` into the
`TraceWriter(...)` in `__post_init__` (mirroring `stages/execute.py:101`'s existing pattern) — and
never silently fall back to an empty `Redactor({})` for a writer that will hold real span data
network-callers can feed. At minimum, if wiring truly isn't ready yet, the manifest must disclose
this as an explicit, named residual rather than claiming RT6 is closed.

## CAPABILITY-COVERAGE: 8/8 reproduced

- RT1 — reproduced: deleting the write block in `TraceWriter._append` (core/trace.py) failed
  `trace_a.exists() and trace_b.exists()` (`AssertionError: assert (False)`).
- RT2 — reproduced: `record_stage`'s `trace_id=self.trace_id` -> `"minted-" + self.trace_id` failed
  the trace_id-equality assertion.
- RT3 — reproduced: dropping the terminal-status guard in `orchestrate.py::_record` failed the
  exact-stage-list assertion (`running` transitions also spanned; 4 items vs 3 expected).
- RT4 — reproduced: `providers/base.py::record`'s `fed_id=fed_id` -> `fed_id=None` failed
  `span.fed_id is not None`.
- RT5 — reproduced: adding a second `judge.trace.record_llm(...)` call site in `stages/grade.py`
  failed the static offender-scan assertion (`offenders == []`).
- RT6a — reproduced: skipping scrub in `_append` (`clean = line`) failed the secret-not-in-raw
  assertion — the raw value literally visible in the persisted `fed_id`.
- RT6b — reproduced: no-opping `Redactor.assert_clean` (body -> `pass`) failed "did not raise on a
  raw secret".
- RT7 — reproduced: hardcoding the duration cell in `ui/routes_report.py::_trace_card` failed the
  mutated-value assertion.

All 8 were single-hunk edits to files named in "What changed"; all reverted cleanly, suite
re-confirmed green (`9 passed`) after each. No CONTRACT_MISMATCH cells.

## My adversarial RT6 wiring probe

Script (run in the throwaway copy, using `MockProvider` + the real `StageContext`/`run_or_resume`
wiring, **no manually-supplied redactor** — i.e. exactly what a real orchestrated run gets today):

```python
provider = MockProvider(model="mock", responses={"agent": [{"steps": []}]})

def ingest_runner(ctx, prev_ref):
    provider.trace = ctx.trace  # exactly orchestrate_runners.make_ingest_runner's own line
    provider.act(f"do something with {SECRET}", object,
                 prompt_file="p.md", fed_id=f"case-{SECRET}")
    ...

ctx = StageContext(store=store, run_id="run_probe", runners={StageName.INGEST: ingest_runner})
run_or_resume(project, ctx)  # ctx.trace auto-built by __post_init__ with NO redactor
```

Result — `trace.jsonl` contents:
```
{"kind":"llm_call", ... "fed_id":"case-sk-real-DEADBEEF12345", ...}
```
`SECRET = "sk-real-DEADBEEF12345"` was found verbatim in the persisted file:
**LEAK CONFIRMED: raw secret found in trace.jsonl via the default StageContext wiring.**

## LIVE-BROWSER (Mode D)

Seeded a scratch `AUTOTESTER_ROOT` with project `demo` + run `run_ui_demo`; `trace.jsonl` written
via the unit's own `TraceWriter`, this time **with an explicitly-populated `Redactor`** (matching
the unit's own test pattern, not the broken default) holding one real secret bound to `fed_id`.
Started `uv run uvicorn autotester.ui.app:app --host 127.0.0.1 --port 8033` from the worktree with
that `AUTOTESTER_ROOT`. Drove a real Chromium instance via the playwright MCP tools to
`/projects/demo/runs/run_ui_demo`:

- HTTP 200; Trace card rendered with a stage row (`ingest`/`done`/`3.00s`) and an LLM row
  (`agent`/`anthropic:claude-sonnet-5`/`1.42s`/`$0.0010`).
- `document.body.innerHTML.includes(<the raw secret>)` -> `false` (confirmed via
  `browser_evaluate`).
- Console messages: 0 errors, 0 warnings (`browser_console_messages`).
- Evidence written: `qa/evidence/browser-t172-run-trace-2026-09-25-checker/report.json`.
- Server stopped after the check (confirmed connection refused on re-probe).

The UI panel itself is correctly built — a genuine read-only view over `trace.jsonl`, no second
store, and it renders nothing raw when the file it reads is actually redacted. The leak is entirely
upstream of this page, in how (or whether) `TraceWriter` gets a real `Redactor` in the first place.

## RT7 stated gap

The maker's disclosed gap ("RT7 is only function-level tested") does not itself block PASS — the
contract's own RT7 falsification ("mutate a fixture run's trace.jsonl ... reload the run view ...")
is satisfied at the function level by `test_the_run_view_panel_reflects_a_mutated_trace_file`, and
this check's own Mode D run today closes the DOM-level gap the maker flagged: the card renders
correctly in a real browser with no raw secret in the DOM. RT7 is not a reason for this FAIL.

## Merge note

T-175 also edits `providers/base.py` (per orchestrator's note) — not evaluated here; this verdict
judges only t172-run-trace's own diff against `master`.

## EXPLANATION

The trace mechanism itself — schema, `TraceWriter`, the RT1/RT2/RT3/RT4/RT5/RT7 plumbing, and the
UI's read-only view — is well-built and all 8 capability-coverage rows reproduce cleanly. But RT6,
the criterion flagged for special adversarial care, fails in the actual production wiring: the only
call site that builds a `TraceWriter` (`StageContext.__post_init__`) never threads a real
`SecretStore`-backed `Redactor` into it, defaulting instead to `Redactor({})`, which redacts
nothing. This is reproducible today with the exact wiring the unit ships (confirmed above) and is
not disclosed anywhere in the manifest as a residual. For a unit whose whole point is a credential-
boundary-adjacent redaction gate (C5), this is a FAIL, not a warning.
