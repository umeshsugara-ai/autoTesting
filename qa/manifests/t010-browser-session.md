# Manifest — t010-browser-session

**Contract:** qa/contracts/browser-and-secrets.md (criteria B5–B9; B2/B3 at the fill boundary) + qa/contracts/core-invariants.md
**Goal task:** T-010 (`user_value: normal`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** AT-021 (S3, carried from T-005 — fixed at the `doctor.run()` path this cycle)

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-010 browser/session.py: headed Playwright Chromium …"` → `no gate — no retired features (rule)`.

## What changed

- `pyproject.toml` / `uv.lock` — `playwright==1.62.0` added (the one runtime dependency this unit needs).
- `src/autotester/browser/session.py` (new, 180 lines) — `BrowserSession`:
  - **B5** `launch_options`: `launch_persistent_context` with `user_data_dir=profiles/<slug>/`, `headless = not project.headed` (headed by default).
  - **B6** `check_destination` → `NavigationRefused` unless `host_of(url)` is non-empty and `Project.allows_domain(host)`; `goto()` checks before touching the page. Reuses `secrets.host_of`, so the AT-007 fail-closed cases (backslash, userinfo, empty) are refused here too.
  - **B2/B3 at the boundary** `fill()`: a `{{SECRET:KEY}}` value is resolved against **`page.url` — the browser's current host, never the step's intended URL** (the verdict's note on AT-007); the input is tagged `data-autotester-secret` and remembered in `state.secret_locators`.
  - **B7** `screenshot()`: injects `MASK_CSS` (`-webkit-text-security: disc; color: transparent` on tagged inputs) before capture; files land in the run dir as `NN-label.png`; returns `Evidence(kind=screenshot, masked=True)` with a run-relative path.
  - **B8** `request_human(prompt)` → `HitlRequest(outcome=BLOCKED_HITL)` stored on `state.hitl` for the executor to surface.
  - **B9** `close()`: closes only this session's context and stops only its own Playwright driver; idempotent. No `taskkill`/`pkill` anywhere (test greps `src/`).
  - Every evidence string passes `secrets.redactor().scrub` (B4).
- `src/autotester/doctor.py` — **AT-021**: `check_ledger` now runs before `check_generated_fresh`, and `check_generated_fresh` reports `stale-generated: cannot regenerate: <ExcType>` instead of raising when the ledger is broken. Test asserts on `doctor.run()`, not the check in isolation.
- `docs/ARCHITECTURE.md` — concept→file row for `browser/session.py`; Status updated (136 lines).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated (new module → map).
- `tests/test_browser.py` (new, 11 tests) — B5–B9 without a browser via a fake page; **one real Chromium test** (headless launch, refuses `evil.test`, takes a masked screenshot) — it **ran, not skipped**, on this machine (Playwright's Chromium 1234 is in the local cache).
- `tests/test_ledger.py` — `test_doctor_run_reports_a_broken_ledger_without_a_traceback` (AT-021).

## How to verify (commands + expected)

- `uv run pytest tests/test_browser.py -q -rs` → exit 0, 11 passed, 0 skipped (if Chromium is missing on the checker's machine the last test skips with a stated reason — that is acceptable per the contract's Verify note)
- `uv run pytest -q` → exit 0 (81 tests)
- `uv run ruff check src tests` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `grep -rnE "taskkill|pkill|killall" src/` → no output (B9)
- AT-021: `printf '{not json\n' > docs/FEATURES.jsonl.bak` — do NOT overwrite the real ledger; instead run `uv run pytest tests/test_ledger.py -q -k broken_ledger_without_a_traceback` → passes
- `wc -l docs/ARCHITECTURE.md` → 136 (≤ 150)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_browser.py -q -rs
...........                                                              [100%]
$ uv run pytest -q
........................................................................ [ 88%]
.........                                                                [100%]
$ uv run ruff check src tests
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- `Project.allows_domain` (schema, pre-existing) checks `allowed_domains` only — its docstring says "base host or allowed domain" but the base URL's host is not added automatically. Not this unit's code; flagged so you can file it if you judge it a defect (a project whose `base_url` host is outside `allowed_domains` would refuse its own base URL — arguably correct fail-closed behaviour).
- No live host is contacted except by the real-Chromium test, which only asserts refusal of `evil.test` and captures a blank page; no Pathlynks credential exists in the repo.
- The executor stage (T-040) will compose these methods; there is no step-runner here by design (B5–B9 only).

## Status: checked-PASS

Verdict: `qa/verdicts/t010-browser-session.md` (Cycle checked: 1, PASS, 7/7 + 8/8; commit 67e2588). Goal task T-010 closed by the checker. `user_value: normal` — no ledger row required.
