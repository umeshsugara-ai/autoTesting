# Verdict — ui-flow-diagram

**Date:** 2026-09-04
**Cycle checked:** 1
**Contract:** qa/contracts/ui-flow-diagram.md (FD1–FD4)
**Manifest:** qa/manifests/ui-flow-diagram.md

## What I re-ran myself

- `uv run pytest tests/test_ui_flow_diagram.py -v` → 5 passed (reproduced independently).
- `uv run pytest -q` → full suite green, no regressions (2 pre-existing skips, unrelated).
- `uv run ruff check src tests scripts` → All checks passed!
- `uv run autotester doctor` → doctor: clean (`theme.py` 93 lines, `theme_style.py` 226 lines —
  neither over the 300-line limit; the split genuinely resolved the prior overage).
- **Independent FD1 probe (own scratch test, not the manifest's):** wrote a fresh test with a
  brand-new `flow_id="signup"` and two cases that diverge on a step never seen in the shipped
  test suite (`click: phone-tab` vs `click: email-tab`, then a novel `fill: phone = 9999999999`
  leaf). The rendered tree correctly collapsed the shared `navigate: /signup` prefix to one
  occurrence and correctly produced a new branch at the actual divergence point — this proves
  `_insert`/`_build_forest` compute the merge from case data live, not a static rendering that
  happens to fit the shipped fixtures.
- **Live Docker check** (`docker compose restart` already applied per the manifest;
  `GET http://localhost:8010/projects/pathlynks/flow-diagram` → HTTP 200, real GET only):
  rendered exactly one tree, `Flow: flow_login`, with `navigate: https://pathlynks.vidysea.com/signin`
  and `fill: input[name="identifier"] = {{SECRET:PATHLYNKS_USER_EMAIL}}` appearing exactly once
  each (shared prefix collapsed across all 3 real cases), branching at
  `fill: input[name="password"]` into the BEST leaf (placeholder
  `{{SECRET:PATHLYNKS_USER_PASSWORD}}`, pill `badge-pass`/green) and the WORST leaf (literal
  `Wr0ng-Password-Deliberately-Not-Real!`, pill `badge-fail`/red), with EDGE branching directly
  off the shared prefix to its own `click: button[type="submit"]...` leaf (pill `badge-blocked`,
  which resolves to `--blocked: #b45309` — genuinely amber, confirmed by reading
  `theme_style.py:22-24`). Exactly 3 pill spans total on the page (`grep`'d the actual
  `<span class='badge ...'>` elements, not raw class-name occurrences, which also match the CSS
  rule definitions in `PAGE_STYLE`) — matches FD2's "every case at exactly one leaf" with no
  duplicate/dropped case.

## Security question — independently re-verified, not re-derived from the manifest's reasoning

Read `src/autotester/ui/routes_flow_diagram.py:31-33` (`_step_key`) myself: it only ever reads
`step.value` off the `Case` object exactly as constructed/loaded — there is no call anywhere in
`routes_flow_diagram.py` into the secret-substitution path (`{{SECRET:...}}` resolution happens
at `page.fill()` time per `core/redact.py`/browser execution, a completely different code path
this route never touches). A `Case`'s own declared step values — whether a real project's literal
placeholder text or a deliberately-fake literal test string — were never inside the runtime
redaction boundary to begin with.

Independently confirmed the WORST case's plaintext value is pre-existing, not introduced by this
unit: read `projects/pathlynks/cases.jsonl` directly (not via the manifest's claim) —
`Wr0ng-Password-Deliberately-Not-Real!` already sits there in plain text on disk for the WORST
case's `password` step, and the BEST case's password step is stored as the unresolved literal
`{{SECRET:PATHLYNKS_USER_PASSWORD}}`, never a real credential. No credential leak. No change
needed.

## Criteria

- **[FD1] MET** — merge is genuinely computed on every request from `Case.steps` (own probe with
  a novel case/flow above), not hand-authored or fixture-fitted. Verified against real pathlynks
  data too.
- **[FD2] MET** — every case appears at exactly one leaf, labeled by title + kind-colored pill
  (best=green/`badge-pass`, worst=red/`badge-fail`, edge=amber/`badge-blocked`, anchor=grey/
  `badge-inconclusive` per `_KIND_TONE`/`_PILL_CLASS`, confirmed in `theme.py:21,55-58` and the
  actual color tokens in `theme_style.py`). Single-case flow renders fine structurally (a
  root-to-leaf chain with no branch) — covered by the shipped fixtures' EDGE case (2 steps) and
  my own probe.
- **[FD3] MET** — `test_empty_project_shows_an_honest_empty_state` reproduced; route (line 89-93)
  uses the shared `theme.empty_state()` helper, same pattern as every other page — not a raw
  error or blank tree.
- **[FD4] MET** — `routes_flow_diagram.py` calls `store.list_cases()` (line 88) and nothing else
  reads or writes persisted state; grepped the file for any `open(`/`write`/`.jsonl` — only the
  one `list_cases()` call exists. No new diagram artifact.

## Invariants

- No run/verdict coloring present on the page (checked the live render and the source — only
  case KIND drives pill color, never a run RESULT) — holds, matches the no-fire list.
- One tree per `flow_id`, no cross-flow merge (`_build_forest` groups by `case.flow_id` before
  inserting) — holds, confirmed by `test_cases_are_grouped_by_flow_id_into_separate_trees` and by
  reading `_build_forest`.
- Read-only — no POST/edit affordance in `routes_flow_diagram.py` (only one `@router.get`) — holds.

## Issues addressed

None claimed by the manifest; none found requiring a new issue.

VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 3/3 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: The merged branch tree is genuinely computed from live case data (verified both with
an independent probe case never in the shipped tests and against the real pathlynks project via
the live Docker container), every case reaches exactly one correctly-colored leaf, the empty
state matches the shared UI pattern, and the route reads only through `ProjectStore.list_cases()`
with no second source of truth. The flagged security question is confirmed non-issue: `_step_key`
has no path to a runtime-substituted secret, and the WORST case's plaintext fake password was
already on disk in `cases.jsonl` before this unit, independently verified rather than taken on
the manifest's word. This is the genuine BFS-style merged branch tree Umesh asked for a second
time, distinct from F-028's DFS single-run trace — every case's path merges from a shared entry
and branches only where they actually diverge.
