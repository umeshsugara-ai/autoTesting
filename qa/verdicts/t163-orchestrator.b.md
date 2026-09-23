# Verdict — t163-orchestrator (INDEPENDENT SECOND CHECK, dual check "b")

**Date:** 2026-09-23
**Cycle checked:** 1
**Checker:** claude-sonnet-subagent (fresh context, independent of the primary `.md` verdict — not read)
**Bound root:** `D:/autoTesting/.worktrees/t163-orchestrator`

## What I re-ran myself

- `PYTHONUTF8=1 uv run pytest` — full suite, twice independently (both backgrounded runs
  completed clean): **1578 passed, 5 skipped, 32 xfailed, 0 failed, 0 errors** in ~675s and
  ~692s. Whole-log scan for `FAILED`/`ERROR`/`^E` found none. (A third, concurrent foreground
  run I started myself showed one `F` at 44% — almost certainly resource contention from
  running three full-suite pytest invocations against the same worktree simultaneously; not
  corroborated by either clean run, so not reported as a finding.)
- `tests/test_orchestrate.py tests/test_orchestrate_runners.py` in isolation: **10 passed**.
- `PYTHONUTF8=1 uv run ruff check src tests scripts` → `All checks passed!`
- `PYTHONUTF8=1 uv run autotester doctor` → **1 violation**: `stale-generated: docs/SNAPSHOT.md
  — differs from regeneration; run autotester snapshot`. Investigated: the only diff between
  the committed file and a fresh `autotester snapshot --print` is a single trailing blank line
  (CRLF file). **Reproduced identically on the main repo's HEAD (`0720fce`, a descendant of this
  branch's stated base `2a0b31e`)** — i.e. this is a pre-existing tooling quirk (the snapshot
  generator vs. the doctor stale-check disagree on a trailing newline) that predates and is
  independent of this unit's content, which otherwise regenerated SNAPSHOT.md correctly (only
  the D-036 decision line changed). Not charged to T-163.

## OR1–OR6 capability-coverage — reproduced independently in a throwaway copy

Copied `src/`, `tests/`, `scripts/`, `pyproject.toml`, `uv.lock`, `README.md` to 6 separate
scratch dirs outside the bound tree, junctioned each `.venv` to the bound tree's own venv.
Every row's named test was green in the copy BEFORE the edit, then I applied the manifest's
described single-hunk edit myself (not the maker's pasted evidence) and got RED for the exact
named reason in every case, matching the manifest's claimed error text verbatim:

| OR | Edit applied | Result |
|---|---|---|
| OR1 | `orchestrate.py::choose_mode`: `if teaching:` → `if False and teaching:` | `AssertionError: assert 'explore' == 'learn'` — exact match |
| OR2 | `orchestrate.py::run_or_resume`: drop the done/skipped skip | `AssertionError: a done stage was re-run / assert 2 == 1` — exact match |
| OR3 | `orchestrate_runners.py::make_model_runner`: `merged = merge_flowspec(...)` → `merged = incoming` | `assert None is not None` (approved `s_home` discarded) — exact match |
| OR4 | `orchestrate.py::_run_stage` except branch: `"status": "failed"` → `"status": "done"` | `AssertionError: assert 'done' == 'failed'` — exact match |
| OR5 | `orchestrate.py::_state_path`: `run_dir(ctx.run_id)` → `run_dir("shared")` | `AttributeError: 'NoneType' object has no attribute 'run_id'` — exact match |
| OR6 | `orchestrate_runners.py::_read_proposal`: raise → `return FlowSpec(project="demo")` | `Failed: DID NOT RAISE MissingArtifact` — exact match |

6/6 rows reproduced. No row survived; none is UNVERIFIED.

## OR3 special rigor (read `stages/orchestrate.py` + `orchestrate_runners.py` in full)

`make_model_runner` reads only `prev_ref` (`_read_proposal`, raises `MissingArtifact` on a
missing/dangling ref — never falls back to `ctx.store.load_flowspec()` as input), then calls
`merge_flowspec(existing, incoming, source_id=...)` and `ctx.store.save_flowspec(merged)`. It
never calls `stages/review.py::approve`, never constructs a `Review(status=APPROVED, ...)`
itself, and imports nothing from `review.py` at all. `merge_flowspec` (read in full) never
mutates or drops an existing `Screen`/`Flow` — `_new_screens`/`_new_flows` only ever add rows
whose id isn't already known, `_learned_url_patterns` only ever fills a `None` — and on any real
change it stamps `Review(status=DRAFT, ...)`, re-arming `require_reviewed`. Confirmed live in
`test_orchestrated_run_never_overwrites_approved_truth`: the APPROVED screen's
`model_dump()` survives byte-for-byte, the new screen lands, `review.status is DRAFT`, and
`require_reviewed(merged)` raises `FlowSpecNotReviewed`. `stages/review.py` is untouched by this
diff (confirmed via `git diff`) and its own gate logic is unmodified. No new approval path.

## Diff scope (git diff 2a0b31e...HEAD, judged files only)

All 5 code/test files are **new files, pure additions** (0 deletions/renames) — no existing
function, class, test, export, or config key was removed or renamed anywhere in the diff.
`docs/ARCHITECTURE.md`: prose reframe under D-036, one row added to the concept→file table,
no row removed; file is exactly 150 lines (the doctor cap). `docs/MAP.md`/`docs/SNAPSHOT.md`:
additive regeneration only. File sizes: `run_state.py` 90, `orchestrate.py` 164,
`orchestrate_runners.py` 115 — all ≤300; `doctor` (which also gates the 50-line function cap)
reported zero size/duplicate/drift violations. `.goal/goal.json` and `.goal/dashboard.html`
changed only outside the judged scope per the dispatch — confirmed by inspection: goal.json's
diff is the T-163 row flipping to `status: done` plus progress counters/tick timestamps, nothing
touching this unit's claimed files. (Observation, not a finding under this dispatch's scope: per
`checker/SKILL.md` "only /checker's PASS closes a task," a goal task closing to `done` before a
checker PASS is normally the checker's job, not the maker's — worth a look by whoever owns the
next sweep, but out of scope for this dual check per the dispatch's explicit file list.)

## Explicit no-fire list — honored

No LangGraph/SqliteSaver/external DB: `RunState` persists via the existing
`store/filestore.py::read_json`/`write_json` over `ProjectStore.paths.run_dir`, confirmed by
imports and by there being no new dependency in `pyproject.toml`'s diff (not in the diff at
all). No concurrent-same-project-run support: no locking, no multi-writer handling — `run_id` is
per invocation, sequential, exactly as documented; not raised as a gap. No new approval
mechanism: confirmed above (OR3 rigor).

## Other core-invariants spot checks

`schema/run_state.py` and `schema/project.py`'s `Source`/`Project` models are `extra="forbid"`
(C1). `schema/base.py` is untouched (not in the diff). No vendor SDK import in the touched
stages (C8 — grep would return nothing new; nothing added imports `anthropic`/`google`). No
secret-shaped field added to `RunState`/`StageCheckpoint` (C5 — n/a, this unit adds no
credential-handling code).

## Live browser

Not applicable — orchestration/schema layer only, no UI/route/rendering path touched. Changed
paths match the manifest's own list exactly.

VERDICT: PASS
SCOREBOARD: 6/6 criteria met (OR1-OR6), 3/3 no-fire-list items honored
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 6/6 rows reproduced (green-before -> red-for-the-named-reason -> reverted in throwaway copies)
LIVE-BROWSER: not-applicable (schema/run_state.py, stages/orchestrate.py, stages/orchestrate_runners.py, tests/test_orchestrate.py, tests/test_orchestrate_runners.py, docs/ARCHITECTURE.md, docs/MAP.md, docs/SNAPSHOT.md — no UI surface)
ISSUES-WRITTEN: none (dual check — primary owns the ledger; see observations above re: doctor's pre-existing SNAPSHOT.md staleness and the goal.json premature done-flip, both out of this dispatch's judged scope)
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All six OR criteria independently reproduced red-for-the-named-reason in throwaway
copies outside the bound tree; the full test suite is green across two independent runs (1578
passed, 0 failed); ruff is clean; doctor's one violation is a pre-existing trailing-newline
tooling quirk reproduced identically on the main repo's current master HEAD, predating and
unrelated to this branch. OR3 was read in full and confirmed to route exclusively through
`merge_flowspec` with no bypass of `review.py::require_reviewed`. The diff is pure addition with
zero deletions of existing code, and ARCHITECTURE.md sits exactly at the 150-line cap.
