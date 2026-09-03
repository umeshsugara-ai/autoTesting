# Verdict — t065-review-gate

**Checked:** 2026-09-03 · Mode A · Cycle checked: 1
**Contract:** qa/contracts/review-gate.md (R1-R4) + qa/contracts/ingest.md (I1-I5, dependency) +
qa/contracts/core-invariants.md
**Manifest:** qa/manifests/t065-review-gate.md

## Re-run evidence (all executed independently in this session, not pasted)

- `uv run pytest tests/test_review.py -v` -> **6 passed** in 0.10s. Matches manifest.
- `uv run pytest -q` -> exit code 0. `uv run pytest --collect-only -q` broken down by file sums
  to exactly **163** tests (4+3+11+9+6+6+6+12+8+10+20+4+8+6+6+8+24+12), matching the manifest's
  "163 collected" claim; progress dots showed one `s` (skip) consistent with the pre-existing
  gated live-Mongo test from T-045, unrelated to this unit.
- `uv run ruff check src tests scripts` -> "All checks passed!"
- `uv run autotester doctor` -> "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` -> 150 (<=150, at the cap as the manifest states, not over it).

## R1 — fresh FlowSpec is unreviewed and blocks

Read `src/autotester/stages/ingest.py::ingest_video` in full: it constructs the returned
`FlowSpec(project=project_slug, screens=screens, flows=flows, source_ids=[source.id])` with no
`review=` kwarg at all — it relies entirely on the schema's default (`ReviewStatus.DRAFT`),
unchanged from before this unit. No other write to `review.status` exists in `ingest.py`.
Read `src/autotester/stages/review.py::require_reviewed`: raises `FlowSpecNotReviewed` whenever
`spec.review.status is not ReviewStatus.APPROVED` — covers both `DRAFT` and `NEEDS_EDIT` by
construction (an `else`-style guard, not an enumerated allow-list that could miss a case), and
the message names the project (`spec.project`) and the exact unblocking CLI command. Confirmed
by re-running `tests/test_review.py::test_fresh_flowspec_is_draft_and_blocked` (raises, message
matches `"draft"`) and `::test_request_edit_sends_back_to_needs_edit_with_a_note` (raises,
message matches `"needs_edit"`). **R1 holds.**

## R2 — approval is human-attributed and does not mutate the original

`approve(spec, by, note=None)` raises `ValueError` when `by` is falsy (`if not by: raise
ValueError(...)`), else builds a new `Review(status=APPROVED, by=by, at=_now_iso(), note=note)`
and returns `spec.model_copy(update={"review": review})` — Pydantic's `model_copy` produces a new
object; the original `spec` is never assigned to or mutated. Re-ran
`test_approve_unblocks_and_records_who`, `test_approve_requires_a_who`, and
`test_approve_does_not_mutate_the_original` (asserts `spec.review.status is
ReviewStatus.DRAFT` unchanged after `approve(spec, ...)` is called) — all pass. **R2 holds.**

## R3 — request_edit sends it back with a mandatory reason

`request_edit(spec, by, note)` raises `ValueError` when `by` or `note` is falsy (`if not by or
not note: raise ValueError(...)`), else returns a new `FlowSpec` via `model_copy` with
`review.status=NEEDS_EDIT` and the given note. Re-ran
`test_request_edit_sends_back_to_needs_edit_with_a_note` (status is `NEEDS_EDIT`, note carried,
then `require_reviewed` raises with `"needs_edit"` in the message) and
`test_request_edit_requires_a_note` (empty note raises `ValueError` matching `"what"`) — both
pass. **R3 holds.**

## R4 — the CLI is a thin wrapper, not a second source of truth

Read the `flowspec_app` sub-app in `src/autotester/cli.py` (`status`/`approve`/`request-edit`
commands). Each command does `store_ = ProjectStore(project)` then
`store_.load_flowspec()` / `store_.save_flowspec(review_stage.approve(...))` /
`store_.save_flowspec(review_stage.request_edit(...))` — no other read or write path, no
parallel state file. Confirmed `ProjectPaths.flowspec` (`core/paths.py`) resolves to
`projects/<slug>/flowspec.json`, the same path `ProjectStore.save_flowspec`/`load_flowspec`
(`store/project_store.py`) already use for every other stage. **R4 holds.**

## Independent manual CLI round-trip (not the maker's pasted transcript)

Built a scratch `AUTOTESTER_ROOT` (not `pathlynks`) with `projects/demo/flowspec.json` seeded to
a minimal valid `FlowSpec`, then ran the CLI myself against it:

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

Reading `projects/demo/flowspec.json` afterward shows `review.status: "needs_edit"`,
`review.by: "umesh"`, `review.note: "missing a flow"` written to the real file on disk through
`ProjectStore` — genuine file I/O, not just in-process function calls. Matches the manifest's
claimed transcript (the em-dash rendered as a mojibake byte in this shell's codepage, cosmetic
only, not a defect). **R4 confirmed independently.**

## Manifest metadata check

`Issues addressed: none` is accurate — no open ledger issue names this feature.

## Tracking metadata (checker authority, per dispatch)

`.goal/goal.json`'s T-065 `done_check` pointed at `tests/test_ingest.py` (a stale placeholder
inherited from T-060). Confirmed the claim and corrected in place to `{"type": "cmd", "cmd": "uv
run pytest tests/test_review.py -q", "expect_exit": 0}` — the actual verify command for this
unit's deliverable. Closed T-065 via `python D:/ai_os/.claude/skills/goal/scripts/goal_cli.py
done --root "d:/autoTesting" --task-id "T-065"` (result: `{"ok": true, "task": "T-065", "percent":
75}`).

Since `user_value: high`, appended a `docs/FEATURES.jsonl` row via `autotester ledger add` citing
the north star's own "derives a reviewed FlowSpec" requirement and AT-017 (the sweep finding that
originally flagged the missing review-gate goal coverage), `--unit T-065 --verdict
qa/verdicts/t065-review-gate.md`. Regenerated `docs/SNAPSHOT.md`.

## VERDICT

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met (R1-R4), 0/0 additional invariants checked beyond R1-R4 (this unit
  restates no core-invariants criterion not already covered by R1-R4)
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: ingest_video still never sets review.status (relies on the schema DRAFT default,
  confirmed unchanged); require_reviewed blocks both DRAFT and NEEDS_EDIT by construction and
  names the fix command; approve/request_edit both use model_copy (original never mutated) and
  both refuse their respective empty-required fields; the CLI commands are confirmed thin
  ProjectStore wrappers with no parallel state, verified further by an independent manual
  round-trip against a scratch AUTOTESTER_ROOT that shows real file I/O, not just in-process
  calls. Full suite (163 tests), ruff, and doctor all re-run clean. Fixed the stale T-065
  done_check, closed the goal task, and appended the FEATURES.jsonl ledger row.
```
