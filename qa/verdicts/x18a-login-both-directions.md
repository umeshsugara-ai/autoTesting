# Verdict — x18a-login-both-directions

**Checker:** Mode A unit check, fresh context, no builder reasoning.
**Date:** 2026-09-17. **Cycle checked:** 1 (matches manifest's `Fix cycle: 1 of max 3`).
**Bound root:** `D:\autoTesting\.work\wave-x18a-login` (worktree of `d:/autoTesting`,
branch `wave/x18a-login-both-directions`, build commit `e70bb2c`, base `c8be82b`).
**Contract:** `qa/contracts/explore.md` X18(a) (amended below) + X1-X17 (re-verified
byte-unchanged where touched) · `qa/contracts/core-invariants.md` C1, C2, C7, C10.
**Manifest:** `qa/manifests/x18a-login-both-directions.md`, Status `ready-for-check`.

## What I re-ran myself

1. **Targeted verify suite** (manifest's own command):
   `uv run pytest tests/test_explore_login_wall.py tests/test_explore_login_spa_live.py
   tests/test_crawl_status_surfaces.py tests/test_explore.py
   tests/test_explore_bounds_last_node.py tests/test_ui_crawl_login.py -p no:cacheprovider
   -o addopts= -q` → **61 passed, 1 warning in 88.21s** (matches the manifest's claim).
2. `uv run ruff check src tests scripts` → **All checks passed!**
3. `uv run autotester doctor` → **doctor: clean**
4. **Full suite** (manifest's command, re-run independently, in the background):
   `uv run pytest -p no:cacheprovider -o addopts= -q -rx --deselect
   tests/test_crawl_inventory_live.py` → **1421 passed, 2 skipped, 2 deselected, 32 xfailed,
   1 warning in 504.43s — zero failures.** The manifest's own run had reported 1 failure in
   `tests/test_mutation_check.py` under the full suite's resource pressure, self-diagnosed as
   an environmental flake (consistent with C7's documented AT-196 precedent: a false FAIL under
   load, never a false PASS). My independent re-run is fully green, confirming that diagnosis.

## Diff scope (step 4c)

`git diff c8be82b...e70bb2c --stat` touches exactly the 7 files the manifest's "What changed"
names: `qa/manifests/x18a-login-both-directions.md`, `src/autotester/stages/explore.py`,
`src/autotester/stages/explore_node.py`, `src/autotester/stages/explore_status.py`,
`tests/fixtures/spa_login_site/index.html`, `tests/test_explore_login_spa_live.py`,
`tests/test_explore_login_wall.py`. No function, class, export, test, or config key is deleted
or renamed; the diff was read in full. Clean.

## Capability coverage (step 4b) — reproduced in a throwaway copy

Built `git archive e70bb2c | tar -x` into the scratchpad, removed `projects/erp`,
`projects/pathlynks`, `projects/vidysea-erp`, ran `uv sync`, confirmed
`autotester.__file__` resolves inside the copy. All three rows reproduced, each restored
byte-identical to the bound tree (diffed) before the next edit — never editing the bound tree:

| capability | check | anchor count | before | after |
|---|---|---|---|---|
| sticky wrong-password banner still LOGIN_FAILED (AT-467) | `test_a_sticky_wrong_password_banner_is_still_login_failed` | 1 | 1 passed in 0.28s | `assert <CrawlStatus.COMPLETED> is <CrawlStatus.LOGIN_FAILED>` — exact match to manifest |
| unobservable login page never silently unqualified (AT-474) | `test_a_login_page_that_cannot_be_observed_is_not_an_unqualified_success` | 1 | 1 passed in 0.29s | `assert 'login not judged' in 'frontier empty'` — exact match to manifest |
| fallback control: dashboard with no matching fields stays COMPLETED (AT-462) | `test_a_dashboard_sharing_the_login_url_without_login_fields_is_not_login_failed` | 1 | 1 passed in 0.06s | `assert <CrawlStatus.LOGIN_FAILED> is <CrawlStatus.COMPLETED>` — exact match to manifest |

Each edit was single-hunk, single-file (`explore_status.py`, named in the manifest's "What
changed"), anchor-count-asserted `== 1` before applying. **CAPABILITY-COVERAGE: 3/3 reproduced.**

**C7 mutation-duty check on the two additional new/rewritten tests not given their own row**
(`test_a_partial_fill_target_match_falls_back_to_signature_only` and the live-browser sticky
test): re-applied row 3's edit (`fill_targets <= selectors` → `bool(fill_targets) and
bool(selectors)`) and ran the whole `test_explore_login_wall.py` file — it kills BOTH
`test_a_dashboard_sharing_the_login_url_without_login_fields_is_not_login_failed` AND
`test_a_partial_fill_target_match_falls_back_to_signature_only` (2 failed, 14 passed),
corroborating the manifest's claim that these ride on the same already-isolated clause. Not
separately mutated for the live test given the underlying logic is identical and already
isolated by row 1; transitively adequate.

## Two hunts from the dispatch, both run against the UNMODIFIED code (no falsification needed)

**Over-report: does the not-judged qualifier fire on a crawl that DID get past login?** Yes,
confirmed directly: `terminal_status(nodes=[<node at a different url_template>],
login_observe_error="...")` returns `(COMPLETED, "... -- login not judged: could not observe
the login page (...)")` even though `never_left_login` already resolved conclusively (via a
plain `url_template` mismatch, needing no signature) that the crawl left the login page. This
is the exact scenario the manifest's own "Known limits" section discloses and
`test_a_login_page_that_cannot_be_observed_is_not_an_unqualified_success` pins as intended
behaviour — status stays correctly `COMPLETED`, only the `stop_reason` text carries an extra,
technically-imprecise qualifier. Judged: **accept as a disclosed, tested, defensible trade**
(never hide a precheck failure), now stated explicitly in the amended X18(a) rather than left
to prose. Not a FAILURE.

**Fill-target over-fire: does a dashboard sharing the login url with a coincidentally-matching
selector get misclassified as LOGIN_FAILED?** Yes, confirmed directly against the unmodified
`_still_login`: a node at the login's `url_template`, a genuinely different signature and
content, but exposing one element with `selector="#email"` (the login case's sole FILL
target) is classified `LOGIN_FAILED`. This directly falsifies the manifest's prose claim ("a
genuinely different screen that merely shares the login's url ... is never caught by this
fallback") as a blanket statement — the formal capability-coverage row (AT-462 control) only
proved the narrower "no fields present" case, which remains true. Judged: **real, undisclosed
gap** — contract amended to drop the blanket claim, state the true narrower one, and record
the gap as a new Known OPEN gap + ledger issue (below). Not blocking this unit's PASS: the
formal, scoped capability-coverage claim was true and verified; the fix is a strict net
improvement over the prior state (no fallback at all); the gap is narrow (requires an SPA
screen that reuses the login's exact FILL-target selectors) and now disclosed, matching this
contract's own established pattern for tracked-not-blocking residuals (X6's Obliterate gap,
X16's AT-105/AT-121-124).

## Contract maintenance (I am the sole writer)

Adopted the manifest's proposed X18(a) wording with **two corrections**, both routine
tightening, neither softening anything: (i) dropped the falsified blanket "never caught by
this fallback" sentence, kept the true narrower claim, and added the Known OPEN gap above as
**ISS-x18a-1**; (ii) stated the not-judged qualifier's intentional over-firing explicitly in
the criterion. Full diff and reasoning in `qa/contracts/explore.md`'s amendment log, dated
2026-09-17. X1-X17 re-verified byte-unchanged (X1: `run_case` still one call site in
`_bootstrap_login`; X2/X10: `grep fill|select_option|upload` and `grep .page.` over the diff
return nothing relevant; X16's tool-failure counting still holds for the new EVIDENCE issue).

## Issues addressed (step 5)

- **AT-474** (`qa/issues.jsonl`, currently `status: open`) — genuinely fixed and independently
  verified (capability-coverage row 2, Mode D console-clean run). **Recommend: open → fixed.**
- **AT-467** — the manifest's claimed issue, referenced in `qa/verdicts/at458-...md` and
  `qa/QUEUE.md`, but **it was never appended to `qa/issues.jsonl` as a formal row** (checked:
  `python` scan of the ledger for `id == "AT-467"` returns zero rows). This is a ledger-hygiene
  gap already tracked as **AT-475** (uncommitted ledger hunks lost across sessions), not
  something this unit can close in the ledger. The underlying defect AT-467 named — a sticky
  wrong-password banner reading `COMPLETED` — is independently verified fixed regardless
  (capability-coverage row 1).

## Live browser (Mode D, step 5b — required, this unit touches crawl status on the crawl page,
crawls table, and report)

Drove my own headless Chromium (the `playwright` MCP was unavailable — connection failure —
so a standalone `uv run python` Playwright script was used, per the dispatch's fallback
instruction). Served `tests/fixtures/spa_login_site` from the isolated throwaway copy,
launched the real UI (`uvicorn autotester.ui.app:app`) against an isolated `AUTOTESTER_ROOT`,
created a synthetic project (`base_url` = the fixture + `?sticky=1`), a wrong-password login
case and a correct-password login case, declared each in turn through the real Crawls page
form, and started a crawl through the real "Explore now" button (small explicit bounds:
`max_screens=5, max_actions=10, wall_clock_s=25, max_depth=3`, to keep a real in-process crawl
fast and bounded).

**First attempt hung ~20 minutes** (near-zero CPU, no crawl ever landing on disk) — root-caused
to `subprocess.PIPE` on the UI server's stdout filling the OS pipe buffer with uvicorn's
request-access logs while nothing drained it, blocking the server's response thread. Verified
by process inspection (`Get-CimInstance Win32_Process`, CPU time ~0.64s of the 21 minutes
elapsed) before killing the stuck processes (confirmed by command line first) and fixing the
script: stdout redirected to a real log file, small bounds, and the whole run wrapped in a
280s hard `timeout`. The re-run completed cleanly in seconds. A second leftover `uvicorn.exe`
was found after that run too (Windows detaches `uv run uvicorn`'s actual process from the
`subprocess.Popen` handle, so `.terminate()` didn't reach it) — confirmed by command line
(`--port 57999`, under the throwaway copy's own path) and killed. No process from either
attempt remains (swept and confirmed after).

**Result**, re-verified with an exact `<tr>...</tr>` parse against the persisted crawl data
(not a substring heuristic — an earlier looser check briefly flagged a false "wrong badge"
from an 800-char window bleeding into the adjacent row; re-parsed properly and resolved, both
row HTML strings pasted in the evidence file):

- **Wrong password:** crawl page and crawls-table row both read `login_failed`, badge class
  `badge-blocked` (warning tone). `stop_reason`: "the login case ran, but every screen reached
  was still the login page (/index.html) -- check the login case's steps and the credentials
  it uses." 2 screens, 1 denied, 1 issue, 0 tool failures. 0 console errors.
- **Correct password (control):** crawl page and crawls-table row both read `completed`,
  badge class `badge-pass` (positive tone). `stop_reason`: "frontier empty." 1 screen, 0
  denied, 0 issues, 0 tool failures. 0 console errors.

Evidence: `qa/evidence/browser-x18a-login-both-directions-2026-09-17-checker/report.json`
(includes the exact `<tr>` HTML for both rows and the full incident note above).

## New issues

```json
{"id": "ISS-x18a-1", "date": "2026-09-17", "severity": "medium", "feature": "explore", "type": "logic-gap", "status": "open", "found_by": "checker-unit", "title": "X18(a)'s fill-target fallback can misclassify a genuinely different post-login screen as LOGIN_FAILED when it coincidentally reuses every one of the login case's FILL-target selectors", "evidence": "src/autotester/stages/explore_status.py:94-100 `_still_login` -- checker built a ScreenNode sharing the login's url_template, a different signature and different content, with one element selector='#email' (the sole FILL target); terminal_status() on the unmodified code returned CrawlStatus.LOGIN_FAILED. No falsification needed. The AT-462 control test only proves the 'no fields present' case.", "expected": "A genuinely different screen (different signature, different content) sharing the login's url_template is never classified LOGIN_FAILED purely because it happens to reuse the login form's FILL-target selectors -- e.g. require the fallback to also see the login form's own submit control, or to also reproduce the observed signature's element count. See qa/contracts/explore.md X18(a) Known OPEN gap for options.", "fixed_date": null, "verified_date": null}
```

## Verdict block

```
VERDICT: PASS
SCOREBOARD: X18(a) [amended] met · X1,X2,X10 (unaffected surfaces) hold · C1/C2/C7/C10 hold
FAILURES (if any):
- none at >80% confidence. ISS-x18a-1 (medium) is a real, checker-found gap but is disclosed,
  narrow, and does not regress any existing guarantee -- tracked, not blocking (see "Two hunts").
CAPABILITY-COVERAGE: 3/3 reproduced (rows verified in an isolated throwaway copy, never editing
the bound tree); the two additional new/rewritten tests confirmed to ride on the same isolated
clause via row 3's mutation.
LIVE-BROWSER: qa/evidence/browser-x18a-login-both-directions-2026-09-17-checker/report.json
ISSUES-WRITTEN: ISS-x18a-1
EXPLANATION: AT-474 is genuinely fixed and independently re-verified (capability row 2 + Mode D
console-clean run); AT-467's underlying defect (sticky wrong-password banner reading COMPLETED)
is independently re-verified fixed, though AT-467 itself was never a formal ledger row (tracked
under the existing AT-475 ledger-hygiene gap, not this unit's to close). The manifest's proposed
X18(a) wording contained one falsified overclaim (fixed via amendment, gap disclosed as
ISS-x18a-1) and one disclosed, defensible over-report trade (accepted, now stated explicitly).
Full suite, targeted suite, ruff and doctor all green on independent re-run; diff scope clean;
Mode D live-browser check confirms both directions on the actual product UI with zero console
errors, after recovering from and documenting a stuck first attempt (root-caused, fixed, and the
orphaned processes killed and verified gone).
```
