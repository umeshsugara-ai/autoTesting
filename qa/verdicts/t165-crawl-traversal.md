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
