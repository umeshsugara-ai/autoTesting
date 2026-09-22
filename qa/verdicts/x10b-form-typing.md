# Verdict — x10b-form-typing (cycle 2)

**Checked by:** /checker (Mode A, fix-cycle recheck, fresh context, no builder reasoning)
**Date:** 2026-09-22
**Project root (bound):** `D:\autoTesting`
**Contract:** `qa/contracts/explore.md` — X10 as amended to X10-b, X5's typing column, X12,
X6/X5 unchanged-rows, X7, V7b.
**Manifest:** `qa/manifests/x10b-form-typing.md` — `Status: ready-for-check`, **Fix cycle 2 of
max 3**. Dual check: no. Issues addressed per manifest: AT-532, AT-533, AT-534, AT-535.

**Cycle checked: 2**

## What I re-ran myself

| Command | My result |
|---|---|
| `uv run pytest tests/test_explore_typing.py tests/test_explore_typing_guards.py tests/test_explore_consent.py` | **15 passed** in ~2s — the manifest claims **"16 passed"**; `--collect-only` counts **15** tests in those three files. The claimed count does not reproduce. (The 16th test the manifest counts was the real-browser proof the cycle-2 diff **deleted** — see the FAILURES section.) |
| `uv run pytest tests/test_explore.py tests/test_explore_safety.py tests/test_crawl_coverage.py` | **97 passed** |
| extra regression sweep: test_explore + test_explore_safety + test_crawl_coverage + test_crawl_coverage_bounds + test_consent + test_crawl_real_cli + test_coverage_wiring + test_actuator_chokepoint + test_browser + test_browser_navigation_secrets + test_secrets + test_crawl_report | **203 passed** |
| extra: test_explore_live (real browser) | **8 passed** |
| extra: test_ui_crawl_login (real browser) | 24 passed, **3 ERRORS at setup** — `monkeypatch.setattr("autotester.stages.explore.require_consent", …)` raises `AttributeError: module 'autotester.stages.explore' has no attribute 'require_consent'` (the seam was moved to `explore_consent.py` and **this test file was not retargeted**; `test_ui_crawls.py` and `test_coverage_wiring.py` were) |
| extra: test_explore_merge, test_explore_login_wall*, test_ui_crawls | 15 + 29 + 27 passed |
| `uv run ruff check src tests scripts` | All checks passed! |
| `uv run autotester doctor` | **NOT clean — 1 violation:** `file-too-long: tests\test_ui_crawls.py — 301 lines > 300` (byte-precise count 301; with the file stashed, doctor reads clean, so the violation is introduced by this unit's own 2-line edit to that file). The manifest claims **"doctor: clean"** — false as submitted. |

## Independent probes (my own code, not the maker's pins)

All probe scripts are in `.work/checker_x10b_c2_*.py`; every case runs `run_crawl` against the
`crawl_fake` site and reads the persisted graph from the store.

### AT-532 — typed action's X7 host re-check — **code FIXED, pin WEAK**
- `explore_typing.py::_type_one` now re-checks the host after settle exactly as `try_action`
  does: `check_destination(rt.project, landed)` → on `NavigationRefused`, a `NAVIGATION` issue +
  an `OFF_DOMAIN_REFUSED` edge, and the off-domain node is never created (explore_typing.py:55-61).
- **My load-bearing probe** (`.work/checker_x10b_c2_probeTrap.py` — crawl seeded directly AT
  `/trap`, the only way the fake can reach `input.offdomain`): the fill records
  `OFF_DOMAIN_REFUSED` with reason `"host 'evil.test' is outside allowed domains ['app.test']"`,
  a `NAVIGATION` issue is filed, zero `evil.test` nodes exist. **Sabotage both directions**
  (`.work/checker_x10b_c2_sab532run.py` + `_restore`): with the `check_destination` block
  removed from `_type_one` in an isolated copy, the same probe regresses to the cycle-1 defect
  shape exactly (`fill` → `same_screen`, no issue, no refusal); restored → refused shape again.
  **The fix is real and load-bearing in code.**
- **But the shipped pin is weak:** `tests/test_explore_typing_guards.py::
  test_a_fill_that_lands_off_domain_is_refused_not_explored` asserts only that *some*
  `off_domain_refused` edge exists. No page in `crawl_fake.SITE` links to `/trap`, so the BFS
  never reaches the trap element and **the typed off-domain scenario cannot fire through the
  crawl in that test** — my probe of the exact guard-test setup shows the asserted
  `off_domain_refused` edge comes from the pre-existing seed link `a.ext` (a NAVIGATE refusal on
  X7's *link* path, present since before this unit). Sabotaging `crawl_fake.FILL_TARGETS` to
  `{}` (typed action never auto-submits) leaves the test **green** — verified
  (`.work/_sabotage_532.py`, `-p _sabotage_532` → 1 passed). **A pin that passes with the fix's
  trigger removed does not defend the fix.** The code is right; the test as shipped would not
  catch a regression.

### AT-533 (per-node cap binds typing) — **NOT MET**
- The click loop now shares the budget: `if tried + typed >= rt.bounds.per_node_action_cap: break`
  (explore_node.py:222), and `type_form` returns its typed count into it. The *click* half is
  real.
- **The typing half is not: `type_form` never reads `per_node_action_cap`.** Its only bound is
  the global `max_actions` (explore_typing.py:95). My stress probe
  (`.work/checker_x10b_c2_probeCap3.py`): 5 fillable fields on the settings node,
  `per_node_action_cap=2`, typing ON → **`_tried(settings) = 5`** — five performed typed
  actions on a cap-2 node, 2.5× the bound (exactly the cycle-1 defect shape, still reachable
  whenever a node carries more typing targets than the cap; the shipped cap test passes only
  because the fixture has exactly 2 typing targets and the settings-page fills are never
  registered fillable in the guards' crawl, so `input.displayname`'s fill ERRORS as tried).
- The shared-budget *test* passes (`tried + typed >= cap` is enforced for clicks), but the
  contract sentence "each records an edge … and counts toward `max_actions` and the per-node
  cap" is still measurably false for the pre-pass itself, and the up-to-2× overshoot the issue
  named (typed + clicked on one node) is now bounded only when `typed ≤ cap` — which nothing
  enforces.

### AT-534 (refused typing recorded, never clicked) — **MET**
- Under READ_ONLY (my probe `.work/checker_x10b_cycle2_probe.py` case C): `DENIED_POLICY` edges
  with reason `TYPING_DISABLED` ("typing disabled under this policy (X10-b)") exist for the
  typing targets; the click loop skips them (`typing_target_allowed(el) and not
  typing_allowed(policy)` → continue, explore_node.py:226-227); `page.clicks` never contains
  `input.displayname` or `select.grade`; coverage holes carry
  `policy:typing disabled under this policy (X10-b)` (inside V7b's closed `policy:*` prefix
  form — no set change needed). Flag-OFF under TEST_ACCOUNT behaves identically (denials
  recorded, targets never clicked). Verified also that `_tried` counts a typing denial as 0.
- One deliberate narrowing, correctly scoped: search-role fields are excluded from the denial
  record (`el.role != "search"`, explore_typing.py:130 — gate option (c), settled in cycle 1),
  and the click-loop skip's `typing_target_allowed` includes "search" but `_record_typing_denials`
  does not, so a search field under READ_ONLY is neither typed, denied-as-typing, nor
  double-counted. Consistent.

### AT-535 (condition 3: non-production target enforced) — **MET**
- `stages/explore_consent.py::require_consent(project, store, bounds, policy)` (new module,
  extracted from explore.py at its line cap): a `policy.synthetic_typing` run covered by a
  `production: true` approval raises `ApprovalRequired` naming the approval id
  (explore_consent.py:42-49) BEFORE the browser opens. `run_crawl` always passes the run's
  policy (explore.py:262), and both production pre-flights (cli_crawl.py:33-34,
  routes_crawls.py:231-233) now pass `SafetyPolicy(write_policy=...)` too.
- My probe (case D): typing ON + production approval → refused (message names the approval id);
  the SAME production approval still covers an ordinary READ_ONLY crawl (no raise); dev
  approval (`production: false`) covers typing (no raise). All three directions verified
  directly against `require_consent`, and the shipped `tests/test_explore_consent.py` (3 tests)
  passes. The flag's `production` field is content-addressed (schema/approval.py:44-61), so
  flipping it invalidates the approval id — the enforcement seam is sound.
- Residual (question, not a failure): the pre-flights construct a fresh
  `SafetyPolicy(write_policy=project.write_policy)` with **no** `synthetic_typing` — correct for
  today (no shipped caller sets the flag), so pre-flight can only refuse when someone edits the
  code path to thread a typing policy through; the runtime seam (`run_crawl`'s own policy) is
  the load-bearing one and is enforced.

### Regression / X1, X2, X6, X10-base — **all hold**
- **X1:** `run_case` in `stages/explore.py`: exactly one call site, inside `_bootstrap_login`
  (explore.py:109). `execute.py`/`execute.md` absent from the diff.
- **X2:** no `playwright` import / `.page.` access in any `stages/explore*.py` or
  `explore_consent.py`; typing composes `rt.session.fill/select_option/first_option`.
- **X6:** never-click at every policy — Log out denied under TEST_ACCOUNT+typing-ON in my
  probe (edge `denied_policy 'never-click pattern (logout/sign-out)'`); deny-list still ON
  under TEST_ACCOUNT (button.del denied in the same probe); AT-092 module-baseline check
  unchanged.
- **X10 base / typing-off:** READ_ONLY and flag-OFF crawls perform zero fills/selects (probes +
  97 regression tests + 203-command extended run, all green). Default `SafetyPolicy()` keeps
  `synthetic_typing=False`.
- **X12:** no provider anywhere in the pre-pass or the consent seam; values from
  `synthetic_values.py` (sha256-keyed, no clock/randomness).
- **X10 verify-grep:** fill/select_option call sites in `stages/explore*.py` exist only in
  `explore_typing.py` (46, 49); no other module imports or re-implements typing.

## New findings this cycle (not charged to fix-cycle failures unless listed above)

1. **The contract's load-bearing real-browser proof was DELETED.** The cycle-2 diff removes
   `test_a_real_browser_types_and_submits_the_filled_form` from `tests/test_explore_typing.py`
   (55 lines, `git diff HEAD` shows the deletion; grep confirms zero copies anywhere in
   `tests/`). The contract's own amendment-log entry (explore.md:624-629) names that test as
   part of what is "Load-bearing by construction" for X10-b, and my cycle-1 verdict re-ran it
   green as the unit's Mode-D evidence. The manifest's cycle-2 section does not disclose the
   deletion, and its "16 passed" line matches a file-set that no longer contains it.
   **Re-derivation (Mode D, checker-driven, real headless Chromium against a live-served
   fixture):** my own probe `.work/checker_x10b_c2_live.py` performs the same proof — the
   typing pre-pass fills the fixture's displayname with the synthetic value and the submit
   carries it in the resulting GET url (`/saved.html?displayname=AutoTester+College+810`,
   crawled status `stopped_bound`/`max_screens`, 8 screens, 2 typed edges same_screen).
   Evidence written to
   `qa/evidence/browser-x10b-form-typing-2026-09-22-checker/report.json`. The capability is
   REAL and now independently proven by the checker — but the suite no longer pins it, and the
   contract sentence that names the test is now stale. Removing the proof weakens nothing in
   X10-b's four conditions as written (the criterion's verify is the grep + the guard tests),
   so this is filed as an issue to restore the pin (or a checker-amended criterion naming the
   replacement), severity medium — not a criterion violation this cycle.
2. **`tests/test_ui_crawl_login.py` — 3 tests ERROR at setup** with
   `AttributeError: module 'autotester.stages.explore' has no attribute 'require_consent'`
   (test_ui_crawl_login.py:84 monkeypatches the OLD seam; the maker retargeted
   `test_ui_crawls.py` and `test_coverage_wiring.py` but missed this file). The suite the
   manifest lists does not include this file, so its pasted "200 passed" is honest for what it
   ran — but a shipped test file erroring at collection-adjacent setup is a real regression
   introduced by the seam extraction. Severity medium; one-line fix (retarget the
   monkeypatch to `explore_consent.require_consent` like the other two files).
3. **`doctor` violation — `tests/test_ui_crawls.py` 301/300 lines.** The unit's 2-line
   `**_kwargs` widening pushed it over. The manifest's "doctor: clean" is false as submitted
   (verified: stash the file → doctor clean; restore → 1 violation). Severity low (split by
   responsibility), but a verify-claim that does not reproduce is itself the thing Mode A
   exists to catch.
4. **Manifest count discrepancy:** "16 passed" vs my measured **15** (collect-only). With the
   real-browser proof deleted the count should read 15 — the pasted number matches neither the
   old 10-test file nor the new 15-test set.

## Per-criterion judgements (FULL set re-judged, not only the four failures)

| Criterion | Judgement |
|---|---|
| X1 (E5 intact, one `run_case` site) | **MET** |
| X2 (browser/ chokepoint) | **MET** |
| X5 matrix (unchanged rows + typing column) | **MET** — deny-list and never-click still ON under TEST_ACCOUNT in my probes |
| X6 (never-click at every policy; unnamed skipped+counted) | **MET** |
| X7 (host re-checked after EVERY action, typed included) | **MET in code** — probe + sabotage-both-directions; the shipped pin is weak (does not isolate the typed path) — recorded as a question, not re-failed (the code-level falsification is proven by MY probe) |
| X10 base (nothing typed outside X10-b) | **MET** — READ_ONLY and flag-off probes produce zero fills |
| X10-b condition 1 (widening policy + explicit flag) | **MET** |
| X10-b condition 2 (synthetic deterministic values only) | **MET** |
| X10-b condition 3 (non-production target) | **MET** — `require_consent` refuses production-typed runs; all three directions probed |
| X10-b condition 4 (non-destructive; X6/X5 unchanged) | **MET** — password-named fields refused, uploads never |
| X10-b first-class actions (bounds bind typing) | **HALF MET** — `max_actions` binds; **per-node cap does NOT bind the pre-pass itself** (AT-533 NOT fixed) |
| X10-b "click loop still runs after the pre-pass" | **MET** |
| X12 (no provider in the stage) | **MET** |
| V7b (refused typing recorded as `policy:typing disabled`, never clicked) | **MET** |
| Manifest claim "16 passed" | **NOT MET as claimed** — 15 collected/passed |
| Manifest claim "doctor: clean" | **NOT MET as claimed** — test_ui_crawls.py 301/300 |
| (unchanged surfaces) X3, X4, X8, X9, X11, X13-X18 | **NOT RE-JUDGED this cycle** — the unit's diff touches only the typing/consent/cap surfaces; 203 + 29 + 15 + 27 + 8(live) regression tests over those surfaces all green, and nothing in the diff touches identity, bounds-naming, dialogs, noise, artifacts, merge, or status logic beyond what cycle 1 already verified |

SCOREBOARD: 13/16 criteria met, invariants (E5 intact, X6 never-click) 2/2 hold.

## FAILURES (each defended at >80 % confidence, reproduced by my own probe)

- **[X10-b first-class-actions / AT-533] sev: medium · `type_form` still ignores
  `per_node_action_cap` — explore_typing.py:95 checks only `max_actions`; my stress probe
  (5 fillable fields, cap=2, typing ON) performs **5** typed actions on the settings node
  (`_tried = 5`); the shipped cap test passes only because its fixture has 2 fillable fields
  (of which one fill errors) so the pre-pass never exceeds the cap by accident — the shared
  budget exists only for the CLICK loop's `tried + typed` check, and a 5-field form node
  performs 5 typed + (cap−5→0) clicks, still overshooting the per-screen bound the criterion
  pins · fix direction: `type_form` stops when `typed >= rt.bounds.per_node_action_cap`
  (one-line check in the loop at explore_typing.py:94-96); falsifying test: 5 fillable
  fields, cap=2 → `_tried(settings) ≤ 2` · issue: AT-533 (stays OPEN)**
- **[doctor/manifest honesty] sev: medium · the manifest's cycle-2 verify block claims
  "doctor: clean" and "16 passed" but the working tree yields `file-too-long:
  tests\test_ui_crawls.py — 301 lines > 300` (1 violation, reproduced twice; byte-count 301
  vs 300 at HEAD) and 15 collected tests in the three named files · fix direction: split
  `test_ui_crawls.py` by responsibility (the maker's own AT-460 extract rule), correct the
  manifest's pasted outputs to what is real · issue: AT-536 (new, open)**
- **[X17 seam regression] sev: medium · the `require_consent` extraction to
  `explore_consent.py` broke `tests/test_ui_crawl_login.py` — 3 tests ERROR at setup
  (`AttributeError: module 'autotester.stages.explore' has no attribute
  'require_consent'`, test_ui_crawl_login.py:84); the unit retargeted two sibling files but
  not this one, so three X17-adjacent UI tests cannot even run · fix direction: retarget the
  monkeypatch to `autotester.stages.explore_consent.require_consent` (same one-line shape as
  test_ui_crawls.py:293 and test_coverage_wiring.py:185-186) · issue: AT-536 (new, open)**

Not charged (questions, not failures, each below the 80% bar): whether `_tried` counting an
ERRORED fill as "performed" is the right cap semantics (a timeout spent real time; AT-533's
shared-budget wording is satisfiable either way — the stress probe above does not depend on
it: 5 fills all recorded `same_screen`, no error involved); the guard test for AT-532 not
isolating the typed path (the code is proven by my own sabotage both directions; a weak pin
without a code defect is a question for the next typing-surface unit, and the maker's own
trap fixture is already on disk — a base_url-`/trap` variant of the existing test would pin
it exactly); the deleted real-browser proof is filed as AT-537 below at low-medium
confidence about its contract status (the criterion's verify sentence never named the test;
only the amendment log did), so it is recorded, not charged as a criterion failure.

## Mode D (live browser) disposition

The unit's changed paths are `src/autotester/{schema,stages,browser}` + two pre-flight
callers — no UI surface of our own app; Mode D as a *driven check of our own UI* stays
not-applicable. The contract's load-bearing REAL-browser proof was deleted from the suite, so
**I re-derived it myself**: my own probe (`.work/checker_x10b_c2_live.py`) drove a real
headless Chromium against a live-served fixture site — the typing pre-pass filled
`input[name=displayname]` with the synthetic value and the form's submit carried
`displayname=AutoTester+College+810` in the reached GET url; crawl `stopped_bound`
(`max_screens`, 8 screens), 2 typed edges (same_screen), zero product issues from typing.
Evidence: `qa/evidence/browser-x10b-form-typing-2026-09-22-checker/report.json`.

LIVE-BROWSER: qa/evidence/browser-x10b-form-typing-2026-09-22-checker/report.json (checker-driven real Chromium; changed paths had no UI surface — the live proof replaces the deleted suite pin)

## Issues

ISSUES-WRITTEN: AT-533 (stays open — fix incomplete), AT-536 (new: manifest verify-claims
false — doctor 1 violation + "16 passed" count + unretargeted test_ui_crawl_login seam), and
the ledger statuses of AT-532/AT-534/AT-535 flipped to `fixed` (verified by my own probes this
cycle; a later cycle moves them to `verified`).

Issues addressed per the manifest, reconciled: **AT-532 fixed** (code + my sabotage
both-directions; pin-weakness noted in EXPLANATION, not charged), **AT-534 fixed**, **AT-535
fixed**, **AT-533 NOT fixed** (stays open).

## EXPLANATION

The four verify commands I re-ran are green except `doctor`, and three of the four cycle-1
failures are genuinely, provably fixed — AT-532's host re-check survives my own
sabotage-both-directions in an isolated copy, AT-534's denial records are real and coverage
carries the typing reason, and AT-535's four-condition gate is now 4-of-4 in code with all
three consent directions probed and both production pre-flights passing the policy. The unit
does not earn PASS: AT-533's core defect survives — the typing pre-pass still never reads
`per_node_action_cap`, and my 5-field/cap-2 stress probe measures five performed typed actions
on one node, 2.5× the bound the criterion pins, with the shipped cap test passing only because
its fixture happens to have exactly two fillable fields that error out. On top of that, the
submitted verify claims are not reproducible: doctor reports one real file-too-long violation
(301/300 on `test_ui_crawls.py`, introduced by this unit's own edit), the claimed "16 passed"
is 15 on collection, and the seam extraction broke three shipped UI-login tests the manifest's
regression list never runs. The deleted real-browser proof is independently re-verified by my
own live Chromium run (capability real), but the suite no longer pins it and the manifest does
not disclose the deletion. One more focused cycle: a per-node-cap check inside `type_form`, the
split of `test_ui_crawls.py` plus the one-line monkeypatch retarget in
`test_ui_crawl_login.py`, honest pasted outputs, and a restored (or checker-accepted
replacement) live proof pin.

VERDICT: FAIL