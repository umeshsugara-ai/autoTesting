# Contract — FlowSpec review gate (T-065)

**Covers:** goal task T-065. **Owner:** /checker. **Criticality:** HIGH — the north star's own
words ("derives a **reviewed** FlowSpec") name this gate as the primary false-positive control;
`stages/expand.py` (T-070) is required to call it before generating any case.
**Depends on:** `core-invariants.md` (all), `ingest.md` (I1-I5, dependency — produces the
`FlowSpec` this gate reviews).

## Purpose

A `FlowSpec` fresh from `ingest_video` is a machine's first guess, not ground truth. This stage
is the mechanism a human uses to say "yes, this is right" (or "no, fix this") before anything
downstream treats it as fact. `FlowSpec.review.status` starts `draft`; only a human-driven
`approve` call moves it to `approved`; any stage that would generate cases from a `FlowSpec` must
refuse to run on anything else.

## Criteria

### R1 — A fresh FlowSpec is unreviewed and blocks
`stages/ingest.py::ingest_video` never sets `review.status` to anything but its default
(`ReviewStatus.DRAFT`) — unchanged by this unit, verified as still true. `require_reviewed(spec)`
raises `FlowSpecNotReviewed` for `DRAFT` and for `NEEDS_EDIT`, naming the project and the exact
CLI command to unblock it.

### R2 — Approval is human-attributed and does not mutate the original
`approve(spec, by, note=None)` returns a **new** `FlowSpec` with `review.status=APPROVED`,
`review.by` set to the given name, `review.at` set to a real timestamp, `review.note` carrying
the optional note — the input `spec` object is never mutated in place (Pydantic's `model_copy`
semantics). `approve` refuses an empty `by` — there is no such thing as anonymous approval.

### R3 — request_edit sends it back with a mandatory reason
`request_edit(spec, by, note)` returns a new `FlowSpec` with `review.status=NEEDS_EDIT` and the
given note — refuses an empty `by` or `note` (a review rejection with no stated reason is not
useful to whoever fixes it next). A `NEEDS_EDIT` spec still fails `require_reviewed`.

### R4 — The CLI is a thin wrapper, not a second source of truth
`autotester flowspec status/approve/request-edit <project>` load and save through
`ProjectStore.load_flowspec`/`save_flowspec` — the same file (`projects/<slug>/flowspec.json`)
and format every other stage reads, no parallel state.

## No-fire list

- `stages/expand.py` actually calling `require_reviewed` — that is T-070's own job, not this
  contract's; T-070's contract is expected to name it as a dependency criterion. This contract
  only requires the guard function to exist and work correctly in isolation.
- A UI review screen — the CLI is the interface for now (T-100).
- Merge/diff logic when a FlowSpec is re-ingested after edits — a future concern, not required to
  approve or reject a spec as a whole.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-065 — no contract existed before this cycle.
