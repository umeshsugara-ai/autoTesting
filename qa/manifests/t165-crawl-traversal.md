# t165-crawl-traversal

**Unit:** T-165 — crawl traversal: hybrid strategy · form-input replay · incremental crawl · change tracking
**Criticality:** CRITICAL (dual check, D-040)
**Commit:** `d0778797` (the build) · `380cfa64` (this manifest + the two gaps falsification found)
**Fix cycle:** 2 (of max 3) — see "Cycle 2" below; everything above it is the cycle-1 record.
**Branch:** `wave/t165-crawl-traversal`, from `72513124` (the `master` this worktree was cut from;
`origin/master` has since moved to `dcb467b7` — I did not rebase, the orchestrator owns the merge)
**Executor:** a `/maker` build subagent (Opus), running in its own git worktree
`D:\autoTesting\.claude\worktrees\agent-a6b3b2d68e31aeec3`. Not the orchestrator session. No
checker was dispatched from here; no merge, no push.
**Contract:** `qa/contracts/crawl-traversal.md` CR1–CR7 (DRAFT) · `qa/contracts/explore.md`
X1–X18 **unamended** · `qa/contracts/core-invariants.md` C1–C3, C8
**Authority:** `docs/DECISIONS.md` **D-040** (Approved-by: Umesh) — lines 833–878. D-040's
acceptance tests (b) and (c) are quoted into CR3 and CR4 and are the tests below.
**Not in scope, deliberately not touched:** API/network assertions (T-170, already done) and
permission-surface coverage (T-171).

## The criterion everything else is subordinate to

From T-165's own goal note, carried verbatim into CR5:

> Complete means frontier exhausted; any safety/time/action/depth bound is named as incomplete
> with every denied, skipped and unreached control visible.

Before this unit, `run_crawl` decided completeness by **string comparison**:
`completed = rt.stop_reason == "frontier empty"`. That is fragile in exactly the direction that
matters — any new stop reason (a skip note, a bound qualifier) silently turns a truthful
"incomplete" into "complete". It is now structural:

```python
rt.frontier_exhausted = rt.stop_reason is None          # explore.py::_bfs, after the queue drains
...
return _finish(rt, _terminal_status(rt, rt.frontier_exhausted, login_case))
```

`frontier_exhausted` is set at the ONE place the queue really drains, and only when no bound had
already fired. **AT-463 is why the `is None` matters:** `_click_loop` can set `stop_reason`
mid-screen while the queue happens to empty in the same iteration — a drained queue is then *not*
an exhausted frontier, because controls were left untried on the screen being visited. My first
draft of `_bfs` set `frontier_exhausted = True` unconditionally; I caught it before committing,
and the falsification pass below then proved the guard is real.

## What changed

**Four new modules** (the contract's own "How a unit is verified" says `explore_node.py`,
`explore_return.py` and `portal_persona.py` are near their caps "so new logic belongs in a
stated-reason new module (C3)"):

| Module | Its one job | Lines |
|---|---|---|
| `stages/explore_traversal.py` | CR1: the frontier ORDER. `next_node_id` pops FIFO for `bfs`; for `hybrid`, prefers the deepest queued node discovered from the last visited one, tie-broken by id, else FIFO. | 86 |
| `stages/explore_incremental.py` | CR3: the persona cache key, the skip decision, and the skip's honest `stop_reason`. | 136 |
| `stages/explore_replay.py` | CR2/CR7: records what X10-b really typed and re-issues it, through the same gate. | 142 |
| `stages/persona_changes.py` | CR4: classify new / changed / missing / broken. | 115 |
| `stages/explore_runtime.py` | the `ExploreRuntime` dataclass, moved out of `explore.py`. | 92 |

**`ExploreRuntime` was moved, `_bootstrap_login` deliberately was not.** `explore.py` sat at
exactly 300 lines. The obvious extraction was the login helpers — and it would have broken X1,
whose verify is literally `grep -n run_case src/autotester/stages/explore.py` showing one call
site inside `_bootstrap_login`. X1 is in a contract I may not amend, so I extracted the runtime
dataclass instead. Verify still holds (pasted below).

**Edited in place:** `schema/enums.py` (`TraversalStrategy`; `NodeStatus.SKIPPED_UNCHANGED`) ·
`schema/crawl.py` (`strategy`, `incremental`, `skipped_unchanged`) · `schema/portal_persona.py`
(five `list[str]` fields + `counts()` on `PersonaRevision`) · `stages/explore.py` ·
`stages/explore_return.py` (the replay call in `_replay_discovery`) · `stages/explore_typing.py`
(the record call) · `stages/crawl_coverage.py` (`skipped_unchanged` reason; the `whole` flag) ·
`stages/portal_persona.py` (the diff onto the revision) · `stages/explore_status.py`
(`displayed_status`, `skip_note`) · `ui/crawl_view.py` · `ui/routes_crawls.py` · `cli_crawl.py` ·
`stages/crawl_report.py` · `tests/crawl_fake.py` (pass-through only; existing callers byte-identical).

**Idea ports, not vendored code.** `explore_traversal.py`'s docstring attributes the depth-first
candidate ordering to Crawljax (Apache-2.0) and `explore_incremental.py`'s the cache key to
Stagehand (MIT). Neither is a dependency; no code was copied. `pyproject.toml` is unchanged.

**PP2 is preserved.** `_merge` is still add-only. CR4 adds a *classification* onto the dated
`PersonaRevision` that PP3 already required; nothing stored is dropped, blanked or rewritten.
Asserted directly: `test_a_removed_screen_lands_on_the_persona_history_even_though_merge_adds_only`
checks the screen list still contains the removed screen.

## Verify — each command run on its own, output pasted

### `uv run pytest` (no CLI `-q`, AT-503)

```
=========================== short test summary info ===========================
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
2 failed, 2083 passed, 6 skipped, 14 xfailed, 15 warnings in 1047.25s (0:17:27)
```

The pre-change baseline on this same worktree was
`2 failed, 2034 passed, 6 skipped, 14 xfailed, 15 warnings in 890.92s` — the same two failures,
+49 passing tests from this unit, nothing newly broken.

Three failures were named in the brief as pre-existing and not chargeable here:
`tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`
(AT-627, load-sensitive) and the two `tests/test_goal_done_checks.py` failures
(`ISS-at638-remainder-2`, traced to orchestrator commit `f9e7d406`). **I confirmed there is no
fourth** — the summary names exactly two, and AT-627's flake probe passed on this run (as it did on
the pre-change baseline). I did not touch any of them.

I also checked the first of the two is not secretly about this unit. Its offenders are
`['T-186', 'T-189', 'T-190', 'T-191', 'T-192']` — **T-165 is not among them**, and cannot be: its
`done_check` names three test files that did not exist on a clean repo, so it fails before the unit
is built, which is exactly what that test demands.

### `uv run pytest tests/test_explore_completeness.py tests/test_explore_traversal.py tests/test_persona_changes.py` — the `done_check`

```
warning: `VIRTUAL_ENV=d:\autoTesting\.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
.........................................                                [100%]
41 passed in 218.40s (0:03:38)
EXIT=0
```

(`tests/test_explore_replay.py` is the fourth file of this unit. It was split out of
`test_explore_traversal.py` when that file crossed the 300-line cap; the `done_check` as written
does not name it, so it is run by the full suite above. Flagged, not hidden.)

### `uv run ruff check src tests scripts`

```
warning: `VIRTUAL_ENV=d:\autoTesting\.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
All checks passed!
```

### `uv run autotester doctor`

```
warning: `VIRTUAL_ENV=d:\autoTesting\.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
doctor: clean
```

Doctor was **not** clean on the first attempt — it caught `explore.py` at 312 and
`test_explore_traversal.py` at 309, and later `cli_crawl.py` at 303. All three were fixed by
moving code to where it belonged (the CR3 helpers into `explore_incremental`, the CR2/CR7 tests
into `test_explore_replay.py`, the skip wording into `explore_status.skip_note`), not by deleting
rationale.

### X1's own verify, unaffected by the `ExploreRuntime` move

```
$ grep -n run_case src/autotester/stages/explore.py
4:invent a click or a navigation** — `execute.md` E5 ("`run_case` performs
6:through `run_case` except for the human-authored login bootstrap case. Every
35:from autotester.stages.execute import run_case
61:    """Run the human-authored login case through `run_case` — the ONLY place
67:    `run_case` blocks for the full step timeout before reporting ERRORED.
79:    result = run_case(case, rt.session)
83:    # AT-528: a COMPLETED step sequence is NOT proof of authentication — run_case
```

One call site, line 79, inside `_bootstrap_login`. The rest are prose.

### CR6's no-provider grep over the four new modules

```
$ grep -n "provider\|openai\|anthropic\|litellm" src/autotester/stages/explore_traversal.py \
    src/autotester/stages/explore_incremental.py src/autotester/stages/explore_replay.py \
    src/autotester/stages/persona_changes.py
src/autotester/stages/explore_traversal.py:4:no provider). A new module rather than more lines in `explore_node.py` or
src/autotester/stages/explore_traversal.py:49:    (CR6). No provider, no clock, no randomness — two crawls over the same graph
```

Both are docstring prose. No import, no call.

## Real-browser evidence — headed Chromium, local fixtures only

Script: `.work/t165_evidence.py` (scratch, not committed). Report:
`qa/evidence/browser-t165-crawl-traversal-2026-09-27/report.json` (committed).
Every crawl ran with `headed=True` against a `127.0.0.1` `http.server` serving
`tests/fixtures/`, under a real signed `RunApproval` (`production=False`) — the D-018 gate was
exercised, never bypassed. `write_policy` was left at its default except for the one arm that
needs X10-b typing, which used `TEST_ACCOUNT` + `synthetic_typing=True` against a local fixture.
**No real product was crawled, no network traffic left the machine, nothing was written to
production.**

### A and B — CR1, same budget, and the incomplete report

| | A_bfs | A_hybrid | **B (max_actions=8)** |
|---|---|---|---|
| strategy | bfs | hybrid | hybrid |
| status | `stopped_bound` | `stopped_bound` | **`stopped_bound`** |
| `is_success` | False | False | **False** |
| `stop_reason` | `max_actions` | `max_actions` | **`max_actions`** |
| actions | 10 | 10 | 8 |
| templates visited | `/`, `/deep1`, `/wide1`, `/wide2` | `/`, `/deep1`, `/deep2`, `/deep3`, **`/deep4`**, `/wide1` | `/`, `/deep1`, `/deep2`, `/deep3` |
| coverage | 52% | 50% | **40%** |
| holes | `bound:max_actions` 2, `not_visited` 7 | `bound:max_actions` 1, `not_visited` 9 | **`not_visited` 12** |

CR1, observed: at an identical 10-action budget the hybrid crawl reached workflow step **4**
(`/deep4.html`) while BFS was still on step 1 — and it still discovered all four `wide*` branches,
so it is not depth-first-with-amnesia (D-023 is not revived).

**The B case is the one the brief asked for.** A bound fired and the report declares itself
incomplete: status `stopped_bound`, `is_success` **False**, `stop_reason` naming the bound,
coverage **40%**, and the 12 controls it never reached listed individually, by screen, selector,
name and reason — e.g.

```json
{ "screen": "/wide3.html", "selector": "#fb3", "name": "Filter beta three", "reason": "not_visited" }
```

with `/deep4.html`, `/wide1..4.html` enumerated in `templates_queued_never_visited`. Nothing was
rounded up, nothing read 100%, and no screen it had not opened was described as explored.

### C — CR2, a screen that only a replayed keystroke can restore

`tests/fixtures/form_site/index.html` reveals a `#panel` (containing `#detail`/`#history`) by JS,
only when `#code` is non-empty — a **client-side STATE at the same URL** (the AT-227 shape). So
`goto` can never restore it and only `_replay_discovery` can, which makes the replay load-bearing
instead of incidentally satisfied by `go_back`.

| | default policy | `TEST_ACCOUNT` + `synthetic_typing` |
|---|---|---|
| controls discovered | 4 | **9** |
| controls exercised | 3 | **9** |
| coverage | 75% | 100% |
| holes | `policy:typing disabled under this policy (X10-b)`: 1 | none |

The stored graph for the typing arm, read back off disk:

```
/            | explored | depth 0 | sig e62dc170fe | ['#code', '#go', 'link Reference guide', '#detail', '#history']
/            | explored | depth 1 | sig 40640fcdca | ['#code', '#go', 'link Reference guide', '#detail', '#history']
/other.html  | explored | depth 1 | sig f716c12737 | ['link Back to the lookup']
--- edges ---
fill  | #code -> same_screen        click | #go  -> navigated
navigate | Reference guide -> navigated
fill  | #code -> same_screen        click | #go  -> same_screen
click | #detail -> same_screen      click | #history -> same_screen
navigate | Back to the lookup -> navigated
```

Two distinct signatures at the same `/`: the base state and the panel state, the panel reached at
depth 1, **explored**, and its controls exercised — after the crawl had navigated away to
`/other.html` and come back. The second `fill #code` in that trace is the replay. CR7's half (the
replay passes the same X10-b gate) is asserted in `tests/test_explore_replay.py` and falsified
below. Note the honest default: **with typing off, the panel is never reached and the report says
so** (75%, one named policy hole) rather than pretending the screen does not exist.

## Capability coverage — every claim, its test, the edit that breaks it, and the result

Falsification method: `git archive HEAD` (not `tar`) into a throwaway copy **outside** the bound
worktree — an archive carries no `__pycache__`/`.pytest_cache`, so no stale `.pyc` `co_filename`
can bake the original path into a traceback. Driver `.work/`-external scratch script; each
mutation is a **single hunk**, applied only after the named test is proven green, reverted
immediately, and the test re-proven green afterwards. Every mutation's anchor was asserted to
appear exactly once before it was applied.

| # | Claim (criterion) | Covering test | Single-hunk falsifying edit | GREEN → RED |
|---|---|---|---|---|
| 1 | CR1 hybrid really descends | `test_explore_traversal.py::test_hybrid_descends_into_the_workflow_just_entered_then_backtracks` | `descend = None` in `next_node_id` | `1 passed in 0.29s` → `1 failed in 0.27s` |
| 2 | CR1/X4 a crawl always terminates | `test_explore_traversal.py::test_every_strategy_removes_exactly_one_id_per_call_so_a_crawl_terminates` | `queue.remove(descend)` → `pass` | `1 passed in 0.20s` → `1 failed in 0.67s` |
| 3 | **CR5 the completeness chokepoint** | `test_explore_completeness.py::test_a_bound_that_fires_mid_node_never_reads_as_an_exhausted_frontier` | `rt.frontier_exhausted = True` | `1 passed in 0.43s` → `1 failed in 0.59s` |
| 4 | CR5 a skip is named in `stop_reason` | `test_explore_completeness.py::test_a_skip_never_reads_as_having_explored_the_screen` (live) | `exhausted_reason` always returns `"frontier empty"` | `1 passed in 45.86s` → `1 failed in 44.92s` |
| 5 | CR5 a skip clears the 100% headline | `test_crawl_coverage.py::test_a_crawl_that_skipped_a_screen_as_unchanged_never_reads_100_either` | `skipped_any = False` | `1 passed in 0.92s` → `1 failed in 0.78s` |
| 6 | CR3 incremental is off by default | `test_explore_completeness.py::test_incremental_is_off_by_default_so_every_existing_caller_is_unchanged` | `load_index` ignores `enabled` | `1 passed in 0.98s` → `1 failed in 1.93s` |
| 7 | CR3 the skip compares the SIGNATURE | `test_explore_completeness.py::test_a_genuinely_changed_project_is_re_explored_not_skipped` (live) | signature comparison removed | `1 passed in 91.75s` → `1 failed in 45.58s` |
| 8 | CR4 a bound may not claim `missing` | `test_persona_changes.py::test_a_bound_truncated_crawl_never_reports_missing_only_unjudged` | `"missing_screens": absent` unconditionally | `1 passed in 0.22s` → `1 failed in 0.52s` |
| 9 | CR4 `broken` is not re-reported | `test_persona_changes.py::test_a_screen_already_recorded_broken_is_not_re_reported` | `_previously_broken` forgets the history | `1 passed in 0.21s` → `1 failed in 0.38s` |
| 10 | CR7 the replay passes the same gate | `test_explore_replay.py::test_a_password_field_is_never_replayed_even_though_it_was_recorded` | `_gated` → `return True` | `1 passed in 0.46s` → `1 failed in 0.50s` |

`10 mutations, 0 problem(s)`.

**Two of these did not falsify on the first run, and both were real test defects, not code
defects.** They are the most useful thing in this manifest:

- **#3, the decisive claim.** Mutating `rt.frontier_exhausted = True` left
  `test_a_bound_stopped_crawl_is_never_completed_and_always_names_the_bound` (six parametrized
  cases) **entirely green** — because every one of those cases stops at the *top* of the traversal
  loop, where `_bfs` returns early and the mutated line never executes at all. The claim I cared
  about most had no test that could see it break. I wrote
  `test_a_bound_that_fires_mid_node_never_reads_as_an_exhausted_frontier`, which builds the actual
  AT-463 shape (a bound set mid-node while the queue drains in the same iteration), and the
  mutation now reddens it.
- **#5.** `skipped_any = False` left the live skip test green, because in that scenario
  `controls_exercised` is 0 so `percent` was already 0 — the arithmetic masked the rule. Isolated
  in `test_crawl_coverage.py` with a skipped screen that contributes no holes, so only the rule
  can keep the figure off 100.

**The bound worktree was verified intact afterwards** — `git status --short` showed only the two
test files I deliberately added, and `git diff --stat HEAD` only their `+72/-1`. No source file
was touched by the mutation pass.

## Persona walk

Walked, not skipped. `qa/contracts/portal-persona.md` PP1–PP6 were read before touching
`portal_persona.py`. PP2 (add-only) and PP3 (dated, non-blank summary) are the two this unit comes
closest to, and both are preserved — PP2 asserted directly (above), PP3 asserted by
`test_pp3_is_unchanged_a_blank_summary_is_still_refused`. PP5 (secrets by shape only) is untouched:
`explore_replay` holds recorded values **in memory only and never persists them**, and
`Crawl.stop_reason` still passes through `secrets.scrub_optional` in `_finish`.

## Contract questions filed, not guessed

Three places in `crawl-traversal.md` are open enough that a different reading would also pass a
literal check. All three are filed **verbatim** in `qa/feedback-inbox.md` (2026-09-27 entry) with
the reading I took and why; I did not edit `qa/contracts/`. In short: (Q1) CR4 `broken` has no
place to store prior state without breaking PP2 — I read it from the append-only revision history;
(Q2) CR4 does not say what a bound-truncated crawl reports instead of `missing` — I added a
disclosed `missing_unjudged`; (Q3) CR3's changed-site arm says "close to" with no figure — I
asserted the strictly stronger `second.actions >= first.actions`.

## Gaps stated, not hidden

1. **CR3's ≤10% figure is measured on one fixture shape** (`deep_site`, 9 screens). The mechanism
   is signature equality, which does not depend on portal size, but the *ratio* in the acceptance
   test is a property of this fixture. A checker should decide whether one fixture is enough for a
   numeric acceptance criterion.
2. **The `done_check` names three files; this unit has four.** `test_explore_replay.py` was split
   out under the 300-line cap after the `done_check` was written. It runs in the full suite. If the
   checker wants it in the `done_check`, that is a `.goal/goal.json` edit I did not make.
3. **CR4's live arm is thinner than CR3's.** The new/changed/missing/broken classification is
   proven by 17 tests including two end-to-end through the real `build_portal_persona` and a real
   store — but not by a headed-browser two-crawl diff. The classification is a pure function of
   nodes already on disk, so a browser adds no signal I can name; I say so rather than implying
   live coverage I do not have.
4. **`missing_unjudged` is my invention** (Q2 above). If the checker rejects it, `persona_changes`
   and one `PersonaRevision` field come out; nothing else depends on it.
5. **The `skipped_unchanged` surfaces were added late,** after I re-read CR5's "every surface X16
   already lists" and found the count was only reaching the coverage holes. Crawl page, crawls
   table, CLI line, workbook and `crawl.json` now all carry it, asserted by
   `test_a_skip_is_visible_on_every_surface_x16_lists`. That test uses a **stored envelope** rather
   than a live crawl, deliberately (the bug class is a renderer omitting a field), but it means
   those five surfaces are not proven end-to-end from a real incremental crawl.
6. **Not rebased onto current `origin/master`** (`dcb467b7`). The branch is cut from this
   worktree's base `72513124`.

## What the two checkers should attack hardest

1. **Try to make a crawl say `completed` when it did not exhaust its frontier.** That is the whole
   unit. Best angles: a bound firing inside `_click_loop` on the last queued screen (AT-463 — now
   tested, attack the test); an incremental crawl that skips everything; `max_depth` truncation
   combined with `hybrid`; and `explore_status.terminal_status`'s login branches, which return
   before the `completed` check and could in principle launder an unexhausted frontier into a
   status a human reads as fine.
2. **Attack #3 and #5 above as a class, not as two fixed bugs.** Two of ten claims had tests that
   could not see their own logic break. Assume there is a third: re-run the mutation set with
   different anchors, especially on `crawl_coverage`'s `whole` flag and `displayed_status`.
3. **CR3's skip is a decision to NOT look.** Every false skip is an unexplored screen reported as
   known. Try: two different screens colliding on `PersonaScreen.key()`; a signature that is stable
   across a real content change; a persona written by an older schema version; `load_index`'s
   bare `except Exception` hiding a corrupt persona (it falls back to skipping nothing, which is
   the safe direction — confirm that is really what happens).
4. **CR2's replay is a write.** Confirm it cannot widen X10-b: try a policy change *between*
   recording and replay, a password field that becomes visible later, an upload input, and a
   recorded value replayed onto a screen on a different domain.
5. **PP2.** Construct a merge path where the CR4 diff could drop or blank a stored screen.

## Cycle 1 — needs-fix (FAILED on a dual check). Kept as history; the record continues below.

Verdict `qa/verdicts/t165-crawl-traversal.md`, **Cycle checked: 1**, both sections present:
check B at `6fc02c68`, check A at `c4a845b6`. **Both checks FAILED independently, on four
non-overlapping defects.** No merge, no push, no PASS — and `qa/contracts/crawl-traversal.md`
therefore stays **DRAFT**, since it goes ACTIVE on this unit's first PASS and there has not been one.

That is the dual check working as designed rather than a bad outcome: two checkers bound to the same
contract, neither seeing the other's findings while deriving them, produced a disjoint union. A single
check would have shipped this unit with three of the four defects still in it.

### The four defects, in the order the fix should take them

| Issue | Sev | Where | What is wrong |
|---|---|---|---|
| `ISS-t165-crawl-traversal-3` | **critical** | `explore_incremental.skip_unchanged()` vs `explore_node._enqueue()` | A skipped node's children are never enqueued, because the skip short-circuits **before** `visit_node()`. So an incremental crawl over a byte-identical site ends with a 1-node graph and `stop_reason` claiming an exhausted frontier, and `classify()` on that graph reports the other 8 screens as `missing_screens` — deletions that never happened. |
| `ISS-t165-crawl-traversal-1` | high | `explore_replay.perform()` | Never calls `check_destination()` after a replayed fill/click. Every other action path in the crawler re-checks the landed host (X7); the replay path does not. |
| `ISS-t165-crawl-traversal-2` | high | `PersonaScreen.key()` | URL-template-only, unlike `ScreenNode.id` which hashes {url_template, signature}. So `_incoming_screens()`'s `seen` set silently drops a second structurally-distinct screen sharing a URL — it can never appear as new/changed/missing/broken in CR4's diff. |
| `ISS-t165-crawl-traversal-4` | low | `persona_changes._previously_broken()` | Reads only the first prior revision with any non-empty category, so a continuously-broken screen is re-flagged as newly broken after an unrelated intervening crawl. Noisy, not silent — not independently blocking. |

**ISS-3 is the one that matters most, and it is worse than a masked mutation.** It is D-040's own
written acceptance test (c) — *"the same two crawls with nothing removed produce zero missing
entries"* — failing on the **ordinary incremental path**, reproduced live in headed Chromium against
`tests/fixtures/deep_site`. The unit exists to make completeness honest, and its mainline incremental
path reports 8 fabricated deletions while claiming the frontier was exhausted. No existing test sees
it because no test joins a real incremental crawl's own graph to `classify()`:
`tests/test_persona_changes.py` uses synthetic fixtures only, and the `incremental_pair` fixture in
`tests/test_explore_completeness.py` never calls `classify()` on its crawl-2 output. **That missing
join is the test the fix must add** — not another synthetic-fixture case.

### What this manifest got right, recorded because it is the useful part

The "Where to attack this" section named two of the four defects before either checker ran.
Attack #3 said *"two different screens colliding on `PersonaScreen.key()`"* — that is exactly
`ISS-2`. Attack #4 said *"confirm CR2's replay cannot widen X10-b"* — check B looked there and found
the missing `check_destination()`, `ISS-1`. Writing down where the unit is weakest is what made two
of these findable in one cycle. It is also the honest reading of attack #2's prediction (*"assume
there is a third masked mutation"*): check A re-ran the mutation set and found **none** — the ten
capability rows held. The defect was in an **eleventh claim nobody wrote a row for**, which is the
sharper lesson: the gap was in the coverage table's scope, not in its rigour.

### Rulings folded into the contract (both checkers, independently identical)

Q1 ratified (`existing.history` reversed is the only PP2-safe source for `broken`'s prior state) ·
Q2 ratified (`missing_unjudged` becomes a named **fifth** CR4 category for the bound-truncated
frontier) · Q3 ratified with `second.actions_used >= first.actions_used` as a **lower bound only**.
Check A derived all three before reading check B's section. The merge resolution in `a25119fa` was
verified sound by both: CR2's `explore_replay.perform()` and AT-335's bounded arrival poll both
survive and are correctly sequenced in `_replay_discovery()`.

### Two things recorded, neither chargeable to this unit

Check A saw `test_hook_prints_the_report_and_exits_zero_on_a_healthy_log` red in a narrow background
run and clean in the full run — reads as this worktree's live `qa/.last-tick` bleeding into a test
that expects a clean `tmp_path`. Filed for a look, not against T-165. And check B caught a false
positive in **its own** first probe (mis-filtered edges by outcome, same-selector instead of
distinct-signature) and corrected it before including the probe in the verdict.

**Cycle 2 is a normal fix cycle — no HUMAN_GATE.** Both checkers said so explicitly, and I agree:
every one of the four is a code defect with a named location, and none of them needs a decision only
Umesh can make.

---

# Cycle 2 — the four defects fixed, plus four more found on the way

**Fix cycle:** 2 (of max 3)
**Commits:** `96bacbbc` (the four defects), `48238b4f` (the three findings the fresh review
raised on `96bacbbc`, two of them defects in the fixes themselves — see the next section) and
`1be188d5` (one added back-compat assertion), on top of the merge `7fdc27cf`
**Branch:** `wave/t165-crawl-traversal`, **now current with `origin/master`** (`2203f644`) — the
gap cycle 1 disclosed is closed. The merge had one conflict, `qa/issues.jsonl`, resolved as a
UNION (it is an append-only ledger; master added `ISS-t191-run-video-3`, this branch added the
four `ISS-t165-*` rows, and both belong). `src/autotester/schema/enums.py` and `docs/MAP.md`
auto-merged.
**Executor:** the same `/maker` build subagent shape (Opus), in the SAME worktree
`D:\autoTesting\.claude\worktrees\agent-a6b3b2d68e31aeec3`. No checker dispatched from here; no
merge to master, no push, no verdict written.

## The fresh review's three findings — two of them defects in the cycle-2 fixes themselves

Lifecycle rule: code I wrote goes to a fresh-context `senior-software-engineer` agent before I say
"done". It reviewed commit `96bacbbc` read-only, against `crawl-traversal.md` CR3/CR4/CR5/CR7 and
`explore.md` X7/X10-b, and **live-reproduced** two defects rather than asserting them. Its verdict
was **Warning**, with the reasoning that the high finding "should go back to the maker before this
unit is treated as closing ISS-4". It did go back. All three are fixed in commit `48238b4f`, on top
of `96bacbbc`, and each one has its own covering test and its own falsification row.

I am recording this at the top of the cycle-2 record rather than burying it, because **two of the
three findings are defects I introduced while fixing the checker's four** — a cycle-2 patch is not
automatically safer than the code it replaces, and a checker should read the fixes with that in
mind.

### HIGH — `_previously_broken` over-corrected, and I had missed half of ISS-4's own `expected`

`ISS-t165-crawl-traversal-4` asks, verbatim, for "the union of `broken_screens` across ALL prior
revisions **minus any later revision that observed the screen and found it not-broken**". I
implemented the union and **not the subtraction**, then wrote a docstring calling the union "the
only reading that cannot forget" — which is true and also the problem: it can no longer *un*-forget.
The review reproduced the consequence in three revisions: `/a` broken, `/a` later reached and
healthy, `/a` genuinely relapses with `ABORTED_ERROR` → `broken_screens == []`, silently, forever.
I had traded a noisy false alert for a silent missed regression, which is the worse of the two for a
tool whose whole job is catching regressions.

The subtraction cannot be computed from the five CR4/CR5 categories, because a screen reached and
found healthy appears in **none** of them — "never re-observed" and "observed healthy" are
indistinguishable in the stored history. So `PersonaRevision` gains one field,
`healthy_screens`, and `_previously_broken` replays the history in order: `broken_screens` adds a
key, `healthy_screens` removes it.

**Everything I did to keep that from becoming a sixth category or a migration:**

- `default_factory=list` — every persona written before this unit still loads. Asserted by
  `test_a_persona_written_before_this_unit_still_loads_and_classifies`, which constructs a revision
  with none of the new fields.
- It is **not** in `PersonaRevision.counts()`; `CATEGORIES` stays exactly five; a new `PROVENANCE`
  tuple holds it. `test_classify_returns_exactly_the_revisions_own_field_names` now asserts all
  three of those facts plus that the two tuples are disjoint — so the five-category surface the
  contract names cannot drift by accident, which is the failure mode adding a field invites.
- It records only keys a **prior revision called broken** that this crawl **visited** and found
  healthy. A `SKIPPED_UNCHANGED` node is not an observation and never lands there — the same
  reasoning `_judged_exhausted` applies to `missing`, and it has its own test
  (`test_a_skipped_screen_is_not_an_observation_of_health`).
- `describe()` gains the word "recovered", which is the only place it surfaces to a human. That
  also means a crawl whose *only* news is a recovery still writes a revision instead of dropping
  the observation on the floor.

**This puts the code in tension with the contract, and the contract is what has to move.**
`crawl-traversal.md`'s "`broken`'s 'prior state' ruling" amendment says the prior state is "the most
recent `PersonaRevision` that classified anything, via its own `broken_screens` list" — which is
*precisely the implementation ISS-4 was filed against*. I implemented the issue, not the clause,
because the clause's own reading is the defect. A checker reading the contract literally will find
the code in violation of it; the clause needs a superseding amendment, and `healthy_screens` needs
ratifying as provenance rather than a sixth category. Filed as **Q8**. I did not touch the contract.

### MEDIUM — the new X7 check in `replay_fills` had no `settle()` in front of it

Every other X7 site settles before re-checking the host: `explore_typing._type_one`, and
`perform()`'s own two branches. `replay_fills` did not. `BrowserSession.fill()` is a bare Playwright
`.fill()` that does not wait for a JS-triggered navigation, so `current_url()` could still return
the old, on-domain URL and the check would pass **for free** — in exactly the auto-submitting-fill
case my own comment claimed to catch. A guard that cannot fail is not a guard.

The tests could not see it, and that is the more useful half of the finding: `_RecordingSession`
returned a constant URL, so no ordering of settle and check could distinguish itself from any
other. The fake now models navigation **asynchronously** — an action only *schedules* the new URL
and `current_url()` changes only when `settle()` runs. All eleven replay tests still pass, and
removing the settle now reddens one (falsification M8). **A fake that cannot be wrong about timing
cannot test a timing-dependent guard**, and I had built one.

### MEDIUM — `PersonaIndex` kept the first-wins map that ISS-2 removed everywhere else

`explore_incremental.PersonaIndex.__init__` still did `setdefault(screen.key(), screen)` — the
identical defect ISS-2 names, in a file cycle 2 had not touched, and reachable **because** the ISS-2
fix made a persona able to hold two states at one URL. A live node matching the *second* stored
state compared against the first, missed, and was re-explored on every incremental crawl. Not a
false skip (the safe direction), but CR3's efficiency guarantee and D-040 acceptance test (b)'s
"≤10% of the first crawl's actions" quietly lost for exactly the X3/X14 shape the ISS-2 fix newly
supports. The index now holds every state at a key and `skip_reason` matches against all of them;
`stored()` still returns one exemplar and its docstring says skip decisions must not use it.

Fixing this also killed a piece of dead code I had written: a `node.signature is None` guard, when
`ScreenNode.signature` is a required `str`. A stored `None` means "unknown" and can never equal a
live signature, so the FlowSpec case is handled without it — and now has an explicit assertion
instead of an unreachable branch.

### One more, which nobody found for me

The `missing_unjudged` prose I wrote in cycle 2 said "not judged (the frontier was not exhausted)".
This cycle's **own Mode D report** contradicts it on the line above: crawl 2 stops with
`stop_reason: frontier empty`. The frontier *was* exhausted; the skip is what blocked the claim. The
label now names both causes, and `test_a_real_incremental_recrawl_of_an_unchanged_site_reports_no_deletion`
asserts the summary and the `stop_reason` cannot contradict each other again (falsification M10).
I found this by reading my own evidence against my own prose, which is the check I should have run
before calling the label "now the true statement".

### What the review looked at and did not find

Recorded because a "no finding" is only worth something if the search was real. It traced the real
import graph and confirmed the function-scoped `from autotester.stages.explore_node import …` in
`_refusal_of` is **necessary**, not sloppiness: `explore_return` imports `explore_replay` at module
scope and `explore_node` name-imports `explore_return`, so a module-scope import would be a genuine
circular-import `ImportError`. It confirmed the new `record_edge` call cannot double-count `rt.edges`
or corrupt `crawl_coverage.compute_coverage` (`exercised` is an `any(... in PERFORMED)`, so an added
`OFF_DOMAIN_REFUSED` edge cannot flip a control either way), and that `actions_used` is untouched by
`explore_replay`, matching the existing convention that a `return_to` replay is not a new X4 action.
It swept every reader of `PortalPersona.screens` for the `key()`→`ident()` switch and found
`portal_persona_view` only iterates for rendering; the one affected reader was `PersonaIndex`, above.

It also left **one open question I could not settle either**, and it is the sharpest thing in this
manifest: `missing` and `changed` still work at `key()` granularity, so if a product has two states
at one URL and **one of them is genuinely removed while the other survives**, the removal appears in
no category at all — not `missing`, not `missing_unjudged`. The contract's own ISS-2 gap note offers
two remedies and this unit takes the storage/reachability one without extending `missing` to
signature granularity. I believe that is an acceptable incremental cut, but I cannot point at a test
or a contract sentence that settles it, so it is the checker's call, not mine.

## What changed, per issue

### `ISS-t165-crawl-traversal-3` (critical) — a skip may not license a `missing` claim

**The diagnosis is checker A's and it is right:** `explore_incremental.skip_unchanged()`
short-circuits before `explore_node.visit_node()`, and `_enqueue()` only ever runs inside
`visit_node`'s click loop, so a skipped screen's children are never discovered on this crawl. The
queue drains, `rt.frontier_exhausted` is set True at the one place it can be, and
`persona_changes.classify()` then reported every stored key the crawl never reached as `missing` —
8 deletions on a byte-identical site.

**The fix is at the claim, not at the traversal.** New `persona_changes._judged_exhausted(nodes,
frontier_exhausted)`: a crawl that skipped any screen may not testify that a screen is gone, so
those keys go to `missing_unjudged` — the disclosed-unknown category CR4 already has for a
frontier that was not exhausted — and `missing` stays empty. `describe()`'s prose moved from "a
bound truncated the frontier" to "a bound or a skipped-unchanged screen left the crawl incomplete". **I got that
label wrong once and caught it against this cycle's own evidence:** my first wording was "the
frontier was not exhausted", which the Mode D report immediately contradicted — crawl 2 stops
with `stop_reason: frontier empty`, so the frontier *was* exhausted and the blocker is the skip.
The label now names both causes and matches the `stop_reason` it sits beside.

**Why I did NOT take check A's suggested fix (seed the frontier from `persona.keys`), stated up
front because it is the biggest judgement call in this cycle.** `PersonaScreen` stores a
`url_template` — a *template* (`/user/{id}`), not a URL — so seeding from it means the crawler
navigating to a destination it never observed, which is what X1/X7 exist to prevent; and
`PersonaTransition` records screen NAMES, so it cannot re-materialise a `ScreenNode` to enqueue
either. Both variants also cost real navigations, which puts CR3's own acceptance test (b) — ≤10%
of the first crawl's actions — out of reach (`deep_site` spends 20 actions on 9 screens; re-reaching
8 of them is ~40%). D-040 asking for ≤10% is D-040 asking for the subtree to be pruned. So the
defect was never that the crawl pruned; it was that the pruned crawl then claimed to have looked.
**This is Q5 in `qa/feedback-inbox.md`, filed verbatim, and it is a contract call the checker may
overturn — if pruning is NOT intended, CR3's ≤10% test and this fix cannot both stand.**

**The test the brief required, and it is the one that matters.** `tests/test_persona_diff_pipeline.py::
test_a_real_incremental_recrawl_of_an_unchanged_site_reports_no_deletion` runs both REAL Chromium
crawls of `tests/fixtures/deep_site` and asserts on the revision `build_portal_persona` really
writes. Not another synthetic-fixture case: the bug lived exactly in the join no test made, and a
sixth synthetic case would have stayed green through all of it.

### `ISS-t165-crawl-traversal-1` (high) — X7 on the replay path

`explore_replay.perform()` now calls `check_destination(rt.project, rt.session.current_url())`
after **every** action it issues, and a `NavigationRefused` is recorded exactly as
`explore_node.try_action` records one: a NAVIGATION issue plus an `OFF_DOMAIN_REFUSED` edge
(`_refusal_of`), with the reason returned upward so `_replay_discovery` reports it rather than
success. "Every action" is literal and deliberate — the check runs after each re-issued fill inside
`replay_fills`, not only after the final click, because a fill whose `onchange` auto-submits can
leave the domain before any click is replayed at all. That is its own test.

**That check originally had no `settle()` in front of it**, which made it a guard that could not
fail — see the review-findings section. It settles now, like every other X7 site.

`NavigationRefused` raised by the fill/click itself (rather than detected afterwards) now takes the
same recording path instead of falling into the generic `except Exception` string.

### `ISS-t165-crawl-traversal-2` (high) — two screens that merely share a URL

New `PersonaScreen.ident()` → `(key(), signature)`, and it is a **method, not a field**.
`_incoming_screens` and `_merge` dedupe on `ident()`, so the second of two structurally distinct
states at one `url_template` is stored instead of dropped. `persona_changes._reached` now maps a
key to **every** node reached at it, so a second state contributes to its key's `changed`/`broken`
classification instead of vanishing behind a `setdefault`. `explore_incremental.PersonaIndex` kept
the identical first-wins `setdefault` and I missed it in `96bacbbc`; the review caught it and
`48238b4f` fixes it, so the second stored state is also recognised as *unchanged* and not
re-explored every crawl.

**`PersonaScreen.key()` is deliberately left signature-free**, against the contract's own first
suggestion ("e.g. include `signature`"). Folding the signature into `key()` destroys CR4's
`changed`, which is *defined* as the same key with a different signature: every edited screen would
read as one `new` plus one `missing`. The contract offers the second closure too ("change the
reachability lookup to keep every same-key-different-signature screen"), and that is the one taken.

**Do existing persona files still load? Yes — asserted, not assumed.** As of `96bacbbc` nothing
stored changed shape at all: no field added, removed or retyped, only a method. `48238b4f` then
added exactly one field, `PersonaRevision.healthy_screens`, with `default_factory=list`, so the
answer is unchanged and the same test proves it — it validates a raw dict with no such key and
asserts the default is `[]`, i.e. "recorded no observation", never "observed everything healthy"
(which would silently clear real broken records on the first crawl after the upgrade). `test_a_persona_written_before_this_unit_still_loads_and_classifies`
validates a pre-T-165 `portal_persona.json` shape (screens with and without a signature, a revision
carrying none of the CR4 category lists) through `PortalPersona.model_validate`, checks `counts()`
reads all zeros, and diffs against it. `extra="forbid"` rejects unknown keys that are PRESENT; an
old file simply lacks the new ones. The one behaviour change a reader should know about: a persona
that already holds a FlowSpec-sourced screen at a URL will now ALSO store the crawled screen at
that URL, because the crawled one carries the signature CR3's skip and CR4's `changed` both need
and the FlowSpec one never can. That is add-only (PP2 intact), and it fixes a quieter bug of its
own — before this, a FlowSpec screen at a URL meant the crawl's signature for that screen was never
stored at all, so it could never be skipped and never be classified.

### `ISS-t165-crawl-traversal-4` (low) — broken-ever

`_previously_broken` replays the **whole** append-only history in order instead of returning the
nearest revision that classified anything. A screen broken in revision 1 and still broken now is no
longer re-flagged because revision 2 happened to record an unrelated new screen.

**This subsection described a union when I first wrote it, and a union was only half the fix.**
The issue's `expected` asks for the union "minus any later revision that observed the screen and
found it not-broken"; I implemented the union, called the residual an honest cost ("a screen that
was broken, then fixed, then broke again is not re-reported") and moved on. The fresh review
live-reproduced it and was right to call it a regression, not a cost: a silently missed relapse is
worse than a stale alert for a regression-catching tool, and the subtraction was in the issue text
all along. `PersonaRevision.healthy_screens` now carries the observation and the replay subtracts
it. Full reasoning, the PP2/CR4 interaction and the contract clause it contradicts are in
"The fresh review's three findings" above and in **Q8**.

## Verify — each command run on its own, output pasted

### `uv run pytest` (no CLI `-q`, AT-503 — the failure LIST, not the exit code)

Run at `1be188d5`, the tree this manifest describes. Earlier runs during this cycle were **thrown
away and restarted**, not reported, each time an edit landed after collection — output that
describes a tree that no longer exists is not evidence.

```
=========================== short test summary info ===========================
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
3 failed, 2132 passed, 5 skipped, 14 xfailed, 15 warnings in 1544.99s (0:25:44)
```

**The failure list, judged one by one. Three red, and I claim none of them is mine — here is the
evidence for each rather than the assertion.**

- `test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail` — **known
  pre-existing red on master**, named in the build brief. Its message is
  `these done_checks pass on a clean repo whether or not their task was started, and carry no
  waiver: ['T-190', 'T-191']` — both are `.goal/goal.json` rows owned by the orchestrator and
  another live build. The brief forbids me touching `.goal/goal.json`; I did not.
- `test_goal_done_checks.py::test_revised_goal_contract_is_registered` — the second known
  pre-existing red, same file, same cause (`progress["total"] == len(data["tasks"]) == 70`).
- `test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`
  — **NOT on the known list, so I did not wave it through.** It is
  `FileNotFoundError: ...\\test_run_once_kills_a_real_hun0\\child.pid` — a real-subprocess timing
  test reading a pid file a child had not written yet. It touches no file this unit changes.
  **Re-run in isolation on the same tree: `2 passed in 10.98s`.** The full run overlapped a headed
  Chromium crawl, a ten-mutation falsification pass and other agents' work on the same machine, so
  a real-process race under load is the explanation I believe. It is still a flake report the
  checker is entitled to re-run, and if it reds again on a quiet machine it is a genuine (though
  unrelated) issue, not this unit's.

**Nothing in `tests/test_persona_changes.py`, `tests/test_persona_diff_pipeline.py`,
`tests/test_explore_replay.py`, `tests/test_explore_traversal.py`, `tests/test_portal_persona.py`
or `tests/test_explore_completeness.py` is red.**

### `uv run ruff check src tests scripts`

```
warning: `VIRTUAL_ENV=d:\autoTesting\.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
All checks passed!
```

### `uv run autotester doctor`

```
warning: `VIRTUAL_ENV=d:\autoTesting\.venv` does not match the project environment path `.venv` and will be ignored; use `--active` to target the active environment instead
doctor: clean
```

Doctor was **not** clean twice on the way here, both times a file over the 300-line cap, both fixed
by splitting rather than by deleting reasoning: `stages/portal_persona.py` hit 305 (trimmed a
docstring that duplicated what `PersonaScreen.ident`'s own docstring says), and
`tests/test_persona_changes.py` hit 345 — split into `tests/test_persona_diff_pipeline.py`, which
owns what the real `build_portal_persona` pipeline records, leaving `test_persona_changes.py`
owning `classify()` as a pure function. **That split widens the disclosed `done_check` gap: the
registered check names three test files, this unit now has five.** I did not edit `.goal/goal.json`.

## Real-browser evidence — headed Chromium (Mode D), local fixture only

Script `.work/t165_cycle2_evidence.py` (scratch, not committed); report
`qa/evidence/browser-t165-crawl-traversal-2026-09-27-cycle2/report.json` (committed). `headed=True`,
a `127.0.0.1` `http.server` over a copy of `tests/fixtures/deep_site`, under a real signed
`RunApproval` (`production=False`) — the D-018 gate exercised, never bypassed. No real product, no
traffic off the machine, nothing written to production.

**Re-run from scratch on `48238b4f`**, after the review fixes, not carried over from `96bacbbc` —
the persona schema gained a field and `PersonaIndex` changed between the two, so the earlier
report would have been evidence about a tree that no longer exists. Numbers below are the fresh
ones and are identical to the earlier run except the corrected `summary` label.

**The exact pair checker A reproduced the bug with, re-run with the fix in:**

| | crawl 1 (full) | crawl 2 (incremental, byte-identical site) |
|---|---|---|
| actions | 20 | **0** |
| screens | 9 | **1** |
| status | `completed` | `completed` |
| `stop_reason` | `frontier empty` | `frontier empty -- 1 screen(s) skipped as unchanged since the stored persona, and so NOT explored on this crawl` |
| `skipped_unchanged` | 0 | **1** |

Persona seeded from crawl 1 with 9 crawl-sourced keys. The revision crawl 2 writes:

```
summary: "screens 8 not judged (a bound or a skipped-unchanged screen left the crawl incomplete)"
missing:  0        missing_screens:  []
new: 0  changed: 0  broken: 0
missing_unjudged: ["/deep1.html","/deep2.html","/deep3.html","/deep4.html",
                   "/wide1.html","/wide2.html","/wide3.html","/wide4.html"]
```

**Cycle 1 produced `missing_screens` with those same 8 entries.** The report also records
`classify()` called directly on crawl 2's own graph with `frontier_exhausted=True` forced — the
shape checker A drove — and it too returns `missing_screens: []`, because the skip is read off the
nodes, not off the caller's flag. `explore_status.displayed_status` independently shows this crawl
as `BLOCKED_NO_ACTIONS`, not success (pre-existing, cycle 1).

## Capability coverage — every claim, its test, the STUB that breaks it, and the result

Method unchanged from cycle 1 and re-verified: `git archive HEAD` (not `tar`) into a throwaway copy
**outside** the bound worktree, so no stale `__pycache__` can bake an original path into a
traceback; each mutation a **single hunk** whose anchor is asserted to occur exactly once, applied
only after the named test is proven green in that copy, reverted immediately, green re-proven
after. Eight of the ten are a **stub to a constant** rather than a line revert, per the brief. The
copy was re-extracted from `48238b4f` and the whole set re-run after the review fixes, not topped
up — a row proven against an older tree proves nothing about this one.

| # | Claim (issue) | Covering test | Single-hunk falsifying edit | GREEN → RED → GREEN |
|---|---|---|---|---|
| 1 | **ISS-3: a skip may not license a `missing` claim** | `test_persona_diff_pipeline.py::test_a_real_incremental_recrawl_of_an_unchanged_site_reports_no_deletion` (two REAL crawls) | `_judged_exhausted` → `return True` (stub) | `1 passed in 61.71s` → `1 failed in 57.87s` → `1 passed in 57.48s` |
| 2 | ISS-1: X7 re-checks the host after a replayed action | `test_explore_replay.py::test_a_replay_that_lands_off_domain_is_refused_and_recorded` (both exits, parametrized) | `_landed_on_domain` → `return None` (stub) | `2 passed in 0.14s` → `2 failed in 0.31s` → `2 passed in 0.09s` |
| 3 | ISS-2 (diff half): every node reached at a key is classified | `test_persona_changes.py::test_a_second_screen_at_a_known_url_is_classified_not_silently_dropped` | `_reached` → `{k: v[:1] …}` (stub to first-wins) | `1 passed in 0.06s` → `1 failed in 0.29s` → `1 passed in 0.13s` |
| 4 | ISS-2 (storage half): `ident()` keeps two screens at one URL | `test_persona_diff_pipeline.py::test_two_distinct_screens_sharing_a_url_are_both_stored` | `ident` → `return (self.key(), None)` (stub) | `1 passed in 0.15s` → `1 failed in 0.36s` → `1 passed in 0.14s` |
| 5 | ISS-4: broken-ever replays the whole history | `test_persona_changes.py::test_a_screen_broken_across_an_unrelated_intervening_revision_is_not_re_reported` | `_previously_broken` → the cycle-1 nearest-revision reading | `1 passed in 0.10s` → `1 failed in 0.26s` → `1 passed in 0.07s` |
| 6 | **review-HIGH: a healed screen that relapses IS reported broken again** | `test_persona_changes.py::test_a_screen_that_healed_and_then_relapsed_is_reported_broken_again` | drop `broken.difference_update(revision.healthy_screens)` → `pass` (stub to the plain union, my first cycle-2 reading) | `1 passed in 0.07s` → `1 failed in 0.26s` → `1 passed in 0.07s` |
| 7 | review-HIGH: a SKIP is not an observation of health | `test_persona_changes.py::test_a_skipped_screen_is_not_an_observation_of_health` | the `SKIPPED_UNCHANGED` clause → `and True` (stub: a skip counts as a visit) | `1 passed in 0.08s` → `1 failed in 0.30s` → `1 passed in 0.07s` |
| 8 | **review-MEDIUM: `replay_fills` settles BEFORE the X7 check** | `test_explore_replay.py::test_a_refill_that_leaves_the_domain_is_caught_before_the_submit_is_clicked` | delete the `rt.session.settle(...)` line before `_landed_on_domain` | `1 passed in 0.08s` → `1 failed in 0.28s` → `1 passed in 0.09s` |
| 9 | review-MEDIUM: `PersonaIndex` sees every state stored at a key | `test_explore_traversal.py::test_the_persona_index_recognises_the_second_stored_state_at_one_url` | `_at_key` → `{k: v[:1] …}` (stub to first-wins) | `1 passed in 0.10s` → `1 failed in 0.26s` → `1 passed in 0.07s` |
| 10 | self-caught: the summary may not contradict the `stop_reason` | `test_persona_diff_pipeline.py::test_a_real_incremental_recrawl_of_an_unchanged_site_reports_no_deletion` (two REAL crawls) | the label → `"not judged (the frontier was not exhausted)"` (stub to my first wording) | `1 passed in 57.44s` → `1 failed in 57.57s` → `1 passed in 57.83s` |

`10 mutations, 0 problem(s)`. **Row 5 is the one exception to "stub to a constant":** stubbing
`_previously_broken` to `frozenset()` also reddens it, but it would only prove the function is
consulted, not that the replay is what fixed ISS-4. Restoring the exact cycle-1 reading is the
sharper falsification, so that is what row 5 does. Row 8 is the other: there is no constant to stub
to — the claim IS the ordering of two statements, so deleting the first one is the only edit that
tests it.

**One falsification was invalid on its first run and I am reporting it rather than the clean
re-run alone.** M10's replacement carried a trailing `# STUB` comment, which commented out the
closing `),` of the tuple it sat in, so the "RED" was a `SyntaxError` in 0.29s — a test that never
ran, not a falsified claim. A red result is not evidence unless the code still *compiles*; the
0.29s against a 57s baseline is what gave it away. Re-run without the comment: RED in **57.57s**,
i.e. the two real crawls ran and the assertion is what failed. Rows 1-9 were checked for the same
defect; none of them replaces a line inside an open bracket.

The bound worktree was verified intact afterwards: `git status --short` empty, no source file
touched by the mutation pass.

Every row from **cycle 1's own table is untouched** — no cycle-1 test was weakened, deleted or
re-scoped. Two cycle-1 tests changed shape and both are strengthenings, stated because "I only
touched the fixture" is what a weakening looks like from the outside:
`test_explore_replay.py`'s `_FakeRuntime` gained `project`, `nodes`, a store and a `current_url()`
(the replay path now reads them; a fake that could not answer "where did that land?" is precisely
why the X7 gap survived a cycle), and `test_persona_changes.py` was split, not trimmed — every
assertion in it still runs, in one file or the other.

**The review fixes changed three more existing tests, and each one is an addition, not a
relaxation. Listed individually because a weakened test is exactly what this list would hide:**

- `test_explore_replay.py::_RecordingSession` now models navigation asynchronously. This is
  strictly harder to pass: `current_url()` no longer reveals the new URL until `settle()` runs, so
  a check placed before a settle now fails where it used to pass for free. All eleven tests in the
  file pass unchanged otherwise, and falsification M8 exists only because of it.
- `test_a_skipped_screen_is_evidence_of_nothing` asserts an **exhaustive dict literal**, so the new
  `healthy_screens` key had to be added to it. It is added as `[]` — i.e. the assertion now also
  states that a skip yields no observation of health, which is one more claim, not one fewer.
- `test_classify_returns_exactly_the_revisions_own_field_names` gained three assertions
  (`CATEGORIES` is still exactly five, `CATEGORIES` and `PROVENANCE` are disjoint, and `counts()`
  still counts exactly the five). Its original assertion is intact, widened only to
  `CATEGORIES | PROVENANCE`. Without the three additions that widening WOULD be a weakening, which
  is why they are there.

## What the checkers should attack hardest — written before either of you runs

Cycle 1's version of this section named two of the four defects before the checkers found them,
which is the most useful thing that manifest did. Here is the ruthless version.

1. **ISS-3's fix is at the CLAIM, not at the TRAVERSAL, and that is the attack surface.** The crawl
   still ends with a 1-node graph on a 9-screen site; what changed is that it no longer says
   screens are gone. Ask whether that is enough: a checker who reads D-040 as requiring the
   frontier to *represent* every known screen should fail this and say so, and Q5 in
   `qa/feedback-inbox.md` is where I argued the other way. Concretely: is a `completed` crawl that
   looked at one screen of nine acceptable because `stop_reason`, `displayed_status`,
   `skipped_unchanged` and coverage all disclose it — or is `COMPLETED` itself the lie?
2. **The capability limit I could not fix (Q6).** With the subtree pruned, an incremental crawl
   cannot see a change BELOW a skipped screen. Change only `deep_site/deep3.html` between two
   crawls and the second one skips `/`, reports `/deep3.html` as `missing_unjudged`, and the edit
   goes unnoticed. CR3's own acceptance test only covers all-changed and none-changed, so nothing
   in the contract catches this — which means it is exactly the shape that ships. I wrote no test
   asserting the *good* behaviour here because there is none to assert; attack whether that is a
   disclosed limit or a CR3 failure.
3. **`_judged_exhausted` is all-or-nothing and I know it is coarse.** ANY skip makes EVERY
   unreached key unjudged, including keys the crawl genuinely explored past and found gone. So a
   crawl that skips one screen and fully explores the rest can no longer report a real deletion
   anywhere. That is the safe direction, but it means CR4's `missing` is now unreachable on any
   incremental crawl at all. Try to construct the case where that hides a genuine deletion a user
   needed to see.
4. **ISS-2 changed a MERGE key on stored data, and I MEASURED the cost — it is real.** `_merge`
   dedupes on `ident()` now, so a screen whose structure changes on every crawl (a DOM timestamp, a
   rotating banner) appends a `PersonaScreen` every single run. Measured, five crawls of one URL
   with a rotating signature: stored screens `1, 2, 3, 4, 5`, one revision each, `changed=['/']`
   every time from crawl 2 on. **Before this change the same input gave 1 stored screen and the
   same `changed` every crawl** — so the new cost is persona GROWTH, not new noise. PP2 forbids
   pruning it, and nothing caps it. I judged the alternative worse (a screen you never learn about
   beats a screen you learn about twice) but this is a real regression against an unstable DOM and
   is filed as Q7. Attack it: decide whether an unbounded persona is acceptable, and whether
   `screen_identity.structural_signature`'s `in_row` exclusion is enough to keep signatures stable
   on a real product. Also check the FlowSpec-overlap behaviour change I disclosed above against
   `qa/contracts/portal-persona.md` PP1-PP6 — I read them, I believe it is add-only and legal, and
   it is still a change to what a human sees in `knowledge.md`.
5. **`changed` fires if ANY reached node at a key carries an unknown signature — I checked the
   obvious worry and it is NOT there.** A stable two-state key does not read `changed` forever:
   measured over three crawls of a `/` with signatures `{sig-base, sig-panel}`, the persona stays
   at 2 screens, writes ONE revision in total, and reports `changed` only on the crawl that first
   saw the second state. Attack it from a direction I did not: three states where one disappears,
   or a state that alternates between crawls.
6. **The X7 replay check calls `current_url()` after every fill.** On a form with many fields that
   is N extra CDP round-trips per replay. I did not measure it. If `return_to` gets slower in a
   real crawl, this is where it went.
7. **Re-run the cycle-1 mutation set, not just mine.** Cycle 1's lesson was that the gap was in the
   coverage table's *scope*, not its rigour — eleven claims, ten rows. Assume the same is true of
   this table. The claims I did not write a row for: that `_refusal_of` records against the right
   element (`_element_for`'s fallback `ElementRef(role="")` is untested), that the union in
   `_previously_broken` is bounded when history is long, and that `test_a_skipped_screen_is_evidence_of_nothing`
   still means what it says now that a skip changes `_judged_exhausted`.

8. **My own attack item 7 predicted this, so treat it as measured rather than as a lucky catch:
   a fresh review found three defects and two were in the cycle-2 fixes.** Item 7 said "assume the
   same is true of this table" — it was, and the table was not what failed; *scope* was, again.
   Specifically: the coverage table had a row proving `_previously_broken` unions the history, and
   the union was **half of what the issue asked for**. A green row proves the test is coupled to the
   line; it proves nothing about whether the line is the right line. So: for each of my ten rows,
   read the issue's `expected` field in `qa/issues.jsonl` next to the row and check the row covers
   the *whole* sentence, not the clause I found easiest to test. That is the mutation the driver
   cannot generate.
9. **`healthy_screens` is a schema addition I made without a contract amendment, and it is the
   single most likely thing to fail this cycle.** It is defaulted, excluded from `counts()`, held in
   `PROVENANCE` not `CATEGORIES`, and guarded by a test that asserts all of that — but `CR4` says a
   `PersonaRevision` "records the counts of all five categories", and I added a sixth *field* while
   arguing it is not a sixth *category*. If you think that distinction does not survive contact with
   `extra="forbid"` and PP2, fail it and rule on Q8; the alternative I would then implement is
   accepting that a relapse is never re-reported, and saying so in the docstring. Also attack the
   direction I chose: I decided a silent missed relapse is worse than a noisy stale alert. That is a
   product judgement, not a contract clause.
10. **The review's open question is the best unresolved thing here and I could not settle it.**
    `missing` and `changed` still work at `key()` granularity. Two states at one URL, one genuinely
    deleted and the other alive: the deletion appears in **no** category — not `missing`, not
    `missing_unjudged`, not `changed`. The ISS-2 fix made that shape *storable* without making it
    *diffable*. I believe it is an acceptable incremental cut and I wrote no test claiming
    otherwise, but there is no contract sentence or test either way, so it is yours to rule on.
11. **A guard I wrote could not fail, and the fake is why.** `replay_fills` checked the host with no
    `settle()` in front of it and every test passed, because `_RecordingSession.current_url()`
    returned a constant. The fake now models navigation asynchronously and the missing settle
    reddens (M8). Assume the same disease elsewhere: go through every fake in
    `tests/test_explore_replay.py` and ask what it *cannot* be wrong about. `_Secrets.scrub_optional`
    and `_CountingStore` are both still constants in exactly that way.
12. **`healthy_screens` depends on a revision being WRITTEN, and I probed it rather than
    asserting it.** `build_portal_persona` only appends a `PersonaRevision` when the summary is
    non-empty, so a recovery on an otherwise-silent crawl could be dropped and the relapse fix
    would regress to the plain union. `describe()`'s new "recovered" label is what closes it.
    **Measured** end-to-end through the real `build_portal_persona` in the throwaway copy, with a
    persona whose only news is that `/a` recovered: `revisions: 2`, `summary: 'screens 1
    recovered'`, `healthy_screens: ['/a']`, and the subsequent relapse gives `broken_screens:
    ['/a']`. **That is one case, not a proof, and it is a probe, not a committed test** — the
    committed relapse test drives `classify` directly and constructs the healing revision by hand,
    so the *plumbing* between `classify` and the stored revision has no covering test. Attack it:
    find a crawl that observes a recovery and writes no revision.

## Contract questions filed, not guessed

Q4 (`missing_unjudged` now covers a skip, not only a bound), Q5 (why check A's frontier-seeding
fix was not taken, and that it is a contract call), Q6 (the change-below-a-skip capability limit),
Q7 (the measured persona growth the ISS-2 merge-key change costs against an unstable signature),
**Q8** (CR4's "prior state" clause and ISS-4's `expected` now contradict each other — the clause
needs a superseding amendment, and `healthy_screens` needs ratifying as provenance, not a sixth
category) and **Q9** (the two defects the cycle-1 dual check did not find: `PersonaIndex`'s
first-wins map and the missing `settle()` — both deserve filed issues so the ledger is honest that
they existed) are all in `qa/feedback-inbox.md`, 2026-09-27, verbatim with the reading I took. I did not edit
`qa/contracts/crawl-traversal.md`; it stays checker-owned and DRAFT.

## Status: checked-PASS (cycle 2 of max 3)

**Closed out by:** the maker orchestrator, 2026-09-27, on two independent verdicts, not on its own
reading. `qa/verdicts/t165-crawl-traversal.md` carries **CHECK B — cycle 2** (`2d6edecc`, line 363)
and **CHECK A — cycle 2** (`f3085ecc`, line 747), each **PASS**, each derived in a fresh context
without reading the other. Merged to `master` as a `--no-ff` merge; the merge is the orchestrator's
and neither checker performed it, as both were instructed. `qa/contracts/crawl-traversal.md` went
**DRAFT → ACTIVE**, flipped by check A after confirming B's section was already on disk — neither
check flipped it alone.

### What the two cycles actually bought, in order

Cycle 1 failed on four defects. Cycle 2 fixed all four, **then found three more of its own** — two
self-introduced while fixing the four — because the build dispatched a fresh review of its own diff
instead of handing back at green. The worst of the three was self-inflicted and would have defeated
the feature's purpose: only half of ISS-4 had been implemented, so a screen that broke, healed, and
then genuinely relapsed reported `broken_screens: []` silently and forever. A missed relapse in a
regression-catching tool is worse than a stale alert. **Finding your own defects is the outcome; the
cycle that found the most was the best cycle.** Both checkers independently confirmed the fix, and
check A filed `-a7` against it *even though the defect existed for one commit only* — because the
coverage table had carried a **green row** for it while the union was half of what the issue asked.

### Rulings that closed the open questions (checker-owned; recorded here, not decided here)

| Q | Ruling | Who, and on what evidence |
|---|---|---|
| Q5 — is fixing ISS-3 at the *claim* rather than the traversal compliance or relabelled silence? | **RATIFIED.** `PersonaScreen.url_template` is a *template*, so seeding the frontier means `goto`-ing a destination never observed — X1/X7 forbid exactly that; and `PersonaTransition` holds `from_screen`/`to_screen` as **names**, not ids or signatures, so prior transitions cannot re-materialise a `ScreenNode`. **Both closures the contract previously offered are withdrawn as unimplementable.** | Check A, verifying both reasons rather than accepting the maker's word. Check B recorded the same position independently without voting on another checker's surface. |
| The all-or-nothing predicate — does it make CR4's `missing` permanently unreachable (the AT-100/Goodhart shape)? | **RATIFIED, and NOT that shape.** Check A tested the premise of its own brief and it did not hold: `missing` *does* fire on a full, non-incremental crawl — the mode in which a deletion claim is honest — and when suppressed the fact is **disclosed, never dropped** (`missing_unjudged`, with the cause in `stop_reason` and `describe()`). **The coarseness costs precision, never honesty.** | Check A, on a constructed crawl that skips one screen *and* fully explores a subtree containing a real deletion. |
| Q7 — unbounded persona growth | **ACCEPTED**, named in the contract with the measurement (5 crawls → 5 screens, revisions 1..5, which was already true before the change, so "growth, not new noise" is accurate). A state that *alternates* between crawls gives `changed=[]` — no churn. Option (b), one entry per key carrying a signature set, recorded as the preferred PP2-compatible closure. | Check A, closing the direction the maker asserted but did not test. |
| Q8(a) — CR4's "broken's prior state" clause | **SUPERSEDED.** The clause prescribed *exactly* the implementation ISS-4 was filed against — the same checker wrote both, and **the clause was the error.** The ruling is now the issue's own `expected`: full in-order history replay with `healthy_screens` subtracting. | Check A and check B, concurring separately. |
| Q8(b) — `healthy_screens` as a sixth *field* rather than a sixth *category* | **RATIFIED as provenance.** Asserted at runtime, not from the docstring: `CATEGORIES` is exactly 5, `counts()` returns exactly those 5 keys, `PROVENANCE` is disjoint, every list field is accounted for by the union with no orphan, and a pre-T-165 raw persona loads with `healthy_screens == []`. | Both checks. |

### The residual Umesh may want to overrule

**Two states at one URL, where one is genuinely deleted, is reported nowhere.** Check A reproduced it
and found it **worse than the manifest disclosed**: on a full, exhausted, non-incremental crawl every
category comes back empty *and* `describe()` returns `None`, so `build_portal_persona`'s `if summary:`
gate never fires and **no `PersonaRevision` is written at all** — nothing reaches `knowledge.md`. It
generalises to n states. Control: deleting a screen with its own URL still yields
`missing_screens == ['/other.html']`, so the machinery is otherwise sound.

Passed anyway, as a disclosed residual (`ISS-t165-crawl-traversal-a8`, open), for three reasons worth
keeping:

1. **Not a regression — strictly narrower than the gap it replaces.** Before this unit, storage
   deduped on `key()`, so the second state was never stored and was invisible in *every* direction.
   This unit is what narrowed it.
2. The maker took the closure **CR4's own gap note offered**. The inadequacy was in the note, which
   was the checker's to write and is now corrected.
3. **The naive closure is a trap, and this ruling is what decided it.** "A key whose reached
   signatures are a strict subset of its stored ones lost a state" fires identically on a state the
   crawl simply did not reach this run — typing off under X10-b, a toggle not clicked. The stored
   evidence cannot distinguish that from a removal, so the closure would replace the silence with a
   **fabricated deletion on every crawl of every two-state screen.** A sound closure needs
   per-signature *reachability*, not presence. The analysis is written into the contract and the
   issue's `expected` so a future unit cannot take it blind.

Check A raised no HUMAN_GATE and said plainly why: if Umesh would rather have this loud and imprecise
than silent and precise, that is a product call that overrides a checker's. **Recorded here as the
one thing in this unit worth a human's eye.**

### Falsification integrity — the reason cycle 2 is trustworthy

Cycle 2 self-reported that **one of its own ten falsifications was invalid**: M10's stub commented out
a closing bracket, so the "RED" was a `SyntaxError` in 0.29s against a 57s baseline. It re-ran it
clean at 57.57s. Both checkers then hunted the same defect in the other rows:

- **Check A reproduced 9 of 10 itself** in a `git archive` throwaway copy outside the worktree, and
  for each one asserted the mutated file `ast.parse`s, that the RED is an `AssertionError` (not a
  collection/import/syntax error), and that it re-greens. **All nine valid.** Only one anchor sits
  inside an open bracket at all — M7 — and it parses and reds correctly.
- **Check B timed the two expensive rows** where the fast-RED tell could hide again: **RED at 59.20s
  and 58.34s against a 64.89s green** — real Chromium crawls ran and the *assertion* failed.
- **Check B found the coverage table UNDERSTATES itself.** It deleted `settle()` at each of the three
  `explore_replay` call sites independently; all three redden, and the missing-settle defect is not
  hiding in the click path. The maker claimed less than it had.
- **One row is weaker than its claim** (check A, observation not defect): stubbing `_reached` to
  *last-wins* leaves M3's test green. It reddens on the actual ISS-2 defect (first-wins), so the code
  is right — but the row proves "the last node survives", not "every node does".

**The generalised lesson, now twice-confirmed on this project: a RED that is a syntax, import or
collection error proves nothing, and the tell is a suspiciously fast RED.** Compare every RED's
wall-clock against its GREEN baseline. This is the same family as the exit-code-masking trap — both
are cases of reading a signal that was never measuring what it appeared to measure.

### A new reporting hazard, found by check A and worth the whole project's attention

Check A's captured `uv run pytest` log contains the warnings summary and the final tally **twice**,
interleaved from two streams — and the *earlier* copy reads `2135 passed, 6 skipped, 14 xfailed` with
**no failure line at all**. Both describe the same run (2134 + 1 = 2135). **A checker grepping the
first `passed` line would have reported a clean suite.** Anyone reading a captured pytest log in this
repo must take the **last** summary block and the explicit exit code. This is the fifth distinct way
this project has found to mislead itself about a test result.

### Verify (each checker's own runs, not the maker's)

- Check A: `1 failed, 2134 passed, 6 skipped, 14 xfailed in 1534.99s` · ruff clean · doctor clean.
- Check B: `1 failed, 2134 passed, 6 skipped, 14 xfailed in 1534.99s` · ruff clean · doctor clean.
- The single red in both is **AT-627**, the known load-sensitive flake, which ran alongside two real
  Chromium falsification crawls and a Mode D walk. Isolated on the same tree: `2 passed in 11.13s`
  (check A) and `2 passed in 14.22s` (check B).
- **The two `test_goal_done_checks.py` reds the cycle-2 manifest reported are gone** — master's fix
  arrived with the `bdac746a` merge and the maker measured before it. Not a finding; the manifest's
  own numbers were stale rather than wrong.

### Mode D — check A's own headed walk, reproducing the maker's numbers

crawl 1: `completed`, 20 actions, 9 screens, 0 skipped, `displayed_status completed`. crawl 2:
`completed`, 0 actions, 1 screen, `skipped_unchanged 1`, `displayed_status blocked_no_actions`.
Revision: `missing 0`, `missing_unjudged 8`. Forcing `frontier_exhausted=True` on crawl 2's own graph
*also* gives `missing []` — the skip is read off the nodes, not the caller's flag. PP2 preserved.
**Cycle 1 gave `missing 8` on this exact pair.** That difference is the unit.

### Carried forward, not silently dropped

- `ISS-t165-crawl-traversal-a8` (open) — the deletion silence above.
- `AT-650` (medium, open, **not chargeable to T-165**; both files byte-unchanged on this branch) —
  `typing_target_allowed`'s docstring promises "never a password/credential field", but
  `enumerate.js::roleOf` maps **every** non-submit/checkbox/radio `<input>` (including
  `type="password"` and `type="file"`) to role `"textbox"`, and `enumerate.js` **computes `type`
  without emitting it**, so `ElementRef` has no `type` and the gate structurally cannot see it. Check
  B probed it: a recorded `#pin`/"PIN" target gets a 4-digit number typed into it. **It also corrects
  cycle-1 check B's own claim** that the gate excludes password-labelled fields from ever being
  recorded — true only for names containing the literal string "password". A guard reading labels
  cannot enforce a promise about types.
- **`PersonaRevision.counts()` has no caller in `src/` at all** (`grep -rn "\.counts()" src/` empty)
  — only tests and the future T-168. Not a CR4 violation, but the five-category surface is currently
  asserted only by tests. `missing_unjudged` likewise has no rendering surface; the only path to a
  human is `describe()`'s sentence via `portal_persona_view._history_section`. **Worth knowing before
  T-168 renders either.**
- **`extra="forbid"` cuts forward too:** a persona written by this build cannot be loaded by a
  pre-T-165 build. A class-level rollback hazard (already true of `missing_unjudged`), now disclosed
  in the contract.
- `ISS-t165-crawl-traversal-1`…`-4` closed as **verified** by check A, byte-preservingly, once both
  verdicts were on disk. The ten documented `id_collision` rows untouched; ledger re-validated at 671
  valid JSONL rows. Check A prefixed its four new rows `-a5`…`-a8` specifically so they could not
  collide with anything check B filed concurrently — the correct reflex on a dual check, and the
  thing whose absence created the ten collisions already on record.
- `.gitattributes` still lacks `qa/issues.jsonl merge=union`. Cycle-1 check B predicted the conflict;
  cycle 2 then paid for it with a hand-resolved merge. **Maker action, queued.**
- One manifest provenance line cites `displayed_status → BLOCKED_NO_ACTIONS` against a `report.json`
  that has no such field. Check B established **the claim is true** (`blocked_no_actions`, plus
  `skip_note`) by re-reading the file rather than trusting the quotation — so the fix is the
  provenance, not the claim. **Queued.**
- One-test debt named by check B: no committed test drives `classify → describe → PersonaRevision`
  end to end for recovery, so if `describe()`'s `"recovered"` label is ever reworded the ISS-4 fix
  silently regresses to the plain union **with nothing going red**. Check B drove it live through the
  real store instead of ruling on it, which is why this is debt and not a defect.
