# Manifest — t172-run-trace
**Contract:** qa/contracts/run-trace.md (DRAFT, RT1-RT7) + qa/contracts/core-invariants.md
**Goal task:** T-172
**Date:** 2026-09-25
**Fix cycle:** 1 of max 3
**Dual check:** no (goal task criticality is `high`, not `critical`)
**Issues addressed:** none
**Executor:** claude-sonnet-subagent
**Executor rationale:** schema/redaction/security-adjacent unit (RT6 touches the secret guard) — stays on a Claude subagent per the "never delegate ... security units" rule; no delegation attempted.

## What changed

New files:
- `src/autotester/schema/trace.py` — `StageSpan`/`LLMSpan` pydantic models (`extra="forbid"`), the on-disk shape of a trace line.
- `src/autotester/core/trace.py` — `TraceWriter` (the only place a span is built + appended, RT5) and `read_spans` (the UI's read path, RT7).
- `src/autotester/core/pricing.py` — `estimate_cost(label, in_tokens, out_tokens)`, a small honestly-partial per-model $/1k-token table; unknown label → 0.0, never a raise.
- `tests/test_run_trace.py` — RT1-RT7 driver, 9 tests, fully offline (mock stage runners + `MockProvider`, temp project dirs).

Edited in place:
- `src/autotester/core/paths.py:110` — added `ProjectPaths.run_trace(run_id)` next to `run_dir`, per the architecture table's "every path on disk lives in core/paths.py".
- `src/autotester/core/redact.py:218-224` — added `Redactor.assert_clean(text)`: the RT6 hard gate, reusing the Redactor's own loaded values so a caller never has to hold raw secrets separately.
- `src/autotester/providers/base.py:16,40-46,59-131` — **confined to record()/span emission as instructed**: `self.trace: TraceWriter | None` attribute; `see_video`/`act`/`judge` gain optional `prompt_file`/`fed_id` kwargs (pure plumbing, raise-stub bodies unchanged); `record()` extended with `prompt_file`/`fed_id`/`latency_s`/`retries`/`fallback_hops` and now calls `self.trace.record_llm(...)` when a writer is attached — the single choke point (RT5). No other part of the file touched (no refactor of `label`, `available`, etc).
- `src/autotester/providers/anthropic.py`, `gemini.py`, `langchain_fallback.py`, `mock.py` — thread the new `prompt_file`/`fed_id` kwargs through, measure real `latency_s` via `time.perf_counter()` around the actual model call, and (langchain_fallback only) pass a real `fallback_hops` = the index of the tier that answered (0 = no fallback).
- `src/autotester/stages/orchestrate.py:16,55-71,110-119` — `StageContext` gains `trace: TraceWriter | None = None`, auto-built in `__post_init__` from `store.paths.run_trace(run_id)` when not given (every run is traced by default, RT1); `_record()` — the one place every checkpoint transition already passes through — writes the stage's `StageSpan` when the checkpoint reaches a terminal status (`done`/`failed`/`skipped`), so a pending/running checkpoint never gets one (RT3's "a stage that never ran produces no span").
- `src/autotester/stages/orchestrate_runners.py:70-74` — `make_ingest_runner`'s closure now does `provider.trace = ctx.trace` before calling `ingest_video`, so INGEST's real LLM call joins the run's own trace file (the one stage `run_or_resume` actually drives today).
- `src/autotester/stages/ingest.py:261-262`, `grade.py:172-173`, `expand.py:125-126`, `analyze_video.py:111-112` — pass `prompt_file=<the stage's own PROMPT_NAME constant>` and `fed_id=<source.id / result.case_id / flow.id>` into their `see_video`/`judge`/`act` calls.
- `docs/MAP.md` — regenerated via `uv run autotester map` (generated section only, per doctor's `stale-generated` check; not hand-edited).

**New module reason (C3):** two new modules (`core/trace.py`, `core/pricing.py`) rather than folding into an existing file — `core/redact.py` is the redaction concept (extended, not duplicated) and `core/paths.py` is the path concept (extended, not duplicated); the trace-span shape and the cost table are each a new concept with no existing home, and both stay well under the 300-line cap.

## How to verify (commands + expected)
- `uv run pytest tests/test_run_trace.py` → expected: exit 0, 9 passed (this is T-172's `done_check`)
- `uv run pytest tests/test_run_trace.py tests/test_orchestrate.py tests/test_orchestrate_runners.py tests/test_providers.py tests/test_ui_report.py tests/test_ui_report_no_runs.py` → expected: exit 0, 43 passed
- `uv run ruff check src tests scripts` → expected: exit 0, "All checks passed!"
- `uv run autotester doctor` → expected: exit 0, "doctor: clean"

## Actual outputs (from maker's own run)

```
$ PYTHONUTF8=1 uv run pytest tests/test_run_trace.py tests/test_orchestrate.py tests/test_orchestrate_runners.py tests/test_providers.py tests/test_ui_report.py tests/test_ui_report_no_runs.py
...........................................                              [100%]
43 passed, 1 warning in 3.20s

$ uv run ruff check src tests scripts
All checks passed!

$ PYTHONUTF8=1 uv run autotester doctor
doctor: clean
```

**Full `uv run pytest` (whole suite): NOT RUN — RAM ceiling.** Free RAM stayed at 1.0-1.1 GB
(`[math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory/1MB,1)`) for most of
the build; it recovered to 5.1 GB after the throwaway-copy verification finished, but at that
point `Get-CimInstance Win32_Process` showed two live `pytest.exe` processes rooted at
`D:\autoTesting\.worktrees\at110-approval-signing\.venv\Scripts\pytest.exe` (a sibling worktree's
run in progress) — the RAM rule's "no other pytest process from a D:/autoTesting path is running"
condition was not met, so the full suite was correctly skipped rather than run concurrently with
another worktree's suite. **Checker to run the full suite.**

## Capability coverage (each new claim -> its isolating falsification)

All eight falsifications below were reproduced in a throwaway copy at
`%TEMP%\claude\d--autoTesting\<session>\scratchpad\rt-verify\` (outside the worktree; `src`,
`tests`, `scripts`, `pyproject.toml`, `uv.lock` copied from the working tree, `.venv` built fresh
in the copy) — never against the bound worktree. Baseline asserted green (`9 passed`) before every
edit; each edit reverted from the pristine worktree file immediately after its red run, with the
suite re-confirmed green before moving to the next row.

| capability (RT#) | the check that covers it | the falsifying edit | observed (pasted runner output) |
|---|---|---|---|
| RT1 — one trace.jsonl per run, incrementally written, never overwriting a sibling run's file | `test_two_runs_of_a_project_get_two_distinct_nonempty_trace_files` | `core/trace.py::TraceWriter._append` — deleted the `mkdir` + `with open("a")...write(...)` block, leaving only the `mkdir` | BEFORE: `9 passed in 2.82s`. AFTER: `assert trace_a.exists() and trace_b.exists()` → `AssertionError: assert (False)` — `.../runs/run_a/trace.jsonl` does not exist. REVERTED → `9 passed in 21.26s`. |
| RT2 — every span's `trace_id` equals `RunState.run_id`, never re-minted | `test_every_span_trace_id_equals_the_runs_own_run_id` | `core/trace.py::TraceWriter.record_stage` — `trace_id=self.trace_id` → `trace_id="minted-" + self.trace_id` | BEFORE: `9 passed`. AFTER: `assert all(line["trace_id"] == "run_tid" for line in lines)` → `assert False`. REVERTED → `9 passed in 1.15s`. |
| RT3 — exactly one span per stage that actually ran, in stage order, no others | `test_a_run_produces_exactly_one_stage_span_per_stage_that_ran` | `stages/orchestrate.py::_record` — `if checkpoint.status in ("done","failed","skipped") and ctx.trace is not None:` → `if ctx.trace is not None:` (also fires on the `running` transition) | BEFORE: `9 passed`. AFTER: `assert [s.stage for s in spans] == custom_stages` → `AssertionError: ... At index 1 diff: MODEL != EXECUTE — Left contains 3 more items`. REVERTED → `9 passed in 1.62s`. |
| RT4 — every LLM-call span carries the case/verdict id it fed, non-null when the call produced one | `test_a_fixture_stage_of_2_judge_calls_and_1_act_call_makes_3_llm_spans` | `providers/base.py::record` — inside the `self.trace.record_llm(...)` call, `fed_id=fed_id` → `fed_id=None` | BEFORE: `9 passed`. AFTER: `assert span.fed_id is not None` → `AssertionError: assert None is not None`. REVERTED → `9 passed in 1.00s`. |
| RT5 — `Provider.record()` is the only site that appends an LLM-call span (no second recorder) | `test_provider_base_record_is_the_only_site_that_appends_an_llm_span` (static scan of `src/autotester/**/*.py` for `.record_llm(` outside `providers/base.py`) | `stages/grade.py::grade` — added one extra line after the real `judge.judge(...)` call: `judge.trace.record_llm(...) if judge.trace else None` (a second, independent call site) | BEFORE: `9 passed`. AFTER: `assert offenders == []` → `AssertionError: ... Left contains one more item: '...\\stages\\grade.py'`. REVERTED → `9 passed in 0.98s`. |
| RT6a — every span passes through `Redactor.scrub` (+ the `assert_clean` hard gate) before touching disk | `test_every_span_is_redacted_before_it_is_persisted` | `core/trace.py::TraceWriter._append` — `clean = self._redactor.scrub(line); self._redactor.assert_clean(clean)` → `clean = line` (both steps skipped in one hunk) | BEFORE: `9 passed`. AFTER: `assert secret_value not in raw` → `AssertionError: ... 'sk-fake-9f2c7a1b' is contained here: id":"case-sk-fake-9f2c7a1b",...`. REVERTED → `9 passed in 2.27s`. |
| RT6b — `Redactor.assert_clean` is a real hard gate, not a no-op | `test_redactor_assert_clean_raises_on_a_surviving_secret` | `core/redact.py::Redactor.assert_clean` — body `assert_no_raw_secrets(text, self._values)` → `pass` | BEFORE: `9 passed`. AFTER: `raise AssertionError("assert_clean did not raise on a raw secret")` fired (the `try/except ValueError` found no exception). REVERTED → `9 passed in 1.06s`. |
| RT7 — the run-view panel is a live VIEW over `trace.jsonl`, not a cached/second copy | `test_the_run_view_panel_reflects_a_mutated_trace_file` | `ui/routes_report.py::_trace_card` — `f"<td>{s.duration_s:.2f}s</td></tr>"` → `f"<td>1.00s</td></tr>"` (ignores the parsed value) | BEFORE: `9 passed`. AFTER: `assert "999.00s" in after` → `AssertionError: assert '999.00s' in "...<td>1.00s</td>..."`. REVERTED → `9 passed in 1.01s`. |

No `UNVERIFIED`/debt rows — every claim in "What changed" above has a covering row. `retries`/
`cost` fields exist on `LLMSpan` and are exercised by RT4's test (non-negative, present) but carry
no dedicated falsification row of their own: `retries` is honestly always `0` today (no provider
in this repo has a retry-on-failure loop yet — falsifying "retries" would mean falsifying a
constant, not a mechanism), and `cost` is a thin pure function (`core/pricing.estimate_cost`)
already exercised indirectly by RT4/RT6's runs; a dedicated mutation of its lookup table would
falsify the pricing constants, not this unit's tracing mechanism.

## Live browser evidence
Not UI-touching in the browser-automation sense, but the run-view panel IS a UI surface
(`src/autotester/ui/routes_report.py`, matches the `**/routes/**` UI-surface glob) — however:

**SKIP — RAM ceiling, no browser launched this cycle.** Free RAM was 1.0-1.1 GB for nearly the
entire build (the RAM RULE's targeted-tests-only threshold), and by the time it recovered to
5.1 GB a sibling worktree (`at110-approval-signing`) had two live pytest processes running,
leaving no safe headroom to also launch a Playwright/Chromium instance without risking that
sibling build. The RT7 capability itself IS verified — `test_the_run_view_panel_reflects_a_mutated_trace_file`
calls `ui/routes_report.py::_trace_card` directly (the exact function `run_view` composes into the
page) against a real `ProjectStore`/temp dir and proves it re-reads the file on every call — but
that is a function-level check, not a rendered-DOM-in-a-real-browser check. The checker should run
Mode D (live browser) on `/projects/demo/runs/<run_id>` once RAM allows, confirming the "Trace"
card renders with real stage/LLM rows.

## Status: ready-for-check
