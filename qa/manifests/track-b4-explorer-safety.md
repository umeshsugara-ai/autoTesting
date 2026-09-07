# Manifest — track-b4-explorer-safety
**Contract:** qa/contracts/core-invariants.md (C1, C2, C3) — pending X5-X9 in `qa/contracts/explore.md`, written by the checker once T-143 (B3, the crawl stage) exists to receive it
**Goal task:** T-142
**Date:** 2026-09-07
**Fix cycle:** 1 of max 3
**Dual check:** no
**Plan:** plan.md §5 "B4 — safety layer, pure", authorised by D-016

## Why this unit exists before the crawl stage
plan.md's own sequencing puts B4 before B3 deliberately: *"B4 (safety) lands before B3 (crawl)
so a crawler never exists in this repo, even for one unit, without brakes."* This unit is that
guard, built and tested against fixtures — the crawl stage that actually calls it is T-143, not
yet built.

## What changed
Full diff in commit `ca7b842`. Pure logic — no browser, no provider, no I/O.

- **New** `stages/explore_safety.py`:
  - `deny_reason(el, policy) -> str | None` — implements the D-016 matrix in one function.
    Checked in this order: never-click (logout/sign-out, at **every** `write_policy` including
    `ALLOW_WRITES`) → unnamed non-link control (denied by default; `click_unnamed` opts out) →
    the destructive-name deny-list (disabled only under `ALLOW_WRITES`) → form-submit (refused
    only under `READ_ONLY`).
  - `link_is_safe(el, project) -> bool` — same-domain hrefs only; `javascript:`/`mailto:`/`tel:`
    and protocol-relative (`//host/...`) hrefs are never safe.
  - `classify_request(url, project, policy) -> str` — `"first_party"` / `"ignored"` (a declared
    analytics/tracker host) / `"noise"` (anything else third-party). Reuses
    `browser.secrets.host_of`, so the same AT-007 backslash-userinfo host-spoofing fix that
    protects secret typing also protects request classification (a spoofed host can never read
    as first-party).
  - `DialogBreaker` — per-node dialog count; `record()` returns `True` once a node exceeds
    `policy.dialog_repeat_limit`; `reset()` clears one node.
  - `policy_for(project, **overrides)` — builds a `SafetyPolicy` from the project's
    `write_policy`, with any field overridable (documented escape hatch: a per-project
    `deny_patterns` extension for control names in another language — English-only detection is
    a stated limit, not silently hidden).
- `tests/test_explore_safety.py` (new, 27 tests): the full write-policy matrix, table-driven,
  over the exact control set plan.md names (`Delete`, `Save`-submit, `Log out`, unnamed button,
  unnamed link, `"Deliverables"`, `"Send"`) × the three policies; link safety including the
  AT-007-style userinfo-spoofing probe (`evil.test\@www.vidysea.com`); the three request buckets;
  the breaker tripping, counting per-node (not globally), and resetting.

## Judgement calls
- **Never-click wins over every other check, including `ALLOW_WRITES`.** Tested explicitly
  (`test_deny_matrix[...ALLOW_WRITES-log_out-True]`) — there is no policy setting that makes the
  explorer click a logout control. This is the one line D-016 does not let a human loosen through
  configuration; it would need a code change.
- **An unnamed non-link control is denied even under `ALLOW_WRITES`**, unless `click_unnamed` is
  explicitly set. Clicking blind is exactly how the prior attempt discovered a Delete button — an
  icon-only button with no accessible name gets refused and reported (a later unit's job), not
  gambled on.
- **"Deliverables" must not match "deliver"** — every deny pattern is word-bounded (`\bword\b`),
  proven by a dedicated test rather than trusted from reading the regex.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest tests/test_explore_safety.py -q` → expected:
  exit 0, 27 pass
- `docker compose exec autotester uv run pytest -q` → expected: `461 passed, 1 skipped` (up from
  434 after T-141)
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: `All checks passed!`
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`

## Status: ready-for-check
