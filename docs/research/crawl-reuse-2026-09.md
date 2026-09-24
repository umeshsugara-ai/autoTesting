# Crawl-reuse spike — traversal, incremental crawl, healing, API capture (2026-09-24)

**Purpose:** verified licence + mechanism for each candidate tool behind T-165 (hybrid BFS/DFS traversal, incremental crawl seeded from the persona, change tracking, permission-surface coverage, back-navigation recovery, API assertions) — extends `market-2026-09.md`, does not repeat it.
**Open me when:** designing T-165 units, or deciding whether a crawl mechanism is ADOPT / PORT / AVOID.

## Summary table

| Tool | Licence (verified) | Verdict | Maps to |
|---|---|---|---|
| Crawljax | Apache-2.0 | **PORT** algorithm only (Java) | `stages/explore.py` traversal strategy + backtrack |
| Scrapling | BSD-3-Clause | **PORT** pattern | future locator-heal / control-identity layer, `stages/screen_identity.py` |
| Stagehand | MIT | **PORT** cache-key pattern | incremental crawl, `stages/explore_node.py` skip-unchanged check |
| Playwright Test Agents (Healer) | Apache-2.0 (bundled in Playwright, already a dependency) | **AVOID** as a tool | not a fit for the crawler; mechanism itself is opaque in public docs |
| Crawlee (Apify) | Apache-2.0 | **PORT** pattern | frontier prioritisation, `schema/screen_graph.py::CrawlFrontier` |
| Playwright HAR / `page.on('response')` | Apache-2.0 (already a dependency) | **ADOPT** — already available, just wire it | network/API assertion capture, `browser/session.py`, `stages/execute.py` |
| browser-use (recovery/stuck-state) | MIT | **AVOID** — immature | back-navigation recovery (Crawljax's replay pattern covers this instead) |

No licence in this table is UNVERIFIED — each was read from the project's own `LICENSE` file on GitHub (raw.githubusercontent.com), except Playwright Test Agents' healer internals, which are not published anywhere beyond marketing-level docs (flagged below).

---

## 1. Crawljax — state-flow graph, DFS, backtrack-by-replay

**Licence:** Apache License 2.0, verified at `raw.githubusercontent.com/crawljax/crawljax/master/LICENSE`.

**Mechanism** (verified from `core/src/main/java/com/crawljax/core/Crawler.java` on GitHub, plus community secondary sources for corroboration):

- **State equality:** a `StateComparator`-backed `StateVertex.equals()` decides whether a newly observed DOM is "the same state" as one already in the graph (`domChanged(Eventable, StateVertex)` compares `newState` against `stateMachine.getCurrentState()`). This is the same job our `screen_identity.py::structural_signature` already does (structural, not URL-only, not free-text) — Crawljax's contribution is the *comparator being pluggable*, not a better signature.
- **Traversal:** depth-first with a hard `maxDepth` — `if (maxDepth == depth) { … stop } else { parseCurrentPageForCandidateElements(); }`. Depth increments per newly-discovered state, not per action, so it maps cleanly onto "bounded DFS per workflow."
- **Backtracking:** Crawljax does **not** use the browser back button and does **not** keep live DOM snapshots to restore. It calls `reachFromHome()`, which computes the shortest path from the index/seed state to the target state through the already-built graph and **replays the stored `Eventable`s** (the clicks/fills that got it there the first time) — "Backtracking by executing {} on element." A fresh `StateMachine` is created and `browser.goToUrl(url)` re-anchors to the seed before replay starts.

**Maps onto AutoTester:** already built. `stages/explore_return.py::return_to` (AT-227) tries browser-back, then the node URL, then `_replay_discovery`, which recursively returns to the parent via `ExploreRuntime.discovery` and re-performs the discovering edge — a replay chain toward the seed bounded by `MAX_REPLAY_DEPTH`. That is Crawljax's `reachFromHome` in substance. **Genuinely missing:** (a) replay re-issues only `click(edge.target)`, never the `fill` values a form step needed, so a screen behind a filled form cannot be re-entered; (b) there is no DFS/hybrid `strategy` — `_bfs` pops FIFO. Port Crawljax's event-sequence replay (clicks AND form inputs) and its depth-first candidate ordering, not the backtrack itself.

**Verdict: PORT.** Java, GPL-adjacent-nothing (Apache-2.0 is fine to read and reimplement), but a JVM dependency has no place in this Python codebase. Reimplement the two ideas — pluggable state-equality hook (already have it) and replay-from-seed backtracking (do not have it) — directly in `explore.py`/`explore_node.py`.

---

## 2. Scrapling — structural-profile fingerprint for element relocation

**Licence:** BSD-3-Clause, verified at `raw.githubusercontent.com/d4vinci/Scrapling/main/LICENSE` ("Copyright (c) 2024, Karim shoair").

**Mechanism** (verified from the project README plus a corroborating secondary technical writeup; Scrapling's own docs describe the *capability*, not the algorithm by name — flagged below):

- Scrapling calls this "Smart Element Tracking." It stores a **structural profile** of an element combining multiple independent signals — **tag, text/content, parent context, position** — rather than one brittle identifier (a single CSS class or XPath index).
- On a later parse of a changed page, it uses a similarity-scoring match over that same signal set to find the closest surviving element, so a class-name rename or container restructure alone doesn't break the reference.
- **Not independently verified from source:** the exact similarity function (edit distance? weighted signal sum?) and how many signals must match to accept a relocation. Public docs describe the feature and its inputs but not the scoring formula. Flag as **partially verified** — the mechanism's inputs are confirmed, its scoring internals are not.

**Maps onto AutoTester:** this is not our crawler's job today (we don't need to re-find a broken CSS selector — `screen_identity.py` already treats identity structurally, and `execute.py` runs pre-authored `case.steps`). It becomes relevant the day `agent_loop.run_with_fallback` (D-031, unwired) needs to repair a broken step in a durable `Script` — Scrapling's multi-signal fingerprint (tag + text + parent + position) is a good starting shape for `case.steps[i].target` re-resolution, since it doesn't depend on one selector surviving a redesign.

**Verdict: PORT the pattern**, not now — park it as the fingerprint shape for D-031's eventual healer, not for T-165 itself. No dependency: reuse the *signal list*, write our own scorer.

---

## 3. Stagehand — action-cache key and invalidation

**Licence:** MIT, verified at `raw.githubusercontent.com/browserbase/stagehand/main/LICENSE`.

**Mechanism** (verified from `docs.stagehand.dev/v3/best-practices/caching`, browserbase.com blog):

- **Cache key composition:** for `act()`, the key is derived from the instruction text + normalized URL (some tracking query params stripped) + relevant options; for `agent()` calls, from instruction + start URL + agent execution options/config. The accessibility-tree/DOM content also factors in — different a11y trees (from viewport, injected third-party DOM, etc.) produce different keys.
- **Storage:** either Browserbase's managed server-side cache, or a local filesystem cache under a configurable `cacheDir` — no separate DB.
- **Invalidation triggers (all confirmed from docs):** page content/structure changes → cache miss, LLM is called again; URL changes (dynamic URLs defeat the key); accessibility-tree differences from environment; instruction wording changes. **Not documented:** what happens specifically when a cached selector's target element is gone (a "selector not found" case) — Stagehand's docs don't separate that from the general "content changed" bucket. Flag as **not fully specified** by the vendor, not guessed here.

**Maps onto AutoTester:** this is the direct pattern for T-165's incremental-crawl requirement ("second crawl on an unchanged fixture issues ≤10% of the first crawl's actions"). We already have the ingredient Stagehand doesn't cleanly separate out — `screen_identity.py::structural_signature` is exactly a DOM/a11y-shape hash. The port is: before `explore_node.visit_node` acts on a node, compute its `PersonaScreen.key()` (`url_template` or folded name) plus `structural_signature`, look it up against `portal_persona.json`'s stored `PersonaScreen.signature` (already a field, `schema/portal_persona.py:65`), and skip re-exploring children whose signature is unchanged from the last run — same idea as Stagehand's DOM-hash-in-the-key, applied as a skip gate instead of an LLM-call gate.

**Verdict: PORT the cache-key composition idea** (URL + structural signature = key; signature-changed = invalidate). No dependency — we already have both ingredients, just not wired together across runs.

---

## 4. Playwright Test Agents (Healer)

**Licence:** bundled in the Playwright project, Apache License 2.0, verified at `raw.githubusercontent.com/microsoft/playwright/main/LICENSE` ("Apache License / Version 2.0"). Playwright itself is already a direct dependency (`browser/session.py`).

**Mechanism** (verified from `playwright.dev/docs/test-agents` and corroborating third-party writeups — the primary doc itself is high-level):

- Three agents: **Planner** (explores the app, writes a Markdown test plan), **Generator** (Markdown plan → runnable `*.spec.ts`, verifying selectors live against the app), **Healer** (runs the suite, and on a failing test replays the failing steps, inspects the current UI for "equivalent elements or flows," patches the locator/wait/data, and re-runs until pass or a guardrail stops it).
- **What is NOT documented anywhere public:** the healer's actual signal set for "equivalent element" — whether it uses the accessibility snapshot, a DOM diff, or something else — and its acceptance criterion beyond "the test then passes." Playwright's own docs use the phrase "inspects the current UI" without specifying the representation. This is a genuine gap in public information, not a research shortcut: I could not find the healer's matching algorithm in the Playwright repo, docs, or blog. **Flag: UNVERIFIED mechanism internals** (licence is verified; the algorithm is not).

**Maps onto AutoTester:** conceptually this is the same slot as `stages/agent_loop.py::run_with_fallback` (D-031, unwired) — "fix one broken step, persist the corrected case." But Test Agents is a whole authored-test-suite product (Planner writes TypeScript tests from a live walkthrough), not a crawler or an incremental-persona system; adopting it would mean running a second, parallel test-generation pipeline next to FlowSpec/Case, which duplicates a concept this project already owns.

**Verdict: AVOID as a tool.** The one idea worth keeping — "replay the failing steps, inspect the current UI, try again, bounded by guardrails" — is already better specified by Crawljax's `reachFromHome` (§1) for crawl backtracking, and by our own `agent_loop.run_with_fallback` scaffold for step repair. Nothing here earns a new dependency or a ported algorithm beyond what's already planned.

---

## 5. Crawlee (Apify) — frontier prioritisation

**Licence:** Apache License 2.0, verified at `raw.githubusercontent.com/apify/crawlee/master/LICENSE.md`.

**Mechanism** (verified from `crawlee.dev/js/docs` API reference pages):

- `RequestQueue` is a FIFO-with-priority, self-deduplicating queue. Deduplication key (`uniqueKey`) is auto-derived from the URL (lowercased, query params sorted, fragment stripped) — two different-looking URLs that are semantically the same request collapse to one queue entry.
- Priority is `forefront: true` — a request pushed with this flag jumps to the front of the queue instead of the back, used for "found something more important, explore it next."
- `enqueueLinks` ships pluggable strategies (`All`, `SameDomain`, `SameHostname`, etc.) for which discovered links get queued at all — a policy layer sitting in front of the queue, not mixed into it.

**Maps onto AutoTester:** `schema/screen_graph.py::CrawlFrontier` today is a plain FIFO list (`explore.py:184` `.pop(0)`) with no dedup-by-normalized-URL and no priority. Two of Crawlee's three ideas are directly portable: (a) a `uniqueKey`-style normalized-URL dedup before a candidate ever reaches the frontier (we likely already avoid exact dupes via node identity, but not near-dupe URLs with different query-param order), and (b) a `forefront` flag for the DFS-per-workflow case — when the crawl commits to going deep on a workflow, pushing its next step to the front of the queue rather than waiting behind the BFS backlog is precisely how "BFS maps, then bounded DFS per workflow" would be implemented without two separate queues.

**Verdict: PORT the pattern** (normalized-URL dedup key + forefront priority flag). No dependency — Crawlee is a whole crawling framework (request lifecycle, storage, proxies) we do not want; we want two small ideas out of `RequestQueue`.

---

## 6. Playwright HAR / `page.on('response')` — network assertion capture

**Licence:** Apache License 2.0 (Playwright itself), verified as in §4. **Already a direct dependency** — no new licence exposure at all.

**Mechanism** (verified from `playwright.dev/docs/mock` and `playwright.dev/docs/network`):

- `page.on('response')` / `page.on('request')` gives a live event stream of every network call during a page's lifetime — usable to assert "this API call happened, returned this status/shape" as a first-party fact, independent of what the UI rendered.
- `context.routeFromHAR()` / `page.routeFromHAR()` can additionally record a full HAR (HTTP Archive) of a session for later deterministic replay, and `page.route()` handlers can intercept a specific endpoint before falling through to a HAR or the live network.

**Maps onto AutoTester:** this is the concrete mechanism for the "first-party API/network assertions" item in Umesh's next-features list, and it sits naturally beside the existing deterministic-assertions pattern (`browser/assertions.py`, D-032 — "records each expectation's met|unmet fact… the grader alone still owns every verdict"). A network assertion is the same shape: during `run_case`/crawl visitation, record observed `(method, url_template, status)` facts as evidence, never as judgement — the grader still decides. No new dependency, since Playwright already drives every browser interaction in `browser/session.py`.

**Verdict: ADOPT — already available, wire it.** This is the one item in this spike that costs zero new licence surface and zero new algorithm design; it's a missing wiring unit, not a research question.

---

## 7. browser-use — stuck-state / back-navigation recovery

**Licence:** MIT, verified at `raw.githubusercontent.com/browser-use/browser-use/main/LICENSE`. (browser-use's *secrets* pattern was already reused per `market-2026-09.md`; this section evaluates a different mechanism — recovery.)

**Mechanism** (verified from browser-use's own GitHub issue tracker, not marketing docs — the most honest source for an in-progress mechanism):

- The maintainers' own open issues describe stuck-state handling as **heuristics over the trajectory**, not a solved mechanism: "detecting when an agent is stuck relies on heuristics… rather than the agent telling developers directly," agents can be observed "repeating the same step infinitely" (issue #1157), and there is "no automatic page-crash recovery" (issue #5067) as of this scan. A structured "per-action causal summary" (did the page actually change?) is a proposal, not shipped.

**Maps onto AutoTester:** this would have been the candidate for SPA back-navigation recovery in `explore_node.py`/`ExploreRuntime.return_error` (already a scratch field named for exactly this failure). It does not hold up — the project itself documents this as unsolved.

**Verdict: AVOID.** Not mature enough to port; Crawljax's replay-from-seed pattern (§1) already covers "how do I get back to a state I've left" more concretely and is what should be ported for this need instead.

---

## Recommended porting order for T-165

1. **Traversal strategy** (BFS map → bounded DFS per workflow) — port **Crawljax's** depth-first candidate ordering: keep the existing structural comparator (`screen_identity.py`, unchanged) and add a `strategy` mode (bfs | hybrid) to `explore.py`'s bounds/policy. Back-navigation already exists (`explore_return.py::return_to` + `_replay_discovery`, AT-227); the gap to close is replaying the **form inputs** of a discovering step, not only its click, so DFS can re-enter screens behind filled forms. (Corrected 2026-09-24 by the orchestrator: the spike first reported `ExploreRuntime.discovery` as unused; it is used at `explore_node.py:114` and `explore_return.py:84`.)
2. **Incremental crawl** (skip unchanged screens) — port **Stagehand's** cache-key composition: `(url_template, structural_signature)` looked up against `portal_persona.json`'s stored `PersonaScreen.signature` before visiting a node.
3. **Change tracking** (new/changed/missing/broken) — combine **Crawljax's** state-equality check (a stored signature now differs = "changed") with a "seen in a prior crawl but not this one" pass over `portal_persona.json`'s existing screens (= "missing"), extending `portal_persona.py::_merge` beyond its current add-only PP2 behaviour into a real diff. No external tool covers this end-to-end; it is a genuine build, informed by both §1 and §3's verified inputs.
4. **Permission-surface coverage** (every reachable control exercised or blocked-with-reason) — no tool in this spike does this job directly; **Scrapling's** multi-signal structural profile (§2) is the closest reusable *shape* for stably identifying "the same control" across runs (so "exercised" state persists even after a minor DOM change), feeding `crawl_coverage.py`. Lower priority than 1-3; can follow once control identity is needed for coverage math, not just screen identity.
5. **API/network assertions** — **ADOPT** Playwright's own `page.on('response')`/HAR support directly (§6); this is a wiring unit alongside `browser/assertions.py`'s existing D-032 pattern, not a design question.

## Open questions for Umesh

1. Crawljax's algorithm is confirmed Apache-2.0 and its *code* is Java (never imported); we'd port the *idea* (state-equality hook + replay-from-seed backtrack) as fresh Python. Confirm that idea-level porting (no code copied, cited in this doc and in the DECISIONS entry) needs no separate attribution beyond what's already here.
2. Item 4 (permission-surface coverage) has no strong reuse candidate — it may be a pure-build unit rather than a "port X" unit. Confirm it stays inside T-165's scope as currently proposed rather than splitting into its own T-id.
3. Playwright Test Agents' Healer mechanism is UNVERIFIED beyond "inspects the current UI, retries." If it matters for D-031 (the still-unwired `agent_loop.run_with_fallback`), that needs its own later spike against the actual `@playwright/agents` source once it's out of a "docs-only" state — not blocking T-165, flagging so it isn't silently dropped.
4. Section 6 (API assertions) is ready to wire with zero new research. Should it land as its own small unit ahead of 1-4, since it has no dependency on the traversal-strategy work landing first?
