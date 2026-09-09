# Verdict — at241-cold-start

**Date:** 2026-09-09 · **Cycle checked:** 1 · **Bound to:** `d:/autoTesting`
**Commit checked:** `abce166` · **Contract:** `ui.md` (U1–U6, U8/U9), `expand.md` (X1),
`coverage.md` (V1–V3), review-gate R1–R3

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met, invariants hold (X1, X4, V1-V3, U5, U8/U9, R1-R3)
FAILURES: none blocking
LIVE-BROWSER: qa/evidence/browser-at241-cold-start-2026-09-09-checker/report-mode-d-independent.json
ISSUES-WRITTEN: AT-263 (medium, non-blocking — see below)
EXPLANATION: Every criterion was re-derived by me in a real browser against a scratch project with
a DRAFT FlowSpec, so the review gate was exercised rather than bypassed. The unit does the thing it
claims: the cold start is closed. Clicking "Generate cases" on an approved flowspec produced 10
cases across 10 distinct taxonomy classes, and a crawl produced the first VideoRequest this product
has ever created. One real defect found (AT-263) is outside this unit's stated criteria and its own
manifest already scoped AT-244 as "partial", so it is filed rather than failed.
```

---

## What I re-ran myself

`uv run pytest` → **910 passed, 2 skipped** · `uv run ruff check src tests scripts` → clean ·
`uv run autotester doctor` → **clean**. (Doctor was RED on three design-rule violations earlier
today — `ui/app.py` 304 lines, `test_ui_learn.py` 302, `flowspec_page` 61 — and the maker fixed all
three, extracting `ui/project_view.py`. AT-258 is stale as a result.)

## The headline result

**The product generated a test case for the first time.** Before this unit, all four projects held
52 cases of which **50 were `happy`** and **none had been generated** — `stages/expand.py` had no
production caller at all.

I approved the flowspec through the UI, clicked **Generate cases**, and ~120s of real model calls
(provider chain: gemini) produced **10 cases across 10 distinct `CaseClass`es** from a single login
flow:

| Band | Classes produced |
|---|---|
| best | `happy` |
| worst | `auth_wrong_creds` |
| edge | `input_empty`, `input_boundary`, `input_unicode_oversize`, `double_submit`, `back_refresh_midflow`, `network_offline_slow`, `viewport_mobile`, `deeplink_unauth` |

That is literally the north star's *"best / worst / edge"*, from a button a non-technical operator
clicks. A second generate left the count at exactly 10 — content-addressed, idempotent.

**And the self-extension loop fired.** A crawl of `checkerdemo` reached `/`, no screen in the
FlowSpec matched, and exactly one `VideoRequest` was created:
`req_bb8e26317632 — "Record a short video showing the screen/flow at '/'"`. A second crawl left the
count at exactly **1** (V3). This is the first time *"when it meets a screen it does not know, it
asks the human for a video instead of guessing"* has actually happened.

## Criteria, each with the evidence I produced

| | Criterion | Result |
|---|---|---|
| C1 | no-FlowSpec page states so and offers a way onward | **PASS** — 200, offers "Add a recording" (`/sources`) and `/cases/new` |
| C2 | unsigned approval refused, changes nothing | **PASS** — clicked Approve with an empty name → 400; disk still `draft`, `by=None` |
| C3 | the gate moves both ways from the UI | **PASS** — signed approve → `approved`, `by=checker-mode-d`, timestamped, note kept; then request-edit → `needs_edit`, attributed |
| C4 | review free-text goes through the credential guard (U8/U9) | **PASS** — posted the real `GEMINI_API_KEY` value as a note → 400 *"looks like it contains a real credential"*. The value never entered the transcript. |
| C5 | Generate refuses as a **page** with no FlowSpec / unapproved (X1) / no provider, and writes no cases | **PASS** — both refusals are themed HTML (`<!doctype html>`), cases stayed 0 (X4) |
| C6 | every gap → exactly one VideoRequest; V1–V3 | **PASS** — 1 request after two crawls |
| C7 | both new GET routes escape project data (U5) | **PASS** — hostile project name → 0 raw payloads, 2 escaped, **`<title>` escaped too** |

C7 is worth naming: the maker's manifest confessed passing `project.name` raw into three call sites
and being caught by its own U5 probe. I re-ran the hostile probe independently and the fix holds,
including in `<title>`, which `theme.page` does not escape for you.

## The one finding — AT-263 (medium, non-blocking)

**Refusals are inconsistent within the same file.** `generate_cases` uses the `_refusal` helper and
returns a themed page — exactly what AT-244 asked for. The three review-gate refusals do not:

- `POST /flowspec/approve` with no name → `{"detail":"an approval needs a name — who is signing it?"}`
- `POST /flowspec/request-edit` with no name → same raw JSON
- `POST /flowspec/request-edit` with no reason → `{"detail":"say what is wrong, so the next pass can fix it"}`

All three are reached by clicking a button on the very page this unit added, so the AT-244 argument
("a refusal is part of the interface") applies identically. **Not a criterion failure:** the manifest
requires only that the gate *refuses and does not mutate* — which it does — and it scopes AT-244 as
"partial" honestly. Filed, not failed.

## What this unit does not close

- **AT-253 stands.** The agent-fallback execution model in `ARCHITECTURE.md:87-90` is still dead
  code — `run_with_fallback` has no production caller.
- **AT-242 stands.** A crawl that learns nothing still reports `status: completed`; I saw it again
  here (`checkerdemo` crawl, 1 screen).
- **T-100 is not closed by this unit** — its own manifest says so, correctly. This is the first half.
- **AT-250 is now historical, not current.** The generator has produced cases; the 50/52 happy-path
  figure describes the world before this unit.

## Ledger movements

`AT-239`, `AT-240`, `AT-241` → **verified** (re-checked live, not merely reported fixed).
`AT-258` → **verified** (doctor clean). `AT-250` → **fixed** (superseded by this unit's evidence).
`AT-263` → filed **open**.
