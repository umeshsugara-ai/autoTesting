# Gate — T-165 scope + D-039 (hybrid traversal, incremental crawl, change tracking, permission surface, API capture)

**Opened:** 2026-09-24 · **Blocks:** T-165 (and T-166/T-167/T-168/T-169 downstream)
**Evidence:** `docs/research/crawl-reuse-2026-09.md` (spike, licences verified from each repo's LICENSE; orchestrator-corrected: back-navigation replay already exists in `explore_return.py`, AT-227)

## Question
Approve D-039 registering T-165's widened scope, and answer the four spike questions.

## Proposed D-039 (to be appended via scripts/append_decision.ps1 only after approval)
- **Traversal:** `strategy: bfs | hybrid` in explore bounds. Hybrid = BFS maps the portal, then bounded DFS per workflow (Crawljax depth-first candidate ordering, ported as fresh Python — Apache-2, idea only). Explicitly NOT D-023's rejected single happy-path DFS.
- **Replay gap:** extend `_replay_discovery` to re-issue a discovering step's form inputs, not only its click.
- **Incremental crawl:** seed the frontier from `portal_persona.json`; skip a screen whose `(url_template, structural_signature)` matches the stored `PersonaScreen.signature` (Stagehand cache-key pattern, MIT, idea only).
- **Change tracking:** persona revision records new / changed / missing / broken screens + flows (extends `portal_persona.py::_merge` beyond add-only PP2) — feeds T-168.
- **Permission surface:** every reachable control exercised or listed blocked-with-reason; writes only under `write_policy=TEST_ACCOUNT` + per-run `RunApproval`, destructive actions last.
- **API capture:** ADOPT Playwright `page.on('response')` (already a dependency) for first-party API/network assertions.
- **Changes-authorized:** ARCHITECTURE.md "Pipeline" + "Execution model" sections (traversal strategy line) · new contract qa/contracts/crawl-traversal.md (checker drafts).

## Options for the four spike questions
1. Idea-level port of Crawljax (no code copied, cited here + in D-039) needs no extra attribution — **recommend: yes**.
2. Permission-surface coverage: stay inside T-165, or split into its own T-id — **recommend: split** (no reuse candidate, pure build, keeps T-165 checkable in one cycle).
3. Playwright Healer internals unverified — **recommend: park as a later spike**, not blocking.
4. API capture as its own small unit landing before traversal (no dependency on it) — **recommend: yes**.

## Answer format
Reply e.g. "D-039 approve · 1 yes · 2 split · 3 park · 4 yes" (or edits). The maker then appends D-039 with `Approved-by: Umesh`, registers the units in goal.json, and builds.
