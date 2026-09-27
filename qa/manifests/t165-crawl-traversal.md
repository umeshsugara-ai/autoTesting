# t165-crawl-traversal

**Unit:** T-165 — crawl traversal: hybrid strategy · form-input replay · incremental crawl · change tracking
**Criticality:** CRITICAL (dual check, D-040)
**Fix cycle:** 1
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

**Status: ready-for-check**
