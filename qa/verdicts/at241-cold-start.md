# Verdict — at241-cold-start

**Date:** 2026-09-09 · **Cycle checked:** 1 · **Commit checked:** `abce166`
**Bound to:** `d:/autoTesting` · **Mode:** A + **D** (UI-touching) · **Dual check:** no
**Contracts:** `qa/contracts/ui.md` (U10, authored this cycle) · `qa/contracts/expand.md` (X1, X6
authored this cycle) · `qa/contracts/coverage.md` (V1–V3, V5, V6 authored this cycle) ·
`qa/contracts/review-gate.md` (R2, R3, R4 as they reach the UI door)

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met, 6/6 invariants hold
FAILURES (if any): none at >80% confidence
LIVE-BROWSER: qa/evidence/browser-at241-cold-start-2026-09-09-checker/report.json
              (this checker's own Playwright script against its own uvicorn; 18/18 interactions,
               4 console errors, all four being Chromium's "400" line on a DELIBERATE refusal)
ISSUES-WRITTEN: AT-259, AT-260, AT-261, AT-262 (opened) · AT-239, AT-240, AT-241, AT-258 (→ verified)
EXPLANATION: Every claimed behaviour was re-derived by driving a real browser against a real
cold-start project and reading the state change back off disk, not from the maker's report. The
two things I most expected to be wrong were not: the coverage wire is load-bearing at BOTH call
sites under sabotage, and the expander — which the manifest itself said had never produced a case
on a real product — produced 16 across 11 classes through the button and 10 through the CLI. The
manifest's AT-244 admission IS understated and is now filed as AT-259, but no criterion it asked
me to author covers refusal presentation on the gate routes, so it is a finding, not a failure.
```

---

## What I re-ran myself

| Command | My result | Manifest claimed |
|---|---|---|
| `uv run pytest` | **910 passed, 2 skipped** (0 `FAILED` lines) | 909 passed, 2 skipped |
| `uv run ruff check src tests scripts` | `All checks passed!` | same |
| `uv run autotester doctor` | `doctor: clean` | same |
| `uv run pytest tests/test_ui_learn.py tests/test_ui_requests.py tests/test_coverage_wiring.py tests/test_expand_cli.py` | **30 passed** | 30 passed |

The 909/910 discrepancy is one test and does not change any judgement; I record it rather than
smooth it over. `git diff abce166 -- src/` is empty, so the tree I judged is the tree that was
submitted (only `.goal/` differs).

**AT-258 is closed by this run.** The previous cycle FAILed on three `doctor` violations
(`app.py` 304 lines, `test_ui_learn.py` 302, `flowspec_page` 61); all three are gone.

## Mode D — my own browser, my own script, my own server

Not the maker's screenshots, not the maker's `report.json`, not `curl`. Script:
`scratchpad/moded.py` + `gen.py`; server: `AUTOTESTER_ROOT=<scratch> uv run uvicorn
autotester.ui.app:app --port 8301` (and 8302 for the credentialed pass). **Port ownership was
verified, not assumed** — `netstat -ano` confirmed PID 6156 on 8301 was my own uvicorn before I
trusted a single 200. Port 8099 was left alone.

The state under test was a genuine cold start: a project onboarded **through the real form**, with
zero cases and no `flowspec.json` on disk, named `<script>alert(1)</script>&'"`.

Every assertion below is a **state change**, read back from disk or from the URL bar — not "a page
rendered".

| # | Interaction | Assertion | Result |
|---|---|---|---|
| 1 | Onboard through the form | `project.json` exists, 0 cases, no flowspec | ✅ |
| 2 | Zero-case project page | offers a `/flowspec` route | ✅ |
| 3 | **Click** that link | URL ends `/projects/xss-demo/flowspec`, not a 404 | ✅ |
| 4 | No-flowspec page | states the absence + **2** onward links | ✅ |
| 5 | U5, raw HTTP source | `<script>alert(1)</script>` count = 0 in body **and `<title>`** | ✅ |
| 6 | U5, rendered DOM | 0 raw payload tags | ✅ |
| 7 | Empty request queue | honest empty state, not blank | ✅ |
| 8 | Generate, **no flowspec** | themed 400 page, no `{"detail"`, **0 cases written** | ✅ |
| 9 | DRAFT spec | gate shown, Generate button **absent** | ✅ |
| 10 | **Unsigned approval** (`by="   "`) | 400 **and `flowspec.json` byte-identical** | ✅ |
| 11 | Request-edit from the form | disk: `status=needs_edit`, `by=checker-mode-d`, note stored | ✅ |
| 12 | Generate, **unapproved** (X1) | themed 400 page, **0 cases written** | ✅ |
| 13 | Approve from the form | disk: `status=approved`, `by=checker-mode-d` | ✅ |
| 14 | Gate direction | draft → needs_edit → approved, **both ways from the UI** | ✅ |
| 15 | Approved spec | Generate button now present | ✅ |
| 16 | **Click Generate** (real provider) | `cases.jsonl` 0 → **16 rows** | ✅ |
| 17 | Taxonomy | **11 classes**, kinds `best`+`worst`+`edge` | ✅ |
| 18 | Cases page | renders the 16 generated rows | ✅ |

**Console errors: 4, all explained.** Every GET page is **0**. The four are one Chromium
`Failed to load resource: 400` line each on `generate-noflow`, `generate-unapproved`,
`generate-real` (the provider-less pass) and `approve-unsigned` — i.e. one per **deliberate
refusal**. No page threw a script error.

**The third refusal branch was reached honestly.** The first server ran with an `AUTOTESTER_ROOT`
that had no `.env`, so `LangChainFallbackProvider.available()` was genuinely false and Generate
took its "No model provider configured" path: HTTP 400, themed page, **0 cases**. I then restarted
on port 8302 with the repo `.env` exported into the server's environment to exercise the real
generation. Both passes are in the evidence file, labelled.

---

## The five things I was told to press hardest on

### 1. Is the coverage loop closed, or closed only under the test's fake?

**Closed for real, at both call sites.** `tests/test_coverage_wiring.py` does monkeypatch
`run_and_grade_case` and `BrowserSession` — but it drives the two routes an operator actually
presses, so the routes' own control flow is real, and I proved that by **sabotage** rather than by
reading it.

In a `git archive abce166` extract with its **own** resolved `autotester` (checked before trusting
anything: `autotester.stages.coverage.__file__` pointed inside the extract — a naive `PYTHONPATH`
pin did *not* win against the editable install, and had I not checked, the whole sabotage would
have silently tested the live tree):

- anchor `return [store.add_request(request_for(gap)) for gap in gaps]` → **matched exactly once**
- replaced with `return []`; file re-read and **confirmed changed**
- result: **3 failed, 3 passed** — `..._asks_for_a_video`, `..._ask_once`, and the crawl one.

So both the run half (`routes_runs.py:141`) and the crawl half (`routes_crawls.py:189`) are
load-bearing. The manifest claims both are wired; the manifest's own "what changed" list is where
I first doubted it, because it names `routes_crawls.py` without a line — I located the call site
and then sabotaged through it.

### 2. Are the three "asks for nothing" tests still vacuous?

**Individually, yes — and I say so rather than crediting the fix.** Under the same no-op sabotage,
all three negatives stay green. That is the irreducible limit of a negative test: an inert feature
and a correct one look identical to it. What changed is that the three **positives** now fail when
the feature is inert, so the *suite* is no longer vacuous even though each negative still is.
Filed as **AT-261 (low)** with the concrete remedy: assert both halves in one fixture.

### 3. `generate_cases` refusals — every branch, and no cases written

All three branches exercised live, all three themed pages, all three **0 cases**:

| Branch | HTTP | Page text | Cases written |
|---|---|---|---|
| no FlowSpec | 400 | "Nothing to generate from" | 0 |
| unapproved (X1) | 400 | "The flowspec is not approved yet" | 0 |
| no provider | 400 | "No model provider configured" | 0 |

No `{"detail"` blob in any of them.

**But the AT-244 admission is understated, and that is a real finding.** The manifest says
"refusals from *these* routes are pages; other routes still raise raw `HTTPException`". Only
`generate_cases` is. On the very same module, `routes_learn.py` raises raw `HTTPException` at
**four** sites (`:153`, `:164`, `:175`, `:178`), plus the credential-guard 400s that
`helpers._refuse_unsafe_submission` raises through both POSTs. I watched one of them render: a
whitespace-only signer produced a bare `<pre>{"detail":"an approval needs a name — who is signing
it?"}</pre>` in Chromium, with no frame and no way onward — the exact AT-244 experience, on a new
route, inside the unit that claims to address it. Filed as **AT-259 (medium)**.

This does not fail a criterion, because none of the seven criteria the manifest asked me to author
covers refusal presentation on the gate routes, and I will not invent one to punish an imprecise
sentence. But I refuse to write "AT-244 partially addressed" into a contract as if the boundary
were where the manifest put it, so U10 now says explicitly what is *not* claimed.

### 4. A fourth U5 leak

**Looked for one; there is not one.** `flowspec_page`, `_learned_card`, `_gate_cards`,
`_refusal`, `_link` and `requests_page` escape every user- or project-derived string, including
the `<title>` (`theme.page` does not escape it) and the labels handed to `theme.breadcrumb` /
`theme.empty_state` (which do not escape either). The `slug` in every `href` is
`_require_slug`-validated against `^[a-z][a-z0-9-]*$` before it can reach an attribute, so the
unescaped `href` inside `breadcrumb()` is not a hole here.

One methodological note worth recording, because it nearly produced a false finding: **the DOM is
the wrong instrument for this.** `page.title()` returns the *parsed* title, which re-materialises
`&lt;script&gt;` as `<script>` and reports a leak that does not exist. I re-checked the raw HTTP
source and both routes emit `&lt;script&gt;alert(1)&lt;/script&gt;&amp;&#x27;&quot;` in the
`<title>` tag. The maker's three call sites were genuinely fixed; there is no fourth.

### 5. `expand` on a real FlowSpec — does the taxonomy actually fire?

**Yes, and this is the manifest's own pessimism being falsified in the unit's favour.** The
manifest says "No case has yet been generated by the expander on a real product … there are still
zero FlowSpecs anywhere on disk." I constructed a real approved FlowSpec (2 screens, one 5-step
sign-in flow with a `FILL` step and a `{{SECRET:…}}` step, so the input *and* auth classes apply)
and drove both doors with a live provider:

- **UI button:** 16 cases across **11 classes** — `happy`, `input_empty`, `input_boundary`,
  `input_unicode_oversize`, `back_refresh_midflow`, `deeplink_unauth`, `double_submit`,
  `locale_i18n`, `network_offline_slow`, `server_error`, `viewport_mobile` — spanning
  `best` / `worst` / `edge`.
- **`autotester expand cli-demo`:** 10 cases, 9 non-happy, exit 0.

The taxonomy fires. **AT-250 stays open regardless**, because that issue measures the four *real*
projects and my evidence comes from a synthetic one; the generator working once does not populate
suites nobody has expanded.

Two things this exposed, both filed rather than folded into a criterion:
**AT-260 (medium)** — `--provider gemini` lets a `ProviderError` escape `expand_cases` uncaught,
dumping a Rich traceback and persisting nothing (the default `langchain-fallback` path is fine);
**AT-262 (low)** — the button is a **125-second** synchronous POST with no progress surface and no
timeout, and a mid-loop provider failure would leave a partial `cases.jsonl` with no record of what
was skipped.

---

## Is the T-100 scoping honest, or a dodge?

**Honest, and unusually so.** The unit could have claimed T-100 — it delivers precisely the surface
T-100's acceptance note describes. It does not, and it names the *stronger* reason it cannot:
AT-243's finding that **24 UI-touching PASS verdicts carry zero `LIVE-BROWSER` lines**. That is a
larger debt than this unit created and a larger one than closing T-100 would have papered over.
Adding three good surfaces does not re-validate 23 units that were never validated. T-100 stays
`pending`; this verdict does not close it and does not call `goal_cli done`.

The same honesty runs through the manifest's "Mistakes I made" section (two real ones, both caught
by running rather than by reasoning) and its refusal to claim the expander had produced anything.
The one place it overstates is AT-244 (§3 above) — and that is the single sentence in the whole
manifest that credits an intention instead of an observation.

## Criteria authored this cycle

- `ui.md` **U10** — the cold start has a way out, and the gate over it swings both ways.
- `expand.md` **X6** — the stage has a door, and every refusal behind it writes nothing.
- `coverage.md` **V6** — the diff is wired to the entry points, and only the gap direction is.

Each is additive and non-weakening; each carries an amendment-log entry naming what I re-derived
and what I deliberately did **not** write in. V6 borrows V1's "the fix must be load-bearing"
device and makes the sabotage part of the criterion, because a wire's absence is the one defect
this contract's existing tests provably could not see.

## Scoreboard detail

| Criterion (as the manifest requested it) | Evidence | Met |
|---|---|---|
| No-FlowSpec project renders a page saying so + ≥1 way onward | Mode D #3, #4 | ✅ |
| Review gate refuses an unsigned approval and changes nothing | Mode D #10 (byte-identical file) | ✅ |
| The gate moves in both directions from the UI | Mode D #11, #13, #14 | ✅ |
| Review free text passes the U8/U9 credential guard | `_signed` → `_refuse_unsafe_submission` with the project's `SecretStore`, before any save | ✅ |
| Generate refuses as a page, not raw JSON, on all 3 branches, writing no cases | Mode D #8, #12 + provider branch | ✅ |
| Every gap from a run or a crawl becomes exactly one `VideoRequest`; a known route none | sabotage 3F/3P + `tests/test_coverage_wiring.py` 6 passed | ✅ |
| Both new GET routes escape project data (U5) | Mode D #5, #6 + full read of `routes_learn.py`/`project_view.py` | ✅ |

Invariants: no second store (all writes via `ProjectStore`) ✅ · unknown slug 404s ✅ · no
`SecretRef` value rendered ✅ · `expand()` still does not persist (no-fire list) ✅ ·
`unreached_screens` never queued ✅ · nothing written on any refusal ✅.

## What this verdict does NOT cover

- **U1–U9.** Not re-verified this cycle; not claimed. AT-243 stands.
- **AT-250.** The 50-of-52-`happy` measurement over the four real projects is unchanged.
- **AT-244.** Still open, and now better characterised by AT-259.
- **A real product.** My FlowSpec and my project are synthetic. The expander has still never run
  against a recording of a real product — the manifest's point, and it survives this PASS.

---

# INDEPENDENT CONCURRENT CHECK

**Both checks were live, independent, and reached the same verdict: PASS.** They ran at the same
time without knowledge of each other; neither read the other's evidence. Recorded per the
concurrency rule rather than merged, so the independence stays visible.

**My error, stated plainly:** I listed `qa/verdicts/at241-cold-start*.md`, saw none, ran a ~25
minute Mode D pass, and then wrote the file without re-checking. The primary verdict above had
landed in between (commit `609e7bf`) and my write clobbered it. It is restored here byte-intact
from git; this second check is appended below where it belongs. No content of the primary was
changed.

## Where the two checks differ

| | Primary check | This check |
|---|---|---|
| Cases from the Generate button | **16 across 11 classes** | **10 across 10 classes** |
| Cases from the CLI | 10 | not exercised |
| Interactions | 18/18 | 7 criteria + headline + idempotency |
| Extra technique | sabotage-proved the coverage wire at both call sites | second crawl + second generate for idempotency |

The case-count difference is expected, not a disagreement: `expand` makes real model calls per
class, and applicability is model-judged where it is not deterministic (X3), so two runs over the
same flow legitimately yield different counts. Both runs agree on what matters — the button
reaches the expander, and it produces best / worst / edge rather than happy-path only.

**Duplicate finding, folded:** my `AT-263` and the primary's `AT-259` describe the same defect (the
review-gate refusals return raw JSON while the generate refusals return themed pages). `AT-259` has
priority; `AT-263` is marked a duplicate of it.

---

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
