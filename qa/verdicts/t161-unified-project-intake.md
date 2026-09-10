# Checker verdict — t161-unified-project-intake

**Date:** 2026-09-10
**Project root:** `D:\autoTesting`
**Implementation judged:** `4c09990` + `d92af87`
**Manifest:** `qa/manifests/t161-unified-project-intake.md`
**Cycle checked:** 2
**Verdict:** PASS

## Independently re-run verification

- `uv --cache-dir .work/uv-cache run pytest -p no:cacheprovider --basetemp=.work/pytest-t161-checker-cycle2 -q` — exit 0, 100% complete with two platform skips.
- Focused T-161/UI/browser/core/schema suite — exit 0; all collected tests passed, with one platform skip.
- Focused atomic-replace, duplicate-line rotation and hostname-secret regression trio — exit 0, 3 passed.
- `uv --cache-dir .work/uv-cache run ruff check src tests scripts` — exit 0, `All checks passed!`.
- `uv --cache-dir .work/uv-cache run autotester doctor` — exit 1 only for the untracked root `AGENTS.md`, which the manifest explicitly excludes as an unrelated runtime artifact; no implementation/design violation was reported.
- `git diff --check 4c09990^ 4c09990` and `git diff --check d92af87^ d92af87` — both exit 0.
- Tracked-secret-path scan found no tracked `.env`, profile, `.work` or run-artifact path (`.env.example` is the expected template, not a secret file).

## Cycle-2 security re-check

At `src/autotester/ui/app.py:244-245`, the intake now constructs `_guard_intake(project, sources,
values)` before `_require_reachable_base_url(base_url, domains)`. The guard therefore includes all
newly submitted values before the reachability helper can produce its hostname/domain-specific
refusal. The pinned regression and a fresh headed-browser attack both returned 400 without echoing
the hostname-shaped credential and without creating a project or changing `.env`.

The `.env` writer also survived independent failure probes: it validates the whole batch before
writing, writes through a same-directory mode-0600 temporary file, flushes/fsyncs, atomically
replaces the target, removes its temp file on failure, preserves the prior bytes when replacement
fails, and replaces every duplicate line for a rotated key.

## Independent Mode D

Fresh headed Chromium evidence is recorded at
`qa/evidence/browser-t161-unified-project-intake-2026-09-10-checker-cycle2-primary/report.json`.
Eight of eight interactions passed: both repeaters, rich canonical persistence, source-kind action
scoping/idempotence, re-onboarding refusal, unset cross-project key ownership, exact AT-284 refusal,
and raw-secret placement. The browser recorded zero application console errors; blocked Google Font
requests and the three deliberate HTTP 400 probes are disclosed in the report.

## Scoreboard

- UI/browser criteria: **22/22 met** — U1-U12 and B1-B10.
- Core invariants: **9/9 hold** — C1-C9.
- AT-284 moved `open → fixed`; this checker did not close the manifest or goal.

VERDICT: PASS
SCOREBOARD: 22/22 criteria met, 9/9 invariants hold
FAILURES (if any):
- none
LIVE-BROWSER: `qa/evidence/browser-t161-unified-project-intake-2026-09-10-checker-cycle2-primary/`
ISSUES-WRITTEN: AT-284 -> fixed
EXPLANATION: Cycle 2 closes the critical pre-guard disclosure: the new-value union guard now runs before the echo-capable reachability validator, and the exact attack is blocked without partial state. The complete suite, focused security probes, atomicity checks and fresh headed-browser run support every tightened U12/B10/C5 clause and all prior criteria.
