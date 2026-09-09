# Reality audit — what is really done, what is not, and what only looks done

**Date:** 2026-09-09 · **Bound to:** `d:/autoTesting` · **By:** the business-truth checker campaign
**Question asked:** *"what all features are really done, what all still remaining, and what all are
really done but not that much validated."*

The ledger's own numbers are **31/45 tasks done (69%)**, **87 verdicts, 86 PASS, 1 FAIL**, and
**39 ledger-live features**. This audit does not trust any of those. It sorts by two harder tests:

1. **Reachability** — is there a production entry point (CLI command or UI route) that calls it?
   A stage nothing calls is inert however well it is tested.
2. **Independent live validation** — did a checker ever drive it in a real browser? Measured:
   **2 of 87 verdicts carry `LIVE-BROWSER:` evidence**, and both are from this campaign.

> ## ⚠ SUPERSEDED IN PART — re-measured later the same day
>
> Sections **2** and **5** below were true when measured (~10:05) and are **no longer current**.
> The maker landed `src/autotester/ui/routes_learn.py` at **10:25** and wired the coverage loop.
> Re-verified by me at ~10:40:
>
> - **AT-239 → fixed.** `autotester expand` exists in the CLI *and* the UI now has
>   `POST /projects/{slug}/cases/generate` (`routes_learn.py:169`).
> - **AT-240 → fixed.** `queue_requests` now has two real production call sites:
>   `ui/routes_runs.py:141` (after a run) and `ui/routes_crawls.py:189` (after a crawl).
>   A `VideoRequest` can be created for the first time.
> - **AT-241 → fixed.** `routes_learn.py` adds the five routes that close the cold start:
>   `GET /flowspec`, `POST /flowspec/approve`, `POST /flowspec/request-edit`,
>   `POST /cases/generate`, `GET /requests` (the video-request queue).
> - **AT-254 → stale.** The tree is green: **909 passed, 2 skipped**; `ruff` clean.
>
> **Still open and unchanged:** AT-253 (the agent fallback is still dead code —
> `run_with_fallback` has no production caller), AT-242, AT-243, AT-250, and the rest.
>
> **These four are `fixed`, NOT `verified`.** No checker has PASSed them, the work is still
> untracked with no manifest, `autotester doctor` is **RED** on 3 design-rule violations, and
> **none of the new UI routes has had Mode D live-browser validation** — which is the exact gap
> this campaign exists to close.


---

## 1. REALLY DONE — reachable, and I verified it myself this session

| Capability | How it was verified |
|---|---|
| **Credential boundary** (F-002) | Scanned every rendered page against real `.env` values: **no secret value appears anywhere**. The three apparent hits are the project's own non-secret `base_url` — the documented AT-078 case. |
| **Consent gates** (T-124) | Clicked Explore with no approval → refused. Granted a deliberately *narrow* grant → refused again, naming the exact bound (`actions 200 > approved 40; wall clock 600.0s > approved 300.0s`). Bounds are checked, not just existence. CN3/CN6 hold. |
| **Explorer safety** (T-142) | Live crawl against an unseen site: declined to type into unnamed inputs, declined to click a form-submit control under `read_only`. Refusals recorded with reasons in `edges.jsonl`. |
| **UI input security** | Path traversal, URL-encoded traversal, an XSS payload as a slug, a null byte and a case-variant slug all refused (404/400). No raw `<script>` reflected. No probe produced a 500. AT-035's fix holds. |
| **Bounded BFS crawl** (T-143) | Ran headed against a product it had never seen; bounds, screen identity and artifacts all produced correctly. |
| **Report informativeness** (F-027) | Overview, scoreboard and per-run breakdown present; FAIL / INCONCLUSIVE / "no verdicts" reported honestly rather than smoothed. |
| **Product-agnostic core** | `src/` is essentially free of product coupling — every `pathlynks`/`vidysea`/`erp` hit is a docstring. One real exception: `stages/issues.py::ISSUE_COLUMNS` is hardcoded to Vidysea's 13-column sheet. |

Also reachable and exercised, though not re-proven by me this pass: `execute`, `grade`,
`review` (CLI), `manual_login`, `report_export`, `media_prep`, `crawl_report`, `explore_merge`,
`ingest`, `analyze_video`, `score`.

---

## 2. LOOKS DONE, ISN'T — the dangerous bucket

These are marked **done** in `.goal/goal.json`, **live** in `docs/FEATURES.jsonl`, and carry a
**checker PASS** — and no user can reach them.

| Claimed | Reality | Issue |
|---|---|---|
| **EXPAND** — T-070 done, F-012 live, called *"the differentiator"* | Zero production callers until this session. An `autotester expand` CLI command now exists but is **uncommitted and unchecked**; there is still **no UI route**. | AT-239 |
| **COVERAGE / "asks for a video"** — T-090 done, F-013 live | `diff_coverage`, `request_for` and now `queue_requests` all have **zero production callers**. No `VideoRequest` has ever been created. The product's self-extension promise has never once happened. | AT-240 |
| **AGENT FALLBACK** — stated as the execution model in `ARCHITECTURE.md:87-90` | `run_with_fallback` is imported only by `tests/test_agent_loop.py`. The sentence *"the agent only pays for new or broken cases"* describes behaviour that cannot occur. | AT-253 |
| **best / worst / edge generation** — the north star | **52 cases across all four projects, 50 of them class `happy`.** Only two are not, and both were hand-written by a script for T-050. **No case was ever generated.** | AT-250 |
| **T-100 (`ui/`) — done**, acceptance note *"full onboarding → report without touching the CLI"* | Disproved live: a newly onboarded product's only route to runnable is hand-writing cases. **T-100 must be reopened to `pending`.** | AT-241 |
| **Crawl on an unseen product — "completed"** | 1 screen, 0 actions, 3 refusals, 3.4s. A zero-learning crawl is indistinguishable by status from an exhaustive one. | AT-242 |

**The pattern is the finding, not any instance.** Three separate headline capabilities are
built, tested, contract-complete, checker-PASSed, ledger-live — and inert. Nothing in the
maker-checker loop ever asks *"can a person reach this?"*

---

## 3. DONE BUT THINLY VALIDATED

- **85 of 87 verdicts were granted without the live-browser validation the checker's own Mode D
  requires** (AT-243). Every UI feature was PASSed on code reading and the maker's own screenshots.
  `qa/evidence/` did not exist before this campaign. Since it was filed, `t136-scorer` has become
  the second verdict to carry `LIVE-BROWSER:` evidence.
- **The report's headline numbers are wrong**: `Total runs 45` counts an onboarding session and a
  crawl as runs (AT-251); `Overall pass rate 69%` is a lifetime average over 43 re-runs of an
  unchanged 3-case login suite and reads as product health (AT-252).
- **BR-9 (beats a human tester) is unmeasured by me.** Commit `99ea27d` claims *"a model watched a
  real recording — the first real number"*, landed after my last pass. Unverified here.
- **The repo's own top risk is still open**: AT-218, *vacuous guards* — countermeasures that cannot
  fail — unchanged across three sweeps, with the maker self-catching 0 of 23.

---

## 4. GENUINELY REMAINING — 14 pending tasks

**High:** T-122 (ERP login — blocked on an open credential gate) · T-134 (Track A5: product map,
journeys, issues and sources pages) · T-136 (Track A acceptance: real recall/FP numbers) ·
T-145 (live read-only crawl of the real ERP) · T-125 (test catalog) · T-151, T-153, T-154 (Track C).

**Normal:** T-123 (medium-issue batch) · T-135 (**coverage/merge/expand loops reconnected** — the
fix for bucket 2) · T-126 (governance debt, ledger backfill) · T-150, T-152, T-155 (Track C).

**Track C — testing an AI application rather than a screen — is entirely unbuilt** (T-150…T-155,
six tasks). `qa/contracts/ai-target.md` and `adversarial.md` do not exist.

---

## 5. STATE OF THE TREE RIGHT NOW

An earlier maker dispatch was **interrupted mid-TDD** and left uncommitted work:

- **Landed and working:** `autotester expand` CLI command; a `.env` bootstrap for the CLI (AT-228).
- **Written but unwired:** `stages/coverage.py::queue_requests` — still zero production callers, so
  **AT-240 is not closed; the dead end moved one layer up.**
- **Red:** 18 failing tests in `tests/test_coverage_wiring.py` (3) and `tests/test_ui_learn.py` (15),
  describing UI routes (flowspec review page, Generate-cases button, video-request queue) that do
  not exist. All four test files are untracked, with no manifest and no fix cycle (AT-254).

That is a legitimate mid-TDD state, but it is unowned. It needs finishing or parking behind an
xfail tied to a unit id, or the next session will read a red suite as a regression.

---

## Bottom line

The **plumbing is real and mostly well built** — safety, consent, credentials, the browser, the
grader, the crawler. What is missing is the **middle of the pipeline actually being connected to a
human**: the product can run test cases, and it cannot yet produce them, ask for what it needs, or
repair a broken one. `INGEST → EXPAND → EXECUTE → GRADE → REPORT + COVERAGE` is drawn in
`ARCHITECTURE.md` as a closed loop; on disk, EXPAND, COVERAGE and the agent fallback are not
attached to anything a person can start.
