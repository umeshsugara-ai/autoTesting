# Verdict — t010-browser-session

**Date:** 2026-09-03
**Cycle checked:** 1
**Contract:** qa/contracts/browser-and-secrets.md (B5-B9; B2/B3 at the fill boundary) + qa/contracts/core-invariants.md (C1-C8)
**Manifest:** qa/manifests/t010-browser-session.md (Fix cycle: 1)

## Re-run evidence (all commands re-executed by /checker, not pasted)

```
$ uv run pytest tests/test_browser.py -q -rs
...........                                                              [100%]
11 passed, 0 skipped in 0.79s   <- confirms the real-Chromium test (last test in the file)
                                    actually launched a live browser on this machine rather
                                    than pytest.skip()-ing (0 skipped is the tell).

$ uv run pytest -q
........................................................................ [ 88%]
.........                                                                [100%]
(84 passed — full suite, includes test_core.py / test_secrets.py / test_ledger.py)

$ uv run ruff check src tests
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest tests/test_core.py tests/test_secrets.py -q
................................. [100%]

$ grep -rnE "taskkill|pkill|killall" src/ tests/
(only match: tests/test_browser.py itself, which asserts the pattern is ABSENT
from src/ — no offending code found in src/)

$ uv run pytest tests/test_ledger.py -q -k broken_ledger_without_a_traceback
.                                                                        [100%]

$ wc -l docs/ARCHITECTURE.md
135 docs/ARCHITECTURE.md   (<= 150; single, non-dangling Status block at the end)

$ git ls-files | grep -E "\.env$"
(no output — .env not tracked)
```

## Adversarial checks performed (read the code, not just the test suite)

- **AT-007 domain confusion, fill() vs goto()** — `browser/session.py::fill()` resolves
  `{{SECRET:KEY}}` against `self.page.url` (the browser's live current host at the moment of
  typing), never the caller's intended destination. `check_destination`/`goto()` refuse before
  navigation; `fill()` is independently guarded by `SecretStore.resolve` → `secrets.py::host_of`,
  which fails closed (returns `""`) on any backslash or userinfo (`user@host`) in the URL — the
  exact AT-007 case (`https://evil.test\@pathlynks.test`). Verified `host_of` source directly
  (secrets.py:70-84), not just the docstring's claim. A page that has "drifted" to
  `evil.test` after navigation (test: `test_fill_refuses_secret_when_page_has_drifted_off_domain`)
  raises `SecretScopeError`/`UndeclaredSecret` before `page.fill()` is ever called — confirmed
  `s.page.filled == {}` after the raise.
- **Mask selector match** — `fill()` sets the attribute via
  `el.setAttribute('data-autotester-secret', '1')` where `MASK_ATTR = "data-autotester-secret"`;
  `MASK_CSS = "[data-autotester-secret] { ... }"` uses the identical literal string. Confirmed by
  reading both constants side by side in session.py:25-29 and the call site at line 145 — same
  string, no typo.
- **screenshot() masks before capture** — `page.add_style_tag(content=MASK_CSS)` is called before
  `page.screenshot(...)` in `screenshot()` (session.py:155-161); the CSS only has effect on inputs
  already tagged by a prior `fill()` call, which happens at fill-time, so by the time any
  screenshot fires, tagged fields are already masked. No evidence of masking happening after
  capture.
- **close() safety** — reproduced independently (not just trusting the manifest's test): a
  `BrowserSession` that never called `start()` (both `_context` and `_playwright` are `None`) had
  `close()` called twice with no exception (see console output above — "never-started close x2
  OK"). The existing unit test additionally exercises the started-then-closed-twice path with
  fake context/playwright doubles, asserting exactly one real `close()`/`stop()` call each. `close()`
  never calls a process-wide kill; confirmed by the `grep` above finding no `taskkill`/`pkill`/
  `killall` anywhere in `src/`.
- **Real-Chromium test genuinely exercised a live browser** — re-ran `tests/test_browser.py -rs`
  myself; output shows `11 passed, 0 skipped`. Since `test_real_headless_launch_navigates_a_data_url`
  is the only test in the file gated by `pytest.importorskip`/an internal `pytest.skip()` on
  browser-launch failure, its presence in the passed count (not skipped) proves Chromium actually
  launched on this machine, refused `evil.test`, and wrote a non-empty screenshot file.
- **AT-021 doctor.run() ordering** — read `doctor.py::run()` directly: the check tuple is
  `(check_file_sizes, check_function_sizes, check_file_names, check_root_clean,
  check_duplicate_definitions, check_ledger, check_generated_fresh, check_architecture_budget,
  check_docs_routed)` — `check_ledger` precedes `check_generated_fresh`, confirmed by source, not
  by the manifest's prose. `check_ledger` catches ledger-load exceptions and returns a
  `ledger-invalid` Violation instead of raising (doctor.py:134-137); `check_generated_fresh`
  independently catches `render_snapshot` exceptions and reports `stale-generated:
  cannot regenerate: <ExcType>` rather than raising (doctor.py:117-122). Re-ran the dedicated
  regression test `test_doctor_run_reports_a_broken_ledger_without_a_traceback`, which asserts on
  `doctor.run()` directly (not `check_ledger` in isolation) with a corrupted `FEATURES.jsonl` —
  passed, both `ledger-invalid` and `stale-generated` present in the violation set, no traceback.
- **ARCHITECTURE.md** — 135 lines (≤150), one `## Status` section at the end, no duplicated or
  dangling status block found on inspection.

## Criteria scoreboard

- B5 (headed by default, persistent profile) — MET: `launch_options` sets
  `headless = not project.headed`, `user_data_dir=profiles/<slug>/`; test confirms both headed and
  headless branches.
- B6 (bounded navigation) — MET: `check_destination` raises `NavigationRefused` before `page.goto`
  is touched; reuses `host_of` so AT-007 hosts are refused too.
- B7 (masked evidence capture) — MET: style injected before screenshot; `Evidence(masked=True)`
  with run-relative path.
- B8 (HITL for OTP) — MET: `request_human` returns `HitlRequest(outcome=BLOCKED_HITL)` stored on
  `state.hitl`.
- B9 (cleanup never harms the developer's browser) — MET: `close()` touches only its own context/
  driver, idempotent, no process-wide kill anywhere in `src/`.
- B2/B3 at the fill boundary — MET: resolution is against `page.url`, fails closed on parser-
  divergent hosts, secret never reaches `state.evidence` (scrubbed via `Redactor`).
- Core invariants C1-C8 — no violations found: `doctor` clean, `ruff` clean, file/function sizes
  within budget, no vendor SDK imports in this unit, `.env` ungitted, artifacts remain
  human-editable files.

## VERDICT

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met (B5,B6,B7,B8,B9,B2,B3-at-boundary), 8/8 core invariants hold
FAILURES (if any):
- none
ISSUES-WRITTEN: none
EXPLANATION: All B5-B9 criteria and the B2/B3 fill-boundary rules are independently evidenced by
re-run tests and direct source reading, including adversarial checks on the AT-007 domain-
confusion fix, mask-selector consistency, screenshot-before-capture ordering, close() safety on
an unstarted/double-closed session, absence of any process-wide kill in src/, and AT-021's
doctor.run() ordering/no-traceback behavior on a broken ledger. Full suite (84 tests), ruff, and
doctor all pass clean. T-010 is user_value normal — per CLAUDE.md's maker rule, no ledger row or
reasoning-ask is required; goal task closed directly.
```
