# Manifest — at054-live-watch-slowmo
**Contract:** qa/contracts/docker.md (D1/D6 — local dev machine only, host-bound ports)
**Goal task:** none (issue-fix unit, user-reported live-demo gap)
**Date:** 2026-09-06
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** none filed (found and fixed live, same session, no ledger gap — see below)

## What changed
- `src/autotester/browser/session.py::launch_options` — reads
  `AUTOTESTER_SLOW_MO_MS` (default `"0"`, parsed as int) and passes it as Playwright's
  own `slow_mo` launch option. Unset/0 is byte-for-byte today's behavior (no default
  change); a human exports a positive value before `docker compose up` to pad every
  browser operation, so a run watched live over noVNC is actually visible instead of
  completing in under a second.
- `docker-compose.yml` — `AUTOTESTER_SLOW_MO_MS=${AUTOTESTER_SLOW_MO_MS:-0}` added to the
  `autotester` service's `environment:` block, sourced from the host shell, defaulting to
  `0` when unset (unchanged behavior for anyone who doesn't opt in).

## How it was found
The user asked to watch a run happen live via the noVNC view and reported "ye tho run hi
nhi ho rha live prr" (it isn't running live) — the run genuinely executed (confirmed via
its verdict.json), but at `duration_s: 0.94` for the whole two-step case, it finished
before a human could see anything happen on screen. Not a broken live view — a real UX gap
in a synchronous, full-speed-only run path with no way to slow it down for observation.

## How to verify (commands + expected)
- `docker compose exec autotester uv run pytest -q` → expected: exit 0, all tests pass
- `docker compose exec autotester uv run ruff check src tests scripts` → expected: exit 0
- `docker compose exec autotester uv run autotester doctor` → expected: `doctor: clean`
- Real end-to-end: `export AUTOTESTER_SLOW_MO_MS=1500 && docker compose up -d`, then
  `curl -X POST http://localhost:8010/projects/vidysea-erp/run`, then read the new run's
  `case_*.json` → expected: `duration_s` visibly higher than the ~0.94s unpadded baseline,
  and the case's `verdict.json` still comes back a real PASS (slow_mo pads Playwright
  operations, it does not change what the case does).

## Actual outputs (from maker's own run)

```
$ docker compose exec autotester uv run pytest -q
........................................................s............... [ 26%]
........................................................................ [ 52%]
........................................................................ [ 78%]
...........................................................              [100%]
(all pass, 1 skip, no failures)

$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!

$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

Real end-to-end, `AUTOTESTER_SLOW_MO_MS=1500`, after `docker compose up -d` recreated the
container with the new env var:

```
run-01M1V2RA8CBWAQX71SRQS7BZYK: duration_s 3.847 (vs 0.94 baseline unpadded) — PASS,
  "Both pages reached successfully."
```

An earlier probe at `AUTOTESTER_SLOW_MO_MS=400` also confirmed the mechanism works at a
smaller pad (`duration_s: 1.701`, still PASS) before settling on 1500ms as genuinely
watchable over noVNC (visually confirmed live via Playwright screenshot of the noVNC tab
mid/post-run, showing the real Chromium context on `vidysea.com/erp/p/me`).

## Status: checked-PASS

Verdict: `qa/verdicts/at054-live-watch-slowmo.md` (Cycle checked: 1, PASS, 3/3 criteria met,
4/4 invariants hold). Closed out 2026-09-06 during `/maker continue` reconcile — the checker's
prior dispatch committed only its own verdict file (`91924f3`); the source changes, tests, and
this manifest were never landed. Landing them now in the same commit as this flip.
