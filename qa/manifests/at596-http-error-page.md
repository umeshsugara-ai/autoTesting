# Manifest — at596-http-error-page

**Unit:** every `HTTPException` raised anywhere under `ui/app.py`'s routers gets a themed HTML page
for a browser, and the exact JSON body FastAPI's default handler already produced for everyone
else — status codes unchanged.
**Contract:** `qa/contracts/ui.md` U5 (escaping discipline) — no criterion yet names this app-wide
handler by number; flagged for the checker to decide whether a new U-item is warranted (U10's
amendment log already tracks the sibling gap on `approve`/`request-edit` as AT-259, deliberately
not claimed here either).
**Date:** 2026-09-26
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-596

## The gap (AT-596, as filed)

`src/autotester/ui/app.py` registered no `HTTPException` handler, so every 4xx raised by any route
— the ordinary 400s, `_load_project_or_404`'s 404s, and T-184/AT-585's new 409 on deleting a
pinned case — fell through FastAPI's default handler as a raw `{"detail": ...}` JSON body. A
browser hitting that route (not a client asking for JSON) got Chrome's own built-in JSON viewer:
no styling, no nav, no link back to the app. Evidence: the checker's own screenshot from the T-184
cycle, `qa/evidence/browser-t184-pinned-regression-2026-09-26-checker/02-after-pinned-delete-attempt.png`.

## What changed

- `src/autotester/ui/error_pages.py` (new, 86 lines) — the whole fix, split out of `app.py` rather
  than added inline because `app.py` was already at 295/300 lines (the design cap) before this
  unit; adding the handler in place would have pushed it to ~305.
  - `_wants_html(request)` — `"text/html" in request.headers.get("accept", "")`. A real browser
    sends `Accept: text/html,application/xhtml+xml,...`; httpx's `TestClient` sends `Accept: */*`
    when a test sets no header at all (confirmed live, see "Actual outputs"), so every pre-existing
    test in this suite that never sets `Accept` keeps seeing JSON, unchanged.
  - `_repo_redactor()` — builds a `core.redact.Redactor` from `parse_env(repo_root() / ENV_FILE)`,
    the same repo-root `.env` file `ProjectPaths(<any slug>).env_file` always resolves to ("one
    credential file for the whole repo," `core/paths.py`) and the same shared-`.env` matching U9
    already requires of the credential guard. Used instead of a project-scoped `SecretStore`
    because an app-wide error page has no single project in scope to load one from.
  - `_error_page(status_code, detail)` — redacts `detail` via `_repo_redactor().scrub(...)`, THEN
    `html.escape`s it (redact-then-escape, not the other way round, or a scrubbed value would need
    to match against already-escaped secret bytes), and renders it inside `theme.card(...)` /
    `theme.page(...)` — the same wrap/card primitives every other themed page in this app already
    uses (`ui/routes_learn.py::_refusal` is the closest existing precedent for "a themed refusal
    with a way onward").
  - `http_exception_handler(request, exc)` — the registered handler: JSON/no-`Accept` callers are
    handed straight to FastAPI's own `fastapi.exception_handlers.http_exception_handler` (so the
    204/304-body-suppression edge case and the JSON shape are exactly FastAPI's, not reimplemented);
    HTML-accepting callers get `_error_page`, with the same `is_body_allowed_for_status_code` guard
    FastAPI's own default handler uses.
  - `register_exception_handler(app)` — `app.add_exception_handler(HTTPException, ...)`. (Named
    this, not `register`, after `autotester doctor`'s `duplicate-concept` check flagged the first
    name against the unrelated `providers/__init__.py::register` — a real name collision, not a
    real duplicate concept; renaming was cheaper than arguing with the linter.)
- `src/autotester/ui/app.py:25-27,72` — `error_pages` added to the shared `from autotester.ui
  import (...)` tuple; `error_pages.register_exception_handler(app)` called once, right after
  `app = FastAPI(...)`, before any router is included. Net +2 lines (295 -> 297; still under 300).
- `tests/test_ui_error_pages.py` (new, 9 tests) — see "Actual outputs" and "Capability coverage."
- `docs/MAP.md` — regenerated (`uv run autotester map`) to list the new module; no hand edits.

## How to verify (commands + expected)

- `uv run pytest tests/test_ui_error_pages.py` -> all pass
- `uv run pytest tests/test_ui_error_pages.py tests/test_ui.py tests/test_ui_case_management.py tests/test_ui_cases.py tests/test_ui_project_name.py tests/test_ui_case_navigate_reachability.py tests/test_ui_learn.py tests/test_pinned_regression.py` -> all pass (the shared `app` fixture + every route this unit's handler now sits in front of, plus the pinned-case 409 this bug was filed against)
- `uv run ruff check src tests scripts` -> `All checks passed!`
- `uv run autotester doctor` -> `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_ui_error_pages.py
.........
9 passed, 1 warning in 3.47s

$ uv run pytest tests/test_ui_error_pages.py tests/test_ui.py tests/test_ui_case_management.py tests/test_ui_cases.py tests/test_ui_project_name.py tests/test_ui_case_navigate_reachability.py tests/test_ui_learn.py tests/test_pinned_regression.py
........................................................................ [ 94%]
....                                                                     [100%]
76 passed, 1 warning in 11.32s

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**Red before the fix.** `tests/test_ui_error_pages.py` was copied into a throwaway checkout OUTSIDE
the worktree (`git archive f5dc842 -- src tests scripts pyproject.toml uv.lock` — the parent commit,
before any of this unit's edits — extracted to the session scratchpad, own `uv sync`'d venv, the
tracked worktree never touched):

```
$ uv run pytest tests/test_ui_error_pages.py -v
ImportError while importing test module '...\tests\test_ui_error_pages.py'.
E   ImportError: cannot import name 'error_pages' from 'autotester.ui' (...\src\autotester\ui\__init__.py)
1 error during collection
```

The whole module failed to collect — `ui/error_pages.py` did not exist, which is the bug itself
(no handler, anywhere).

**First doctor run was not clean.** Before the rename below, `autotester doctor` reported:
```
duplicate-concept: src\autotester\ui\error_pages.py:85 — 'register' also defined in src\autotester\providers\__init__.py
```
Fixed by renaming `register` -> `register_exception_handler` (both the definition and its two call
sites, in `app.py` and this unit's own test file); re-ran clean (see "Actual outputs" above).

## Capability coverage (each claim -> its isolating falsification)

Throwaway copy built OUTSIDE the worktree from the **fixed** commit (`d9a4182`): `git archive
d9a4182 -- src tests scripts pyproject.toml uv.lock` extracted to the session scratchpad
(`scratchpad/at596-falsify`), own `uv sync`'d venv, confirmed green (9/9) before any falsification.
Every falsifying edit below is a single hunk in `error_pages.py`, applied, run, then reverted —
confirmed byte-identical to the tracked worktree's copy (`diff` empty) and green again before the
next row. The tracked worktree itself was never edited for this purpose.

| claim | falsifying edit (single hunk) | check | observed |
|---|---|---|---|
| a browser (`Accept: text/html`) gets the themed HTML page | `_wants_html`: `return "text/html" in request.headers.get("accept", "")` -> `return False` | `test_{400,404,409}_with_html_accept_renders_a_themed_page`, `test_html_error_page_escapes_the_detail`, `test_html_error_page_redacts_a_known_secret_from_the_repo_env` | PASS before (9/9). FAIL after: all 5 fail — every HTML-accepting request instead gets the raw JSON body |
| a JSON/no-`Accept` client's response is byte-for-byte what FastAPI's default handler already produced | `_wants_html`: same function -> `return True` (unconditional) | `test_{400,404,409}_with_json_accept_is_unchanged`, `test_400_with_no_accept_header_stays_json` | PASS before. FAIL after: all 4 fail — `response.json()` raises `JSONDecodeError` on the HTML body it now gets instead |
| the detail is HTML-escaped before it reaches the page | `_error_page`: `safe_detail = escape(_repo_redactor().scrub(detail))` -> `safe_detail = _repo_redactor().scrub(detail)` (drop `escape`) | `test_html_error_page_escapes_the_detail` | PASS before. FAIL after: `assert '<script>alert(1)</script>' not in response.text` fails — the raw tag is on the page |
| a known secret in the detail is redacted before it reaches the page | `_error_page`: same line -> `safe_detail = escape(detail)` (drop `.scrub()`, keep `escape`) | `test_html_error_page_redacts_a_known_secret_from_the_repo_env` | PASS before. FAIL after: `assert 'sk-supersecretvalue123' not in response.text` fails — the raw secret is on the page |
| the exception's original status code reaches the response unchanged | `_error_page`: `return HTMLResponse(theme.page(title, body), status_code=status_code)` -> `status_code=200` | `test_{400,404,409}_with_html_accept_renders_a_themed_page`, `test_html_error_page_escapes_the_detail`, `test_html_error_page_redacts_a_known_secret_from_the_repo_env` | PASS before. FAIL after: all 5 fail — every themed page comes back `200` instead of its real status |

Five distinct behaviors, five distinct single-hunk falsifications, each isolating exactly the test
rows that claim it and leaving the rest green (e.g. the escaping-drop edit only fails the one
escaping test, not the redaction test or the negotiation tests) — confirming the tests are actually
pinned to the claims they name, not incidentally passing.

## Live browser evidence

`uv run uvicorn autotester.ui.app:app --host 127.0.0.1 --port 8069` (scratch `AUTOTESTER_ROOT`),
driven with `curl` sending real header sets rather than `TestClient` (a genuinely separate process,
real HTTP, not the in-process ASGI transport `TestClient` uses):

- `curl -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" .../projects/does-not-exist`
  (Chrome's actual default `Accept` header, byte for byte) -> full themed page: doctype, `<title>404
  Not Found — AutoTester</title>`, the shared stylesheet + topbar + sidebar, and
  `<div class='card'><h2>404 Not Found</h2><p>no project &#x27;does-not-exist&#x27;</p><p
  style='margin-top:14px'><a class='btn' href='/'>&larr; Back to projects</a></p></div>` — escaped
  apostrophe, real nav, a way back.
- Same URL with `Accept: application/json` -> `{"detail":"no project 'does-not-exist'"}`.
- Same URL with no `Accept` header at all -> identical JSON body — confirms the negotiation default
  matches what every existing JSON-asserting test already assumed.
- `curl -X POST -H "Accept: text/html" .../projects/demo/cases/nope/delete` (409/404 path) -> same
  themed shell, `<h2>404 Not Found</h2>` (no `demo` project existed in that scratch root, which is
  itself the expected 404 behavior along the same handler path the 409 also travels).

**This is a real browser-facing behavior change** (not merely a `TestClient`-observed one) and the
checker's own Mode D recipe is below for an independent run. Server was killed after
(`taskkill /F` on the uvicorn PID; confirmed via `netstat` that port 8069 has no `LISTENING` entry
left, only expiring `TIME_WAIT` remnants from already-closed connections) — no monitor left running.

### Checker Mode D recipe

1. `uv run uvicorn autotester.ui.app:app --host 127.0.0.1 --port 8069` against a scratch
   `AUTOTESTER_ROOT`.
2. In a real browser (not `curl`, not `TestClient`): onboard a project, add a case, pin it (there is
   no UI button for pinning yet — AT-585's own gap — so seed `pinned=True` via `ProjectStore`
   directly against the scratch root, same as `tests/test_ui_case_management.py`'s
   `test_deleting_a_pinned_case_through_the_ui_is_refused_with_409` does), then click the case's
   delete control.
3. Expect: a page in this app's own visual language (topbar, sidebar, card, heading naming the
   status), not Chrome's built-in JSON viewer; a working "Back to projects" link; zero unexplained
   console errors.
4. Repeat for a plain 404 (visit an unknown `/projects/<slug>`) and a plain 400 (submit `/onboard`
   with a blank name) to confirm the same page shape across all three status codes this unit's
   tests cover.
5. Confirm an API-style request (e.g. `curl -H "Accept: application/json"` against any of the three
   URLs above) still gets the plain `{"detail": ...}` JSON it got before this unit.

## Known limits / gaps (disclosed, not claimed)

- **Full suite not run** (RAM ~0.9GB free per the dispatch brief) — targeted UI tests covering every
  route this handler now sits in front of, plus ruff and doctor, were run and are green; see "Actual
  outputs."
- **Only `fastapi.HTTPException` is handled**, exactly as scoped ("registers no HTTPException
  handler" in the filed issue, and every route in this app raises exactly that class). A framework-
  level 404 for a URL matching no route at all raises Starlette's own `HTTPException` and is
  **not** covered — the MRO-based handler lookup only matches `fastapi.HTTPException` and its
  subclasses, not its Starlette superclass. Not claimed here; flagged in case the checker considers
  it in-scope for "every 4xx."
- **U10's `approve`/`request-edit` raw-JSON refusals (AT-259) are untouched.** Those routes return
  `HTMLResponse`/raw JSON directly rather than raising `HTTPException`, so this handler never sees
  them — a pre-existing, separately tracked gap this unit does not claim to close.
- **No new `qa/contracts/ui.md` criterion added** — flagged above under "Contract" for the checker
  to decide (my brief said do not edit `qa/contracts/`).
- **The repo-root `.env` redactor is rebuilt (file read + parsed) on every themed error render.**
  Cheap for a local single-operator tool serving error pages, not a hot path; not cached, since
  caching a credential file's contents in memory across requests felt like the wrong tradeoff to
  make silently in a fix-cycle-1 unit — flagged rather than assumed fine.

## Status: ready-for-check
