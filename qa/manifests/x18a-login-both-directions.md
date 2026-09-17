# Manifest — x18a-login-both-directions

**Unit:** X18(a) is honest in both directions (AT-467, AT-474): a wrong password that leaves a
sticky error banner must still read LOGIN_FAILED, and a login page that cannot be observed must
never read as an unqualified success.
**Contract:** `qa/contracts/explore.md` X18(a) (proposed tightening below, for the checker to
fold before/at check time) · `qa/contracts/core-invariants.md` C1, C2, C7
**Goal task:** none (issue-driven, QUEUE.md unit 3)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-467 (medium), AT-474 (high)

## Proposed X18(a) wording (for the checker to adopt or amend)

> A reached node counts as "still the login screen" when its `url_template` equals the login
> case's own template AND EITHER its `signature` equals the signature OBSERVED on the login page
> before the case typed, OR — when that comparison cannot decide, because the signature moved (a
> sticky wrong-password banner, AT-467) or was never observed at all (AT-474) — every FILL step
> target of the login case is still present as an element's `selector` on that node. A FILL target
> absent from the node's elements leaves the signature-only rule in force, so a genuinely
> different screen that merely shares the login's url (AT-462's single-page-app dashboard) is
> never caught by this fallback. When the login page's signature could not be observed AND X18(a)
> still could not be judged by either mechanism, the crawl's `stop_reason` carries a qualifier
> naming why ("-- login not judged: could not observe the login page (`<Type>: <msg>`)") and an
> `IssueKind.EVIDENCE` `CrawlIssue` is filed (so `tool_failures` counts it) — never a crash, never
> a silent, unqualified COMPLETED.

## Why this shape

**AT-467.** The old rule compared `(url_template, signature)` only. A wrong-password page that
redisplays the form plus a persistent, *interactive* extra control (a "Dismiss" button on an
error banner) changes the structural signature — `enumerate.js` only tracks interactive elements,
so a static `<p>` error message never moved it, but a `<button>` does. Signature-only comparison
then reads the wall as a *different* screen and the crawl completes. The fallback asks a narrower,
safer question: is the login FORM still there? — using the exact selectors the login case itself
types into, which are already known and already trusted (X10: nothing else types). "Every FILL
target must appear" (not "any") keeps AT-462's single-page-app dashboard (no `#email`/`#password`
at all) out of the fallback's reach — verified as its own control row/test.

**AT-474.** `observed_signature` already swallowed every exception into `None` (never a crash,
by design). The defect was that the skip was invisible: no field, no log, no issue. The fix keeps
the "never crash" contract and adds exactly two things: (i) the fallback above still judges when
the signature is `None` (a `None` signature can never equal a node's, so the fallback is the only
path that can still say LOGIN_FAILED); (ii) when even the fallback cannot decide (its target
selectors aren't on the reached node either, or the case has no FILL step), the final `stop_reason`
gets an appended qualifier and an EVIDENCE issue is filed. The status itself is left alone
(COMPLETED / STOPPED_BOUND / BLOCKED_NO_ACTIONS as before) — the crawl's own further evidence
(other screens reached, actions taken) is real and not overridden; what changes is that "we could
not confirm X18(a) itself ran soundly" is now on record rather than silent. Chosen over inventing
a new `CrawlStatus` member because every surface X16 already lists renders `stop_reason` beside the
status (crawl page, crawls table, CLI line, workbook Summary), so the qualifier reaches every one
of them for free, and no enum/schema change is needed.

## What changed

- `src/autotester/stages/explore_status.py:50-56` — `observed_signature` now returns
  `tuple[str | None, str | None]` (signature, error) instead of swallowing the exception into a
  bare `None`.
- `src/autotester/stages/explore_status.py:60-63` (new) — `login_fill_targets(case)`: the set of
  every `Action.FILL` step's `target` in the login case's steps.
- `src/autotester/stages/explore_status.py:65-99` — `never_left_login` rewritten around a local
  `_still_login(node)` predicate implementing the OR above (signature match, or fill-target
  subset match); same public signature, same return contract.
- `src/autotester/stages/explore_status.py:102-131` — `terminal_status` gains two optional
  kwargs, `login_observe_error` and `current_stop_reason`; the BLOCKED_NO_ACTIONS suffix logic
  (previously in `explore.py`) moved here alongside the new not-judged qualifier, so both compose
  correctly instead of one silently overwriting the other.
- `src/autotester/stages/explore_node.py:34-39` (new) — `record_login_observe_failure(rt, error)`:
  files an `IssueKind.EVIDENCE` `CrawlIssue` (node_id="" — no node exists yet at the login
  precheck) when `error is not None`, so `tool_failures` counts it (X16's crawler-failure-not-a-
  product-bug rule).
- `src/autotester/stages/explore.py` — `ExploreRuntime` gains `login_observe_error: str | None`;
  `_already_past_login` (~line 124) unpacks `observed_signature`'s new tuple and calls
  `explore_node.record_login_observe_failure`; `_terminal_status` (~line 199) passes the new
  kwargs through and no longer duplicates the BLOCKED_NO_ACTIONS suffix. Net **+0 lines** (300 →
  300; a trimmed blank line in `_already_past_login`'s docstring paid for the new field +
  precheck call, and moving the suffix logic into `explore_status.py` paid for the new kwargs).
- `tests/test_explore_login_wall.py` — `ElementRef` import, `_LOGIN_FIELDS`, `_node()` gains an
  `elements` param, and four new tests (below). 300 → 300 lines (trimmed two existing docstrings
  to fit the cap — no test deleted or weakened).
- `tests/fixtures/spa_login_site/index.html` — `?sticky=1`: a wrong password now leaves a
  persistent error banner **plus a `<button id="dismiss">`** (the old `<p id="error" hidden>` was
  never interactive, so it never moved the signature — that is *why* the live fixture needed a
  real control, not just an unhide). `sessionStorage` (not a JS variable) carries the "last
  attempt failed" flag across the full page reload `run_crawl`'s re-seed causes.
- `tests/test_explore_login_spa_live.py` — `_crawl()` gains a `sticky: bool = False` kwarg; one
  new live test. 87 → 98 lines.

## How to verify (commands + expected)

- `uv run pytest tests/test_explore_login_wall.py tests/test_explore_login_spa_live.py tests/test_crawl_status_surfaces.py tests/test_explore.py tests/test_explore_bounds_last_node.py tests/test_ui_crawl_login.py -p no:cacheprovider -o addopts= -q` → all pass
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- Full suite `uv run pytest -p no:cacheprovider -o addopts= -q -rx --deselect tests/test_crawl_inventory_live.py` → ~1413 passed + this unit's new tests, 32 xfailed

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_explore_login_wall.py tests/test_explore_login_spa_live.py tests/test_crawl_status_surfaces.py tests/test_explore.py tests/test_explore_bounds_last_node.py tests/test_ui_crawl_login.py -p no:cacheprovider -o addopts= -q
.............................................................            [100%]
61 passed, 1 warning in 54.19s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest -p no:cacheprovider -o addopts= -q -rx --deselect tests/test_crawl_inventory_live.py
1 failed, 1420 passed, 2 skipped, 2 deselected, 32 xfailed, 1 warning in 561.80s (0:09:21)
  FAILED tests/test_mutation_check.py — scripts/mutation_check.py:279 MutationError:
  "baseline is NOT green (pytest exit 4294967295)" — a subprocess-level exit code, not a
  test assertion. Re-run in isolation immediately after:
$ uv run pytest tests/test_mutation_check.py -p no:cacheprovider -o addopts= -q
...................                                                      [100%]
19 passed in 111.69s (0:01:51)
```

Clean in isolation, in a module this unit never touched (`scripts/mutation_check.py`,
`tests/test_mutation_check.py` — my changed files are all in `src/autotester/stages/` and the
explorer test files). Read as an environmental flake under the full 9-minute run's resource
pressure (same failure direction the contract already documents for a busy machine — C7's
amendment log, AT-196: a false FAIL, never a false PASS, so no verdict rests on it). Not
attributed to this unit's diff.

**Red before the fix** — the two new tests targeting AT-467/AT-474 were run against the
unmodified (pre-fix) `explore.py`/`explore_status.py`/`explore_node.py` (temporarily restored via
a tagged `git stash`, then re-applied — never a bare `git stash`/`pop`, per the shared-worktree
rule), the other 14 tests in the same file staying green as controls:

```
$ uv run pytest tests/test_explore_login_wall.py -p no:cacheprovider -o addopts= -q
.........F...F..                                                         [100%]
FAILED tests/test_explore_login_wall.py::test_a_sticky_wrong_password_banner_is_still_login_failed
  AssertionError: assert <CrawlStatus.COMPLETED: 'completed'> is <CrawlStatus.LOGIN_FAILED: 'login_failed'>
FAILED tests/test_explore_login_wall.py::test_a_login_page_that_cannot_be_observed_is_not_an_unqualified_success
  AssertionError: assert 'login not judged' in 'frontier empty'
2 failed, 14 passed in 0.94s
```

## Capability coverage (each new claim -> its isolating falsification)

Throwaway copy built OUTSIDE the repo: `git archive HEAD | tar -x` into the scratchpad, this
cycle's uncommitted files (`explore.py`, `explore_node.py`, `explore_status.py`, the fixture, and
both test files) copied on top and diffed byte-identical against the live tree, `projects/erp`,
`projects/pathlynks`, `projects/vidysea-erp` removed, `uv sync` run, and
`uv run python -c "import autotester; print(autotester.__file__)"` confirmed it resolves inside
the copy (`...\scratchpad\x18a-capcov\src\autotester\__init__.py`). Every falsifying edit below
was applied with a Python anchor-count assertion (`== 1`), run, and the file restored — confirmed
byte-identical to the live tree after each restore — before the next row.

| capability | check | falsifying edit (single hunk) | observed |
|---|---|---|---|
| a wrong-password page with a persistent extra control (changed signature) is still caught via its login-form fields (AT-467) | `test_a_sticky_wrong_password_banner_is_still_login_failed` | `explore_status.py`: `return bool(fill_targets) and fill_targets <= selectors` → `return False` | PASS before: `1 passed in 0.44s`. FAIL after: `assert <CrawlStatus.COMPLETED: 'completed'> is <CrawlStatus.LOGIN_FAILED: 'login_failed'>` |
| a login page that could not be observed at all still gets a named, visible qualifier + an EVIDENCE issue, never a silent unqualified status (AT-474) | `test_a_login_page_that_cannot_be_observed_is_not_an_unqualified_success` | `explore_status.py`: `if login_case is not None and login_observe_error is not None:  # AT-474` → `if False:  # SABOTAGE row2` | PASS before: `1 passed in 0.21s`. FAIL after: `assert 'login not judged' in 'frontier empty'` |
| the fallback never over-fires: a genuinely different screen sharing the login's url with none of the login case's fields present stays COMPLETED (AT-462 control) | `test_a_dashboard_sharing_the_login_url_without_login_fields_is_not_login_failed` | `explore_status.py`: `return bool(fill_targets) and fill_targets <= selectors` → `return bool(fill_targets) and bool(selectors)` (any elements at all, ignoring which ones) | PASS before: `1 passed in 0.15s`. FAIL after: `assert <CrawlStatus.LOGIN_FAILED: 'login_failed'> is <CrawlStatus.COMPLETED: 'completed'>` |

Each row's edit was applied to `src/autotester/stages/explore_status.py`, named in "What changed"
above, and reverses to byte-identical content (diffed) before the next row's edit. The
partial-fill-target control (`test_a_partial_fill_target_match_falls_back_to_signature_only`) and
the live-browser sticky test are additional regression coverage not separately falsified here —
they exercise the same `_still_login` predicate the three rows above already isolate line-by-line
(the `bool(fill_targets) and fill_targets <= selectors` expression's two clauses).

## Live browser evidence

**This unit changes crawl status shown on the crawl page/crawls table/report (X16/X18).**

- **Real-browser regression (maker, headless Chromium, local fixture only):**
  `uv run pytest tests/test_explore_login_spa_live.py -p no:cacheprovider -o addopts= -q` → all 3
  pass, including the new `test_a_wrong_password_with_a_sticky_error_banner_is_still_login_failed`
  against `tests/fixtures/spa_login_site/index.html?sticky=1` — a real DOM whose wrong-password
  state genuinely changes structurally (a real `<button id="dismiss">` renders), not merely a
  scripted fake. This exercises `run_crawl` end-to-end against a live page.
- **UI drive (crawl page / crawls table / report): Maker smoke — not run.** Driving the actual
  product UI (spinning up the app, a synthetic project, a login case, a crawl approval, and
  reading the crawl page/crawls table) is out of scope for this cycle — the `playwright` MCP
  browser tool was unavailable this session (connection failure), and the fixture-level real
  browser test above already proves the underlying status computation against a real DOM.
  **Suggested for the checker's Mode D:** serve `tests/fixtures/spa_login_site?sticky=1` locally
  on `127.0.0.1`, run the UI from an isolated extract, seed a synthetic project + login case +
  crawl approval, submit a wrong password, and confirm the crawl page shows a non-success
  `login_failed` tone (never green) — local fixtures only, no live target.

## Known limits (disclosed, not claimed)

- **The not-judged qualifier is intentionally conservative.** It fires whenever the login
  precheck's own `observe()` failed and X18(a) did not positively resolve to LOGIN_FAILED — even
  if the crawl later reaches many genuinely different, successfully-authenticated screens. This
  trades a rare extra qualifier on an otherwise-clean success against ever silently hiding a
  precheck failure; narrowing it further (e.g. only when every reached node shares the login's
  url_template) is a smaller, defensible alternative the checker may prefer — flagged here rather
  than decided unilaterally.
- **The fallback is selector-exact.** A login form whose field selectors change between renders
  (e.g. a regenerated non-stable id) would not match even though the form is "the same" to a
  human. `enumerate.js`'s `selectorFor` already prefers stable ids/aria-labels/data-testid over
  generated ones, so this is the same stability guarantee X3's screen identity already relies on,
  not a new assumption.
- **AT-467's contract wording above is a proposal, not yet adopted.** Per the maker/checker
  split, the checker either folds it into `explore.md` X18(a) verbatim, amends it, or asks a
  question before this unit can close — flagged in "Proposed X18(a) wording" rather than assumed.

## Status: checked-PASS (qa/verdicts/x18a-login-both-directions.md, cycle 1, commit 1d2f817; X18(a) wording adopted with two corrections; checker filed ISS-x18a-1 (medium): the fill-target fallback can call a post-login screen that reuses the login selectors LOGIN_FAILED)
