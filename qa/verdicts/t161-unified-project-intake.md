# Checker verdict — t161-unified-project-intake

**Date:** 2026-09-10  
**Project root:** `D:\autoTesting`  
**Implementation judged:** `4c09990` (`feat(ui): add unified project intake`)  
**Manifest:** `qa/manifests/t161-unified-project-intake.md`  
**Cycle checked:** 1  
**Verdict:** FAIL

## Contract maintenance folded before judgement

- Added UI criterion U12 for the single bare-or-taught intake, canonical `Project`/`SecretRef`/
  `Source` persistence, repeated-row validation/idempotence, overwrite refusal and cross-project
  credential-key ownership.
- Added browser/secrets criterion B10 for all-secret guarding and atomic `.env` batch persistence.
- Tightened core invariant C5 so newly submitted raw values become secrets before any same-request
  validator can echo or persist another field.
- These are additive safety/product criteria; U1-U11, B1-B9 and the prior C5 clauses were not weakened.

## Independently re-run verification

All commands ran in a detached worktree at exact commit `4c09990`.

- `uv --cache-dir .work/uv-cache run pytest -p no:cacheprovider --basetemp=.work/pytest-t161-primary -q`
  — exit 1. The only failure was
  `tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered`, because the historical
  commit's `.goal/dashboard.html` did not reflect its `.goal/goal.json`; two platform skips occurred.
  The manifest explicitly excludes unrelated `.goal/*` runtime artifacts, so this does not create a
  T-161 defect, but the maker's stated full-suite result is not reproducible from the commit alone.
- `uv --cache-dir .work/uv-cache run pytest -p no:cacheprovider --basetemp=.work/pytest-t161-unit tests/test_ui_project_intake.py -q`
  — exit 0, 14 passed.
- Targeted schema/core/secrets/browser/T-161 suite — every test outside the same excluded dashboard
  assertion passed.
- `uv --cache-dir .work/uv-cache run ruff check src tests scripts` — exit 0, `All checks passed!`.
- `uv --cache-dir .work/uv-cache run autotester doctor` — exit 0, `doctor: clean`.
- `git diff --check 4c09990^ 4c09990` — exit 0.
- `git ls-files` secret-path scan — no tracked `.env`, profile, `.work` or run-artifact paths.
- Stage vendor-import scan — no direct Anthropic/Google imports in `src/autotester/stages`.

## Independent adversarial evidence

`qa/evidence/browser-t161-unified-project-intake-2026-09-10-checker/report.json` records 17/17
headed-Chromium checks using fake values only. The checker interacted with the real form and proved:

- every intake category coexists in one form and both credential/source repeaters add rows;
- a rich project persists canonical refs and five source kinds while raw values occur only in the
  repo-root `.env`;
- duplicate statements collapse to one content-addressed row and non-video sources offer no Analyze;
- re-onboarding, unset cross-project key collisions, a secret smuggled into an eval, and an invalid
  second credential row all refuse without partial artifacts;
- no unexplained application console errors occurred. Expected 400-resource messages came from the
  deliberate refusal probes; blocked Google Fonts requests are recorded with their URLs and are an
  environment/network condition, not an application error.

`atomicity.json` independently proves every duplicate existing `.env` line rotates, a simulated
`os.replace` failure preserves the previous file byte-for-byte, and no temp file is orphaned.

The additional headed-browser attack in `secret-echo-reproduction.json` fails. A fake
hostname-shaped value was submitted simultaneously as `credential_value`, `credential_domains` and
`allowed_domains`. `app.py:223` invokes `_require_reachable_base_url` before the credential batch is
parsed and before `_guard_intake` builds the union guard; `helpers.py:73-75` interpolates the submitted
domain list into the 400 detail. The raw submitted credential therefore rendered verbatim in the
browser refusal. The project and `.env` remained unwritten, so atomicity held while confidentiality
did not. Screenshot: `pre-guard-secret-echo.png`.

## Scoreboard

- UI/browser criteria: **21/22 met**. U1-U12 and B1-B9 hold; B10 fails.
- Core invariants: **8/9 hold**. C1-C4 and C6-C9 hold; tightened C5 fails.
- Issue written: **AT-284** (critical, open).

## Required fix direction

Build the temporary guard from the complete submitted credential batch before any validator can echo
another submitted field, or make every pre-guard refusal generic. Pin the hostname-shaped overlap as
a response/log/artifact non-disclosure regression and re-submit on cycle 2.

VERDICT: FAIL  
SCOREBOARD: 21/22 criteria met, 8/9 invariants hold  
FAILURES (if any):
- [B10/C5] sev: critical · pre-guard URL/domain validation echoes a newly submitted hostname-shaped credential in the 400 response · guard the complete submitted batch before echo-capable validation or make the refusal generic · issue: AT-284  
LIVE-BROWSER: `qa/evidence/browser-t161-unified-project-intake-2026-09-10-checker/`  
ISSUES-WRITTEN: AT-284  
EXPLANATION: The unified intake, typed persistence, repeated rows, ownership checks and atomic `.env` writer otherwise survived independent code, disk and headed-browser attacks. Cycle 1 cannot pass because a raw credential reaches a rendered refusal before the new all-secret guard exists.
