# Verdict — ui-back-nav-and-live-clarity

**Contract:** qa/contracts/ui.md
**Manifest:** qa/manifests/ui-back-nav-and-live-clarity.md
**Date:** 2026-09-07
**Cycle checked: 1**
**Checker:** Mode A, fresh context, bound to `D:/autoTesting`

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 1/1 invariants hold
FAILURES: none
ISSUES-WRITTEN: AT-057 (new, out-of-scope gap the manifest logged honestly)
EXPLANATION: All four adapter verify commands re-run by me in the container reproduce the
maker's claims exactly (287 passed/1 skipped; 12 passed in test_ui_dashboard.py; ruff clean;
doctor clean). All 8 breadcrumb replacements across 6 files are faithful — I diffed each old
hand-written trail against the new theme.breadcrumb(...) call and against the live rendered
HTML: same labels, same link targets, back button added. U5 holds under an independent hostile-
input probe I wrote myself (a project named `<script>alert(1)</script>&'"` renders escaped on
every route including the new breadcrumb). Deferring the "no UI path to add a case" gap is
legitimate scoping — ui.md carries no criterion requiring it and its no-fire list already defers
run-triggering — but I filed AT-057 so it becomes queued work rather than an inbox line only.
```

## What I re-ran myself (never trusted the pasted output)

| Command | My result | Manifest claim | Match |
|---|---|---|---|
| `docker compose exec autotester uv run pytest -q` | 4 dot-lines, `[100%]`, 287 passed / 1 skipped, exit 0 | "all pass, no failures" | yes |
| `docker compose exec autotester uv run pytest -q tests/test_ui_dashboard.py` | `12 passed, 1 warning in 1.46s` | "12 passed" | yes |
| `docker compose exec autotester uv run ruff check src tests scripts` | `All checks passed!` | same | yes |
| `docker compose exec autotester uv run autotester doctor` | `doctor: clean` | same | yes |

Live end-to-end I performed independently (container already `Up`, serving the new code; I
fetched the rendered HTML rather than reading the maker's `.work/` screenshots):

- `GET /projects/erp` → `<div class='crumbs'><a class='btn btn-back' href='/'>&larr; Back</a><div class='breadcrumb'><a href='/'>Projects</a> / ERP</div></div>`
- `GET /projects/erp/env` → back targets `/projects/erp` (the **parent**, not home) — the nested-back claim is real on the live server, not just in a test.
- `GET /projects/erp/report` → back `/projects/erp`; `GET /projects/erp/flow-diagram` → back `/projects/erp`
- `GET /settings/providers`, `GET /onboard`, `GET /live` → back `/`
- `GET /` → **zero** `<a class='btn btn-back'` occurrences (home correctly has none)
- `GET /live` → contains "A black screen below is normal" (1 hit) and `AUTOTESTER_SLOW_MO_MS` (1 hit); the stale `regression_proof.py` tip is **gone** (0 hits).

## Criterion-by-criterion

### U1 — Onboarding creates a real, CLI-compatible project — MET
Untouched by this unit. `POST /onboard` still builds `Project(...)` and persists via
`ProjectStore.save_project` (`ui/app.py:173-179`); the diff changes only the markup string in
`onboard_form`. My own probe posted a project and read it back through `/projects/xss` — the
record was created and rendered from the store. No UI-only representation introduced.

### U2 — Project detail reflects real state, no caching/duplication — MET
`project_detail` still calls `_load_project_or_404` (which 404s an unknown slug) and reads
`review.status` / case count live; the diff replaces only the breadcrumb line. Verified live:
`/projects/erp` renders `0 Cases` and `no flowspec yet` read from the store on the request.

### U3 — The env editor never renders a real secret value — MET
`routes_credentials.py` diff touches only the breadcrumb block. `_status_cell` still renders
`● Set` / `○ Not set` pills, the input is `type='password'` with no `value=`, and the write path
is still `set_env_value`. No secret value appears in the rendered HTML I fetched.

### U4 — Run/report views read real persisted evidence — MET
`routes_report.py` diff is breadcrumb-only in both `run_view` and `report`. Live `/projects/erp/report`
(a project with no runs) returns **200** with an empty-state, not an error, as U4 requires.
`report()`'s no-runs branch still consumes the `breadcrumb` local correctly (the assignment shape
changed but the variable is still used, and 12/12 UI-dashboard + the whole `test_ui_report.py`
suite pass).

### U5 — User-supplied values are HTML-escaped — MET (the item I scrutinised hardest)
`theme.breadcrumb()` interpolates both `label` and `href` raw, relying on caller-escaping — the
same stated discipline as `theme.page()`. I audited **every one of the 8 call sites**, not a
sample:

| Call site | Label(s) | Href(s) | Escaped? |
|---|---|---|---|
| `app.py::onboard_form` | `"Projects"`, `"Onboard"` | `"/"` | literals |
| `app.py::project_detail` | `"Projects"`, `name` | `"/"` | `name = escape(project.name)` at `app.py:192` |
| `app.py::live_view` | `"Projects"`, `"Live view"` | `"/"` | literals |
| `routes_credentials.py::env_editor_view` | `"Projects"`, `name`, `"Credentials"` | `"/"`, `/projects/{safe_slug}` | `name = escape(project.name)` at line 28; `safe_slug = escape(slug)` at line 29 |
| `routes_flow_diagram.py::flow_diagram` | `"Projects"`, `safe_slug`, `"Flow diagram"` | `"/"`, `/projects/{safe_slug}` | `safe_slug = escape(slug)` |
| `routes_report.py::run_view` | `"Projects"`, `safe_slug`, `"Report"`, `"Run"` | `"/"`, `/projects/{safe_slug}`, `/projects/{safe_slug}/report` | `safe_slug = escape(slug)` |
| `routes_report.py::report` | `"Projects"`, `safe_slug`, `"Report"` | same | `safe_slug = escape(slug)` |
| `routes_settings.py::provider_settings_view` | `"Projects"`, `"Settings"` | `"/"` | literals |

**Project NAME** — the free-form user input the dispatch flagged — is used as a breadcrumb label
in exactly two places (`project_detail`, `env_editor_view`) and **both** pass `escape(project.name)`.
**No user-controlled string reaches an `href=` at all:** every href is either a literal or
`/projects/{safe_slug}[/report]`, and `safe_slug` is `escape()` of a slug already validated by
`helpers._require_slug` against `^[a-z][a-z0-9-]*$` (no quote, `<`, `>`, or space is representable).

I did not stop at reading. I wrote and ran my own probe inside the container (a project named
`<script>alert(1)</script>&'"`, onboarded through `POST /onboard`, then fetched on 5 routes):

```
/projects/xss              RAW_SCRIPT_PRESENT= False | escaped= True
/projects/xss/env          RAW_SCRIPT_PRESENT= False | escaped= True
/projects/xss/report       RAW_SCRIPT_PRESENT= False | escaped= True
/projects/xss/flow-diagram RAW_SCRIPT_PRESENT= False | escaped= True
/                          RAW_SCRIPT_PRESENT= False | escaped= True
```

And the helper's own two branches:
```
breadcrumb(("A", None))
  -> "<div class='crumbs'><div class='breadcrumb'>A</div></div>"          # no back button at the root
breadcrumb(("A","/a"),("B","/b"),("C",None))
  -> "...<a class='btn btn-back' href='/b'>&larr; Back</a>..."            # back = LAST href'd crumb
```

### Invariant — shared-layout / one-concept-one-place (ui.md 2026-09-03 amendment) — HOLDS
The unit strengthens it: 8 duplicated inline `<div class='breadcrumb'>` blocks across 5 modules
collapse to one helper. `doctor` is clean and does not regress.

## Point 2 of the dispatch — are the 8 replacements faithful?

Yes. I compared each removed string in `git diff` to the new call, and then to the live HTML:

| Route | Old trail | New trail | Delta |
|---|---|---|---|
| onboard | Projects(/) / Onboard | identical | + back → `/` |
| project detail | Projects(/) / name | identical | + back → `/` |
| live | Projects(/) / Live view | identical | + back → `/` |
| credentials | Projects(/) / name(`/projects/<slug>`) / Credentials | identical | + back → `/projects/<slug>` |
| flow diagram | Projects(/) / slug(`/projects/<slug>`) / Flow diagram | identical | + back → `/projects/<slug>` |
| run view | Projects(/) / slug(`/projects/<slug>`) / Report(`/projects/<slug>/report`) / Run | identical | + back → `/projects/<slug>/report` |
| report | Projects(/) / slug(`/projects/<slug>`) / Report | identical | + back → `/projects/<slug>` |
| settings | Projects(/) / Settings | identical | + back → `/` |

**No link target silently changed.** The only CSS-side behavior change is `margin-bottom` moving
from `.breadcrumb` to the new `.crumbs` wrapper — purely presentational, and `.breadcrumb`'s own
font/color/transform rules are unchanged.

The live-view copy change is the one non-navigation behavior change, and it is an honesty
improvement, not a functional one: the old tip named `scripts/regression_proof.py` (a path that
predates the ▶ Run tests button) and is now replaced by a correct explanation of the idle black
display plus the AT-054 `AUTOTESTER_SLOW_MO_MS` opt-in. No route logic, no store call, no
`ProjectStore`/`SecretStore` access was added or removed anywhere in the diff.

## The KNOWN GAP the manifest deferred — legitimate scoping

The manifest logs, and does not fix, that a freshly-onboarded project has zero cases, a
permanently disabled ▶ Run tests button, and **no UI path anywhere to add a case**. I confirmed
this live: `/projects/erp` renders `0 Cases` and the Run action is greyed out.

Judged against `ui.md`: **deferring was correct.** U1 requires onboarding to create a real,
CLI-compatible project record — it does. No criterion U1-U5 requires case creation from the UI,
and the no-fire list already defers "triggering a run or an onboarding video from the UI" as a
future enhancement. Folding it into this unit would have been scope creep into a genuinely
different contract cycle. The manifest logged it verbatim to `qa/feedback-inbox.md` (2026-09-07
entry, confirmed present) rather than dropping it, which is exactly the right disposal.

It is, however, a real product gap that should not live only as prose in an inbox, so as ledger
writer I filed **AT-057** (severity high, `open`) with the live evidence. It needs its own
contract-scoped unit — likely a `ui.md` criterion added after the maker or Umesh decides whether
the answer is an add-a-case flow or an explicit next-step prompt. That decision is not mine to
make inside a verdict.

## Point 3 of the dispatch — did the source changes actually get committed? (AT-055 lesson)

**I had to commit them myself.** At the time I began this check, `git status --porcelain` showed
all seven source files, the test file, the manifest, and the feedback inbox as **modified but
uncommitted** — the exact AT-055 failure mode (PASS paperwork committed, the actual fix left in
the working tree). The last three commits (`4504aae`, `3d13a71`, `32e6c20`) contained none of
this unit's source changes.

I therefore committed, with a narrow pathspec covering exactly the unit's files and nothing else
(no `git add -A`; `.goal/`, `docs/SNAPSHOT.md`, `goal.md`, `qa/.last-tick`, and the untracked
`projects/erp/` were deliberately left alone as other owners' state):

```
src/autotester/ui/theme.py
src/autotester/ui/theme_style.py
src/autotester/ui/app.py
src/autotester/ui/routes_report.py
src/autotester/ui/routes_credentials.py
src/autotester/ui/routes_flow_diagram.py
src/autotester/ui/routes_settings.py
tests/test_ui_dashboard.py
qa/manifests/ui-back-nav-and-live-clarity.md
qa/feedback-inbox.md
qa/verdicts/ui-back-nav-and-live-clarity.md
qa/issues.jsonl
qa/contracts/ui.md
```

Each of the ten dispatch-named paths is verified tracked and present in that commit.

## Contract maintenance performed

Appended a routine, non-weakening amendment row to `qa/contracts/ui.md` recording the shared
breadcrumb/back-button invariant and the live-view copy fix — closing the AT-056/AT-043/AT-048
contract-staleness pattern (a unit shipping with no contract-side trace) before it recurs.

## Observations (not failures — I would not defend these as defects)

- `theme.breadcrumb()` trusts callers for both label and href escaping. Every current caller is
  correct, so U5 is met. But `page()` at least only takes a pre-built body, whereas `breadcrumb()`
  puts a caller string inside an `href='...'` attribute — a future caller passing an unescaped
  name into an href position would be an injection, and nothing in the code stops it. Cheap
  hardening if the maker ever wants it: `escape(href, quote=True)` inside the helper (idempotent
  for the already-safe values in use today). Filing no issue; it is a design-discipline question,
  not a present defect.
- The parametrized back-button test covers 7 pages; the run view (`/projects/<slug>/runs/<id>`) is
  the one breadcrumb call site with no direct back-button assertion. Its trail is exercised by
  `tests/test_ui_report.py` and I read the diff, so I am satisfied — but it is the one call site
  a future refactor could break silently.
