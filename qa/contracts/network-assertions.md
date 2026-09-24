# Contract — network-assertions (first-party API/network capture as evidence)

**Status:** DRAFT (goes DRAFT->ACTIVE on T-170's first checker PASS).
**Feature:** ADOPTs Playwright's `page.on('response')` (already a direct dependency, already
attached once per session via `browser/observe.py::PageObserver.attach`) to record first-party
API/network calls made during a crawl or a run as first-class **evidence** — `(method, url pattern,
status)` — and discharges `browser/assertions.py`'s own stated deferral of `ExpectedState.network`
("`network` is observer-derived", D-032) by giving a case step's declared `network` patterns a real
met/unmet check, recorded the same way `absent_text`/`dom_asserts` already are.
**Covers:** goal task T-170. **Deps:** T-163 (orchestrator; done). **Grounding:** D-040 (ADOPT
verdict + this task's registration); `docs/research/crawl-reuse-2026-09.md` §6 (mechanism +
licence verification: Apache-2.0, already a dependency, zero new licence surface); T-165's original
"first-party API/network assertions" clause, moved here per D-040.

## What it is

No new library, no new browser hook: `PageObserver` (`browser/observe.py`) already installs
`page.on("response", ...)` for failure/4xx+ detection (X9's first-party-issue path). This unit adds
a **second, evidence-producing** read of that same stream — every first-party response's `(method,
url pattern, status)` is captured as `EvidenceKind.NETWORK` evidence, independent of whether the
status is an error, and independent of any case step's declared expectations. A step that declares
`ExpectedState.network` patterns gets those patterns checked against the captured stream and
recorded met/unmet, the same evidence shape `browser/assertions.py::assert_expected` already uses
for `absent_text`/`dom_asserts` — extending that module rather than building a second one (C3).

## Criteria (NA1-NAn) — each judged on re-runnable evidence

- **NA1 — First-party network calls are captured as evidence, every crawl and every run.** During
  both `stages/explore.py`'s crawl and `stages/execute.py::run_case`, every first-party response
  observed on the page is recorded as `EvidenceKind.NETWORK` evidence carrying `(method, url
  pattern, status)` — not only the failing ones X9 already counts as `CrawlIssue`s. Third-party
  hosts (declared analytics/tracker hosts, and any other third party) are excluded from this
  evidence stream, reusing X9's first-party test rather than a second one. (Falsifiable: a fixture
  page issuing one first-party 200 and one third-party 200 → exactly one `NETWORK` evidence item,
  for the first-party call; the third-party call produces none.)
- **NA2 — Observation only, never judgement (core-invariants C7).** Recording a network call as
  evidence never itself assigns PASS/FAIL to anything — a captured 500 on a first-party endpoint is
  a fact for the grader (or, during a crawl, X9's existing `CrawlIssue` derivation) to weigh, never
  a verdict this stage produces on its own. (Falsifiable: `stages/execute.py`'s network-capture path
  has no import of `stages/grade.py`, matching T-153's already-proven capturer/grader separation
  pattern; a captured error status alone, with no declared `ExpectedState.network` pattern, changes
  no `RawResult.outcome`.)
- **NA3 — A declared `network` pattern gets a real check, not silence.** A `Case` step's
  `ExpectedState.network` (a list of expected request patterns, `schema/flowspec.py:68`) is
  evaluated against the captured first-party stream by `browser/assertions.py::assert_expected`
  exactly as `absent_text`/`dom_asserts` are — one `assert network: met|unmet (<pattern>)` DOM/NETWORK
  evidence item per declared pattern, recorded, not raised. A step declaring no `network` pattern is
  unaffected (no evidence item fabricated for nothing declared). This is the specific deferral D-032
  named ("`network` is observer-derived") and this unit is what discharges it — the docstring in
  `browser/assertions.py` naming `network` as unhandled must be updated in the same unit, not left
  stale claiming a gap that no longer exists. (Falsifiable: a step expecting a network pattern that
  did occur → `met`; a step expecting one that did not → `unmet`; both produce a recorded evidence
  item, neither raises.)
- **NA4 — Deterministic, no provider (core-invariants C8).** Capture and the `network` pattern check
  are pure reads of the observed response stream — no model call anywhere in this unit; a run
  completes this capture with `provider=mock`, the same discipline X12 already holds the crawl to.
  (Falsifiable: `grep -rn` for a `Provider`/vendor-SDK import in the new capture module returns
  nothing, matching C8's existing repo-wide check.)
- **NA5 — Secrets never reach captured evidence (core-invariants C5).** A captured URL or any
  recorded request/response detail passes through `core.redact.Redactor.scrub` (or an equivalent
  guard) before it is persisted as evidence — a secret value appearing in a query string or header
  must never land in `qa/evidence/` or a project artifact. (Falsifiable: a fixture request carrying
  a `{{SECRET:KEY}}`-sourced value in its URL → the persisted NETWORK evidence item does not contain
  the raw value.)
- **NA6 — One capture mechanism, not two (C3).** This unit extends the existing `PageObserver`
  attach point and the existing `assert_expected` evidence-recording path; it does not introduce a
  second listener, a second evidence-recording function, or HAR-based recording/replay
  (`routeFromHAR`) as a parallel mechanism — `docs/research/crawl-reuse-2026-09.md` §6 ADOPTs
  `page.on('response')` specifically and leaves HAR unadopted. (Falsifiable: `grep -rn "on(\"response\"" \
  src/autotester/browser/` returns exactly the existing `PageObserver` attach site; no second
  `page.on` response listener exists anywhere in `src/`.)

## Explicit no-fire list (do not raise these as findings)

- HAR recording/replay (`context.routeFromHAR` / `page.routeFromHAR`) — explicitly NOT adopted
  (crawl-reuse-2026-09.md §6); raising "should also support HAR replay" is out of scope.
- Deep response-body schema assertions (contract testing, JSON-shape diffing) — this unit captures
  `(method, url pattern, status)` only; body-shape checking is Track C territory (T-153/T-155), not
  this contract.
- Vendoring a third-party network-mocking or contract-testing library — Playwright's own
  already-dependency hook is the whole mechanism; a new dependency here is a defect, not a feature.
- Judging *which* first-party endpoints "should" exist — this unit records what was observed; a
  missing-endpoint judgement belongs to a rubric/grader, not this capture layer.
- X9's existing `CrawlIssue` counting for failed first-party requests is unchanged by this
  contract — NA1 adds a parallel *evidence* stream alongside it, not a replacement.

## How a unit is verified (adapter slot 1)

`uv run pytest tests/test_network_assertions.py` (bare, no CLI `-q`, AT-503) + `uv run ruff check
src tests scripts` + `uv run autotester doctor`, all exit 0; each NA criterion carries a
capability-coverage row with a single-hunk falsifying edit reproduced
green→red-for-the-named-reason→revert→green. File/function caps (core-invariants C2) apply; if
`browser/assertions.py` has no headroom under its 300-line cap, the new logic lands in a new,
justified module per C3 rather than pushing the file over budget.

## Amendment log (append-only; git history is the version)

- 2026-09-24 · init · contract authored by /checker as DRAFT, from D-040 (Approved-by Umesh — "go
  on" to `qa/gates/t165-d039-traversal-scope.md`) and `docs/research/crawl-reuse-2026-09.md` §6.
  No prior draft existed; nothing amended.
