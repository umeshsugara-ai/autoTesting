# Manifest — ui-flow-diagram

**Contract:** qa/contracts/ui-flow-diagram.md FD1-FD4 (new this cycle)
**Goal task:** none (`.goal/goal.json` is 20/20 done — direct user feedback, not a plan section)
**Date:** 2026-09-04
**Fix cycle:** 1 of max 3
**Issues addressed:** none

## Why this unit

The original 2026-09-03 mindmap ask ("ek mindmap wise screen by screen kya kya hai and branch
by branch reporting") was built partially this session as F-028's DFS per-run trace (one case's
own path). Umesh, after seeing F-028: "abhi bhi tune bfs wala setup kiya nhi hai" — explicitly
asked for the other half: the full branch tree, every case's path merged from a shared entry
screen, branch by branch — not deferred any further.

## What changed

- `qa/contracts/ui-flow-diagram.md` (new) — FD1 (a real merged tree computed from case data on
  every request, never hand-authored) · FD2 (every case reachable at exactly one leaf, labeled
  by title/kind) · FD3 (honest empty state) · FD4 (no second source of truth — reads only
  `ProjectStore.list_cases()`).
- `src/autotester/ui/routes_flow_diagram.py` (new) — `GET /projects/{slug}/flow-diagram`. The
  actual algorithm: `_insert` walks each `Case.steps` into a shared trie (`_Node`), keyed by
  `action + target (+ value)` at each position — steps identical across cases collapse into one
  chain node; the first differing step becomes a real branch. `_build_forest` groups by
  `flow_id` (one tree per flow, per FD1's no-cross-flow-merge rule). Rendered as a nested
  `<ul>`/`<li>` tree; leaves carry the case's title + a kind-colored pill (best=green,
  worst=red, edge=amber, anchor=grey).
- `src/autotester/ui/theme.py` — `_PILL_CLASS` gains a `"danger"` tone (`badge-fail` red) for
  worst-case leaves — pills previously had no way to render red (only badge() did, for test
  RESULTS specifically, a different vocabulary from case KIND).
- `src/autotester/ui/theme.py` / **new** `src/autotester/ui/theme_style.py` — split the raw CSS
  template (`PAGE_STYLE`) out of `theme.py` into its own module (adding the tree CSS pushed
  `theme.py` to 310 lines, over the 300-line design limit) — `theme.py` keeps only the Python
  component functions; `theme_style.py` is pure style, imported once. Also added `.flow-tree`
  org-chart CSS (connector lines via `::before`/`::after`, the standard CSS-only tree pattern).
- `src/autotester/ui/app.py` — wired `routes_flow_diagram.router`; added a "🌳 Flow diagram"
  link to `project_detail()`'s actions card (per-project, so it belongs there, not the global
  nav — unlike Settings/Live view which are project-agnostic).
- `tests/test_ui_flow_diagram.py` (new, 5 tests) — empty-state; every case appears exactly
  once; shared-prefix steps render only once while the actual divergence (two different
  `password` fill values) both appear; cases group into separate trees per `flow_id`; the link
  is reachable from `project_detail`.
- `qa/feedback-inbox.md` — logged the follow-up ask verbatim before building.

## A security question raised and resolved during this unit's own verification

Live on `pathlynks`, the WORST case's step tree showed
`fill: input[name="password"] = Wr0ng-Password-Deliberately-Not-Real!` in plain text — paused to
check this wasn't a new credential leak. Confirmed it is **not**: this literal value already sits
in plain text in `projects/pathlynks/cases.jsonl` on disk (checked directly) — it is the case
author's own deliberately-fake test value, never a real secret. The actual secret boundary held
correctly: the BEST case's real credentials render as the literal placeholder text
`{{SECRET:PATHLYNKS_USER_EMAIL}}` / `{{SECRET:PATHLYNKS_USER_PASSWORD}}` — never substituted,
never a real value — because `_step_key` renders `Step.value` exactly as stored on the `Case`
object, and a `Case`'s own declared values (placeholder or literal test data) were never inside
the redaction boundary to begin with (only a *substituted, runtime* secret value is). No change
needed; documented here so the checker verifies this reasoning rather than re-deriving it.

## Deliberate scope decisions (per the contract's own no-fire list)

- No run/verdict coloring on this page — it is a structural map of the suite itself; UR2's
  per-run DFS step-flow remains the place to see what a specific run actually captured.
- No cross-flow merging — one tree per `flow_id`, exactly as FD1 requires.
- Read-only — no edit-from-UI affordance, matching every other `ProjectStore` view in this UI.

## Real verification performed (not simulated)

```
$ uv run pytest tests/test_ui_flow_diagram.py -v   # 5 passed
$ uv run pytest -q                                  # full suite green, no regressions
$ uv run ruff check src tests scripts               # All checks passed!
$ uv run autotester doctor                          # doctor: clean (file-too-long on theme.py
                                                     #   resolved by the theme_style.py split)
$ uv run autotester map                             # docs/MAP.md regenerated
```

**Real live Docker verification against the real `pathlynks` project (not a demo):**

```
$ docker compose restart && curl http://localhost:8010/   # 200
```
- Navigated to `/projects/pathlynks/flow-diagram`, took a real screenshot: one tree
  (`Flow: flow_login`) with a genuine merged structure —
  `navigate: /signin` → `fill: identifier = {{SECRET:PATHLYNKS_USER_EMAIL}}` (shared by all 3
  real cases, rendered exactly once) → branches: BEST continues through the real password
  placeholder to its own leaf; WORST branches off at its own (fake) wrong-password fill to its
  own leaf; EDGE branches directly off the shared prefix straight to a `click: submit` leaf
  (its case has only 2 steps). Kind pills render green/red/amber for best/worst/edge
  respectively, exactly as designed.

## How to verify

- `uv run pytest tests/test_ui_flow_diagram.py -v` → 5 passed.
- `uv run pytest -q` / `ruff check` / `autotester doctor` → all clean.
- Open `/projects/pathlynks/flow-diagram` in a real browser — confirm one merged tree per flow,
  shared steps appearing once, real divergence at the actual differing step, no placeholder or
  secret value ever shown as anything but its own declared literal/placeholder text.

## Scope notes for the checker

- Please confirm FD1's actual claim independently — that the merge is genuinely computed from
  case data (e.g. add a case with a slightly different step and confirm the tree reflects it),
  not a static/hardcoded rendering that happens to look right for pathlynks today.
- Please also independently judge the security question above — read `_step_key` yourself and
  confirm it never has access to a real substituted secret value, only the `Case`'s own stored
  `Step.value` (placeholder or literal), matching the credential-boundary architecture.

## Status: ready-for-check
