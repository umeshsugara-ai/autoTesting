# Manifest — at076-navigation-secret-escape-hatch

**Unit:** AT-076 — a fail-closed lockout with no working escape hatch for navigate targets
**Contract:** `qa/contracts/browser-and-secrets.md` (B2, B3, B6), `qa/contracts/core-invariants.md` (C5)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 2 of max 3
**Dual check:** no
**Issues addressed:** AT-076 (medium), AT-341 (critical, found by cycle-1 checker, fixed this cycle)

## Cycle 2 — what the cycle-1 checker found and how it's fixed

**Cycle 1 FAILed** (verdict `qa/verdicts/at076-navigation-secret-escape-hatch.md`, commit
`bb23965`): the fix wired `resolve_for_navigation` ahead of the pre-existing, unaudited
`check_destination`, whose own refusal message embeds the full `url` verbatim — including a
resolved secret, when a secret-bearing navigate target is refused for being outside
`project.allowed_domains`. That unredacted message reaches disk via two sinks:
`stages/execute.py`'s `RawResult.error` and `stages/explore_node.py`'s `record_edge`/`add_issue`.
Filed as **AT-341** (critical).

**Fixed, all four points the checker's `expected` field named:**

1. `src/autotester/browser/session.py::check_destination` — the refusal message now names only
   the already-computed `host` (never secret) or `"an unparseable destination"`, never the raw
   `url`. This is a GENERAL fix, not scoped to the secret-navigation path — every caller benefits,
   because the message was never safe to build from the raw destination in the first place.
2. `src/autotester/stages/execute.py::_result` — `error`/`hitl_prompt` are now scrubbed through
   `session.secrets.redactor()` before ever reaching a `RawResult`, the same boundary `_record`
   already holds for evidence paths — defense-in-depth against ANY exception's message, not only
   `NavigationRefused`.
3. `src/autotester/stages/explore_node.py::add_issue` / `record_edge` — `detail`/`reason` are now
   scrubbed the same way before reaching `CrawlIssue`/`ScreenEdge`.
4. **Regression tests added at all three levels**, per the checker's explicit ask (not just
   `pytest.raises(NavigationRefused)`):
   - `tests/test_browser.py::test_refusal_message_never_embeds_the_raw_destination` — unit-level,
     `check_destination` directly.
   - `tests/test_browser_navigation_secrets.py::test_goto_still_refuses_a_resolved_destination_outside_project_domains`
     — strengthened with a token-bearing value, now asserts the token is absent from both the
     exception message AND `session.state.evidence`.
   - `tests/test_execute.py::test_a_secret_value_inside_an_exception_message_is_scrubbed_before_persisting`
     — a NON-`NavigationRefused` exception (simulating a third-party error echoing page state)
     proves the `_result` scrub is generic, not keyed to one exception type.
   - `tests/test_explore_error_causes.py::test_add_issue_scrubs_a_secret_out_of_the_detail_before_persisting`
     and `test_record_edge_scrubs_a_secret_out_of_the_reason_before_persisting` — direct unit
     tests against `explore_node.add_issue`/`record_edge`.

## What was wrong

A long, legitimate value held in the shared repo-root `.env` (e.g. a project's own login URL) is
matched by the credential guard (`_refuse_unsafe_submission` / `Redactor.is_clean`, by design —
AT-083 scopes this over every `.env` value, declared or not) and refused if typed literally into a
case's navigate target. The refusal's own advice says *"reference it as `{{SECRET:KEY}}`"* — but
that advice was false for a navigate target: `session.goto()` never called `secrets.resolve()`,
only `session.fill()` did. A case author had no working way to navigate to a URL that happened to
be a `.env` value.

## What changed

- `src/autotester/browser/secrets.py` — new `SecretStore.resolve_for_navigation(value) -> str`.
  Unlike `resolve()` (used by `fill()`, which always has a known CURRENT-page host to scope by
  before substitution — AT-007), a navigation target can be the placeholder itself with **no**
  literal host around it (the whole value is a login URL). There is nothing to check a host
  against until AFTER substitution, so the order flips: substitute first (raising `UndeclaredSecret`
  / `MissingSecret` exactly as `resolve()` would for an unknown/absent key), then check the
  **resulting** host against every referenced secret's own declared `domains` — fails closed if the
  destination the value resolves to isn't one the secret is scoped to.
- `src/autotester/browser/session.py::goto` — now calls `resolve_for_navigation` when the target
  contains a `{{SECRET:KEY}}` placeholder, then runs the **existing** `check_destination` call
  against the *resolved* value exactly as it would a plain literal URL — so `project.allowed_domains`
  still binds regardless of what a secret's own `domains` list says. Two independent gates, not one:
  a secret with stale/wrong `domains` still can't navigate the browser outside the project.
- `tests/test_secrets.py` — 6 new tests for `resolve_for_navigation` directly (bare placeholder,
  placeholder embedded in a literal URL, plain value passthrough, undeclared key, missing value,
  wrong-domain scope).
- `tests/test_browser_navigation_secrets.py` (**new file**, split from `test_browser.py` to stay
  under the 300-line cap) — 5 tests at the `BrowserSession.goto()` level: bare placeholder resolves,
  embedded placeholder resolves, evidence never carries the raw resolved value, `check_destination`
  still refuses a resolved destination outside `allowed_domains` even when the secret's own domains
  would permit it (defense-in-depth), a misbound secret (`domains` not covering where its own value
  resolves to) is refused, and a plain URL passes through untouched.

## How to verify (commands + expected)

- `uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py tests/test_execute.py tests/test_explore_error_causes.py -q`
  → expected: exit 0, 69 passed (15 + 5 + 30 + 9 + 10)
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py tests/test_execute.py tests/test_explore_error_causes.py -q
.....................................................................    [100%]  (69 passed)

$ uv run pytest -q
[all dots, exit 0] — one PRE-EXISTING unrelated failure seen once mid-cycle
(tests/test_mutation_check.py::test_the_sandbox_is_removed_when_the_run_finishes, a known
concurrent-session temp-dir race, passes clean in isolation) and one unrelated in-flight
concurrent session's own file (tests/test_ui_credential_transforms.py, AT-339, not touched by
this unit) — neither reproduces on a clean re-run excluding that file; full suite including it
is exit 0 after the concurrent session's own unit settled.
EXIT: 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline) — cycle 2, all FOUR defense layers now, tested
independently:**

1. **Baseline**: extract + full cycle-1+cycle-2 uncommitted diff layered on → `uv sync` →
   confirmed `autotester.__file__` resolves inside the extract → all touched test files green,
   exit 0.
2. **Mutation A — revert `check_destination`'s host-only message fix**: **exactly the 2 predicted
   tests failed** (`test_refusal_message_never_embeds_the_raw_destination`,
   `test_goto_still_refuses_a_resolved_destination_outside_project_domains`), reproducing the
   original AT-341 leak live (`SUPERSECRETTOKEN123` visible in the assertion diff).
3. **Restored, then mutation B — revert `execute.py::_result`'s scrub**: **exactly the 1
   predicted test failed** (`test_a_secret_value_inside_an_exception_message_is_scrubbed_before_persisting`,
   `hunter2` visible in the assertion diff) — proving this defense-in-depth layer independent of
   `check_destination`'s own fix (this test uses a non-`NavigationRefused` exception).
4. **Restored, then mutation C — revert `explore_node.py`'s `add_issue`/`record_edge` scrubs**:
   **exactly the 2 predicted tests failed** (`test_add_issue_scrubs_a_secret_out_of_the_detail_before_persisting`,
   `test_record_edge_scrubs_a_secret_out_of_the_reason_before_persisting`, both showing
   `zorro-battery-42` unmasked).
5. (Cycle 1's mutations 1–3 on the resolution/domain-scoping logic itself were already proven in
   cycle 1 and are unchanged by cycle 2 — not re-run here, since cycle 2 touched none of that code.)

All four gates (resolution-happens-at-all, per-secret domain scope, `check_destination`'s
message, and the two persistence-layer scrubs) independently proven load-bearing. Extract deleted
after each mutation was confirmed and restored from saved originals; live tree confirmed
unchanged throughout.

## Live browser evidence

**Not UI-touching in the route/template sense — no surface changed.** Changed paths:
`src/autotester/browser/secrets.py`, `src/autotester/browser/session.py` (browser-session
internals, not a UI route), plus test files. Exercised through `FakePage`-backed unit tests
(the same pattern the pre-existing `fill()`/`goto()` tests in `test_browser.py` already use) —
a real Chromium session isn't needed to prove the resolution/scoping logic, and
`test_real_headless_launch_navigates_a_data_url` (real Chromium, skipped if unavailable) already
covers the real-browser path for `check_destination`, unchanged by this unit.

## What this unit does not claim

- Does not change `fill()` or its CURRENT-page-host scoping (AT-007) — untouched, still covered
  by its own existing tests.
- Does not weaken the credential guard on the UI side (`_refuse_unsafe_submission`) — that already
  exempted `{{SECRET:KEY}}`-containing values before this unit (verified by reading
  `helpers.py::_refuse_unsafe_value`); this unit only makes the advertised escape hatch actually
  work at execution time.
- Does not claim every possible navigation-target shape is covered — only that a placeholder,
  bare or embedded in a literal URL, resolves correctly and stays within both the secret's own
  declared domains and the project's `allowed_domains`.
- Does not claim every exception-message sink in the whole codebase is now scrubbed — only the
  three the cycle-1 checker traced and reproduced (`check_destination`'s message,
  `execute.py::_result`, `explore_node.py::add_issue`/`record_edge`). A different, untraced sink
  carrying a raw secret would be a fresh finding, the same discipline this whole chain follows.

## Status: ready-for-check
