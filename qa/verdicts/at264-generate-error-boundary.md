# Verdict — at264-generate-error-boundary

**Cycle checked:** 1
**Date:** 2026-09-09
**Checker:** fresh subagent, bound to `D:/autoTesting`
**Commit checked:** dc8acef (fix), 4dad729 (tick)

## What I re-ran

- `uv run pytest tests/test_ui_learn.py` → 12 passed, 1 warning (matches manifest).
- `uv run pytest` → 913 passed, 2 skipped, 1 warning in ~85s (matches manifest exactly).
- `uv run ruff check src tests scripts` → All checks passed!
- `uv run autotester doctor` → doctor: clean.

## Sabotage confirmation (C1)

In a `git archive dc8acef` extract (never the live tree, never `git stash`/`checkout`/`restore` —
AT-101), reverted the anchor
```
try:
    cases = expand(spec, provider, RepoDocs())
except ProviderError as exc:
    return _refusal(...)
for case in cases:
    store.add_case(case)
```
back to the bare
```
for case in expand(spec, provider, RepoDocs()):
    store.add_case(case)
```
— anchor matched exactly once. Ran the new test alone against the sabotaged extract:
`test_generate_when_the_model_fails_midway_is_refused_as_a_page_not_a_500` FAILED with
`autotester.providers.base.ProviderError: mock provider has no queued response for role=agent`
propagating uncaught out of the route — the exact pre-fix failure mode. Confirmed the fix (already
in the live tree) makes the same test pass (913/913 in the full run above). The sabotage extract
was deleted after use.

## Exception-shape check (C2)

`providers/mock.py::_next` raises `ProviderError` on an empty response queue — the same class
`providers/gemini.py` raises at lines 107 (`GEMINI_API_KEY` unset), 109 (missing schema), 123
(wrapped SDK exception), 128 (unparsed response), and 144 (schema-validation failure). The test's
"starved queue" reproduces the identical exception type and the identical catch site
(`routes_learn.py:223 except ProviderError as exc`) that production hits — not a look-alike
exception that happens to also be caught.

## Partial-write safety (C3)

Read `stages/expand.py::expand`/`expand_flow`: both build and return a plain `list[Case]`
(`cases: list[Case] = []` / `cases.extend(...)` / `cases = [_happy_case(...)]` + `.append(...)`),
never a generator. An exception raised mid-loop inside `expand_flow` propagates before `expand`
returns anything to the caller, so `generate_cases`'s `for case in cases: store.add_case(case)`
structurally cannot run on a partial result — confirmed by reading the code, not assumed from the
type annotation alone. Live-browser run below independently confirms zero `cases.jsonl` writes.

## The live-browser gap — found a way to close it (C4)

The manifest disclosed a genuine limitation for the *maker's* black-box approach, but it is not the
hardest limit available. `LangChainFallbackProvider._default_chain()` (`providers/langchain_fallback.py`)
adds an `ollama` tier whenever `OLLAMA_BASE_URL` is set, with **no code change and no in-process
monkeypatching** — it's already-available config surface. Started a real `uvicorn` with
`OLLAMA_BASE_URL=http://127.0.0.1:1` (unreachable/uninstalled tier) against an approved scratch
FlowSpec. `provider.available()` is `True` (chain non-empty) so the route passes every gate check,
then the actual model call fails for real — `ollama: ModuleNotFoundError: No module named
'langchain_ollama'` — reaching the exact `except ProviderError` catch live, in a running server
process, driven by a real browser click. This is the identical failure *shape* AT-264 describes
(a `ProviderError` from an "available" provider, raised after the gates pass), reached without
monkeypatching. The manifest's own reproduction technique (pytest sabotage) is not invalidated —
it independently pins the exception-class/code-path identity (C2) that this live path doesn't need
to re-prove — but the "cannot be driven live" framing was too strong, and the contract has been
amended (see below) to record how it can be.

## Mode D — live browser (own instrument)

The shared Playwright MCP browser's Chrome profile was actively locked (`LOCK` files under
`Default/`, recently modified — a concurrent session, not a stale lock) — I did not force it, since
killing another session's browser is disruptive and unnecessary. Instead launched an independent
`playwright.chromium` instance directly from the project's own venv (`playwright` package already
installed) against my own `uvicorn` on port 8091, `AUTOTESTER_ROOT` set to a proper Windows-style
absolute scratch path (not `/d/autoTesting` — the WSL-style bug the maker hit), with a real
onboarded project + APPROVED FlowSpec built via `ProjectStore` (same as the CLI/UI would).

7/7 interactions passed:
1. Open `/projects/checkerdemo/flowspec` — 200, correct title.
2. Generate-cases button visible (flowspec is approved).
3. **Click** Generate with the `OLLAMA_BASE_URL` trick active → themed 400 page, title "The model
   could not complete this — AutoTester", `Internal Server Error` absent.
4. Onward link ("Check the provider's credentials") present in the DOM.
5. `/projects/checkerdemo/requests` still renders (no regression).
6. `/projects/checkerdemo/flowspec` approve form still present (no regression to the gate).
7. Console errors: 1, and it is the page's own intentional HTTP 400 navigation response — not a JS
   defect (same pattern the maker's evidence for the sibling no-provider path already found).

Confirmed on disk: `projects/checkerdemo/cases.jsonl` does not exist in the scratch root after the
failed generate — zero cases written, live, not just under pytest.

Evidence: `qa/evidence/browser-at264-generate-error-boundary-2026-09-09-checker/report.json`.
Server stopped after the run (port 8091 confirmed free of LISTENING sockets).

## Secret-leak check (C6)

Read every `raise ProviderError(...)` site in `providers/gemini.py` (lines ~107, 109, 123, 128, 144,
plus the `ValidationError` wrap) and `providers/langchain_fallback.py` (`_call`/`_try_tier`). None
interpolates a raw API key, `.env` value, or full prompt text into the message: `_unparsed_reason`
reports only a `finish_reason` label; the schema-mismatch branch reports `ValidationError`'s own
text (field names/types, not values from a secret-bearing prompt, since X5's prompt design never
asks the model to echo a real credential); the `langchain_fallback` fallback message wraps
`type(exc).__name__: exc` from the underlying SDK exception (e.g., a connection or import error) —
confirmed live: the actual interpolated string was `ModuleNotFoundError: No module named
'langchain_ollama'`, nothing sensitive. `f"Generating cases failed partway through: {exc}"` in
`routes_learn.py:226` is safe on every code path checked.

## Contract amendment

`qa/contracts/expand.md` X6 previously named only three refusal paths on this route. Amended
in-place to add the fourth (`ProviderError` raised mid-generation, AT-264) plus the structural
reason it holds (`expand()` returns a materialized list), and appended an amendment-log entry.
Routine, non-weakening — adds detail, softens nothing. `qa/contracts/ui.md`'s U-criteria don't
claim generate refusals are themed (that's expand.md's X6 job per ui.md's own "Deliberately not
claimed here" note), so no change needed there.

## Ledger

`AT-264` flipped `open → fixed` with a `checker_note` citing this verdict and the sabotage/live
evidence. No new issues filed — everything probed held.

```
VERDICT: PASS
SCOREBOARD: 4/4 U/X criteria evidenced (X6 amended+met, U1-U9 unaffected/untouched by this unit), 0 invariants violated
LIVE-BROWSER: qa/evidence/browser-at264-generate-error-boundary-2026-09-09-checker/report.json
ISSUES-WRITTEN: none (AT-264 flipped open -> fixed)
EXPLANATION: Sabotage-confirmed the fix in a git-archive extract (never the live tree), verified expand() returns a materialized list so no partial write is possible, and closed the manifest's own disclosed live-browser gap by finding an env-var-only way (OLLAMA_BASE_URL) to drive the exact mid-generation ProviderError live through an independently-launched Chromium instance -- zero regressions on sibling routes, zero cases.jsonl writes, no secret leakage in the exception message. Contract amended to name the fourth refusal path.
```
