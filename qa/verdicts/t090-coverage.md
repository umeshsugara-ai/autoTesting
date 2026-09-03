# Verdict — t090-coverage

**Date:** 2026-09-03
**Cycle checked:** 1
**Checker:** fresh subagent, Mode A, no builder context

## What I re-ran myself

- `uv run pytest tests/test_coverage.py -v` → `6 passed in 0.10s`
- `uv run pytest` (full suite, addopts already `-q`) → `176 passed, 1 skipped in 1.37s`
  (matches manifest's "177 collected": 176 + 1 skip = 177)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `wc -l docs/ARCHITECTURE.md` → `150` (≤ 150 cap)

## Criteria (qa/contracts/coverage.md V1-V4)

- **V1 — known route → no gap.** Read `src/autotester/stages/coverage.py::diff_coverage`
  (`_known_paths` builds `{urlsplit(s.url_pattern).path for s in spec.screens if s.url_pattern}`;
  `_path_of` normalizes every observed URL the same way via `urlsplit(url).path or "/"` before
  comparing) — host/query genuinely ignored since only `.path` is taken from `urlsplit`. Confirmed
  by `test_known_route_produces_no_gap`. **MET.**
- **V2 — unseen route → exactly one gap, deduped across cases.** `diff_coverage` builds
  `gaps: dict[str, CoverageGap]` keyed on `gap.id` via `gaps.setdefault(gap.id, gap)`.
  `CoverageGap.id` (schema/coverage.py `model_post_init`) is `content_id("gap", {"p": project,
  "k": kind, "s": subject})` — content-addressed on `(project, kind, subject)`, unchanged from the
  pre-existing schema. Two cases hitting the same unseen path produce identical `(project, "route",
  path)` → identical id → `setdefault` keeps one. Confirmed by
  `test_the_same_unseen_route_seen_by_two_cases_dedupes_to_one_gap`. **MET.**
- **V3 — exactly one VideoRequest per gap, idempotent across store calls.** `request_for(gap)`
  builds `VideoRequest(project=gap.project, gap_id=gap.id, prompt=...)`; `VideoRequest.id` is
  `content_id("req", {"p": project, "g": gap_id})` — same gap always yields the same request id.
  `ProjectStore.add_request` (project_store.py:101-106) checks `any(r.id == request.id for r in
  self.list_requests())` before appending — same pattern as the pre-existing `add_case`/`add_source`.
  Traced two separate calls with a request built from the same gap: second call's id matches an
  existing row's id, so it returns without appending. Confirmed live (not just by the maker's test)
  — `test_add_request_is_idempotent` re-run and passed; also confirmed by direct code trace, not
  just trusting the test. **MET.**
- **V4 — redacted evidence never mistaken for a route.** `_seen_urls` filters
  `ev.kind is EvidenceKind.URL and ev.path.startswith(("http://", "https://"))`. The string
  `"[REDACTED]:PATHLYNKS_USER_LOGIN_URL"` starts with `[`, not `http`/`https`, so it is excluded
  before any `urlsplit` parse is attempted. Confirmed by
  `test_redacted_evidence_string_is_not_treated_as_a_route`. **MET.**

## Scope / no-fire list

- Screen-level (name/signals) gap detection correctly absent — only `kind="route"` URL-path
  diffing is implemented, matching the no-fire list.
- No dispatch/notification of open `VideoRequest`s added — correctly out of scope (T-100).
- `stages/ingest.py::ingest_video` was checked — confirmed it does not set `Screen.url_pattern`,
  consistent with the manifest's disclosure that this unit's tests use fixture FlowSpecs rather
  than a real Pathlynks-ingested one.

## Issues addressed

None claimed by the manifest; none to cross-check against the ledger.

## Verdict

VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 0/0 invariants (contract has no separate [I*] invariants beyond V1-V4)
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: All four contract criteria (V1-V4) are evidenced directly against
src/autotester/stages/coverage.py, schema/coverage.py, and project_store.py — traced by hand, not
just trusted from the maker's tests — and every verify command was re-run fresh with matching
output. No scope creep, no softened criteria, no gaps.
