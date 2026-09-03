# Manifest — t070-expand

**Contract:** qa/contracts/expand.md (X1–X5, new this cycle) + qa/contracts/review-gate.md
(R1-R4, dependency) + qa/contracts/ingest.md (I1-I5, dependency)
**Goal task:** T-070 (`user_value: high`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none directly (advances the pipeline)

## Why this unit

Umesh: "don't stop until you achieve the /goal." T-070 was the next unblocked, high-value unit
(deps=[T-060, T-065], both done) and is explicitly named "the differentiator" in its own
goal-task note.

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-070 stages/expand.py: FlowSpec -> cases covering every
applicable CaseClass"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for expand. Wrote `qa/contracts/expand.md` (X1–X5) before writing any code.

## What changed

- `qa/contracts/expand.md` (new) — X1 (refuses unreviewed FlowSpec) · X2 (happy case is the
  flow's own steps, no model call) · X3 (deterministic-where-confident class applicability,
  D-004) · X4 (a decline produces no case) · X5 (prompt instructs no real-looking fake secrets).
- `src/autotester/schema/case.py` — added `ExpandedSteps` (the model's raw answer for one
  class — `steps[]` + a mandatory `rationale`; empty `steps` means "not applicable"). No
  existing class changed.
- `src/autotester/prompts/expand_case_v1.md` (new) — the per-class expansion prompt: keep
  unrelated steps unchanged, modify only what the scenario needs, decline (empty steps) if it
  genuinely doesn't apply, never write a real-looking credential.
- `src/autotester/stages/expand.py` (new, 118 lines) — `applicable_classes(flow)` (deterministic
  input/auth detection from step shape + the 8 always-asked universal classes),
  `build_expand_prompt`, `expand_flow(flow, project, provider, docs=None)` (one `Case` per
  applicable class, `HAPPY` built directly with no model call), `expand(spec, provider,
  docs=None)` (calls `require_reviewed` first, then `expand_flow` over every flow).
- `tests/test_expand.py` (new, 8 tests) — login flow (has fill + auth fields) gets input/auth
  classes; a no-fill flow skips them but still gets universal classes; the login flow produces
  **>=12 cases** (matches the goal task's own acceptance bar verbatim); the happy case's steps
  are the flow's own steps unchanged; a model declining every class leaves only the happy case;
  `expand()` refuses a `DRAFT` `FlowSpec` (raises `FlowSpecNotReviewed`); `expand()` runs every
  flow once approved; the prompt is read from a file and interpolates correctly.
- `docs/ARCHITECTURE.md` — concept→file row for `stages/expand.py::expand`; merged the
  standalone "Anthropic provider" row into the multi-vendor fallback row to make room (net zero
  line change — table entries are getting dense enough that this contract's own checker may want
  to flag a future consolidation pass); Status line updated (expand.py built, Next = coverage.py
  + ui/). 150 lines (at the C2 cap, not over — `doctor`'s check is `> 150`).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## How to verify (commands + expected)

- `uv run pytest tests/test_expand.py -v` → 8 passed
- `uv run pytest -q` → exit 0, 171 collected
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 150 (≤ 150)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_expand.py -v
........                                                                 [100%]
8 passed
$ uv run pytest -q
................................s....................................... [ 42%]
........................................................................ [ 84%]
...........................                                              [100%]
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- Per the no-fire list: this stage does NOT call `ProjectStore.add_case` itself (returns the
  `list[Case]`, persistence is the caller's job); rubric/script refs are left `None`; no live
  model call anywhere in the default test suite.
- X5's "never a real secret literal" guarantee is a **prompt-level instruction**, verified by
  reading `prompts/expand_case_v1.md`, not independently enforced by code in this unit — flagged
  explicitly rather than overclaimed, since `expand.py` has no mechanism of its own to detect or
  reject a model answer that ignored the instruction. Any case this stage produces still passes
  through `execute.py`'s existing credential boundary (`{{SECRET:KEY}}` resolution, domain
  scoping) unchanged before it could ever touch a real browser — that boundary, not this stage,
  is the actual safety net.
- `applicable_classes`'s auth-detection (`_has_auth_field`) checks for the substring `"SECRET"`
  in a `FILL` step's value — matches the `{{SECRET:KEY}}` placeholder convention used everywhere
  else in this codebase (`core/redact.py::PLACEHOLDER_RE`), not a new convention.
- No secrets touched — this unit has no credential surface; test fixtures use fake target/value
  strings only.

## Status: checked-PASS

Reconciliation note (2026-09-03): this manifest was never flipped from ready-for-check at the time, even though qa/verdicts/t070-expand.md recorded PASS and the unit shipped (see docs/FEATURES.jsonl / .goal/goal.json). Corrected during a disk-state reconciliation pass -- no re-check performed, no new claim made; the verdict file is the actual evidence, this is only the manifest catching up to it.
