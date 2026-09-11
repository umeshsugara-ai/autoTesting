# Manifest — at076-navigation-secret-escape-hatch

**Unit:** AT-076 — a fail-closed lockout with no working escape hatch for navigate targets
**Contract:** `qa/contracts/browser-and-secrets.md` (B2, B3, B6), `qa/contracts/core-invariants.md` (C5)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 3 of max 3 (LAST)
**Dual check:** no
**Issues addressed:** AT-076 (medium), AT-341 (critical, fixed cycle 2), AT-350 (critical, found by
cycle-2 checker's fifth-sink hunt, fixed this cycle)

## Cycle 3 — the cycle-2 checker's adversarial fifth-sink hunt found one more

**Cycle 2 FAILed** (verdict `qa/verdicts/at076-navigation-secret-escape-hatch.md`, commit
`5328d32`): all four of AT-341's named points were confirmed genuinely fixed, but the checker was
explicitly asked to hunt for a fifth sink beyond what cycle 1 traced — and found one. A goto()
failure that is **not** `NavigationRefused` (a real Playwright `net::`/timeout error, which
characteristically embeds the destination it was navigating to) reaches `explore.py`'s
`_already_past_login`/`_seed` generic `except Exception` handlers, folds into
`rt.login_precheck_error`/`rt.seed_error`, and from there into `Crawl.stop_reason` — persisted via
`_finish`/`save_crawl` with no redaction anywhere in that path. Filed as **AT-350** (critical).

**Fixed, taking the checker's own recommended BETTER approach** (its `expected` field named two
options: scrub each call site, or scrub once at the single write site — the latter, because it
covers every future caller "by construction" instead of requiring the next contributor to
remember to audit a new call site):

- `src/autotester/browser/secrets.py` — new `SecretStore.scrub_optional(text) -> str | None`: the
  shared one-liner (`redactor().scrub(text) if text else text`) every exception-derived free-text
  field needs before disk. Extracted because by cycle 3 the same idiom had been hand-written three
  times (`execute.py`, `explore_node.py` ×2) — a fourth call site is a DRY violation, not just a
  missed one, and the extraction also bought back the lines a structural fix costs (see file-cap
  note below).
- `src/autotester/stages/explore.py::_finish` — `stop_reason` is now scrubbed with
  `scrub_optional` at its single write site, before the `Crawl` is built. This covers
  `login_precheck_error`, `seed_error`, AND any future source of `stop_reason` — not enumerated
  call sites.
- `src/autotester/stages/execute.py` / `explore_node.py` — cycle-2's own scrub calls simplified to
  use the new shared helper (no behavior change, just the DRY cleanup that made room for cycle 3's
  fix under the 300-line cap without shaving unrelated comments).
- `tests/test_explore_secret_scrubbing.py` (**new file**, split from `test_explore_error_causes.py`
  once that file crossed the 300-line cap with cycle-3's addition) — the two AT-341 tests moved
  here unchanged, plus a new
  `test_a_seed_failures_exception_message_is_scrubbed_in_the_persisted_crawl`: a real `run_crawl`
  with a monkeypatched `session.goto` raising a `net::`-shaped `RuntimeError` embedding the
  resolved secret, asserting the persisted `Crawl.stop_reason` never carries it.

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

- `uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py tests/test_execute.py tests/test_explore_error_causes.py tests/test_explore_secret_scrubbing.py tests/test_explore.py -q`
  → expected: exit 0
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py tests/test_execute.py tests/test_explore_error_causes.py tests/test_explore_secret_scrubbing.py tests/test_explore.py -q
[all dots, exit 0]

$ uv run pytest -q
[all dots, exit 0] — fully clean, including tests/test_ui_credential_transforms.py (the earlier
concurrent AT-339 session had settled by this cycle; its own tests now pass and it is no longer
uncommitted)
EXIT: 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline) — cycle 3:**

1. **Baseline**: extract + full cycle-1+2+3 uncommitted diff layered on (the new
   `tests/test_explore_secret_scrubbing.py` copied in manually, untracked as of HEAD) → `uv sync`
   → confirmed `autotester.__file__` resolves inside the extract → all touched test files green,
   exit 0.
2. **Mutation D — revert `_finish`'s `scrub_optional` call on `stop_reason`** (back to
   `"stop_reason": rt.stop_reason,`): **exactly the 1 predicted test failed**
   (`test_a_seed_failures_exception_message_is_scrubbed_in_the_persisted_crawl`,
   `zorro-battery-42` visible unmasked in the persisted `Crawl.stop_reason`) — reproducing AT-350
   live.
3. **Restored, then mutation E — make the new shared `SecretStore.scrub_optional` a no-op**
   (`return text` unconditionally): **exactly the 4 predicted tests failed across three files**
   (`test_a_seed_failures_exception_message_is_scrubbed_in_the_persisted_crawl`,
   `test_add_issue_scrubs_a_secret_out_of_the_detail_before_persisting`,
   `test_record_edge_scrubs_a_secret_out_of_the_reason_before_persisting`,
   `test_a_secret_value_inside_an_exception_message_is_scrubbed_before_persisting`) — proving the
   DRY refactor genuinely wires through every caller, not just the ones it was written against.
4. (Cycles 1–2's own mutations on the resolution/domain-scoping logic and the other two
   persistence sinks were already proven in their own cycles and are unchanged by cycle 3 — not
   re-run here, since cycle 3 touched none of that code directly, only the shared helper they now
   call through.)

All gates across all three cycles (resolution-happens-at-all, per-secret domain scope,
`check_destination`'s message, and now three persistence-layer scrubs sharing one helper)
independently proven load-bearing. Extract deleted after each mutation was confirmed and restored
from saved originals; live tree confirmed unchanged throughout.

## Live browser evidence

**Not UI-touching in the route/template sense — no surface changed.** Changed paths:
`src/autotester/browser/secrets.py`, `src/autotester/browser/session.py`,
`src/autotester/stages/explore.py`, `execute.py`, `explore_node.py` (browser-session and crawl-
stage internals, not a UI route), plus test files. Exercised through `FakePage`-backed unit tests
and a real `run_crawl` with a monkeypatched `goto` (the same pattern the pre-existing tests in
`test_browser.py`/`test_explore.py` already use) — a real Chromium session isn't needed to prove
this scrubbing logic, and `test_real_headless_launch_navigates_a_data_url` (real Chromium, skipped
if unavailable) already covers the real-browser path for `check_destination`, unchanged by cycles
2–3.

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
  four sinks two independent checker cycles traced and reproduced (`check_destination`'s message,
  `execute.py::_result`, `explore_node.py::add_issue`/`record_edge`, `explore.py::_finish`'s
  `stop_reason`). The cycle-3 fix chose the structural form (scrub once at each stage's single
  write site, not per-exception-handler) specifically so a *future* call site is covered without
  needing a *third* adversarial hunt — but a genuinely different persistence path this session's
  two checkers did not think to trace would still be a fresh finding, the same discipline this
  whole three-cycle chain has followed throughout.

## Status: ready-for-check
