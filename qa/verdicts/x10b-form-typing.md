# Verdict — x10b-form-typing (cycle 3, LAST cycle)

**Checked by:** /checker (Mode A, fix-cycle recheck cycle 3, fresh context, no builder reasoning)
**Date:** 2026-09-22
**Project root (bound):** `D:\autoTesting` — every path read/written resolves inside it.
**Contract:** `qa/contracts/explore.md` — X10 as amended to X10-b, X5's typing column, X12,
X6/X5 unchanged rows, X7, V7b (full criterion set re-judged, not only the three open issues).
**Manifest:** `qa/manifests/x10b-form-typing.md` — `Status: ready-for-check`, **Fix cycle 3 of
max 3**. Dual check: no. Issues addressed per manifest: AT-532, AT-533, AT-534, AT-535 (+
cycle-3: AT-533, AT-536, AT-537).

**Cycle checked: 3**

## What I re-ran myself (whole output, not piped)

| Command | My result |
|---|---|
| `uv run pytest tests/test_explore_typing.py tests/test_explore_typing_guards.py tests/test_explore_consent.py tests/test_ui_crawls.py tests/test_ui_crawl_approval.py tests/test_ui_crawl_login.py` | **46 passed** in 79.44s (re-run: 90.70s) — matches the manifest's "46 passed". `test_ui_crawl_login` contributes **10 passed, 0 errors** (at HEAD's seam it reads 7 passed + 3 setup ERRORs — verified by stash-restore in BOTH directions, so the retarget is the cause of the fix, not a coincidence). |
| `uv run pytest tests/test_explore.py tests/test_explore_safety.py tests/test_crawl_coverage.py` | **97 passed** (19 + 67 + 11). |
| `uv run ruff check src tests scripts` | `All checks passed!` (twice) |
| `uv run autotester doctor` | `doctor: clean` (twice — REAL this time: `tests/test_ui_crawls.py` is 206 lines, `test_ui_crawl_approval.py` 138; no file over the 300 cap anywhere among the unit's files). |
| adapter slot-1: `uv run pytest` (FULL suite, the instrument `qa/adapter.json` actually names) | **3 failed, 1511 passed, 5 skipped, 32 xfailed** in 722.67s — exit 1. The 3 failures are exactly `tests/test_approve_cli.py::{test_approve_writes_a_row_that_covers_the_cli_defaults, test_an_approval_narrower_than_the_run_still_refuses, test_the_grant_and_the_runtime_agree_on_every_expiry_they_accept}`, each dying at **ImportError: cannot import name 'require_consent' from 'autotester.stages.explore'** (lines 63, 78, 164). This file is UNTOUCHED by the unit's diff; it passes 10/10 with `explore.py` reverted to HEAD (stash-restore verified). The unit retargeted three sibling files of the same seam but missed this fourth one. Filed as **AT-539**. |
| extra regression sweep (my own) | test_explore_merge + test_explore_login_wall* + test_explore_login_bypass + test_crawl_coverage_bounds + test_consent + test_coverage_wiring + test_crawl_real_cli + test_actuator_chokepoint = **94 passed**; test_browser + test_browser_navigation_secrets + test_secrets = **50 passed**; test_explore_live = **8 passed**; test_crawl_report + test_ui = **18 passed**; test_crawl_real_cli again = **7 passed**. X18/X16 surfaces (explore_status.py, schema/, crawl_coverage.py, explore_merge.py, explore_safety.py) are untouched by this cycle's diff (`git diff HEAD --name-only` over those paths: empty). |

## Independent probes (my own code, `.work/checker_x10b_c3_*.py`)

### AT-533 — per-node cap binds the typing pre-pass itself — **FIXED, verified both directions**
- **Structural check (read):** `type_form`'s loop now carries
  `if typed >= rt.bounds.per_node_action_cap: return typed` BEFORE each fill/select
  (`src/autotester/stages/explore_typing.py:99-100`), ahead of the candidate filter — the
  cap is checked per iteration regardless of how many fillable fields the node has. The
  click loop's share (`tried + typed >= cap`, `explore_node.py:222`) is unchanged from cycle 2.
- **My stress probe** (`.work/checker_x10b_c3_probeCap.py`, the exact shape the cycle-2 verdict
  demanded — 5 fillable fields on the settings seed, `per_node_action_cap=2`, typing ON):
  **performed = 2** (`_tried`), fills = 2, clicks = 0.
- **Sabotage both directions:** replacing `type_form` with the same loop minus the cap check
  reproduces the cycle-2 defect shape EXACTLY — **performed = 5** — and restoring the check
  returns it to 2. The check is structural and load-bearing; the shipped 2-field pin
  (`test_typing_and_clicking_share_one_per_node_budget`, asserts `_tried(seed) <= 2`) is green
  and its fixture's weakness no longer matters because the bound lives in the loop.

### AT-536 — honest verify outputs + seam retarget + file split — **FIXED (its three named sub-items)**
- `tests/test_ui_crawls.py` split is **lossless**: HEAD's 18 tests = working tree's 13 +
  `test_ui_crawl_approval.py`'s 5, no test lost and none invented (set-diff verified);
  both files 206 and 138 lines; the 5 consent-approval tests are present in the new file
  and all pass; **doctor: clean reproduced twice** (my byte counts, not the manifest's claim).
- `tests/test_ui_crawl_login.py:84` retargeted to `explore_consent.require_consent`:
  10/10 green now vs 7 passed + 3 setup ERRORS at HEAD's seam — both directions re-measured
  by stashing/restoring the file.
- Manifest pasted outputs now match my runs: 46 passed (×2 reproduced), 10 passed for the
  typing file (incl. the ~55s real-Chromium proof), ruff clean, doctor clean. One cosmetic
  inaccuracy survives: the manifest says the typing test file is "219/300"; my byte count is
  222 (still comfortably under the cap — noted, not a failure).

### AT-537 — real-browser proof restored — **FIXED**
- `test_a_real_browser_types_and_submits_the_filled_form` is back in
  `tests/test_explore_typing.py:171` and is **verbatim-identical to `0e225a5`** — the
  whole-file diff against 0e225a5 contains docstring mojibake (pre-existing `—`/`…`
  characters double-encoded) and one duplicated comment banner, and **zero code-line
  differences**; all 10 test functions from the cycle-1 file are present, none lost.
- My own run: `uv run pytest tests/test_explore_typing.py` → **10 passed**; the proof test
  alone → **1 passed in 55.35s** (real headless Chromium inside the suite run, as the
  dispatch expected ~40s). The contract's load-bearing sentence
  (explore.md:624-629) is true again: the suite pins that Playwright actually types and the
  submit carries the synthetic value.

### Regression re-judgement (the full criterion set, fix cycles can regress)
- **AT-532 (typed action's X7 host re-check) — HOLDS.** My isolated probe
  (`.work/checker_x10b_c3_probeTrap.py`): crawl seeded AT `/trap` so the home page's `a.ext`
  link path is unreachable and any off_domain_refused edge can only come from the typed
  action — result: `fill/off_domain_refused` with reason
  `"host 'evil.test' is outside allowed domains ['app.test']"`, one `NAVIGATION` issue, and
  **zero** `evil.test` nodes (`_type_one` re-checks the host after settle,
  explore_typing.py:57-61).
- **AT-534 (denial records) — HOLDS.** Probe case A: under READ_ONLY,
  `DENIED_POLICY`/`TYPING_DISABLED` edges for `input.displayname` and `select.grade`; neither
  appears in `page.clicks`; coverage hole reads `policy:typing disabled under this policy
  (X10-b)` (inside V7b's closed `policy:*` prefix form); `_tried` counts the denials as 0.
- **AT-535 (condition 3, non-production target) — HOLDS.** Probe cases B/C: typing ON +
  `production: true` approval → `ApprovalRequired` naming the approval id
  (explore_consent.py:42-49, before the browser opens); the SAME production approval still
  covers an ordinary READ_ONLY run; a `production: false` approval covers typing; both
  pre-flights (cli_crawl.py:33-34, routes_crawls.py:231-233) pass `SafetyPolicy`.
- **X6/X5 unchanged (never-click + deny-list under TEST_ACCOUNT with typing ON) — HOLD.**
  Probe case D: `a.out` denied with `never-click pattern (logout/sign-out)`;
  `button.del` never clicked; `DEFAULT_NEVER_CLICK_PATTERNS` module-baseline check unchanged
  (explore_safety.py:103-105).
- **X10 base (nothing typed outside X10-b) — HOLDS.** Flag-off under TEST_ACCOUNT probe:
  zero fills, zero selects. Default `SafetyPolicy()` keeps `synthetic_typing=False`
  (schema/crawl.py:89-96).
- **X10-b condition 1/2/4 — HOLD.** Gate = `typing_allowed` only
  (explore_safety.py:36-41); values from `synthetic_values.py` — sha256-keyed, no
  clock/randomness/provider (synthetic_values.py imports only hashlib); password-named
  fields refused by `typing_target_allowed`, combobox reads real options through
  `session.first_option` (browser/session.py:191-201), uploads never touched.
- **X12 (no provider in the stage) — HOLDS.** `run_crawl` takes no provider; the pre-pass
  and consent seam import no provider; values are DOM-derived only.
- **X1 (E5 intact) — HOLDS.** One `run_case` call site in `explore.py`, inside
  `_bootstrap_login` (explore.py:109, function spans 90-129); `execute.py`/`execute.md`
  absent from the diff.
- **X2 (browser/ chokepoint) — HOLDS.** No playwright import outside `browser/`; no
  `.page.` access in any stage; the pre-pass composes
  `rt.session.fill/select_option/first_option`.
- **X10 verify-grep (verbatim):** `.fill(`/`.select_option(`/`.upload(` call sites in
  `stages/explore*.py` exist ONLY in `explore_typing.py` (46, 49) — no other module imports
  or re-implements typing (`explore_consent.py`, `explore_return.py` are pure plumbing).
- **X4/X16/X18 surfaces untouched:** the cycle-3 diff does not touch `explore_status.py`,
  `schema/`, `crawl_coverage.py`, `explore_merge.py`, or `explore_safety.py`; the X18
  login-wall suites (29 tests) and coverage-bounds suites are green.
- **doctor/MAP freshness:** the unit's diff adds `stages/explore_consent.py`; `docs/MAP.md`
  carries its row; I regenerated `autotester map` and the file is byte-stable (the row was
  already present and correct).

## NEW finding this cycle (the one FAIL line)

**[X17-adjacent / adapter slot-1 / AT-539] sev: medium · the AT-535/AT-536 seam extraction
(`require_consent` → `stages/explore_consent.py`) left a FOURTH unretargeted import site —
`tests/test_approve_cli.py:63, :78, :164` still import `autotester.stages.explore.
require_consent`, so its 3 consent-runtime tests FAIL at ImportError and the adapter's
slot-1 verify (`uv run pytest`, expected exit 0) exits 1: 3 failed, 1511 passed, 5 skipped,
32 xfailed. The file is untouched by this unit's diff and passed 10/10 with `explore.py`
reverted to HEAD — the break is the unit's cycle-2 seam move, not a pre-existing defect. The
unit retargeted three sibling files of exactly this class; a `rg "from
autotester.stages.explore import require_consent" tests/` sweep — the same sweep the AT-536
fix required — finds this fourth one. The criteria's own verify sentences do not name this
file and every contract criterion is evidenced; what fails is the project's own instrument
(`qa/adapter.json` slot-1), which a checker must re-run, not the maker's narrower list ·
fix direction: three one-line import retargets (`from
autotester.stages.explore_consent import require_consent`, the same shape already shipped in
`test_crawl_real_cli.py:131`) — then `uv run pytest` exits 0 · issue: AT-539 (new, open)**

Everything the cycle-2 verdict charged is fixed and re-verified; the only red is this
sibling seam the maker never knew about because no check before this one ran the full suite.

## Per-criterion judgements (FULL set re-judged)

| Criterion | Judgement |
|---|---|
| X1 (E5 intact, one `run_case` site in `_bootstrap_login`) | **MET** |
| X2 (browser/ chokepoint) | **MET** |
| X5 matrix (unchanged rows + typing column) | **MET** — deny-list and never-click still ON under TEST_ACCOUNT+typing-ON (probe D) |
| X6 (never-click at every policy; unnamed skipped+counted) | **MET** |
| X7 (host re-checked after EVERY action, typed included) | **MET** — isolated typed-path probe refuses + files NAVIGATION issue + creates no evil node |
| X10 base (nothing typed outside X10-b) | **MET** — READ_ONLY and flag-off probes produce zero fills/selects |
| X10-b condition 1 (widening policy + explicit flag) | **MET** |
| X10-b condition 2 (synthetic deterministic values only) | **MET** — sha256-keyed, no clock/randomness |
| X10-b condition 3 (non-production target) | **MET** — all three consent directions re-probed |
| X10-b condition 4 (non-destructive; X6/X5 unchanged) | **MET** |
| X10-b first-class actions (bounds bind typing) | **MET** — pre-pass cap check structural; 5-field/cap-2 probe = 2; sabotage = 5 |
| X10-b "click loop still runs after the pre-pass" | **MET** |
| X12 (no provider in the stage) | **MET** |
| V7b (refused typing recorded as `policy:typing disabled`, never clicked) | **MET** — closed reason set unchanged |
| Manifest verify claims (46 / 97 / ruff / doctor) | **MET as claimed** — all four reproduce (minor "219/300" vs 222 noted) |
| AT-537 pin (10-test file incl. real-Chromium proof) | **MET** — 10 passed, proof 55.35s |
| adapter slot-1 `uv run pytest` exit 0 | **NOT MET** — 3 failed (test_approve_cli.py import seam, AT-539) |
| (untouched surfaces) X3, X8, X9, X11, X13-X18 | **NOT RE-JUDGED** — zero diff lines over identity/dialogs/noise/artifacts/merge/status this cycle; 94 + 50 + 18 + 29 regression tests over those surfaces green |

SCOREBOARD: 16/17 criteria met, invariants (E5 intact, X6 never-click) 2/2 hold.

## FAILURES

- **[adapter slot-1 / AT-539] sev: medium · `tests/test_approve_cli.py` imports the removed
  `explore.require_consent` at lines 63/78/164 — 3 tests fail at ImportError, `uv run pytest`
  exits 1 (3 failed, 1511 passed, 5 skipped, 32 xfailed, reproduced once full-suite after
  the targeted batteries); the unit's diff never touches the file, and reverting `explore.py`
  to HEAD makes it 10/10 green, so the break is this unit's seam move · fix direction: three
  one-line retargets to `explore_consent.require_consent` · issue: AT-539 (new, open)**

## Issues

ISSUES-WRITTEN: **AT-539** (new, open — fourth unretargeted seam in test_approve_cli.py);
ledger statuses flipped on my own cycle-3 evidence: **AT-533 open → fixed** (structural cap
check + sabotage-both-directions probe), **AT-536 open → fixed** (split lossless + login
retarget + honest counts; residual of its class filed as AT-539), **AT-537 open → fixed**
(restored verbatim + green); AT-532/AT-534/AT-535 checker_notes updated with cycle-3
re-verification.

## Mode D (live browser) disposition

The unit's changed paths are `src/autotester/{schema,stages,browser}` + two pre-flight
callers + test files — no UI surface of our own app, so Mode D as a driven check of our own
UI stays not-applicable. The contract's load-bearing REAL-browser proof is restored IN THE
SUITE (AT-537) and I re-ran it myself in this cycle's 10-passed run (1 passed in 55.35s, real
headless Chromium, submit carries the synthetic value in the GET url) — the maker's pin and
my own execution coincide. Prior checker-driven live evidence remains at
`qa/evidence/browser-x10b-form-typing-2026-09-22-checker/report.json` (cycle 2).

LIVE-BROWSER: qa/evidence/browser-x10b-form-typing-2026-09-22-checker/report.json + this cycle's in-suite re-run of test_a_real_browser_types_and_submits_the_filled_form (1 passed, 55.35s) (changed paths had no UI surface of our own)

## EXPLANATION

All three cycle-2 verdict failures are genuinely, provably fixed on my own executed evidence:
AT-533's cap check now lives inside `type_form`'s loop and my 5-field/cap-2 stress probe
performs 2 typed actions where removing the check reproduces 5 exactly (the cycle-2 defect
shape); AT-536's file split is lossless with doctor clean reproduced twice and the login-file
seam retargeted (10/10 vs the 7-passed-3-errors shape I reproduced at HEAD by stash-restore);
AT-537's real-browser proof is restored verbatim from 0e225a5 and runs green. Every
regression the cycle-2 verdict verified holds on fresh probes — AT-532's typed X7 re-check,
AT-534's denial records, AT-535's production refusal, X6/X5 under typing-ON, X10 base, X1,
X2, X12. What keeps this from PASS is one new finding outside every previously-run set: the
full-suite run the adapter's own slot-1 demands exposed that the same seam extraction broke
a fourth file (`tests/test_approve_cli.py`, 3 ImportError failures, `uv run pytest` exit 1).
The contract's criteria are all met and the manifest's own verify commands all reproduce —
but the project's verify instrument is red, and a checker that PASses a unit with a red
instrument is not verifying anything. This is cycle 3 of 3 (last), so the unit is terminal:
AT-539 carries the three one-line retargets for a follow-on unit; no production code is
involved and the consent runtime itself is correct (probe D).

VERDICT: FAIL