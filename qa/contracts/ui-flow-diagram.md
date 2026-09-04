# Contract — ui-flow-diagram (full branch-tree mindmap of a flow's cases)

**Status:** ACTIVE. The BFS-style companion to `qa/contracts/ui-report.md` UR2's DFS-scoped
per-run step flow — the original mindmap idea from `qa/feedback-inbox.md`'s 2026-09-03 entry,
built in full after being deferred once (as the DFS single-run trace) and then explicitly
asked for again by Umesh: "abhi bhi tune bfs wala setup kiya nhi hai."

## Why this exists

Umesh's original ask: "ek mindmap wise screen by screen kya kya hai and branch by branch
reporting" — a single diagram per flow showing every case's path branching from a shared entry
screen, not one run's single path (that is UR2's DFS trace, a separate, narrower view).

## Criteria

- **FD1 — a real merged tree, not a decoration.** `GET /projects/{slug}/flow-diagram` builds one
  tree per `flow_id` by merging every `Case.steps` sequence for that flow on a genuine common
  prefix (same `action` + `target` + `value` at the same position) — steps shared by every case
  collapse into one chain; the first point of divergence becomes a real branch. This must be
  computed from the actual case data on every request, never a hand-authored diagram.
- **FD2 — every case reachable, no case silently dropped.** Every case belonging to the flow
  appears at exactly one leaf of its flow's tree, labeled with its title and kind
  (best/worst/edge/anchor, colored consistently with the rest of the UI). A flow with only one
  case still renders (a single-branch "tree"). Traceability, not full detail — leaves show the
  case's title/kind, not every step's screenshot (that stays UR2's per-run job).
- **FD3 — honest empty state.** A project with zero cases shows the same empty-state pattern
  every other page in this UI uses, not a raw error or a blank tree.
- **FD4 — no second source of truth.** Reads only through `ProjectStore.list_cases()`, exactly
  like every other UI page (design principle 8) — never a new persisted diagram artifact.

## No-fire list (out of scope for this contract)

- Any run/verdict data (pass/fail coloring, screenshots) — this is a structural map of the test
  suite itself, not a report of one run's outcome. UR2's DFS step-flow remains the place to see
  what a specific run actually captured.
- Cross-project or cross-flow merging — one tree per `flow_id`, never merged across flows.
- Editing the tree from the UI — read-only, exactly like every other UI view of `ProjectStore`
  data.
