# Contract — browser session and credential handling

**Covers:** goal tasks T-010 (`browser/session.py`) and T-011 (`browser/secrets.py`).
**Owner:** /checker. **Criticality:** T-011 is CRITICAL — it is the control that keeps
credentials out of models, logs, and artifacts.
**Depends on:** `core-invariants.md` (all criteria apply, C5 especially).

## Purpose

Drive a real, visible browser through a target product on behalf of the tester, authenticated,
without ever exposing the credentials to a model or writing them to disk outside `.env`.

## Criteria — T-011 `browser/secrets.py` (build this first)

### B1 — Loading
- Loads `projects/<slug>/.env` into a `SecretStore` keyed by the `SecretRef[]` declared in `project.json`.
- A declared key missing from `.env` raises a named error identifying the key; it never falls back
  to an empty string or an environment variable from another project.
- A key present in `.env` but not declared in `project.json` is ignored and reported, not used.

### B2 — Placeholders only, in every direction
- `resolve(step_value, host)` accepts `{{SECRET:KEY}}` and returns the real value **only** when
  `host` is within that `SecretRef`'s `domains`; otherwise it raises.
- A value returned by `resolve` is never stored, logged, or returned to a caller that persists it.
- Any string headed for a provider passes `core.redact.assert_no_raw_secrets` first; a raw secret
  value in a prompt raises rather than being masked-and-sent.

### B3 — Domain scoping is enforced, not advisory
- A secret whose `domains` do not include the current page host cannot be resolved, even when the
  host is otherwise in the project's `allowed_domains`.
- Navigating outside `allowed_domains` is refused by the session.

### B4 — Evidence is clean
- `Redactor` built from the loaded store masks every secret value in logs and artifacts.
- Screenshots mask inputs whose field carries a `secret_key` before capture (see B7).

**Verify:** `uv run pytest tests/test_secrets.py -q` exits 0, covering: missing key, undeclared key,
wrong-host refusal, correct-host resolution, prompt gate, redaction of a resolved value.

## Criteria — T-010 `browser/session.py`

### B5 — Real visible browser by default
- Launches Chromium headed when `Project.headed` is true (the default); headless only on explicit request.
- Uses a persistent profile at `profiles/<slug>/` so an interactive login survives to later runs.

### B6 — Bounded navigation
- Refuses to navigate to a host outside `Project.allowed_domains`, raising a named error.

### B7 — Evidence capture with masking
- Captures screenshots to the run directory; before each capture, inputs bound to a `secret_key`
  are masked so the rendered image cannot contain a credential.
- Produces `Evidence` records (schema) with `masked=True` and run-relative paths.

### B8 — Human-in-the-loop for OTP
- When a flow needs a one-time code, the session surfaces a `blocked_hitl` state carrying a prompt
  for the human, rather than guessing, retrying, or failing silently.

### B9 — Cleanup does not harm the developer's own browser
- Teardown closes only the contexts this session opened, identified by its own `user_data_dir`.
- No process-wide `taskkill`/`pkill` of Chrome anywhere in the codebase.
  (Brain recipe `selenium-browser-cleanup-targeted.md`: a naive kill destroyed a developer's open tabs.)

**Verify:** `uv run pytest tests/test_browser.py -q` exits 0. Tests that need a real browser are
marked and may be skipped when Playwright browsers are not installed, but the domain-refusal,
masking, and cleanup-scope tests must run without a browser.

## Out of scope for these units

Real Pathlynks credentials, live login against a production host, and any write to a real account.
Those belong to T-030 and require the human gate. These units are proven against a local fixture
page and mocks.

## No-fire list

- Absence of Gemini/Anthropic providers (later tasks).
- Absence of a UI (T-100).
- Cross-browser support beyond Chromium (not required by any criterion).
- Performance of browser startup.
