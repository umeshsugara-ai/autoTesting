# Contract — EXPAND stage (T-070)

**Covers:** goal task T-070. **Owner:** /checker. **Criticality:** HIGH — the product's
differentiator; the whole taxonomy exists so a suite covers more than the happy path anyone
would write by hand.
**Depends on:** `core-invariants.md` (all), `review-gate.md` (R1-R4 — the gate this stage must
respect), `ingest.md` (I1-I5 — produces the `FlowSpec` this stage consumes).

## Purpose

Turn one reviewed `Flow` into a set of `Case`s — one per taxonomy class that genuinely applies,
never fewer than the flow's own happy path. This is the plan's differentiator: "a systematic
matrix derived from observed UI," not a hand-written happy-path test. T-070's own goal-task note:
"the differentiator: >=12 cases for the login flow, >=1 per applicable taxonomy class."

## Criteria

### X1 — Refuses an unreviewed FlowSpec
`stages/expand.py::expand` calls `stages/review.py::require_reviewed` first — an unapproved
`FlowSpec` (`DRAFT` or `NEEDS_EDIT`) raises `FlowSpecNotReviewed` before any provider call is
made, never silently expanding a guess.

### X2 — Every flow gets its own happy-path case, unmodified
`expand_flow` always produces exactly one `CaseClass.HAPPY`/`CaseKind.BEST` case whose steps are
the flow's own observed steps, verbatim — no model call needed or made for this one case.

### X3 — Class applicability is deterministic where confident, model-judged where not
`applicable_classes(flow)` decides input/auth classes (`INPUT_EMPTY`, `INPUT_BOUNDARY`,
`INPUT_UNICODE_OVERSIZE`, `AUTH_WRONG_CREDS`, `AUTH_EXPIRED_SESSION`) purely from the flow's own
step shape (does it have a `FILL` step; does a `FILL` step reference a `{{SECRET:KEY}}`) — no
model call decides whether these apply. Every flow is additionally asked about the 8 universal
classes (`DOUBLE_SUBMIT`, `BACK_REFRESH_MIDFLOW`, `NETWORK_OFFLINE_SLOW`, `SERVER_ERROR`,
`VIEWPORT_MOBILE`, `LOCALE_I18N`, `CONCURRENT_TAB`, `DEEPLINK_UNAUTH`) via the model, which may
decline with an empty `ExpandedSteps.steps` (D-004: the rule decides only where it can be
certain; everywhere else, a judgment call is spent, not guessed).

### X4 — A model's decline produces no case, never an empty/broken one
When `ExpandedSteps.steps` is empty, `expand_flow` produces no `Case` for that class — it never
constructs a `Case` with zero steps or synthesizes placeholder steps to force one.

### X5 — Never a real secret literal invented for a "wrong" value
The prompt (`prompts/expand_case_v1.md`) instructs the model to invent an obviously-fake value
for a "wrong credential" scenario, never something resembling a real secret, and to leave a
genuinely-needed real credential's `{{SECRET:KEY}}` placeholder untouched — this is a prompt-level
instruction (verified by reading the prompt file), not independently enforced in code this cycle
(no case produced by this stage is ever run against a real product without going through
`execute.py`'s existing credential boundary regardless).

### X6 — The stage has a door, and every refusal behind it writes nothing
A stage nobody can reach is an absent feature, not a slow one. `expand` is called from **two real
entry points a person uses**, not only from tests:

- `cli.py::expand_cases` (`autotester expand <project>`) — loads and persists through
  `ProjectStore`, and `expand()` itself still does not persist (this contract's no-fire list keeps
  that the caller's job).
- `ui/routes_learn.py::generate_cases` (`POST /projects/{slug}/cases/generate`) — the button, shown
  **only** once `review.status is APPROVED`, so X1 is enforced by the interface as well as by the
  code behind it.

The button's three refusal paths — **no FlowSpec**, **an unapproved FlowSpec** (X1 reaching the
UI), and **no provider with credentials** — each return a themed page carrying a next action, never
a raw `{"detail": …}` blob, and each writes **zero** cases. A refusal that half-persists is worse
than one that refuses, because the operator cannot tell which of the two happened.

**Evidenced, not asserted:** this criterion is only met while a real run of it exists. Against a
real approved `FlowSpec` and a live provider, the button produced **16 cases across 11 classes,
spanning all three `CaseKind`s (best / worst / edge)**, and `autotester expand` produced 10 across
10 classes — the first cases this stage has ever generated outside a `MockProvider`.


## No-fire list

- Actually persisting the produced `Case`s via `ProjectStore.add_case` — that's the caller's job
  (a future CLI command or pipeline orchestrator), not `expand()`'s.
- `Case.rubric_ref`/`script_ref` — left `None`; grading rubrics per expanded case are a future
  concern.
- Real live model calls in the default test suite — `tests/test_expand.py` uses `MockProvider`
  exclusively.
- Merging/deduplicating cases across multiple `expand()` runs on an updated `FlowSpec` — `Case`'s
  own content-addressed id (unchanged by this unit) already makes `ProjectStore.add_case`
  idempotent; this stage does not add its own merge logic on top.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-070 — no contract existed before this cycle.

- 2026-09-09 · /checker (at241-cold-start unit, cycle 1) · **new criterion X6 added** — X1–X5 all
  described what `expand` does when called, and for the whole life of this contract **nothing called
  it**: `expand_flow` had no caller in `src/` or `scripts/`, and 50 of 52 cases across four real
  projects were `happy`. A contract that never asks whether a feature is reachable will pass a
  feature that is not. Routine, non-weakening (adds a criterion, softens none). Re-derived by this
  checker rather than read from the manifest, which had claimed the opposite was still true ("no case
  has yet been generated by the expander on a real product"): driving the **button in a real browser**
  against a live provider produced 16 cases across 11 classes with `best`/`worst`/`edge` all present
  (`qa/evidence/browser-at241-cold-start-2026-09-09-checker/report.json`), and `autotester expand`
  produced 10. All three refusal branches were exercised live and each wrote zero cases — including
  the provider branch, reached honestly by running a server whose root had no credentials. X1 was
  confirmed through the button, not merely in `expand()`: a `needs_edit` spec refused with a themed
  page and no cases. One residual filed rather than folded in: **AT-260** — `autotester expand
  --provider gemini` lets a `ProviderError` escape uncaught, dumping a full traceback and persisting
  nothing; the default `langchain-fallback` path is unaffected. AT-250's 50-of-52 measurement over
  the four REAL projects is untouched — this evidence comes from a synthetic project, and the
  taxonomy firing once does not retroactively populate suites that were never expanded.
