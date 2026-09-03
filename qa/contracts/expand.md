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
