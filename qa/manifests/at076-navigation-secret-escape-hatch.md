# Manifest — at076-navigation-secret-escape-hatch

**Unit:** AT-076 — a fail-closed lockout with no working escape hatch for navigate targets
**Contract:** `qa/contracts/browser-and-secrets.md` (B2, B3, B6)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-076 (medium)

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

- `uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py -q`
  → expected: exit 0, 49 passed
- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_browser.py tests/test_browser_navigation_secrets.py tests/test_secrets.py -q
.................................................                        [100%]  (49 passed)

$ uv run pytest -q
[all dots, exit 0]
EXIT: 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv,
never the live tree (AT-101 discipline).** Given this touches the credential boundary — a hard
boundary per this project's own CLAUDE.md — all three defense layers were mutated and tested
**independently**, not just the one whose test happens to fail first:

1. **Baseline**: extract + uncommitted diff layered on (including the new untracked test file,
   copied in manually since `git apply` only carries tracked-file diffs) → `uv sync` → confirmed
   `autotester.__file__` resolves inside the extract → 49 passed, exit 0.
2. **Mutation 1 — disable `goto`'s resolution call entirely** (`real = url`, no
   `resolve_for_navigation` call at all): **exactly the 3 predicted goto-level tests failed**
   (bare placeholder, embedded placeholder, misbound-domain test — each for a different reason,
   all traceable to the missing resolution), the other 46 stayed green.
3. **Restored, then mutation 2 — remove `resolve_for_navigation`'s own host-vs-`ref.domains`
   check** (the per-secret scoping clause): **exactly the 2 predicted tests failed** — one at the
   `SecretStore` unit level (`test_resolve_for_navigation_refuses_a_secret_scoped_to_a_different_domain`)
   and one at the `BrowserSession` integration level
   (`test_goto_refuses_a_secret_scoped_to_a_different_domain_than_it_resolves_to`) — the other 47
   stayed green.
4. **Restored, then mutation 3 — remove `goto`'s `check_destination` call on the resolved value**:
   **3 failures**, including the two PRE-EXISTING B6 tests
   (`test_goto_refuses_before_touching_the_page`, `test_real_headless_launch_navigates_a_data_url`
   — confirming this call is load-bearing for the ORIGINAL behavior too, not only this unit's new
   one) plus the new defense-in-depth test
   (`test_goto_still_refuses_a_resolved_destination_outside_project_domains`).

All three gates (resolution-happens-at-all, per-secret domain scope, project-level
`check_destination`) independently proven load-bearing. Extract deleted after each mutation was
confirmed and restored from the saved originals; live tree confirmed unchanged throughout
(`git status --porcelain` on the four touched paths, before and after).

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

## Status: ready-for-check
