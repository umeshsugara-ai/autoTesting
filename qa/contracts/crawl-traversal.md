# Contract — crawl-traversal (hybrid BFS+bounded-DFS, form replay, incremental crawl, change tracking)

**Status:** DRAFT (goes DRAFT->ACTIVE on T-165's first checker PASS).
**Criticality:** CRITICAL — T-165 stays a **dual check** per D-040 (two independent checkers,
`qa/verdicts/<slug>.md` and `qa/verdicts/<slug>.b.md`, same protocol as `explore.md`'s own X-series
work). This contract governs code that widens what the explorer visits and re-visits automatically,
in a real browser against a real product — the same criticality class `explore.md` itself carries.
**Feature:** widens T-165 in place (D-040), on top of the existing bounded-BFS crawl
(`qa/contracts/explore.md`, unamended by this contract — see "Relationship to explore.md" below):
a `strategy: bfs | hybrid` traversal mode, form-input replay in `_replay_discovery`, an incremental
crawl seeded from `portal_persona.json`, and change tracking (new/changed/missing/broken) extending
`portal_persona.py::_merge` beyond add-only PP2.
**Covers:** goal task T-165. **Deps:** T-163 (orchestrator, done), T-144 (crawl report, done).
**Grounding:** D-040 (authorization, exact scope); `docs/research/crawl-reuse-2026-09.md` (verified
licences + ported mechanisms: Crawljax Apache-2.0 idea-port for traversal, Stagehand MIT idea-port
for the incremental cache-key); `.goal/goal.json` T-165's note (frontier-completeness wording,
carried forward verbatim into CR5); Umesh, `qa/feedback-inbox.md` 2026-09-23T07:30 (source demand).

## Relationship to `explore.md` (read first — this contract does not replace it)

`explore.md`'s X1-X18 govern the crawl's identity, safety matrix, dialog handling, artifact
durability and merge discipline; **none of them are amended, softened, or duplicated here.** This
contract governs only the four widenings D-040 named. In particular:
- X1 (only `explore.py` invents a click), X2 (actuator chokepoint), X5/X6 (the safety matrix,
  deny-list, never-click), X10/X10-b (nothing typed except synthetic values under the four gated
  conditions) are **byte-unchanged and still in force** — every criterion below that touches
  clicking or typing is a *replay of an action already permitted once*, never a new kind of action.
- X3 (structural identity), X13/X14 (propose-never-approve, conflicts kept not resolved) are the
  identity and merge primitives this contract's incremental/change-tracking criteria are built on
  top of, not around.
- Permission-surface coverage (every reachable control exercised or blocked-with-reason) and
  first-party API/network assertions were both split OUT of T-165 by D-040, into T-171 and T-170
  respectively — **not this contract's job** (see no-fire list).

## Criteria (CR1-CRn) — each judged on re-runnable evidence

### CR1 — Traversal strategy is explicit, bounded, and does not revive D-023's rejection
A `strategy: bfs | hybrid` field governs traversal. `bfs` is byte-identical to today's FIFO
`_bfs`/`.pop(0)` behaviour (`stages/explore_node.py`). `hybrid` means: BFS still maps the whole
portal first — every discovered screen is still enqueued breadth-first — and, per discovered
workflow, a **bounded** depth-first descent (Crawljax's depth-first candidate ordering, ported as
fresh Python per `crawl-reuse-2026-09.md` §1 — idea only, no code copied, Apache-2.0 read
permission) goes deeper than plain BFS would before backtracking. `hybrid` invents no new bound: it
is governed by the same `max_screens`/`max_actions`/`wall_clock_s`/`max_depth` from X4, unchanged.
This is explicitly **not** D-023's rejected single happy-path DFS — D-023 rejected DFS as the
*only* traversal (a single depth-first line through the portal, never mapping the whole thing);
`hybrid` here always maps breadth-first first and only then goes deep, per workflow, bounded.

**Falsifiable (D-040's acceptance test (a)):** on a fixture site with a workflow at least N screens
deep behind a branch BFS would ordinarily defer, a `hybrid` crawl under a fixed action budget
reaches a depth-N screen that a `bfs` crawl under the *same* budget does not.

### CR2 — Form-input replay: `_replay_discovery` re-issues fill values, not only the click
`stages/explore_return.py::_replay_discovery` re-performs the `ScreenEdge` that discovered a node.
Today it replays only `rt.session.click(edge.target)` (line 94); this criterion requires that when
the discovering edge was itself a typed action (an X10-b `FILL`/`SELECT` edge, synthetic values,
already permitted and already recorded once), the replay re-issues those same recorded values
before re-performing the submitting click — so a screen reachable only behind a filled, submitted
form can be re-entered by `return_to`, not just a screen reachable by a bare click chain. This
criterion **widens nothing under X10/X10-b**: it replays an action the crawl already performed
once, under conditions the safety matrix already approved; it originates no new value, no new
target, and no action `explore_typing.py::type_form`'s four gate conditions did not already clear
for the discovering edge itself.

**Falsifiable:** a fixture with a screen reachable only after filling and submitting a form (built
under X10-b's gated conditions) → after the browser navigates away, `return_to` on that screen
succeeds by replaying both the fill and the click; reverting the fill-replay addition (click-only)
in an isolated copy reproduces the original failure to re-enter (a `_replay_discovery` failure
naming "landed on a different screen" or an unresolved form-gated node).

### CR3 — Incremental crawl: persona-seeded skip
Before the crawl visits a candidate node, it looks up `(url_template, structural_signature)`
against `portal_persona.json`'s stored `PersonaScreen` (`PersonaScreen.key()` for the URL half,
`PersonaScreen.signature` for the structural half — both fields already exist,
`schema/portal_persona.py:64-67`) — the Stagehand cache-key idea-port named in
`crawl-reuse-2026-09.md` §3. A match **skips** re-visiting that node (no click, no re-fingerprint,
no re-enumeration of its already-known candidates) rather than re-exploring it from scratch; a node
with no persona match, or whose live signature differs from the stored one, is explored as normal.
A skipped node is recorded with its own status (never silently absent from the crawl's counts — see
CR5) and never counted as a "visited" action toward `CrawlFrontier.actions_used`.

**Falsifiable (D-040's acceptance test (b)):** a second crawl of a fixture project **unchanged**
since the first crawl (persona already seeded from crawl 1) issues **≤10%** of the first crawl's
`actions_used`; the same second crawl against a fixture with every screen's structure genuinely
changed issues close to the first crawl's action count (the skip triggers on stored-and-matching,
not merely on "seen before").

### CR4 — Change tracking: new / changed / missing / broken, extending `_merge` past add-only PP2
`portal_persona.py::_merge` (its current behaviour is PP2, add-only: new screens/transitions/flows
are added, nothing existing is dropped or blanked) gains a real diff when a crawl runs against a
project with an existing persona. Every persona screen the crawl's frontier could have reached is
classified as exactly one of:
- **new** — discovered this crawl, absent from the stored persona;
- **changed** — matched by `key()` but the live `structural_signature` differs from the stored one;
- **missing** — present in the stored persona, in the reachable frontier, but not reached this
  crawl (a genuine absence, not a bound-truncated frontier — see CR5's interaction);
- **broken** — reached this crawl, but the visit produced an error/timeout/off-domain-refusal
  status that the prior stored screen did not carry.

A `PersonaRevision` (PP3, already dated + non-blank-summary-enforced) records the counts of all four
by name — not merely a prose "what changed" sentence, a machine-checkable count per category. PP2's
existing add-only guarantee is **preserved, not replaced**, for any merge path this criterion does
not touch (a taught-flow merge from FlowSpec review, for instance): CR4 is additive to `_merge`,
scoped to crawl-sourced screen classification.

**Falsifiable (D-040's acceptance test (c)):** removing a fixture screen between two crawls of the
same project produces exactly one `missing` classification on the second crawl's `PersonaRevision`;
the same two crawls with nothing removed produce zero `missing` entries. A screen whose structure
was edited between crawls produces exactly one `changed` entry, naming the screen.

### CR5 — Completeness stays honest under the new machinery (frontier-completeness, carried forward)
"Complete" still means the actionable frontier was exhausted, or a named safety/time/action/depth
bound stopped it — carried forward verbatim from T-165's own goal-task note and from `explore.md`
X4/X16/X18, which this contract does not amend. This criterion is what stops the new machinery
from quietly breaking that honesty:
- A `hybrid`-strategy crawl that stops on a bound still names that bound in `stop_reason`, exactly
  as X4 already requires for `bfs` — `hybrid` is not a second code path that forgets to set it.
- A CR3 skip decision is recorded as its own status (e.g. "skipped — unchanged since <revision>"),
  **never** folded into "frontier empty" / `COMPLETED` as if the skipped node had been explored —
  a persona-seeded incremental crawl that skips 90% of the portal must not read as having explored
  90% of the portal.
- Every denied, skipped, and unreached control remains visible on every surface X16 already lists
  (crawl page, crawls table, CLI line, workbook, `crawl.json`) — this contract adds skip-for-
  unchanged as a new named category alongside `DENIED_POLICY`/`SKIPPED_UNNAMED`/`OFF_DOMAIN_REFUSED`,
  it does not let a skip disappear from those surfaces.

**Falsifiable:** a bound-stopped `hybrid` crawl's `stop_reason` names the bound (same test shape as
`explore.md` X18's own verify); a fixture crawl with a mix of persona-skipped and freshly-explored
nodes shows every skipped node counted and labelled on the crawl report, and the report's headline
completeness language does not claim full exploration when skips occurred.

### CR6 — DOM-driven and deterministic, still (X12 carried forward)
Strategy selection (`bfs` vs `hybrid`), the depth-first candidate ordering within `hybrid`, and the
CR3 skip decision are all pure functions of frontier/persona state on disk — no provider, no model,
anywhere in this unit (core-invariants C8). A `hybrid` crawl completes with `provider=mock`, the
same discipline `explore.md` X12 already holds `bfs` to; a model's only permitted role anywhere in
this contract is unchanged from X12 — naming an already-discovered screen for human readability,
never choosing a traversal step or a skip.

**Falsifiable:** `grep -rn` for a `Provider`/vendor-SDK import in the traversal/incremental modules
this unit adds returns nothing; a `hybrid` crawl run with `provider=mock` completes and its
strategy/skip decisions are identical to a run with a real provider configured but never called
(same assertion shape as `explore.md` X12's existing verify).

### CR7 — Nothing here widens the safety matrix, deny-list, or typing rules (X5/X6/X10 untouched)
This is a traversal and bookkeeping contract. `write_policy` enforcement (X5), the never-click
session-ending guard (X6), and the X10/X10-b typing gate are byte-unchanged by anything in CR1-CR6.
CR2's replay is explicitly bound by this: it may only replay a fill the crawl already performed once
under X10-b's four conditions — it can never originate a new typed value, a new target, or fire
under a policy/approval combination the original action itself would have been refused under.

**Falsifiable:** a fixture where the discovering edge's typing would be refused under the CURRENT
run's policy (e.g. `READ_ONLY`, or `synthetic_typing=False`) never has its form replayed — CR2's
"read the recorded values" path still passes through the same X5/X10-b gate a fresh type would, not
a bypass that only checks "was this typed once before."

## Explicit no-fire list (do not raise these as findings)

- **Back-navigation replay "not built"** — it already exists (`stages/explore_return.py::return_to`
  + `_replay_discovery`, AT-227, shipped under `explore.md`). Only the **fill-value gap** (CR2) is
  new; raising "build replay from scratch" is wrong and ignores the existing mechanism.
- **Permission-surface coverage** (every reachable control exercised or blocked-with-reason) — split
  to **T-171** by D-040, not this contract. A finding that this crawl doesn't yet report coverage of
  every permission the role has belongs against `qa/contracts/permission-surface.md` (future, T-171),
  not here.
- **First-party API/network assertions** — split to **T-170** by D-040
  (`qa/contracts/network-assertions.md`), not this contract.
- **Vendoring Crawljax, Stagehand, Scrapling, Crawlee, or Playwright Test Agents as a dependency** —
  every one of them is a verified idea-PORT (Apache-2.0/MIT/BSD, no code copied) or an explicit
  AVOID (`crawl-reuse-2026-09.md`'s own verdict table); importing any of them as a library, or a JVM
  dependency for Crawljax specifically, is a defect against this contract, not a feature.
- **Locator self-healing / element relocation across a redesign** (Scrapling's structural-profile
  idea) — explicitly parked in `crawl-reuse-2026-09.md` §2 for D-031's future healer, not T-165.
- **Resuming an interrupted crawl mid-run** — still not built; unchanged from `explore.md`'s own
  no-fire list, this contract does not claim it either.
- **Relaxing `READ_ONLY`'s form-submit denial, or widening the default bounds** — both explicitly
  declined in `explore.md`'s 2026-09-16 amendment log entry and untouched here; CR7 restates why.
- **Persona merges for non-crawl material** (a taught-flow review merge, for instance) — PP1-PP6's
  existing add-only behaviour for those paths is unchanged; CR4 only extends the crawl-sourced
  screen-classification path.

## How a unit is verified (adapter slot 1)

`uv run pytest tests/test_explore_completeness.py tests/test_explore_traversal.py
tests/test_persona_changes.py` (bare, no CLI `-q`, AT-503) + `uv run ruff check src tests scripts` +
`uv run autotester doctor`, all exit 0; each CR criterion carries a capability-coverage row with a
single-hunk falsifying edit reproduced green→red-for-the-named-reason→revert→green. Being a CRITICAL
unit, T-165 additionally requires the dual-check protocol (two independent verdicts,
`qa/verdicts/t165-*.md` and `.b.md`) before it may close. File/function caps (core-invariants C2)
apply to every new or extended module; `explore_node.py`, `explore_return.py`, and
`portal_persona.py` are all near their existing caps per prior amendment history, so new logic
belongs in a stated-reason new module (C3) rather than pushed into a file already at budget.

## Amendment log (append-only; git history is the version)

- 2026-09-24 · init · contract authored by /checker as DRAFT, from D-040 (Approved-by Umesh — "go
  on" to `qa/gates/t165-d039-traversal-scope.md`) and `docs/research/crawl-reuse-2026-09.md`.
  `qa/feedback-inbox.md` 2026-09-23T07:30 (the source demand) is folded here in full — its DFS,
  schema/flow persistence, and change-tracking asks map to CR1, CR3/CR4, and CR4 respectively; its
  "permission = testing surface" ask is explicitly routed to T-171 (not this contract) per D-040.
  No prior draft existed; nothing amended.
