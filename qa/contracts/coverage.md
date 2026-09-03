# Contract — COVERAGE stage (T-090)

**Covers:** goal task T-090. **Owner:** /checker. **Criticality:** MEDIUM — the self-extension
half of the north star ("when it meets a screen it does not know, it asks the human for a video
instead of guessing"), not itself on the critical path to a first scorecard.
**Depends on:** `core-invariants.md` (all), `execute.md` (E1-E5 — produces the `RawResult`
evidence this stage diffs against).

## Purpose

Compare what a run's evidence actually reached against what the `FlowSpec` already knows. A URL
whose path matches no known screen becomes a `CoverageGap`; each gap gets exactly one
`VideoRequest`, deduped by content-addressed id, so re-running the same cases never re-asks for
the same thing twice.

## Criteria

### V1 — A known route produces no gap
`diff_coverage(spec, results)` compares each observed URL's **path** (`urlsplit(url).path`, host
and query ignored) against every `Screen.url_pattern` already in the `FlowSpec` — a match
produces nothing.

### V2 — An unseen route produces exactly one gap, deduped across cases
Two different cases in the same `results` list that both reach the same unseen path produce
**one** `CoverageGap`, not two — `CoverageGap.id` is content-addressed on `(project, kind,
subject)` (unchanged from the existing schema), and `diff_coverage` uses that id to dedupe within
a single call.

### V3 — Exactly one VideoRequest per gap, idempotent across store calls
`request_for(gap)` produces a `VideoRequest` whose `gap_id` names the gap and whose `prompt`
names the specific unseen path. `ProjectStore.add_request` is idempotent on `VideoRequest.id`
(content-addressed on `(project, gap_id)`) — calling it twice for the same gap (e.g. the diff
re-runs on a later run that reaches the same unseen path) never queues a second request.

### V4 — Redacted evidence is never mistaken for a route
An `Evidence` entry whose `path` is a redacted string (e.g. `[REDACTED]:KEY`, produced by
`Redactor.scrub` for an undeclared/masked value) never starts with `http://`/`https://` and is
therefore never treated as an observed URL — `diff_coverage` filters on that prefix before
attempting to parse anything as a route.

## No-fire list

- Screen-level (as opposed to route-level) gap detection — `Screen.name`/`signals` matching is a
  future enhancement; this contract covers URL-path diffing only, matching `kind="route"`.
- Automatically dispatching or notifying anyone about an open `VideoRequest` — that is a UI/
  notification concern (T-100), not this stage's.
- Populating `Screen.url_pattern` from `stages/ingest.py` — `ingest_video` does not currently set
  it (a vision model watching a video frequently cannot read a hidden address bar), so today's
  real Pathlynks `FlowSpec` has no `url_pattern`s to diff against; this contract's tests use
  fixture `FlowSpec`s with `url_pattern` set to prove the mechanism works when that data exists.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-090 — no contract existed before this cycle.
