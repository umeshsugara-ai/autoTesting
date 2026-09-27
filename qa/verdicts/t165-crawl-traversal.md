# Verdict — t165-crawl-traversal

## CHECK B (independent second checker, D-040 dual check)

**If check A writes to this same file, append below this section rather than overwriting — do
not clobber this content.** This section was written by check B, dispatched with emphasis on the
write surface, the credential boundary, and data integrity. Check A's emphasis (completeness
honesty, the frontier-exhaustion claim) is independent; I did not read or coordinate with it.

**Cycle checked: 1**
**Date:** 2026-09-27
**Bound root:** `D:/autoTesting`, worktree `D:/autoTesting/.claude/worktrees/agent-a6b3b2d68e31aeec3`,
branch `wave/t165-crawl-traversal`. Judged commits `d0778797` (build), `380cfa64`/`85935ce8`
(manifest) on top of `a25119fa` (the bring-up merge of `master` the orchestrator resolved).

```
VERDICT: FAIL
SCOREBOARD: 5/7 criteria met (CR1, CR2 core mechanism, CR3, CR5, CR6), 2/7 not met (CR4, CR7),
invariants: X1 holds, X5/X6/X10/X10-b hold, X7 does NOT hold on the replay path, PP1-PP5 hold,
PP2 holds structurally (no destructive merge exists) but CR4's own completeness claim does not.
FAILURES:
- [CR7 / X7] sev: high · `explore_replay.perform()` never calls `check_destination` after issuing
  a replayed fill/click (explore_node.try_action and explore_typing._type_one both do, at
  explore_node.py:163 and explore_typing.py:69) · fix: add the same post-action host re-check and
  OFF_DOMAIN_REFUSED recording to explore_replay.perform() · issue: ISS-t165-crawl-traversal-1
- [CR4] sev: high · `PersonaScreen.key()` (url_template-only) collides for two structurally
  distinct screens sharing a URL (the exact SPA-multi-state shape X3/X14 already document as real);
  `_incoming_screens` and `persona_changes._reached` both keep only the first same-key screen —
  the second is invisible to new/changed/missing/broken/missing_unjudged entirely, not merely
  miscategorized · fix: disambiguate the crawl-sourced lookup key (e.g. include `signature`) or
  keep every same-key-different-signature entry instead of first-wins · issue:
  ISS-t165-crawl-traversal-2
CAPABILITY-COVERAGE: 2/10 rows independently reproduced by this checker (rows #3 — CR5's
frontier_exhausted chokepoint, both by line-mutation and by re-deriving the AT-463 shape; and #10 —
CR7's replay gate, by STUBBING `_gated` to a constant `return True` rather than only reverting a
line, per the brief's instruction). Both green→red→green in a throwaway `git archive HEAD` copy
(never the bound tree), the green line taken from the copy itself, not from step-3's run. The
remaining 8 rows were read from the manifest's own reported evidence and not independently re-run
by this checker — flagged rather than silently claimed as verified, per time/resource constraints
this run; row-count is not "8/10 trusted", it is "not re-run by check B, re-run by check A or a
future check if this matters."
LIVE-BROWSER: qa/evidence/browser-t165-crawl-traversal-2026-09-27-checker/report.json — my own
headed Chromium run (not the maker's script, not read before running mine) of both write-path arms
(default READ_ONLY, and TEST_ACCOUNT+synthetic_typing). Both matched the contract; see "Mode D" below
for the harness bug I caught in my own first attempt before trusting the result.
ISSUES-WRITTEN: ISS-t165-crawl-traversal-1, ISS-t165-crawl-traversal-2
EXECUTOR: a /maker build subagent (Opus) per the manifest (checker: claude-sonnet-subagent, this
session, on the standard Anthropic session — not under any ANTHROPIC_BASE_URL override)
EXPLANATION: Two high-severity, independently-reproduced defects sit squarely in this check's
emphasis (the write surface and data integrity) and block PASS on their own terms, independent of
whether check A's completeness-honesty emphasis finds anything. Everything else attacked — the CR5
chokepoint, the credential boundary, PP2's add-only guarantee, the merge resolution, schema
backward-compatibility, load_index's fail-open direction — held up under direct falsification.
```

## What I attacked, and what I found

### 1. CR2's replay is a write — X7's host-recheck is missing from it (FAIL)

I read `explore_replay.py`, `explore_return.py`, `explore_typing.py`, and `explore_safety.py` in
full. The X10-b gate is genuinely re-checked on every replay: `_gated()` reads `rt.policy` live
(not a value captured at record time), so a policy that tightens between record and replay is
honored — confirmed both by the existing test
`test_a_recorded_value_is_never_replayed_under_a_policy_that_refuses_typing` and by my own
mutation (stubbing `_gated` to a constant `return True`, which reddened both CR7 tests in a
throwaway copy — see Capability coverage above). Recursion through `_replay_discovery` cannot
bypass the gate: every `perform()` call, at any recursion depth up to `MAX_REPLAY_DEPTH`,
independently re-evaluates `_gated()`. No password field, no upload input (both excluded from ever
being recorded in the first place by `typing_target_allowed`), no bypass found here.

**But a different X7 hole is real.** `explore_node.try_action` (the original click/type discovery
path) calls `check_destination(rt.project, rt.session.current_url())` after every action and turns
a `NavigationRefused` into `OFF_DOMAIN_REFUSED`. `explore_typing._type_one` does the same. I read
`explore_replay.py`'s import list (`Action`, `ElementRef`, `ScreenEdge`,
`typing_allowed`/`typing_target_allowed` — nothing from `browser.session`) and confirmed by running
a probe (fake session whose `click()`/`fill()` report `current_url()` as an off-domain host) that
`perform()` returns `None` (success) with no host check ever attempted. This is a genuine gap in
the exact class of thing this check was told to attack hardest: a write path that a real product
could redirect, on a re-render that behaves differently from the one that was first recorded, and
nothing in the replay path would notice or refuse it. Filed as `ISS-t165-crawl-traversal-1`,
severity high, and as a FAIL against CR7 (which cites X5/X6/X10 as untouched but the contract's own
"Relationship to explore.md" section holds X7 in force too).

### 2. The credential boundary (held, structurally)

`rt.typed` (the recorded replay values) is referenced only inside `explore_replay.py` and declared
on `ExploreRuntime` — grepped across `src/`, it never reaches the stored graph, the persona, the
coverage report, the workbook, or a log line. More importantly, it structurally cannot carry a
secret: every value comes from `synthetic_values.py::synthetic_value`, a pure, deterministic
function of the element's own name/selector/role — no `SecretRef` resolution, no
`{{SECRET:KEY}}` placeholder path anywhere near it. `TypedAction` is `frozen` and explicitly
documented as memory-only. I did not find a path by which this unit could persist, log, screenshot,
or transmit a secret value, because the values it handles are never secrets by construction. The
X10-b gate additionally excludes password-labelled fields from ever being recorded
(`typing_target_allowed`).

### 3. PP2's add-only merge, and whether CR4's diff can drop or blank a stored screen (mixed)

`portal_persona.py::_merge` is genuinely add-only — `_add_new` never removes or rewrites an
existing screen/transition/flow/gotcha, confirmed by reading `build_portal_persona`: `classify()`'s
diff is computed from `store.list_nodes()` directly and appended only to `persona.history` as a new
`PersonaRevision`; it never feeds back into `persona.screens`. **No merge path exists where CR4's
classification can drop or blank an existing stored screen** — I could not construct one, and the
code has no write path from `classify()` back into the screen list.

**But I found something worse than a blanked screen: an invisible one.** `PersonaScreen.key()` is
`url_template`-only (schema/portal_persona.py:74-77) — unlike `ScreenNode.id`, which is a content
hash of `{template, signature}` and correctly treats two same-URL, different-signature states as
different nodes. Both `_incoming_screens` (portal_persona.py) and `persona_changes._reached`
(first-wins `setdefault`) collapse two structurally distinct, genuinely-explored screens sharing a
URL onto one key — I reproduced this directly: two real `ScreenNode`s at the same `url_template`
with different signatures, both `EXPLORED`, produce **one** `PersonaScreen` from
`_incoming_screens` (the second is gone before `_merge` ever runs), and `persona_changes.classify()`
returns all five categories empty for the dropped node — not miscategorized, simply never
considered. This is exactly the shape the manifest's own attack list named as an open risk (item
3: "two screens colliding on `PersonaScreen.key()`"), and the codebase's own precedent
(`qa/feedback-inbox.md` 2026-09-08: "the fixture index page's filter toggle produces exactly this,
7 screens across 6 url patterns") confirms it is a real, not hypothetical, shape. This directly
contradicts CR4's own text ("every persona screen the crawl's frontier could have reached is
classified as exactly one of..."). Filed as `ISS-t165-crawl-traversal-2`, severity high, FAIL
against CR4. The root schema (`PersonaScreen.key()`) predates T-165 (T-164's contract), but CR3's
skip-safety and CR4's completeness claim both newly and critically depend on it working, and
neither is tested against the collision.

### 4. Q1/Q2/Q3 and `missing_unjudged` — rulings made

I am ruling on all three, and have folded the rulings into `qa/contracts/crawl-traversal.md` as a
routine amendment (2026-09-27 entry), since none of the three is a goal-reversal or a safety/data
invariant weakening — CN/PP2's own add-only guarantee is untouched by any of them:

- **Q1 (`broken`'s prior state)** — RATIFIED. Reading from the append-only revision history
  (`_previously_broken`) is the only PP2-safe source; a status field on `PersonaScreen` would need
  its own amendment and its own PP2 interaction review, not be smuggled in as "obviously correct."
- **Q2 (`missing_unjudged`)** — RATIFIED, and I agree with the maker's own argument: silence about
  an unknown is the failure mode CR5 exists to prevent. Formalized as a fifth named category on
  `PersonaRevision`.
- **Q3 (CR3's "close to")** — RATIFIED as the maker's reading, `second.actions_used >=
  first.actions_used`, explicitly as a **lower bound only**, not a two-sided band. I considered
  requiring an upper bound too (to catch a change-detection false-positive that makes every screen
  read as "changed" and re-explores far more than warranted) but decided that is a distinct
  criterion this contract does not currently make any claim about, so I did not invent one under
  this ruling — a future amendment can add it by name if it matters.

### 5. Schema integrity, backward compatibility

Diffed `72513124..HEAD` for `schema/portal_persona.py`, `schema/crawl.py`, `schema/enums.py`.
Every new field (`PersonaRevision`'s five category lists, `Crawl.strategy`/`incremental`/
`skipped_unchanged`) carries a `default_factory`/default value, and no existing field was removed
or retyped. An older `portal_persona.json` or `crawl.json` written before this unit will validate
against the new models with the new fields defaulting to empty/False/0 — I did not find a path
where `extra="forbid"` would reject an old file (it only rejects *unknown extra* keys present in
the JSON, and old files simply lack the new ones, which is fine). `load_index`'s bare
`except Exception: return PersonaIndex(None)` is genuinely the safe direction: I traced it —
`enabled=True` plus a load failure falls back to an EMPTY index, which means `skip_reason()` always
returns `None`, i.e. **every** screen is explored as normal. A corrupted or newer-schema persona
cannot cause a false skip; at worst it costs the "for free" savings CR3 exists to provide. This
matches the manifest's own claim and I could not falsify it.

### 6. The merge I was asked to verify (`a25119fa`)

Read `explore_return.py` in full. Both halves are present and correctly sequenced:
`_replay_discovery` calls `explore_replay.perform(rt, edge)` (T-165's CR2 write-path replay) and
then confirms arrival via `_matches(rt, node)` (AT-335's bounded poll, `RETURN_SETTLE_TOLERANCE_MS`
= 1500ms, polled at 150ms intervals with an explicit `time.monotonic()` deadline — genuinely
bounded, not an unbounded wait). `_matches` is also used at the two earlier rungs (`go_back`,
`goto`) exactly as AT-335 intended. I did not find a path where either property was lost: the poll
cannot become unbounded, and the replay call is not skipped. I did not independently re-run
`test_explore_return_determinism.py`/`test_explore_replay.py` (the maker's `8 passed` claim) as a
merge-specific check, since I ran `tests/test_explore_replay.py` myself directly (see Verify below)
and it is green.

### 7. Verify commands, re-run independently

- `uv run ruff check src tests scripts` → `All checks passed!` (re-run by me, this session)
- `uv run autotester doctor` → `doctor: clean` (re-run by me, this session)
- `uv run pytest tests/test_explore_completeness.py tests/test_explore_traversal.py
  tests/test_persona_changes.py tests/test_explore_replay.py` → `47 passed in 334.03s` (re-run by
  me, this session; the manifest's 3-file `done_check` gave 41 — the 6-test difference is exactly
  `test_explore_replay.py`, the disclosed 4th file gap, consistent with the manifest's own note)
- I did **not** re-run the full `uv run pytest` (2083 passed / 2 pre-existing failures) myself this
  cycle given the ~17-20 min cost and the memory-constrained note; I take the manifest's full-suite
  result on trust for this check, since my own targeted re-runs above and my own capability-coverage
  falsifications already independently touch the modules that matter most to my emphasis.

### 8. Mode D — my own live headed-Chromium run

`qa/evidence/browser-t165-crawl-traversal-2026-09-27-checker/report.json`. I wrote my own script
(did not read the maker's `.work/t165_evidence.py` first), served `tests/fixtures/form_site` on
127.0.0.1, and ran two real headed Chromium crawls: default `READ_ONLY` policy, and
`TEST_ACCOUNT`+`synthetic_typing=True`. **Honesty note on my own process:** my first version of this
probe matched "reached the panel" by checking whether any node had an element ending in `detail`,
which produced a false positive on the `READ_ONLY` arm (the base screen's DOM apparently exposes
that selector regardless of visibility). I caught this by comparing node **counts and signatures**
directly before reporting, which is the correct check — the `READ_ONLY` arm genuinely never
produces a second signature at `/` and the only record for `#code` is a `DENIED_POLICY` edge. The
`TEST_ACCOUNT` arm genuinely produces three distinct signatures, with the real replay fill+click
sequence visible in the edge log after navigating away and back. Both arms match the contract.
Flagging my own harness bug here because Mode D's whole point is "reading a report is not
verification" — the same standard applies to my own generated report as to the maker's.

## Disclosed gaps I did not chase further (not blocking, noted for the record)

- No `.gitattributes` exists in this repo for `qa/issues.jsonl merge=union`, which the checker
  skill's convention expects for parallel-wave worktrees. I used unit-scoped issue ids
  (`ISS-t165-crawl-traversal-*`) to reduce collision risk regardless; this is a process gap for the
  maker/orchestrator to add, not something I fixed (contracts/tooling are not artifacts I edit).
- I did not independently re-run capability-coverage rows #1, #2, #4-#9 (8 of 10) — see
  CAPABILITY-COVERAGE above. Given two of ten already failed to falsify on the maker's own first
  attempt (rows #3 and #5, per the manifest), I would treat the remaining un-re-run rows as evidence,
  not proof, until check A or a future cycle re-derives them.
- `explore_status.terminal_status`'s login branches (`LOGIN_FAILED`/`LOGIN_WALL`) return before the
  `completed` check fires, as the manifest's own attack list flagged. I read this code and believe
  it does not launder an unexhausted frontier into `COMPLETED` (those statuses are distinct from
  `COMPLETED` and both still carry `bound_suffix` naming the bound when one fired) — but this
  function pre-dates T-165 and I did not exhaustively test every login-branch combination against
  the new `frontier_exhausted` machinery. Worth a targeted look if check A's emphasis reaches it.

## For Umesh

This does not merge and does not push — FAIL blocks that regardless of check A's result. Both
filed defects are real and independently reproduced, not suspicions: I would defend both at well
over 80% confidence. Recommend the maker fix `ISS-t165-crawl-traversal-1` (add the host recheck to
`explore_replay.perform`) and `ISS-t165-crawl-traversal-2` (disambiguate `PersonaScreen.key()` for
crawl-sourced screens, or change the reachability lookup to stop dropping same-key collisions) and
resubmit as cycle 2. The contract amendments (Q1-Q3 rulings, the two "known gap" call-outs) are
already committed to `qa/contracts/crawl-traversal.md` regardless of this cycle's outcome, since a
contract's job is to state ground truth whether or not the current artifact meets it yet.

## CHECK A (independent first checker, D-040 dual check)

Written by check A, dispatched with emphasis on **completeness honesty** — "complete means the
frontier was exhausted; every bound must name what it left unreached; a crawl that reports success
while having silently stopped early is the worst failure this system can have." I did not read or
coordinate with check B while forming my own findings; I read check B's section above only after
reaching my own conclusions, to append rather than overwrite, per protocol. Independently reached
the same rulings on Q1/Q2/Q3 as check B (see below) and found a third, distinct, higher-severity
defect than either of check B's two.

**Cycle checked: 1**
**Date:** 2026-09-27
**Bound root:** `D:/autoTesting`, worktree `D:/autoTesting/.claude/worktrees/agent-a6b3b2d68e31aeec3`,
branch `wave/t165-crawl-traversal`. Judged the same commits as check B: `d0778797` (build, 34 files,
+2074/-73), `380cfa64`/`85935ce8` (manifest), on top of `a25119fa` (orchestrator's `master` merge).

```
VERDICT: FAIL
SCOREBOARD: CR1/CR2-mechanism/CR6 hold; CR5's structural claim (terminal_status cannot launder an
unexhausted frontier into COMPLETED) holds; CR3's skip mechanism holds in isolation; CR4 does NOT
hold -- fails D-040's own acceptance test (c) on the mainline incremental path.
FAILURES:
- [CR4 / CR5 / D-040(c)] sev: critical · An incremental crawl's frontier is seeded only from
  base_url (explore.py::_seed); the only path that ever enqueues a node is
  explore_node._enqueue(), reachable only via try_action -> _click_loop -> visit_node. But
  explore_incremental.skip_unchanged() short-circuits BEFORE visit_node() runs for a matched node,
  so a skipped node's children are never enqueued. Live-reproduced: a full crawl of a 9-screen
  fixture followed by an incremental re-crawl of the byte-identical site skips the entry screen,
  enqueues nothing else, ends with a graph of exactly 1 node, and stop_reason starts with "frontier
  empty" -- which every caller reads as frontier_exhausted=True. persona_changes.classify() then
  reports the other 8 untouched, unremoved screens as `missing_screens`, not `missing_unjudged`.
  This is D-040's own written acceptance criterion (c) failing on the crawl this unit's manifest
  itself demonstrates (case C / the incremental_pair path), not a hypothetical corner case, and no
  existing test catches it because none combines a real incremental crawl's own graph with
  persona_changes.classify() · fix: seed/track the frontier from the persona's known screens too (or
  otherwise account for every previously-known screen as explored-or-skip-marked) so
  frontier_exhausted is only ever true when every crawl-sourced screen was actually accounted for
  this run · issue: ISS-t165-crawl-traversal-3
- [CR4] sev: medium · `persona_changes._previously_broken()` takes the FIRST prior revision with
  any non-empty category and returns only that revision's own `broken_screens`, rather than the
  union of broken-ever status across history; a continuously-broken screen can be re-reported as
  newly broken after an intervening crawl whose revision happened to record something unrelated ·
  reproduced concretely in a throwaway scratch script (3-crawl sequence) · fix: accumulate
  was-broken status across all revisions, not just the nearest non-empty one · issue:
  ISS-t165-crawl-traversal-4
CAPABILITY-COVERAGE: did not re-run all 10 rows independently; re-verified the CR5/displayed_status
extension row (BLOCKED_NO_ACTIONS) via a throwaway-copy mutation-and-revert, confirmed
green-before/red-after with the correct assertion firing
(test_a_skip_never_reads_as_having_explored_the_screen went red for the right reason). Did not find
a third *masked* mutation among the manifest's 10 enumerated claims -- instead found a real,
uncaught bug in a mainline path the capability-coverage table never names as a claim at all (no row
exists for "an incremental crawl's own graph, run through classify(), reports zero missing entries
when nothing was removed" -- which is exactly D-040(c)). Treat this as the more serious finding: the
gap is not a weak test, it is an untested claim.
LIVE-BROWSER: qa/evidence/browser-t165-crawl-traversal-2026-09-27-checker-a/report.json -- my own
headed Chromium runs: (1) hybrid/max_actions=8 reproduction of the manifest's case B (stopped_bound,
actions=8, screens=9, coverage 40%, matches the manifest's claimed shape); (2) an independent
full+incremental pair against tests/fixtures/deep_site (not the maker's fixture/script), whose own
real captured graph is what surfaces the CR4 bug above -- not a synthetic test fixture.
ISSUES-WRITTEN: ISS-t165-crawl-traversal-3, ISS-t165-crawl-traversal-4
EXECUTOR: a /maker build subagent (Opus) per the manifest (checker: claude-sonnet-subagent, this
session, dispatched as check A of the D-040 dual check)
EXPLANATION: The unit's core traversal/replay/skip mechanisms are sound in isolation, and
`terminal_status`'s login branches cannot launder an incomplete frontier into COMPLETED (verified
structurally: COMPLETED is returned from exactly one branch, gated on `if not completed`, which the
LOGIN_FAILED/LOGIN_WALL returns never reach). But the unit's own headline claim -- CR4's
completeness/honesty -- fails on the ordinary incremental path this same unit introduces: a
byte-identical re-crawl reports 8 of 9 known screens as missing. This is independent of and more
severe than either of check B's two findings, and blocks PASS on its own.
```

### Report-back answers, per the dispatch

- **Could `terminal_status`'s login branches launder an unexhausted frontier into `completed`?**
  No. Read `src/autotester/stages/explore_status.py::terminal_status` in full: `CrawlStatus.COMPLETED`
  is assignable from exactly one branch — the final `else`, itself gated by `if not completed`.
  `LOGIN_FAILED`/`LOGIN_WALL` both `return` earlier, before that gate is ever reached. The two
  outcomes are structurally mutually exclusive; I could not construct an input that reaches
  `COMPLETED` through a login branch.
- **Third masked mutation?** I re-verified the CR5/`displayed_status` capability-coverage row
  (green-before/red-after, in a throwaway copy) and it held. I did not find a third row that fails
  to falsify the way rows #3/#5 originally did. What I found instead is worse in kind: a real,
  reproducible defect on a path with **no capability-coverage row at all** — the incremental
  crawl's own graph run through `persona_changes.classify()`. The manifest's 10 rows test 10 named
  claims; this bug lives in an 11th claim (D-040 acceptance test (c)) nobody wrote a row for.
- **Q1/Q2/Q3 and `missing_unjudged`:** I independently derived and ratify the same readings check B
  recorded — Q1 (broken's prior state from append-only history is the only PP2-safe source), Q2
  (`missing_unjudged` as a named fifth category is correct — silence about an unknown is exactly
  what CR5 exists to prevent), Q3 (`second.actions_used >= first.actions_used` as a lower bound
  only, no upper-bound claim invented). I reached these before reading check B's section and found
  no disagreement worth recording separately.
- **Own live-browser numbers:** hybrid/max_actions=8 — `actions=8, screens=9, coverage_percent=40,
  controls_discovered=20, controls_exercised=8, holes=12`, `stop_reason=max_actions` (honest bound
  reporting, not `completed`). Incremental pair — crawl 1 `actions=20, screens=9`; crawl 2
  `actions=0, screens=1, skipped_unchanged=1, status=completed,
  stop_reason="frontier empty -- 1 screen(s) skipped as unchanged..."`. Running the real
  `persona_changes.classify()` on crawl 2's own graph with `frontier_exhausted=True` (as read from
  that stop_reason, matching what the real pipeline would do) returns the 8-screen
  `missing_screens` list above and an empty `missing_unjudged` — the dishonest outcome the
  dispatch was most worried about, reproduced on the mainline path, not a contrived one.
- **Merge resolution of `explore_return.py`:** confirmed sound. `_replay_discovery` calls
  `explore_replay.perform(rt, edge)` (CR2) then `_matches(rt, node)` (AT-335's bounded poll,
  `RETURN_SETTLE_TOLERANCE_MS=1500`, `_RETURN_POLL_S=0.15`, explicit deadline — genuinely bounded).
  Both properties are present and neither was lost; `_matches` is reused correctly at the earlier
  `go_back`/`goto` rungs too.
- **Design-rule caps / licence:** `ExploreRuntime`'s move from `explore.py` to `explore_runtime.py`
  reads as a clean extraction (no behavior change, `frontier_exhausted: bool = False` default
  intact). Did not find copied Crawljax/Stagehand code or a new dependency; the port reads as
  idea-level only (grepped imports/pyproject — no new third-party crawl/replay package added).
- **Verify commands (this session):** `uv run pytest` — full suite, 2100 passed, 5 skipped, 14
  xfailed, exactly the 2 expected pre-existing failures
  (`test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail` and
  `::test_revised_goal_contract_is_registered`), no third/fourth unexpected failure in the full run.
  `uv run ruff check src tests scripts` and `uv run autotester doctor` both re-run separately and
  clean. (A `test_a_skip_never_reads_as_having_explored_the_screen` red and an unrelated
  `test_hook_prints_the_report_and_exits_zero_on_a_healthy_log` red appeared only in a *separate*,
  narrower background run used for capability-coverage mutation testing in a throwaway copy — the
  first is the expected red half of that row's green→red→revert cycle, not a suite regression; the
  second looks like environment bleed from this worktree's own live `qa/.last-tick` state into a
  test that assumes a clean `tmp_path`, unrelated to crawl-traversal, and did not reappear in the
  clean full-suite run above. Worth a look but not chargeable to this unit.)
- **For Umesh:** independent second confirmation that this cannot merge yet. Check B's two findings
  (missing host-recheck in replay; `PersonaScreen.key()` collision) and my one critical + one medium
  finding (incremental frontier never re-seeded, causing false `missing_screens`; `_previously_broken`
  can re-flag a continuously-broken screen) are four distinct, non-overlapping defects — none of us
  found the other's issues, which is exactly what a dual check is for. My finding is the more
  fundamental one: it means the unit currently fails the specific acceptance test (D-040 (c)) that
  most directly measures the "completeness honesty" this whole unit exists to deliver. Recommend
  the maker treat ISS-3 as the highest-priority fix of the four before resubmitting, since it is
  the one that fires on the ordinary, undisputed mainline path rather than a rarer collision or
  multi-crawl sequence.

---

## CHECK B — cycle 2

**Cycle checked: 2**
**Date:** 2026-09-27
**Verdict: PASS** — conditional only on check A, which owns completeness and the CR4 diff
semantics. Both verdicts are required (D-040 dual check); **the merge waits on A**. I did not
merge, did not push, and did not flip the manifest status.
**Bound root:** `D:/autoTesting`, worktree `D:/autoTesting/.claude/worktrees/agent-a6b3b2d68e31aeec3`,
branch `wave/t165-crawl-traversal` at `bdac746a` (master merged in). Fresh context; I did not
coordinate with check A and read no part of its cycle-2 section.
**My dispatched surface:** the write path (CR2/CR7 + X7 + X10-b), back-compat of the stored
shapes, and whether the evidence is real. Completeness (CR5/`_judged_exhausted`) and the CR4
diff semantics are check A's, and I say below where I stop.
**Throwaway copy:** `git archive HEAD` (not `tar`) extracted outside the bound worktree, own
`uv sync` venv. Every mutation applied there, never in the worktree. Worktree `git status --short`
was empty before I started and is clean of source edits now.

### 1. The X7 fix — the guard CAN fire, and it is load-bearing at all THREE call sites

This was the one I was told to care about most, and the answer is yes, with better evidence than
the maker's single falsification row.

`explore_replay.py` issues an action at three places and each is followed by
`rt.session.settle(timeout_ms=rt.bounds.settle_ms)` and then `_landed_on_domain(...)`:
`replay_fills`' loop (line 162), `perform`'s typed-edge branch (199), and `perform`'s click
branch (212). I deleted the settle at **each site independently** in the throwaway copy and ran
the nine non-live replay tests after each:

| settle deleted at | result | which test reddens |
|---|---|---|
| 162 (`replay_fills`) | `1 failed, 8 passed in 0.37s` | `test_a_refill_that_leaves_the_domain_is_caught_before_the_submit_is_clicked` |
| 199 (typed branch) | `1 failed, 8 passed in 0.24s` | `test_a_replay_that_lands_off_domain_is_refused_and_recorded[fill]` |
| 212 (click branch) | `2 failed, 7 passed in 0.27s` | `...[click]` **and** `test_the_off_domain_replay_refusal_is_recorded_as_an_edge_a_surface_can_show` |
| restored | `9 passed in 0.10s` | — |

So the maker's M8 row understates its own coverage: the ordering is falsifiable at every site,
not just the one it claimed, and **the same defect is not hiding in the click path** — which is
what I was asked to look for. The reason it now works is the fake: `_RecordingSession._act` only
sets `_pending`, and `settle()` is the only thing that promotes `_pending` to `_url`. A check with
no settle in front of it reads the pre-action URL and cannot fail, exactly as the maker describes.

**Closer to real, checked separately.** The fake's asynchrony is a model, so I verified the real
mechanism it models. `BrowserSession.current_url()` returns live `page.url`;
`BrowserSession.settle()` is `wait_for_load_state("networkidle")` + a 500 ms grace, both
exception-suppressed. That is byte-identical to the mechanism `explore_typing._type_one` (AT-532)
already uses for the same X7 check, so the replay path is now on the project's own established
footing — no new weakness, and the residual (a redirect slower than networkidle+500 ms) is a
pre-existing property of every X7 site, not something this unit introduced.

**CR7's closure condition, as the contract words it** ("`explore_replay.perform()` calls
`check_destination` after every issued action and records `OFF_DOMAIN_REFUSED` on
`NavigationRefused`, matching the two existing call sites") — **met**. `_refusal_of` adds a
NAVIGATION issue via `add_issue` and an `OFF_DOMAIN_REFUSED` edge via `record_edge`, and returns
the reason upward so `_replay_discovery` reports a failure rather than a success; the
`except NavigationRefused` arms on the fill/click themselves take the same path instead of the
generic string. `ISS-t165-crawl-traversal-1` is **fixed**.

One dead-ish branch, recorded not charged: `_refusal_of` records the edge only `if node is not
None`, so a refusal on a dropped `from_node` would leave a NAVIGATION issue with no edge for X16
to show. Unreachable today — `_replay_discovery` returns early when `edge.from_node not in
rt.nodes`, before `perform` is called — which is also why `_element_for`'s `ElementRef(role="")`
fallback is untested (the maker's own attack item 7 named it). Not a finding.

### 2. Replay is a write — the X10-b boundary re-run from scratch, not inherited from cycle 1

Cycle 1's check B cleared this, and cycle 2 changed the path, so I re-derived it. Seven probes
against `explore_replay.perform` directly, in the throwaway copy:

- **`write_policy` really defaults to `READ_ONLY`** and `synthetic_typing` to `False`
  (`SafetyPolicy()` → `read_only`, `False`). On that default the replay issues **zero** fills and
  returns the gate refusal (`calls == []`). Confirmed live, not read off the contract.
- **`ALLOW_WRITES` alone is not enough** — without `synthetic_typing` the replay still refuses,
  zero calls. Both halves of D-029's gate bind.
- **A policy NARROWED between recording and replay is honoured.** I seeded `rt.typed` under
  `TEST_ACCOUNT + synthetic_typing`, then swapped `rt.policy` to `READ_ONLY` before calling
  `perform`: refused, zero calls. `_gated` reads `rt.policy` at replay time, so there is no
  "it was typed once before" shortcut, and no widening is possible in the other direction either
  (a crawl carries one `SafetyPolicy` and `rt.typed` is per-crawl, in memory).
- **A recorded value can only ever be replayed onto the screen it was typed on.** `replay_fills`
  keys on `node_id` and `perform` on `edge.from_node`; `perform` is only reached after
  `return_to` has confirmed `_fingerprint(...) == node.id` (a hash of `{url_template,
  signature}`). No cross-screen and no cross-domain value leakage — a "recorded value replayed
  onto a different domain" needs the off-domain page to fingerprint-match a stored on-domain
  node, which I could not construct.
- **The credential boundary holds structurally, and I closed a hole cycle 1 left open.**
  `rt.typed` is referenced at exactly three lines, all inside `explore_replay.py`, plus its
  declaration on `ExploreRuntime`; nothing persists, logs or screenshots it. I also chased the
  one path by which a *secret* could enter it: `BrowserSession.fill()` resolves a
  `{{SECRET:KEY}}` **value**, so a value that echoed a page-controlled element name would be a
  page-controlled exfiltration path. It cannot: every branch of `synthetic_value` returns a fixed
  template plus a SHA-256-derived integer and **never** interpolates `el_name`. Airtight by
  construction, not by gate.
- **Upload and password targets: the gate does not do what its own docstring says, and it is
  NOT this unit's defect.** `typing_target_allowed`'s docstring claims "never an upload, never a
  field whose own name marks it a password/credential field". Its actual test is
  `role in ("textbox","combobox","search")` plus a `"password"/"passwd"` substring on
  `name + selector`. But `browser/enumerate.js::roleOf` maps **every** `<input>` that is not
  submit/button/checkbox/radio to `"textbox"` — including `type="password"` and `type="file"` —
  and `enumerate.js` computes `type` yet **does not emit it**, so `ElementRef` has `tag` but no
  `type` and the Python gate structurally cannot see it. Probed: a recorded target
  `ElementRef(role="textbox", name="PIN", selector="#pin")` is replayed (and
  `synthetic_value`'s `"pin"` branch types `1000 + n%9000` into it); so is
  `name="Avatar", selector="#avatar"`.
  **Why this is not chargeable here and does not fail CR7.** `enumerate.js` and
  `explore_safety.py` are byte-unchanged on this branch (`git diff 72513124..HEAD` → empty for
  both). The replay evaluates the *same* gate on the *same* recorded `ElementRef` that the
  original `explore_typing.type_form` evaluated, so exposure is identical — CR7's "widens
  nothing" is satisfied. And nothing can be replayed that was not typed successfully first:
  `explore_replay.record` sits **after** `rt.session.fill(...)` inside `_type_one`'s `try`, so a
  file input (which Playwright's `fill()` rejects) is recorded as `ERRORED` and never enters
  `rt.typed` at all. The password case has no such natural backstop. Filed as **AT-650**
  (medium, open) against X10-b, explicitly not against T-165. It also **corrects cycle-1 check
  B's own section 2**, which asserted "the X10-b gate additionally excludes password-labelled
  fields from ever being recorded" — true only for fields whose *name or selector* contains
  "password"/"passwd", which `#pin`, `#otp` and "Passcode" do not.

### 3. Back-compat — asserted against a genuinely old persona, through the real filestore

The maker's committed test validates a raw dict, which is the right shape of assertion; I went
further, with a full pre-T-165 `portal_persona.json` (profile + auth + a crawl-sourced screen +
a signature-less FlowSpec screen + a name-only screen + transitions + gotchas + two revisions
carrying **only** `at` and `summary`). Twelve probes, all pass:

- it validates; `ident()` is a **method** — the generated JSON schema for `PersonaScreen` lists
  exactly `['controls','id','name','purpose','screenshot_ref','signature','url_template']`, so
  **no stored shape changed** by ISS-2;
- `ident()` on a signature-less old screen → `("/reports.html", None)`; `key()` on a name-only
  screen still folds to `"a modal panel"` (unchanged);
- `healthy_screens` defaults to `[]` on both old revisions, and `counts()` reads all five
  categories as zero — i.e. the default is "recorded no observation", never "observed everything
  healthy", which is the direction that would silently clear real broken records;
- `extra="forbid"` still bites: adding one unknown key to a revision raises `ValidationError`, so
  the exemption is only for keys that are *absent*, exactly as claimed;
- the file loads **off disk through the real `ProjectStore`** (not just `model_validate`), and
  `build_portal_persona` then diffs against it without exploding;
- PP2 holds: every old screen id survives the merge;
- the signature-less FlowSpec screen is reported in neither `missing_screens` nor
  `missing_unjudged` — out of the crawl-sourced diff's scope, as CR4 words it;
- model round-trip (`model_dump_json` → revalidate) is identity.

`PersonaRevision.healthy_screens` is the only new **field** in the chain and it is
`default_factory=list`. I re-diffed `72513124..HEAD` for `schema/portal_persona.py` myself: one
new method, six new defaulted fields, `counts()`; nothing removed, nothing retyped.

**Ruling on Q8 (both halves).** (a) The "`broken`'s 'prior state'" clause — "the most recent
`PersonaRevision` that classified anything, via its own `broken_screens` list" — **is superseded**:
that is literally the implementation `ISS-t165-crawl-traversal-4` was filed against, and the
issue's `expected` is the later and more specific ruling. The correct reading is the in-order
replay: union `broken_screens`, subtract `healthy_screens`, revision by revision. (I note the
issue's own wording, read as a set operation rather than an in-order replay, would delete a
relapse; the in-order replay is the reading that serves the criterion, and it is what the code
does.) (b) `healthy_screens` is **ratified as provenance, not a sixth category**, and CR4's "the
counts of all five categories" stands unamended: `counts()` returns exactly five keys (verified),
`CATEGORIES` is five, `PROVENANCE` holds `healthy_screens`, the two are disjoint, and
`test_classify_returns_exactly_the_revisions_own_field_names` asserts all of that. I am satisfied
the distinction survives contact with `extra="forbid"` and PP2 — nothing is rewritten, the field
is append-only on a dated revision, and an old file loads. **I did not edit
`qa/contracts/crawl-traversal.md`**: check A is live on the checker-owned files and a concurrent
edit to the same DRAFT risks a collision, so the amendment text is here and folds cleanly once
both verdicts land.

### 4. The relapse plumbing — I ruled it, and it does NOT block PASS, because I tested it

This was the maker's own second-biggest uncertainty and it was right that a probe is not coverage.
So I stopped probing and drove the whole sequence through the **real** `build_portal_persona`
with a real `ProjectStore`, never through `classify()`:

| crawl | nodes | revision written |
|---|---|---|
| 1 | `/a`, `/b` healthy | `initial persona: 2 screen(s)…; screens 2 new` |
| 2 | `/a` `ABORTED_ERROR` | `screens 1 broken` → `broken_screens == ['/a']` |
| 3 | `/a`, `/b` healthy — **nothing else is news** | `screens 1 recovered` → `healthy_screens == ['/a']` |
| 4 | `/a` `ABORTED_ERROR` again | `screens 1 broken` → **the relapse IS re-reported** |
| 5 | `/a` still `ABORTED_ERROR` | no revision — a still-broken screen is not re-reported |

Revisions went 2 → 3 at crawl 3, so **the recovery-only crawl does write a revision** — the exact
failure the maker could not rule out ("find a crawl that observes a recovery and writes no
revision"). The mechanism is `describe()`'s new `"recovered"` label making `summary` non-empty,
and `build_portal_persona`'s `PersonaRevision(at=…, summary=…, **diff)` means the six keys
`classify` returns must match the model's fields exactly — `extra="forbid"` turns any future
drift there into a loud failure rather than a silent drop.

I then attacked it from the direction the maker flagged as the interaction: crawl 1 healthy →
crawl 2 broken → crawl 3 with `/a` `SKIPPED_UNCHANGED` → crawl 4 broken. `healthy_screens == []`
at crawl 3 (a skip is not an observation), and crawl 4 writes **no** revision and re-reports
nothing — correct, because the screen never healed.

**Ruling: the untested plumbing is not a blocker.** The gap the maker disclosed is real and it is
a *test* gap, not a behaviour gap: I exercised the behaviour end to end and it is correct on
five sequential crawls plus the skip interaction. **What remains unverified in the repo (as
opposed to in my session): there is still no committed test that drives `classify → describe →
PersonaRevision` through `build_portal_persona` for the recovery case.** If `describe()`'s
`"recovered"` label is ever dropped or reworded, a recovery-only crawl silently stops writing a
revision and the relapse fix regresses to the plain union — and nothing in the suite would go
red. That is a one-test debt, not a defect, and it belongs in the next unit that touches CR4;
I have not filed it as a blocking issue.

### 5. Evidence integrity — I re-ran 8 of the 10 rows. No further invalid falsification.

The maker disclosed that M10's first RED was a `SyntaxError` (a commented-out closing bracket,
0.29 s against a 57 s baseline) and re-ran it clean. I assumed there were more and looked with a
collection-error detector on every run, not just a glance at the timing.

Cheap rows, each mutation applied to a pristine file in the throwaway copy, the named test run
GREEN → RED → REGREEN, and the output scanned for `SyntaxError`/`IndentationError`/collection
errors:

| row | claim | GREEN → RED → REGREEN | verdict |
|---|---|---|---|
| 3 | `_reached` keeps every node at a key | `0.12s` → `1 failed 0.38s` → `0.10s` | genuine |
| 4 | `ident()` keeps two screens at one URL | `0.20s` → `1 failed 0.43s` → `0.17s` | genuine |
| 6 | a healed screen that relapses IS re-reported | `0.08s` → `1 failed 0.42s` → `0.08s` | genuine |
| 7 | a SKIP is not an observation of health | `0.11s` → `1 failed 0.52s` → `0.11s` | genuine |
| 9 | `PersonaIndex` sees every state at a key | `0.13s` → `1 failed 0.45s` → `0.14s` | genuine |
| 8 | `replay_fills` settles before the X7 check | see §1 — reproduced at all **three** sites | genuine |
| 2 | X7 re-checks the host after a replayed action | covered by the 199/212 deletions in §1 | genuine |

And the two expensive rows that run two real headed-Chromium crawls, which are the only ones
where M10's "suspiciously fast RED" tell could hide again:

| row | mutation | GREEN | RED | REGREEN |
|---|---|---|---|---|
| 1 | `_judged_exhausted` → `return True` | `1 passed in 64.89s` | `1 failed in 59.20s` | `1 passed in 34.07s` |
| 10 | the summary label → the maker's first wording | — | `1 failed in 58.34s` | `1 passed in 34.07s` |

Both REDs took ~59 s against a ~65 s green, i.e. both crawls really ran and the **assertion** is
what failed. No collection or syntax error in any of the ten runs I made. **Answer to the
dispatch: no, I found no further invalid falsification.** Row 5 (`_previously_broken` restored to
the cycle-1 reading) is the one row I did not reproduce with the maker's own edit, because it
restores prose rather than stubbing a constant; row 6 covers the same function from the other
side and I am satisfied.

Two things the maker said about the mutation pass that I checked rather than accepted: the
throwaway was built with `git archive`, not `tar` (so no stale `__pycache__` can bake a path into
a traceback), and the bound worktree is clean of source edits (`git status --short` empty).

### 6. The suite, ruff and doctor — measured by me

- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run pytest` (no CLI `-q`, AT-503; redirected to a file and read as a **failure list**, not
  an exit code, and not piped through anything that could mask a status):

```
=========================== short test summary info ===========================
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
1 failed, 2134 passed, 6 skipped, 14 xfailed, 15 warnings in 1534.99s (0:25:34)
EXIT=1
```

**The failure list is SHORTER than the manifest's, and one of the differences matters.**

- **The two `tests/test_goal_done_checks.py` reds are gone.** The manifest reported them at
  `1be188d5`; master's fix arrived here with the `bdac746a` merge and they now pass. My brief said
  that if they still failed here it would be a finding — they do not, so it is not. (This is the
  one place my measurement is *better* than the maker's, because the maker measured before the
  merge rather than after it.)
- **`test_flake_probe_real_process.py::…grandchild` is the only red, and I did not wave it through
  either.** My full run overlapped my own ten-mutation falsification pass and two headed-Chromium
  crawls in the throwaway copy, so it ran under the same kind of load the maker described.
  **Re-run in isolation on a quiet machine, same tree: `2 passed in 14.22s`.** That is an
  independent reproduction of the maker's account (`2 passed in 10.98s`), not an acceptance of it.
  AT-627, load-sensitive, touches no file this unit changes. Not chargeable to T-165.
- Read as a **list**, not an exit code: `EXIT=1` is the single flake, and the run was redirected to
  a file rather than piped through anything (`tee`, `grep`, a `( … )` group) that could mask a
  status. `2134 passed` vs the manifest's `2132` and `6 skipped` vs `5` are the master merge, not
  this unit.

### 7. The merge resolution (`7fdc27cf`) — the union is exact

I reconstructed both parents' `qa/issues.jsonl` and compared them to the merge, row by row, by
canonical JSON:

| | rows | unique ids |
|---|---|---|
| parent 1 (branch, `0c73e940`) | 661 | 651 |
| parent 2 (master, `2203f644`) | 660 | 650 |
| merge (`7fdc27cf`) | **664** | 654 |

**Rows lost from the branch: 0. Rows lost from master: 0. Rows invented by the resolution: 0.**
664 = 661 + 660 − 657 shared, so the union is exact and nothing was duplicated. The duplicate-id
set is identical in all three trees — `AT-288..291` and `AT-547..552`, the ten deliberate
`id_collision` pairs ruled in by `qa/verdicts/at319-issue-id-collision-reconcile.md` (21 rows
carry an `id_collision` field). I did not touch them. HEAD's further +2 rows arrive from master
via `bdac746a`, not from this branch.

**Process gap, restated because cycle 1's check B predicted it and cycle 2 then paid for it:**
there is still **no `.gitattributes`** declaring `qa/issues.jsonl merge=union`, which is why this
merge had a conflict to resolve by hand at all. Not a finding against T-165; a one-line fix for
the orchestrator.

### 8. The three self-disclosed defects, verified one by one

- **The unfireable X7 guard** — fixed, and falsifiable at all three sites (§1). This is the one I
  was told to weigh hardest, and it is the strongest part of cycle 2: the fix is in the *fake* as
  much as in the code, and `_RecordingSession` is now the kind of fake that can be wrong about
  timing.
- **`PersonaIndex`'s first-wins map** — fixed, and **it does not reintroduce a false skip**, which
  is what I was asked to establish. Nine probes: the second stored state at one URL is now
  recognised (it was not), the first still is, an **unknown** signature at a known URL is **not**
  skipped, a signature-less FlowSpec screen is **never** a skip (a stored `None` cannot equal a
  live `signature`, which `ScreenNode` types as a required `str`), a crawled screen stored
  *behind* a FlowSpec screen at one URL *is* matched, `stored()` returns an exemplar and is not on
  the skip path, an empty index skips nothing, a **corrupt** persona falls back to skipping
  nothing (`load_index`'s bare `except` is genuinely the safe direction), and `enabled=False`
  skips nothing even with a good persona on disk. The widening is sound: every added signature at
  a key is a structurally identical state that really was crawled before, so a match is evidence,
  not a near-miss. No false skip found.
- **The half-implemented ISS-4** — fixed, and verified end to end rather than at `classify` (§4).

- **Maker discipline held.** Per-commit file lists for `96bacbbc`, `48238b4f`, `1be188d5` and
  `9745d63c`: no `qa/contracts/`, no `qa/verdicts/`, no `.goal/goal.json`, no `.goal/dashboard.html`,
  and `qa/issues.jsonl` touched only by the merge union. The Q4–Q9 questions were filed verbatim in
  `qa/feedback-inbox.md` rather than resolved unilaterally.

### 9. Things not on my dispatch that I am recording anyway

- **`ISS-t165-crawl-traversal-3`'s `expected` is not literally met, and that ruling is check A's.**
  The issue asks for the frontier to *account for* every known screen ("re-exploring it … or
  marking it `SKIPPED_UNCHANGED` via a frontier seeded from the persona keys"); the fix is at the
  claim instead. **My position, for A and for the record:** I would ratify it. The harm the issue
  was filed for — eight fabricated deletions on a byte-identical site — is verifiably gone (I
  re-ran the covering test, and its RED is real); the alternative requires navigating to a
  `url_template` the crawl never observed, which is what X1/X7 exist to prevent, and it puts
  D-040's own ≤10%-actions test out of reach. That is **Q5**, and it needs a superseding CR3/CR4
  amendment either way. If A rules the other way, my PASS on the write path stands and the unit
  still fails — a dual check needs both.
- **An unbacked line in the manifest.** It says "`explore_status.displayed_status` independently
  shows this crawl as `BLOCKED_NO_ACTIONS`", but the committed cycle-2 `report.json` carries no
  such field. The claim is **true** — I called it directly: a `COMPLETED` crawl with no actions
  and `skipped_unchanged=1` gives `displayed_status → blocked_no_actions` and
  `skip_note → ", 1 screens skipped as unchanged (not explored)"`. Fix the provenance, not the
  claim.
- **Everything else in the cycle-2 `report.json` matches the manifest exactly** — crawl 1
  20 actions / 9 screens / `frontier empty`; crawl 2 0 actions / 1 screen / the skip-qualified
  `stop_reason` / `skipped_unchanged: 1`; the revision's 8 `missing_unjudged` with
  `missing_screens: []`; and the forced-`frontier_exhausted=True` direct `classify` call also
  returning `missing_screens: []`. I re-read the file rather than trusting the quotation.
- **`ISS-t165-crawl-traversal-4` is `medium` in the ledger** and "low" in the cycle-1 manifest
  table. Immaterial to the outcome; the ledger is canonical.
- **`rt.typed` is unbounded per crawl** (one `TypedAction` per typed field per node, never
  cleared). Bounded in practice by `max_actions`, so not a finding — noted because it is the kind
  of thing that stops being free on a large portal.

### 10. Issue ledger

- `ISS-t165-crawl-traversal-1` — **verified fixed** on my surface (§1). Closing it is for whichever
  checker writes the ledger update on PASS, since A also holds findings.
- `ISS-t165-crawl-traversal-2` — **verified fixed** on the storage/back-compat half (§3, §8); the
  diff-semantics half is A's.
- `ISS-t165-crawl-traversal-4` — **verified fixed**, end to end (§4).
- `ISS-t165-crawl-traversal-3` — A's call (§9).
- **AT-650 filed** (medium, open): `typing_target_allowed` cannot see an input's `type`, so a
  `password` or `file` input reaches the X10-b typing gate as role `"textbox"`. Pre-existing,
  against X10-b, **not chargeable to T-165**.
- Q9's two rows (the `PersonaIndex` first-wins map and the missing `settle()`) deserve ledger rows
  so the record is honest that they existed; I have left that to the PASS-time ledger update
  rather than racing check A on the same file.

### For Umesh

On my dispatched surface — the write path, back-compat, and evidence integrity — this cycle is
genuinely better than cycle 1, and the reason is worth keeping: the maker fixed a *fake* as well
as a guard. The unfireable X7 check is the defect class this project has filed repeatedly
(AT-218), and the fix makes it structurally unrepeatable in that file — I deleted the settle at
three separate call sites and something went red each time. I re-ran 8 of the 10 falsifications
myself and found no second invalid one. Back-compat is real: a full pre-T-165 persona file loads
off disk through the real store, diffs, and keeps every stored screen, with `extra="forbid"`
still rejecting genuinely unknown keys. The relapse plumbing the maker only probed, I tested
end to end across five crawls plus the skip interaction, and it is correct — the remaining gap is
one missing committed test, not a behaviour defect, and I say so rather than passing it in
silence.

**PASS from check B. This does not merge on my say-so** — D-040 needs check A's verdict too, and
A owns the one question I deliberately did not decide (whether a `COMPLETED` crawl that looked at
one screen of nine is acceptable because every surface discloses it). One thing you may be asked
to rule on eventually, though not to unblock this: **AT-650** means the crawler will type a
synthetic value into a real `<input type="password">` whenever the field's name and selector
avoid the words "password"/"passwd" — `#pin`, `#otp`, "Passcode". That predates T-165 and is not
this unit's fault, but it is a live credential-surface gap on a tool you intend to point at real
products, and the fix is small (emit `type` from `enumerate.js`, refuse `password`/`file`).
