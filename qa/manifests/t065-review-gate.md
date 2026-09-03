# Manifest — t065-review-gate

**Contract:** qa/contracts/review-gate.md (R1–R4, new this cycle) + qa/contracts/ingest.md
(I1-I5, dependency) + qa/contracts/core-invariants.md
**Goal task:** T-065 (`user_value: high`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none directly (advances the pipeline; north star's own "reviewed FlowSpec"
requirement, previously an uncovered goal-gap)

## Why this unit

Umesh: "don't stop until you achieve the /goal." T-065 was the next unblocked, unambiguous unit
(deps=[T-060], now done) and is HIGH value — the north star's own text says "derives a
**reviewed** FlowSpec," and no prior contract covered the review step at all.

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-065 FlowSpec review gate: Review.status must be
approved before expand runs"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for the review gate. Wrote `qa/contracts/review-gate.md` (R1–R4) before
writing any code.

## What changed

- `qa/contracts/review-gate.md` (new) — R1 (fresh spec is DRAFT, blocked) · R2 (approval is
  human-attributed, immutable original) · R3 (`request_edit` requires a reason, still blocked) ·
  R4 (CLI is a thin `ProjectStore` wrapper, no parallel state).
- `src/autotester/stages/review.py` (new, 51 lines) — `approve(spec, by, note=None)`,
  `request_edit(spec, by, note)` (both return a NEW `FlowSpec` via `model_copy`, never mutate the
  input), `require_reviewed(spec)` (raises `FlowSpecNotReviewed` unless `APPROVED`, naming the
  project and the exact CLI command to fix it). `stages/expand.py` (T-070) is expected to call
  `require_reviewed` first — that wiring is explicitly this unit's no-fire list, not delivered
  here (`expand.py` doesn't exist yet).
- `src/autotester/cli.py` — new `flowspec` typer sub-app: `status`, `approve --by [--note]`,
  `request-edit --by --note` commands, each a thin `ProjectStore.load_flowspec`/`save_flowspec`
  wrapper (R4). No existing command changed.
- `tests/test_review.py` (new, 6 tests) — fresh spec is DRAFT and blocks; approve unblocks and
  records who/when/note; approve refuses an empty `by`; approve does not mutate the original;
  `request_edit` sends back to `NEEDS_EDIT` with the note, still blocked; `request_edit` refuses
  an empty note.
- `docs/ARCHITECTURE.md` — concept→file row; Status line updated (review.py built, expand.py
  named as Next). 150 lines (at the C2 cap, not over it — `doctor`'s check is `> 150`).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## Real validation performed (not simulated)

Ran the actual CLI commands against a scratch project (not `pathlynks` — a throwaway
`AUTOTESTER_ROOT`) to prove the wiring genuinely round-trips through `ProjectStore`, not just the
in-memory `review.py` functions in isolation:
```
$ AUTOTESTER_ROOT=<scratch> uv run autotester flowspec status demo
demo: draft
$ AUTOTESTER_ROOT=<scratch> uv run autotester flowspec approve demo --by umesh --note "looks good"
demo: flowspec approved by umesh
$ AUTOTESTER_ROOT=<scratch> uv run autotester flowspec status demo
demo: approved — looks good
$ AUTOTESTER_ROOT=<scratch> uv run autotester flowspec request-edit demo --by umesh --note "missing a flow"
demo: flowspec sent back for edit by umesh
$ AUTOTESTER_ROOT=<scratch> uv run autotester flowspec status demo
demo: needs_edit — missing a flow
```

## How to verify (commands + expected)

- `uv run pytest tests/test_review.py -v` → 6 passed
- `uv run pytest -q` → exit 0, 163 collected
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 150 (≤ 150)
- Manual CLI round-trip against a scratch `AUTOTESTER_ROOT` (see above) — real file I/O through
  `ProjectStore`, not just in-process function calls.

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_review.py -v
......                                                                   [100%]
6 passed
$ uv run pytest -q
................................s....................................... [ 44%]
........................................................................ [ 88%]
...................                                                      [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- Per the no-fire list, `stages/expand.py` calling `require_reviewed` is explicitly NOT this
  unit's job — `expand.py` doesn't exist yet (T-070). This contract only requires the guard
  function to exist and be correct in isolation, verified by the tests above.
- No UI — the CLI is the review interface for now, matching T-100's own place in the plan.
- No secrets touched — this unit has no credential surface at all.
- `.goal/goal.json` T-065's `done_check` is currently `uv run pytest tests/test_ingest.py -q` —
  a stale placeholder pointing at T-060's test file, not this unit's own `tests/test_review.py`.
  Flagging for the checker to correct it to `uv run pytest tests/test_review.py -q` (matching how
  the checker corrected T-045's stale `done_check` earlier this session).

## Status: ready-for-check
