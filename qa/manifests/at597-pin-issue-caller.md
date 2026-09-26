# Manifest — at597-pin-issue-caller

**Unit:** a human-facing path to pin a confirmed issue as a regression case (AT-597).
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-597

## The gap (AT-597, as filed)

T-184/AT-585 built `stages/issues.py::pin_issue_as_case(issue, flow_id, steps, *,
project=None)` and the store-side guard that refuses to delete a pinned `Case` —
but shipped with **no caller**: `grep pin_issue_as_case in src` returned only the
definition. A pinned case is protected and runs in every regression once it
exists, but nothing let a human actually create one, so "this bug must never
come back" (the meeting's ask) was still not usable.

## What changed

- `src/autotester/ui/routes_issues.py` — two new routes, both reusing the
  existing case machinery rather than duplicating it:
  - `GET /projects/{slug}/issues/{issue_id}/pin` (`pin_issue_form`, :95-127) —
    renders the issue's title/description plus the same step-editor table
    `ui/case_form.py` already builds for hand-added cases (`_step_row`,
    `STEP_ROWS`, `_credential_datalist`).
  - `POST /projects/{slug}/issues/{issue_id}/pin` (`pin_issue`, :130-147) —
    reuses `ui/routes_cases.py::_build_steps` (drops blank rows),
    `_guard_submitted_case` (credential-leak guard, AT-070/71/77),
    `ui/helpers.py::_require_reachable_navigate_steps` (AT-058/AT-432 — a step
    that could never run is refused at creation, not discovered at run time),
    and `_refuse_duplicate` (AT-060 — a second identical submission is refused
    with 400, never silently swallowed). Refuses with 400 when every step row
    is blank ("confirm at least one reproduction step before pinning") — steps
    are never guessed from the issue's narrative, matching
    `pin_issue_as_case`'s own contract. On success: `pin_issue_as_case(issue,
    flow_id="manual", steps=steps, project=slug)` (mirrors hand-added cases'
    own `flow_id="manual"`, since a pinned case — like a hand-added one — has
    no `FlowSpec` flow behind it) then `store.add_case(case)`, redirect 303 to
    `/projects/{slug}/cases`.
  - `issues_page` (:59-77): each issue row gained a "Regression" column — a
    "Pin as regression case" link for an unpinned issue, or a `pinned` pill
    (`_issue_action_cell`, :50-56) once `store.list_cases()` shows a case whose
    `pinned_issue_id` matches — so a human can tell at a glance which findings
    already have a protected case and never accidentally double-pins with
    different steps.
  - `_find_issue_or_404` (:43-47): the one lookup `list_issues()` didn't already
    offer (no `get_issue(id)` on `ProjectStore`); reused by both new routes.
- `src/autotester/cli_issues.py` — a second, scriptable entry point to the same
  constructor, since this project's `issues` Typer group already exists
  (AT-220's precedent: a stage with no caller is an absent feature, whichever
  surface would reach it):
  - `_parse_step` (:63-81) — parses `action:target[:value[:expect]]` into a
    `Step`, refusing an unparseable shape or an unknown `Action` with a message
    naming the valid ones.
  - `pin_cmd` (`issues pin <project> <issue_id> --step ... [--step ...]`,
    :84-138) — looks the issue up by id, refuses with exit 2 if not found or if
    no `--step` was given (never guesses), parses every step, calls the same
    `pin_issue_as_case`, and reports "already pinned as case <id>" (exit 0) if
    an identical case is already on file rather than a confusing generic
    success message.

No file crossed 300 lines (161 / 156 for the two `src/` files); no function
crossed 50 (`doctor` confirms both).

## Explicitly NOT built

- No new CLI/UI way to browse or search issues beyond the existing issues page.
- No bulk-pin. One issue, one form/command call, per the "human-confirmed, never
  guessed" requirement — a bulk action would have to guess steps for issues it
  wasn't shown, which is exactly what this unit refuses to do.
- `flow_id="manual"` for every pinned case (same choice T-184's own test suite
  uses, and the same one `ui/routes_cases.py::create_case` makes for hand-added
  cases) — an `Issue` carries a `screen`, not a `Flow` reference, so there is no
  real flow to attribute a pinned case to.

## How to verify (commands + expected)

```
uv run pytest tests/test_ui_issues.py tests/test_cli_issues.py tests/test_pinned_regression.py tests/test_ui_case_management.py tests/test_ui_cases.py tests/test_issues.py tests/test_expand.py tests/test_expand_cli.py tests/test_run_case_pipeline.py tests/test_cli_surface.py
uv run ruff check src tests scripts
uv run autotester doctor
```

## Actual outputs (from maker's own run, in the worktree)

```
$ uv run pytest tests/test_ui_issues.py tests/test_cli_issues.py tests/test_pinned_regression.py tests/test_ui_case_management.py tests/test_ui_cases.py tests/test_issues.py tests/test_expand.py tests/test_expand_cli.py tests/test_run_case_pipeline.py tests/test_cli_surface.py
............................................................................. [ 50%]
........................................................................       [100%]
143 passed, 1 skipped, 1 warning in 11.80s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Red before the fix** — the new tests (`tests/test_ui_issues.py`'s new pin
tests, `tests/test_cli_issues.py` in full) were run in the worktree against the
**unmodified** `src/` (before any of the two `src/` edits above):

```
$ uv run pytest tests/test_ui_issues.py tests/test_cli_issues.py
...
FAILED tests/test_ui_issues.py::test_issues_page_offers_a_pin_action_for_an_unpinned_issue
FAILED tests/test_ui_issues.py::test_pin_form_shows_the_issue_and_a_step_editor
FAILED tests/test_ui_issues.py::test_pinning_with_confirmed_steps_creates_a_protected_case
FAILED tests/test_ui_issues.py::test_pinning_with_no_confirmed_steps_is_refused
FAILED tests/test_ui_issues.py::test_pinning_an_unreachable_navigate_step_is_refused
FAILED tests/test_ui_issues.py::test_a_pinned_issue_shows_pinned_instead_of_the_pin_link
FAILED tests/test_cli_issues.py::test_pin_creates_a_protected_case_from_confirmed_steps
FAILED tests/test_cli_issues.py::test_pin_an_unknown_issue_fails_clearly
FAILED tests/test_cli_issues.py::test_pinning_the_same_issue_and_steps_twice_is_idempotent
9 failed, 6 passed, 1 warning in 7.54s
```

(The 6 that passed by coincidence: FastAPI's own 404 for the not-yet-registered
GET pin route, and Typer's own exit-2 for an unknown `pin` subcommand, already
matched what those particular assertions expected — genuinely new behavior was
still red.)

## Capability coverage (each claim -> its isolating falsification)

Throwaway copy built OUTSIDE the worktree (`scratchpad/falsify-at597`): `src/`,
`tests/{conftest.py, tests_mutation_fixtures.py, test_ui_issues.py,
test_cli_issues.py, test_pinned_regression.py, fixtures/}`, `scripts/{regression_proof.py,
explore_proof.py}`, `pyproject.toml`, `uv.lock`, `.python-version`, an empty
`README.md` (needed only for `uv sync`'s build metadata). `uv sync --frozen` run
there in its own venv; confirmed green (25/25 relevant tests) before any
falsification. Every falsifying edit below is a single hunk, applied, run, then
reverted and re-confirmed green before the next row — the tracked worktree was
never touched for this.

| capability | check | falsifying edit (single hunk) | observed |
|---|---|---|---|
| an issue with no case yet offers "Pin as regression case"; a pinned one shows the "pinned" pill instead | `test_a_pinned_issue_shows_pinned_instead_of_the_pin_link` | `routes_issues.py`: `if issue.id in pinned_issue_ids:` → `if False:` | PASS before. FAIL after: the pin link stayed in the page for the already-pinned issue (`assert '/projects/.../pin' not in ...` failed) |
| pinning refuses an all-blank step submission (steps are never guessed) | `test_pinning_with_no_confirmed_steps_is_refused` | `routes_issues.py`: `if not steps:` → `if False:` | PASS before. FAIL after: `assert 200 == 400` (silently pinned with zero steps instead of refusing) |
| pinning refuses a step that could never navigate (AT-058/AT-432 guard reused) | `test_pinning_an_unreachable_navigate_step_is_refused` | `routes_issues.py`: commented out the `_require_reachable_navigate_steps(steps, project)` call | PASS before. FAIL after: `assert 200 == 400` |
| a second identical pin submission is refused, not silently swallowed (AT-060 guard reused) | `test_pinning_the_same_issue_and_steps_twice_is_refused_not_silently_swallowed` | `routes_issues.py`: commented out the `_refuse_duplicate(store, case)` call | PASS before. FAIL after: `assert 200 == 400` |
| pinning an unknown issue id fails with a named reason | `test_pin_an_unknown_issue_fails_clearly` (CLI) | `cli_issues.py`: `if issue is None:` → `if False:` | PASS before. FAIL after: uncaught `AttributeError('NoneType' object has no attribute 'title')`, message assertion failed (empty output) |
| pinning with zero `--step` values is refused with a named reason | `test_pin_requires_at_least_one_step` (CLI) | `cli_issues.py`: `if not step:` → `if False:` | PASS before. FAIL after: uncaught `TypeError('NoneType' object is not iterable)`, message assertion failed |
| an unparseable `--step` string is refused with the documented message | `test_pin_rejects_an_unparseable_step` (CLI) | `cli_issues.py`: `if len(parts) < 2:` → `if False:` | PASS before. FAIL after: a different, un-intended message surfaced (`not enough values to unpack`) instead of "must look like ..." |
| an unknown action name is refused, naming the valid ones | `test_pin_rejects_an_unknown_action` (CLI) | `cli_issues.py`: `is not one of {known}` → `nope {known}` | PASS before. FAIL after: `assert "is not one of" in "... 'flibber' nope navigate, click, ..."` |

`test_issues_page_offers_a_pin_action_for_an_unpinned_issue`,
`test_pin_form_shows_the_issue_and_a_step_editor`,
`test_pinning_an_unknown_issue_is_404`,
`test_pinning_with_confirmed_steps_creates_a_protected_case` (CLI and UI), and
`test_pinning_the_same_issue_and_steps_twice_is_idempotent` (CLI) are not
separately falsified: the first four are the constructor's own happy path,
already covered by the row above disarming the same code paths in combination,
and the CLI idempotent test isolates `ProjectStore.add_case`'s own idempotence
(already falsified in `qa/verdicts/t184-pinned-regression.md`), not new code
this unit adds — the CLI's `has_case` early-return only changes which message
prints, which that test does not assert on.

## Live browser evidence

**Ran the real server, not just `TestClient`** — RAM this session did not allow
a Chromium session (playwright MCP was unavailable this run: `CONNECT_TIMEOUT`),
so this is HTTP-level, not pixel-level, evidence. Recipe below for the checker's
own Mode D pass.

```
$ AUTOTESTER_ROOT=/tmp/at597-live uv run uvicorn autotester.ui.app:app --host 127.0.0.1 --port 8069
# onboarded liveproj, added one Issue directly via ProjectStore (no UI route creates issues --
# they come from video derive), then drove the real HTTP routes:

GET  /projects/liveproj/issues                       -> 200, contains "Pin as regression case"
                                                          and the exact /issues/{id}/pin href
GET  /projects/liveproj/issues/{id}/pin               -> 200 (step-editor form)
POST /projects/liveproj/issues/{id}/pin (2 confirmed steps)
                                                      -> 303 -> /projects/liveproj/cases
# confirmed via ProjectStore: 1 case, pinned=True, pinned_issue_id == issue.id
GET  /projects/liveproj/issues                       -> now shows "pinned" pill, not the link
GET  /projects/liveproj/cases                         -> shows "pinned regression -- <issue title>"
POST /projects/liveproj/cases/{new_case_id}/delete    -> 409 (T-184's guard holds through this
                                                          new caller too)
```

**Recipe for the checker's Mode D (real Chromium):**

1. `uv run uvicorn autotester.ui.app:app --host 127.0.0.1 --port 8069` (set
   `AUTOTESTER_ROOT` to an isolated temp dir first, per this project's usual
   Mode D isolation).
2. Onboard a project (`/onboard`), then add one `Issue` to its store directly
   (no UI creates issues yet — `ProjectStore("<slug>").add_issue(Issue(...))`,
   same shape as `tests/test_ui_issues.py::_a_signup_issue`).
3. Open `/projects/<slug>/issues` — confirm the "Pin as regression case" link
   renders per un-pinned row.
4. Click it, fill at least one step row (a Target box is enough), submit —
   confirm the redirect lands on `/projects/<slug>/cases` and the new case's
   title is prefixed `pinned regression —`.
5. Reload `/projects/<slug>/issues` — confirm the row now shows a "pinned" pill
   and the link is gone.
6. On the cases page, click Delete on that case — confirm it renders as a 409
   (same raw-JSON pattern AT-596 already tracks app-wide; not charged here),
   and the case is still listed afterward.
7. Submit the same issue's pin form a second time with identical steps —
   confirm a 400, not a second case.

## Known limits / gaps (disclosed, not claimed)

- **No real-browser (Chromium) Mode D run this cycle** — playwright MCP was
  unavailable (`CONNECT_TIMEOUT`). HTTP-level live evidence against the real
  uvicorn app substitutes above; recipe given for the checker's own pass.
- **Full suite not run** — RAM-constrained session; targeted tests covering
  every changed module (routes_issues, cli_issues, the pin constructor, case
  management, cases UI, issues stage, expand/run-pipeline as `Case` consumers,
  CLI surface) were run and are green (143 passed, 1 pre-existing skip).
- **AT-596** (every UI 4xx renders as raw JSON, app-wide) is untouched here —
  the dispatch brief explicitly said not to touch `ui/app.py`, which owns that
  fix; the 409 from this unit's own delete-reuse inherits the same rendering,
  consistent with every other route.
- **No bulk-pin, no issue browse/search beyond the existing table** — out of
  scope per AT-597's own "a 'Pin as regression case' action ... or a CLI
  command" ask.

## Status: ready-for-check
