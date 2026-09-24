# Manifest — t123-medium-batch
**Contract:** qa/contracts/docker.md (D2, D4), qa/contracts/ui.md (U9 amendment log)
**Goal task:** T-123
**Date:** 2026-09-24
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-085, AT-065 (AT-086 and AT-087 deferred — see below)
**Executor:** claude-sonnet-subagent
**Executor rationale:** both fixes are scoped, single-repo Python (a new FastAPI route +
introspection, and a one-off migration script following the repo's own `migrate_url_patterns.py`
precedent) — no external delegation was worth its overhead.

## What changed

- `src/autotester/ui/routes_live.py:1-89` — new `GET /healthz` route (AT-085). Reads
  `_PROCESS_STARTED_AT` (frozen once, at module import — the same moment a real `uv run uvicorn`
  process without `--reload` starts, per `docker/entrypoint.sh`) and computes
  `_newest_source_mtime()` fresh on every request (scans `src/autotester/**/*.py`). Returns
  `{started_at, newest_source_mtime, serving_stale_code}` — one HTTP call standing in for the
  `ps -o lstart=` + `find -newermt` archaeology the AT-085 checker had to do by hand. Presentation
  -only: no `ProjectStore`/`SecretStore` call, no project param, same invariant D4 pins for `/live`.
- `scripts/migrate_stamp_legacy_rubrics.py` (new, 146 lines) — AT-065's own fix direction: "a
  one-off migration that stamps provenance on rubrics whose shape is byte-identical to
  `_rubric_for_claim(embedded_claim, ...)`, reviewed by a human per file — not an automatic
  runtime heuristic." Follows `scripts/migrate_url_patterns.py`'s exact shape (dry-run by default,
  `--write` to apply, `--root` for a sandbox), adds `--only <path>...` so `--write` can be scoped
  to one reviewed file at a time. `candidate(rubric)` parses the claim out of a `provenance: null`
  rubric's single `c1` criterion, rebuilds what `run_case_pipeline._rubric_for_claim` would
  produce for that claim, and returns the claim to stamp with ONLY when the rebuilt
  `criteria`/`no_fire` are byte-identical to what's stored — any hand-written shape, or anything a
  human has edited since generation (even with `provenance` stripped), is never touched.
- `tests/test_ui_healthz.py` (new, 79 lines) — 5 tests: the three response fields are present;
  fresh when no source is newer than start; detects a source edit after start (the exact AT-085
  scenario, via a monkeypatched `_SRC_ROOT`/`_PROCESS_STARTED_AT`, never the real repo tree); an
  empty source root is never stale; the route touches no project/secret store (read via
  `inspect.getsource`).
- `tests/test_migrate_stamp_legacy_rubrics.py` (new, 157 lines) — 11 tests covering
  `candidate()`/`scan()`/`apply()`/`main()`: a legacy generator-shaped rubric is a candidate; a
  hand-written one never is; an already-stamped one never is (idempotent); one a human edited
  since generation (same criterion id, different `no_fire`) is never a candidate even with
  `provenance` stripped; `scan()` finds only the legacy-shaped files; `apply()` stamps provenance
  and changes nothing else (id, case_id, criteria, no_fire all preserved); running it twice is a
  no-op the second time; the CLI is dry-run by default; `--write` stamps every candidate;
  `--write --only <path>` stamps just the named file; a missing `--root` is reported (exit 2), not
  raised.
- `docs/MAP.md` — regenerated via `uv run autotester map` (doctor's `stale-generated` check).

## Deferred — needs a decision

**AT-087** — NOT built. `qa/contracts/ui.md` U9 itself names this "a scope decision rather than a
bug fix," and CLAUDE.md's credential boundary is a hard boundary I will not narrow on my own
judgment. The fix would (a) turn `exempt` from a flat `frozenset[str]` into a `dict[field_label,
value]`, scoping an exemption to the one field it was stored for, AND (b) put exempt fields BACK
into the concatenation join as context (exempt from being flagged alone, not exempt from being
combined with a fresh field). Both changes widen what the guard inspects on
`POST /projects/{slug}/edit` and `POST /projects/{slug}/secrets` — a legitimate no-op resave that
happens to share a substring with a freshly-typed field could newly 400 where it does not today.
**Question for Umesh:** should the project-edit/secrets routes' concatenation check start
including each field's own already-stored value as join context (catching a credential split
across an exempt field and a fresh one), accepting the new false-positive surface that a per-field
`exempt` dict would introduce on a re-save? The case form (U8) is unaffected either way — it
passes no `exempt` set at all.

**AT-086** — NOT built. Also named a scope decision in the same U9 paragraph. A project whose
`base_url` is byte-identical to a non-secret `.env` value (e.g. `pathlynks`'s own
`PATHLYNKS_USER_LOGIN_URL`) cannot be onboarded at all: AT-083's guard deliberately matches every
`.env` value, declared or not, and a brand-new project has no stored data yet for the `exempt`
byte-identity check to match against — the exemption that fixed U9 for *editing* an existing
project structurally cannot apply to *creating* one. Two directions, both of which touch the
credential-boundary hardening AT-083 exists for:
  (a) let a `.env` entry be declared non-secret/public config, exempt from the credential scan
      universe entirely — narrows AT-083's "match every value, declared or not" rule; or
  (b) exempt onboarding input that is byte-identical to some OTHER *already-onboarded* project's
      stored config — a new, cross-project trust relationship the guard has never had.
**Question for Umesh:** is either direction acceptable, and if so which — given both narrow the
boundary AT-083 was written to widen? (No existing project is broken today; this only blocks
onboarding a *new* one whose URL collides with a stored `.env` value.)

## How to verify (commands + expected)

- `uv run pytest tests/test_ui_healthz.py tests/test_migrate_stamp_legacy_rubrics.py -v` →
  16 passed
- `uv run pytest` (full suite, no CLI `-q`, AT-503) → all passed except the known
  pre-existing failure `tests/test_flake_probe_real_process.py::
  test_run_once_kills_a_real_hung_process_and_its_real_grandchild` (ISS-t164-1, not mine)
- `uv run ruff check src tests scripts` → exit 0
- `uv run autotester doctor` → `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ui_healthz.py tests/test_migrate_stamp_legacy_rubrics.py -v
============================= test session starts =============================
platform win32 -- Python 3.11.15, pytest-9.1.1, pluggy-1.6.0
collected 16 items

tests\test_ui_healthz.py .....                                           [ 31%]
tests\test_migrate_stamp_legacy_rubrics.py ...........                   [100%]
======================== 16 passed, 1 warning in 4.58s =========================
```

```
$ uv run ruff check src tests scripts
All checks passed!
```

```
$ uv run autotester doctor
doctor: clean
```

```
$ uv run pytest
...
=========================== short test summary info ===========================
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
1 failed, 1600 passed, 5 skipped, 32 xfailed, 1 warning in 1394.57s (0:23:14)
```

The one failure is the pre-existing, known-flaky `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` (ISS-t164-1) — a real-process/real-grandchild timing test unrelated to anything this unit touched (`stages/flake_probe.py` is not in "What changed"). Not mine; not fixed here per the dispatch instructions.

## Capability coverage (each new claim -> its isolating falsification)

| capability (one line) | the check that covers it | the falsifying edit | observed (pasted runner output) |
|---|---|---|---|
| `GET /healthz` reports `serving_stale_code=true` when a source file is newer than process start (AT-085) | `tests/test_ui_healthz.py::test_healthz_detects_a_source_edit_after_process_start` | `src/autotester/ui/routes_live.py` — flip `"serving_stale_code": newest > _PROCESS_STARTED_AT` to `newest < _PROCESS_STARTED_AT` | before: `tests\test_ui_healthz.py::test_healthz_detects_a_source_edit_after_process_start PASSED`. after: `FAILED ... assert False is True` (the exact `serving_stale_code` assertion, not an import/collection error) |
| `migrate_stamp_legacy_rubrics.candidate()` refuses a rubric a human edited since generation, even with `provenance` stripped (AT-065's shape-only guard) | `tests/test_migrate_stamp_legacy_rubrics.py::test_a_rubric_edited_since_generation_is_never_a_candidate` | `scripts/migrate_stamp_legacy_rubrics.py` — delete the `if rubric.criteria != rebuilt.criteria or rubric.no_fire != rebuilt.no_fire: return None` guard, leaving bare `return claim` | before: `tests\test_migrate_stamp_legacy_rubrics.py::test_a_rubric_edited_since_generation_is_never_a_candidate PASSED`. after: `FAILED ... AssertionError: assert 'the login page is shown' is None` (the exact `candidate(edited) is None` assertion) |

Both falsifying edits were applied, run, observed red for the named reason, then reverted and
re-confirmed green (see "Actual outputs" above — the 16/16 pass is the post-revert state).

## Live browser evidence

`src/autotester/ui/routes_live.py` is a route file under `ui/`, so this is not a blanket SKIP, but
the only change is a new **JSON API route** — `/healthz` returns a dict, no template, no DOM, no
interaction target for a click-through smoke to exercise. Instead of a browser, I started a real
`uv run uvicorn` process against this worktree (not the FastAPI `TestClient`, which never runs
without `--reload` and can hide wiring gaps `TestClient` shortcuts around) on port 8765 and drove
it with real HTTP requests:

```
$ curl -s http://127.0.0.1:8765/healthz
{"started_at":"2026-09-24T09:32:43.258216+00:00","newest_source_mtime":"2026-09-24T09:30:01.910513+00:00","serving_stale_code":false}
$ curl -s -o /dev/null -w "live: %{http_code}\n" http://127.0.0.1:8765/live
live: 200
$ curl -s -o /dev/null -w "index: %{http_code}\n" http://127.0.0.1:8765/
index: 200
```

Then, live, reproduced the exact AT-085 scenario against the running process — touched
`src/autotester/ui/theme.py` (no restart) and re-hit `/healthz` without restarting the server:

```
$ touch src/autotester/ui/theme.py
$ curl -s http://127.0.0.1:8765/healthz
{"started_at":"2026-09-24T09:32:43.258216+00:00","newest_source_mtime":"2026-09-24T09:33:19.671621+00:00","serving_stale_code":true}
```

`serving_stale_code` flipped `false` → `true` against a live server with no restart — the exact
failure mode AT-085 describes, now surfaced by one HTTP call. Server stopped afterward
(`Stop-Process`); confirmed `curl` connection-refused post-kill. No project/secret state was
touched at any point (`/`, `/live`, `/healthz` only). `scripts/migrate_stamp_legacy_rubrics.py` is
a CLI script with no UI surface — covered by its own pytest suite above, no browser applicable.

## Status: ready-for-check
