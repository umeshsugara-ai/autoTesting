# Verdict — business-truth campaign (AutoTester judged against its own business goal)

**Date:** 2026-09-09
**Bound to:** `d:/autoTesting`
**Cycle checked:** 1
**Dispatched by:** Umesh, directly — *"jo features banate gaye hain unke edge to edge sab test and
validate karna in visible browser … tester ko pehle business logic samajhna hota hai … maker
development point of view se banata hai, tester ko business requirement ke point of view se validate
karna hota hai."*

**This is not a Mode A unit check.** There is no manifest, and no unit was submitted. It is a
business-goal audit plus the first Mode D live-browser validation this repo has ever had. It judges
the **product against the north star**, not units against contracts — because the contracts encode
what the maker built, and the instruction was to check what the business needs.

---

```
VERDICT: FAIL
SCOREBOARD: 4/10 business requirements met, 3 partial, 3 not met (14 findings: 6 high, 6 medium, 2 low)
FAILURES:
- [BR-2] sev: high · stages/expand.py::expand — the repo's own "differentiator" — has zero
  production callers; no user can generate a case from a FlowSpec · give it a CLI command and a
  UI action · issue: AT-239
- [BR-5] sev: high · the self-extension loop is dead code: diff_coverage/request_for/add_request
  are called only from tests, so a VideoRequest can never be produced and the product never "asks
  for a video" · wire coverage into the run and crawl paths · issue: AT-240
- [BR-1] sev: high · cold start dead end: a newly onboarded product's only route to runnable is
  hand-writing cases; no UI path to add a recording, review a FlowSpec, or generate cases ·
  surface ingest + review + expand in the UI · issue: AT-241
- [BR-0/BR-8] sev: high · a crawl that learned nothing reports status "completed" (1 screen, 0
  actions, 3 refusals, 3.4s on an unseen login-gated product) · add a terminal state that means
  "could not act", and escalate instead of succeeding · issue: AT-242
- [BR-7] sev: high · Mode D has never run here: 86 verdicts, zero LIVE-BROWSER lines, qa/evidence/
  absent — every UI-touching PASS was granted without independent browser validation · re-check
  UI units live · issue: AT-243
- [BR-1] sev: medium · clicking a UI button returns a raw JSON 403 instructing a non-technical
  operator to run a CLI command · themed refusal page with an in-UI grant route · issue: AT-244
- [BR-8] sev: medium · /projects/{slug}/runs/{unknown} returns 200 and renders "Run nonexistent —
  No case results in this run yet", fabricating a pending run · 404 · issue: AT-245
- [BR-10] sev: medium · the UI hardcodes CrawlBounds(); the operator cannot set the blast radius
  of an outward-facing run · expose bounds before starting · issue: AT-247
- [core] sev: medium · AT-229's evidence misattributes this campaign's artifacts to `uv run
  pytest`; two checker sessions shared one worktree · re-verify or withdraw · issue: AT-249
LIVE-BROWSER: qa/evidence/browser-business-truth-2026-09-09-checker/report.json
ISSUES-WRITTEN: AT-239 .. AT-252 (14 rows)
EXPLANATION: The harness is fully green — 818 tests pass, ruff clean, doctor clean — while the two
stages the product's own promise rests on (EXPAND and COVERAGE) are unreachable by any user, and an
operator onboarding a new product cannot get past a hand-written case form. Every contract criterion
was met and every unit PASSed; the product still does not do the job the north star describes. That
is the maker-drift Umesh named, and it was invisible to a checker reading contracts.
```

---

## What was measured, not asserted

**Baseline (re-run by me, not read from a manifest):** `uv run pytest -q` → 818 passed, 2 skipped ·
`uv run ruff check src tests scripts` → clean · `uv run autotester doctor` → clean.

**The ruler.** Business requirements were derived from the north star, `.goal/goal.json`, and Umesh's
own words in the `reason` field of the feature ledger — not from `qa/contracts/`.

| BR | Requirement | Result |
|---|---|---|
| BR-0 | Works on any web product, not the ones it was built against | **Partial** — onboarding an unseen product works; learning it does not |
| BR-1 | An operator reaches a report without the CLI | **Not met** — AT-241, AT-244 |
| BR-2 | Cases cover best / worst / edge | **Not met** — AT-239, the generator is unreachable |
| BR-3 | Runs happen in a real visible browser | **Met** — headed by default, verified live |
| BR-4 | A new feature cannot silently break an old one | **Partial** — regression proof exists; not re-run this pass |
| BR-5 | Asks for a video on an unknown screen | **Not met** — AT-240, the code is dead |
| BR-6 | Credentials never leak | **Met** — no `.env` value appears in any rendered page |
| BR-7 | Verdicts are trustworthy | **Partial** — the grader is independent, but AT-243 |
| BR-8 | The report tells a human what is broken | **Partial** — crawl table honest; AT-242, AT-245 |
| BR-9 | Beats a human tester, measurably | **Not assessed** — t136-scorer was mid-fix and left alone |
| BR-10 | Refuses safely | **Met, with a gap** — refusals correct; AT-247 |

## What genuinely holds (stated because a FAIL verdict is not a verdict on everything)

The consent gate is real and well built: it refused an unapproved crawl, then refused a crawl whose
bounds exceeded the grant, naming the exact bound that failed. Path traversal, encoded traversal, an
XSS payload as a slug, a null byte and a case-variant slug are all refused; no raw `<script>` is
reflected; no probe produced a 500. The crawler's safety refusals are correct — it declined to type
into unnamed inputs and declined to click a form-submit control under `read_only`. `src/` is almost
entirely free of product-specific coupling: every `pathlynks`/`vidysea`/`erp` hit is a docstring, not
logic. The one real exception is `stages/issues.py::ISSUE_COLUMNS`, hardcoded to Vidysea's 13-column
sheet — defensible for T-136's comparison, but not configurable for a second customer.

## The shape of the failure

`T-135 — "coverage/merge/expand loops reconnected"` is already **pending**, so the maker knows those
stages are disconnected. Yet `docs/FEATURES.jsonl` still lists F-012 (expand, "the differentiator")
and F-013 (coverage) as **live**, and `.goal/goal.json` still marks T-070 and T-090 **done** on
checker PASSes. The unit was built and tested; the wire was never run to a user. Nothing in the
maker-checker loop reads "can a person reach this?", so a feature can be simultaneously
contract-complete, test-covered, PASSed, ledger-live — and inert.

## Reopen-power applied

Per Umesh's instruction (reopen UI-touching units, file the rest), scoped to what was directly
disproved live rather than to everything unvalidated:

- **T-100 (`ui/`) → must be reopened to `pending`.** Its own acceptance note is *"full onboarding →
  report without touching the CLI."* Driven in a real browser, that is false: a newly onboarded
  product cannot be made runnable without hand-authoring cases, and the one automated learning button
  returns a raw JSON 403 naming a CLI command.
  **The flip is handed to the maker rather than performed here, deliberately.** `goal_cli.py` exposes
  no `reopen` subcommand, so the only route is editing `.goal/goal.json` — which a concurrent maker
  session was actively writing throughout this campaign (it committed `2c00dea`, `b5c4610`, `5cba7bb`
  while this ran). Racing it risks destroying its work, which is a worse outcome than a late flip.
  This is a stated obligation, not a silent omission.
- T-070 and T-090 are **not** reopened — they are not UI units, and T-135 already carries the
  reconnection work. They are filed as AT-239 / AT-240 with the ledger-accuracy problem named.

## Second tranche — the measured consequence (added same session)

Driving the report page surfaced the number that makes AT-239 concrete rather than theoretical.

- **AT-250 (high)** — across **all four projects AutoTester holds 52 cases, 50 of them class `happy`**. The only two that are not (`auth_wrong_creds`, `input_empty` on pathlynks) were hand-written by `scripts/run_pathlynks_first_cases.py` for T-050. **No case in any project
  was generated.** F-012 claims a login flow yields 14 cases across 14 applicable `CaseClass`es;
  the shipped system has produced zero outside a test fixture. A product whose north star is
  "best / worst / edge" is running a 96% happy-path suite.
- **AT-251 (medium)** — the report's headline `Total runs 45` counts an onboarding session and a
  crawl as runs; both also appear in Run history as rows reading "no verdicts", so a crawl is
  presented as a test run that produced nothing.
- **AT-252 (medium)** — `Overall pass rate 69%` is the lifetime average across 43 re-runs of an
  unchanged 3-case login suite (many early INCONCLUSIVEs being the since-fixed AT-044/AT-049
  grading bugs). It reads as "69% of Pathlynks passes". It is not a product-health metric.

Credit where due on the same page: F-027's informativeness fix genuinely holds — the overview,
scoreboard and per-run breakdown are present and the FAIL/INCONCLUSIVE/"no verdicts" rows are
reported honestly rather than smoothed away.

**Revised scoreboard: 4/10 business requirements met, 3 partial, 3 not met — 14 findings
(6 high, 6 medium, 2 low).** BR-2 moves from "not met" to "not met, and quantified": the
generator has never produced a case.

## Not tested, stated rather than hidden

Video ingest end-to-end on an unseen product · report readability at scale · regression + bench
re-proof · Phase 3 recall/FP against `ERP_Issues_Trainers.xlsx` — the `t136-scorer` unit was being
fixed by a concurrent maker session throughout this campaign and was left alone by agreement; it has
since PASSed cycle 2 (commit `2c00dea`) and is now available to check.
