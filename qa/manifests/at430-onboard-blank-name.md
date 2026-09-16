# Manifest — at430-onboard-blank-name

**Unit:** AT-430 — `/onboard` accepted a blank project name, leaving a ghost link on every page
**Contract:** `qa/contracts/ui.md`; core-invariants C2, C3, C7
**Goal task:** none — issue-driven (found by the independent live-browser validation, `qa/verdicts/live-2026-09-16-ui.md`)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-430 (medium)

## What was wrong

A blank or whitespace-only name posted to `/onboard` was **saved**. The project then rendered with an
empty `<h1>`, a tab title of ` — AutoTester`, and — the visible harm — a **text-less link in the
sidebar of every page**: `<a class='sidebar-link' href='/projects/p-blank'></a>`.

The browser's `required` attribute was the only guard, and a direct POST ignores it.

**The rule already existed, in the wrong shape.** `routes_project_edit.py:188` had it inline —
`if not name.strip(): raise HTTPException(400, "a project needs a name")` — and onboard, the one
route that *creates* projects, had no copy. It was also **untested on the edit route**, so the one
place that got it right was unverified too. A rule held on one route and not the other is exactly
how this defect was born.

## What changed

- `src/autotester/ui/helpers.py` — new `_require_project_name(name)`, beside the existing `_require_slug`
  and `_require_reachable_base_url`, following their pattern exactly. Rejects blank and
  whitespace-only names with a 400 and **never echoes the submitted value** (AT-088: a password
  pasted into the wrong field must not come back in the body or the access log).
- `src/autotester/ui/app.py::onboard_submit` — calls it immediately after `_require_slug`, i.e.
  **before anything is saved**.
- `src/autotester/ui/routes_project_edit.py::edit_project_submit` — the inline copy **replaced** by the
  same call. One definition, both routes.
- `tests/test_ui_project_name.py` (new) — 7 test cases. Separate from `test_ui.py`, which is at 291
  lines and would cross the doctor's 300-line rule; the seam is the single invariant "a project has a
  name" asserted across every route that writes one.

### Why not a schema validator on `Project.name`

It looks like the "one place" answer and is the wrong tool here, for two measured reasons:

1. In `onboard_submit`, `Project(...)` would raise a Pydantic `ValidationError` that nothing catches —
   turning today's 200-with-bad-data into a **500**, which is worse.
2. The edit route builds its update with `model_copy(update=...)`, which **skips validation** — so a
   schema validator would never fire there, and the route would still need its own copy of the rule.

I checked the risk before rejecting it: no persisted `project.json` has a blank name, and only two
`Project(...)` constructions exist in `src/`. It was safe; it just would not have fixed the bug.

## Capability coverage

| Capability claimed | Check that isolates it | Falsifying edit (single hunk) | Observed |
|---|---|---|---|
| Onboard refuses a blank/whitespace name | `test_ui_project_name.py::test_onboard_refuses_a_blank_or_whitespace_name` | `app.py`: delete the `_require_project_name(name)` call | GREEN before (`7 passed`); after **5 failed, 2 passed** — all 4 parametrized cases + the ghost-link test |
| Edit still refuses one after the rule moved | `::test_edit_still_refuses_a_blank_name_after_moving_the_rule` | `routes_project_edit.py`: delete the `_require_project_name(name)` call | GREEN before; after **FAILED exactly 1** |
| Whitespace-only counts as blank, not just `""` | the 3 whitespace parametrizations | `helpers.py`: `if not name.strip():` → `if not name:` | GREEN before; after **5 failed** — the 3 whitespace cases, the ghost-link test and the edit test; the `""` case **stays green**, correctly |
| **Nothing is saved** — not merely "a 400 is returned" | `::test_onboard_refuses_...` (`load_project() is None`) + `::test_a_refused_blank_name_leaves_no_ghost_link_in_the_sidebar` | `app.py`: **save the project first, then refuse** — the status is still 400 | GREEN before; after **5 failed** |

**Row 4 is the one that matters.** A status-only test would have passed that mutation: the response
is still a 400. It fails because the tests assert the project was not written and that no ghost link
renders — the actual harm. That is the difference between a check that watches the symptom and one
that watches the status code.

Every anchor asserted to match exactly once and to produce a real change; none broke import or
collection (7 collected every run). Baseline confirmed from a readable summary line
(`7 passed, 1 warning in 0.40s`) rather than a truncated tail.

## Live browser evidence

**`qa/evidence/browser-at430-onboard-blank-name-2026-09-16/report.json`** — a **maker smoke**, not
the validation. Real Chromium, isolated root with the Vidysea projects deleted.

- **Blank name through the real form and the real "Create project" button**, with `required` removed
  (the exact bypass): **HTTP 400**, `{"detail":"a project needs a name"}`.
- **Home page after the refusal:** sidebar = `[Regression Proof Demo]` only, **0 empty links**, the
  refused slug not listed, and `/projects/ghost-browser` → **404** — it was never created.
- **A real name through the same button:** redirected to `/projects/named-browser`, title and `<h1>`
  correct, sidebar entry has text, **0 console errors**.
- **Console errors attributed:** 1 on `/onboard` = the deliberate 400; 1 on `/` = my own fetch
  confirming the 404. None from page code.

## What this does not claim — including one thing the browser showed that I did not fix

- **The refusal renders as raw JSON.** `{"detail":"a project needs a name"}` replaces the whole page —
  no theme, no link back, and the operator's typed values are lost. **That is pre-existing**: every
  `/onboard` 400 (non-URL, domain mismatch, bad slug, duplicate) looks identical, and the independent
  live checker noted other routes such as crawl-approval *do* render a themed refusal. It is correct,
  but it is not friendly, and fixing it is a separate unit rather than scope creep into this one.
- It does not trim or normalise names that are *non*-blank (e.g. leading spaces are still stored).
- The edit route's refusal is proven by test, not by a browser run.
- It does not address AT-431/432/433/434/435, the other defects from the same live validation.

## How to verify (commands + expected)

- `uv run pytest tests/test_ui_project_name.py tests/test_ui.py -q` → exit 0
- `uv run pytest -q` → exit 0
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ui_project_name.py -p no:cacheprovider -o addopts= -q
7 passed, 1 warning in 0.40s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

```
$ uv run pytest -q
........................................................................ [  5%]
..................................xx....xx..xxxxxx....xx..xxxxxx..xxxxxx [ 11%]
xxxxxxxx................................................................ [ 16%]
........................................................................ [ 22%]
..............................................s......................... [ 27%]
........................................................................ [ 33%]
........................................................................ [ 38%]
........................................................................ [ 44%]
........................................................................ [ 49%]
........................................................................ [ 55%]
........................................................................ [ 60%]
........................................................................ [ 66%]
........................................................................ [ 71%]
........................................................................ [ 77%]
.....................................s.................................. [ 82%]
........................................................................ [ 88%]
........................................................................ [ 94%]
........................................................................ [ 99%]
......                                                                   [100%]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:53
  D:\autoTesting\.venv\Lib\site-packages\starlette\testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.
    _PortalFactoryType = Callable[[], AbstractContextManager[anyio.abc.BlockingPortal]]

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
EXIT: 0
```

The command's entire output, redirected rather than tailed. **The `x` marks are 32 expected failures, and none are this unit's:** `uv run pytest -o addopts= -q -rx` attributes all 32 to `tests/test_browser_scroll_invariance.py`, committed by the concurrent session at `d4fb88c` (AT-425/426), clean in git and untouched by AT-430. They were absent from earlier suite runs today only because that commit landed in between. The two `s` are skips; no `N passed` line appears because `pyproject.toml:62` makes the adapter's command `-qq`.

**Sabotage confirmation (C7):** `git archive HEAD` extract with its own `uv sync`;
`autotester.ui.helpers.__file__` confirmed resolving inside the extract; baseline 7 passed; four
mutations from pristine backups with exactly-once anchors — results in the table. Extract deleted;
**then** the suite (sabotage first, suite last).

## Data-boundary gate (MC-003)

Exits 1 on the missing `data_class` — AT-365, open, at HUMAN_GATE. Not introduced here.

## Checker ruling (2026-09-16, verdict 963a8a3) — PASS, 5/5 criteria, 9/9 invariants

**Validated in the checker's own live browser**, own server on port 8020, own isolated root with the
Vidysea projects deleted and this unit's four files layered on — so it tested the fix, not HEAD.

- **Onboard, every blank variant** (blank with `required` removed, whitespace, tab, blank plus a
  credential row): 400, slug page 404, nothing written to disk.
- **The edit route in the browser**, closing the gap I disclosed: `"   "` → 400 with heading, title
  and sidebar unchanged; a real rename works. `""` returns FastAPI's own **422**, because `Form(...)`
  rejects the empty field before the helper runs — pre-existing behaviour, name unchanged.
- **8 console errors, all attributed** to its own deliberate 400/422 probes; none from page code.
- **AT-088 held:** the refusal is fixed text; a sentinel entered as a credential value or as the name
  appeared in no response and **0 times in the server log**.
- All 4 capability rows reproduced. **Row 4 confirmed load-bearing:** under save-then-refuse the 400
  and `detail` assertions *still passed* — only the state assertions caught it.

**It tested my design reasoning by building the alternative, rather than reading my argument.** It put
a real validator on `Project.name` in its copy and removed both helper calls:
- (a) held: onboarding a blank name returned **500** — there is no exception handler in `ui/`.
- (b) held, **and the real outcome was worse than I wrote**: edit's `model_copy` skipped the validator
  and saved `name=''`, after which **the project could not be loaded at all.** I had said the validator
  "would never fire" on edit; the consequence is a project that bricks itself on the next load.

### The original bug was worse than filed

**A whitespace-only name gets past the browser's `required` attribute with the attribute left in
place** — `required` only checks for emptiness. So before this fix any ordinary user could create the
ghost project by typing a few spaces; no bypass was ever needed. AT-430 was filed as reachable only by
a direct POST.

### Filed, not blocking

**AT-439 (low)** — refusals on `/onboard` and edit render as raw JSON replacing the whole page, and
edit's empty field returns a bare 422. Confirmed pre-existing on a path the diff does not touch (a
duplicate slug renders identically), and no contract criterion requires a themed refusal there.

## Status: checked-PASS (cycle 1, verdict `qa/verdicts/at430-onboard-blank-name.md`, commit 963a8a3; ledger AT-430 open → fixed; AT-439 filed)
