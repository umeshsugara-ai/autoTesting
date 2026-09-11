# Verdict — at227-first-paint-modal

**Cycle checked:** 1
**Date:** 2026-09-11
**Checker:** fresh subagent, Mode A + Mode D, no builder context, bound to `D:/autoTesting`.

## What I re-ran myself (never trusted the pasted output)

- `uv run pytest -q` — first run (concurrent with my own manual mutation-check invocations)
  showed one failure, `test_the_sandbox_is_removed_when_the_run_finishes`, caused by MY OWN
  concurrent `mutation_check.py` runs racing on the `mutation-check-*` temp-dir glob that test
  asserts against. A clean, isolated re-run came back **exit 0, 0 failures** — confirmed
  self-inflicted, not a defect in the unit.
- `uv run ruff check src tests scripts` — `All checks passed!`
- `uv run autotester doctor` — **`doctor: clean`**, not the `root-clutter: AGENTS.md` the
  manifest pastes. AT-283 (commit `dd2ab83`, already on disk before this unit) allowlisted
  `AGENTS.md` in `doctor.py:21`. The manifest's pasted output is stale evidence from before that
  fix reached this working tree — noted, not a finding (the real, current state is strictly
  better than what was claimed, and no criterion depends on it).
- `uv run python scripts/mutation_check.py qa/evidence/at227-first-paint-modal/mutations-safety.json`
  — **3/3 killed**, independently re-run, kill-attribution checked line by line: every mutation's
  named `kills` test(s) appear in the run's actual `FAILED` list, not merely a non-zero exit.
- `uv run python scripts/mutation_check.py qa/evidence/at227-first-paint-modal/mutations-crawl.json`
  — **9/9 killed**, independently re-run, same attribution check performed by hand against the
  raw output. Matches the manifest's pasted numbers and test names exactly.
- **Mode D — my own browser**, not the maker's screenshots or script: started an ad-hoc
  `python -m http.server` on `tests/fixtures/modal_site`, drove Chromium via the Playwright MCP
  tools (not curl, not the maker's Playwright script). Confirmed independently:
  - `document.elementFromPoint` at the centre of `#reports-link` resolves to `#veil`, not the
    link, while the modal is up.
  - A real Playwright mouse click on `a#reports-link` **times out after 5s**, with Playwright's
    own actionability log stating `<div id="veil">…</div> intercepts pointer events` — a covered
    control is genuinely unclickable by a real pointer, not merely flagged by the app's own
    heuristic.
  - Clicking `#skip-modal` removes the veil client-side (same URL, no navigation).
  - The identical `a#reports-link` click that timed out 30 seconds earlier now succeeds
    immediately and navigates to `/reports.html` — a real, asserted state change, not a
    rendering check.
  - 0 console errors attributable to the app (one `favicon.ico` 404 is the browser's own
    default request against a fixture with no favicon file; unrelated to the unit).
  Evidence written to
  `qa/evidence/browser-at227-first-paint-modal-2026-09-11-checker/report.json`.
- Read every changed source file in full against the manifest's claims: `enumerate.js`
  (`isObscured`, fail-open off-viewport, fails-open-else semantics), `screen_graph.py`
  (`ElementRef.obscured`, defaults False), `enums.py` (`IssueKind.OVERLAY`, correctly documented
  as a PRODUCT observation), `screen_identity.py` (`structural_signature` — confirmed it does
  **not** exclude obscured elements, with the docstring explaining why: excluding them would
  collapse one modal shown over two different pages into one node), `explore_node.py`
  (`_report_overlay`, obscured elements skipped as candidates, `_enqueue` now threads the
  discovering `ScreenEdge`), `explore_return.py` (new file, `MAX_REPLAY_DEPTH = 3` bounds the
  recursive replay chain per X4, every exit of `_replay_discovery` names its own cause — no bare
  `False`), `explore_safety.py` (`link_is_safe` now takes `base_url`, resolves via the same
  `urljoin` the navigation uses, and a resolved URL with no host is refused rather than waved
  through).
- Confirmed the self-mutation-testing journey's FINAL state, not just the narration: the
  `structural_signature` exclusion really is deleted (not merely justified away); `panel_site`
  fixture really exists (`tests/fixtures/panel_site/{index,other}.html`) and really is exercised
  (`test_a_replay_that_lands_elsewhere_is_a_failure_not_a_near_miss` in
  `tests/test_explore_modal.py`, asserting the opened panel node is `ABORTED_ERROR`, files a
  `NAVIGATION` issue naming "Open panel", and does not silently explore whatever the replay
  actually landed on).
- Checked X1/X2/X10 by grep: `run_case` has exactly one call site (`_bootstrap_login` in
  `explore.py`); no `playwright` import or `.page.` access outside `browser/` in the touched
  files; `grep fill|select_option|upload` over `explore*.py` returns nothing.
- Checked the ledger: `AT-227` and `AT-333` were both still `status: open` despite the manifest's
  "Issues addressed" claiming them fixed — that's expected (only the checker flips
  `open → fixed`), and I did so above after independently verifying both. `AT-334` and `AT-335`
  were correctly left `open` (filed, not fixed) as the manifest states.

## Judging the three self-disclosed corner cases

1. **AT-334 (directory-index double-counting), deliberately not fixed — DEFENSIBLE, not a
   blocker.** It is a pre-existing screen-identity property untouched by this unit's core change
   (occlusion + return-to), orthogonal to the modal work, entangled with a blocked T-135 gate the
   maker does not control, and filed with full reproduction evidence rather than hidden. The
   fixture was changed to route around it (`./` instead of `index.html`) precisely so this unit's
   own tests do not silently depend on unproven behaviour — consistent with the scoping precedent
   this contract has repeatedly upheld (X14's AT-102/AT-109 residuals).

2. **AT-335 (1-in-14 crawl flake), filed not fixed — ACCEPTABLE, contained rather than
   ignored.** The mutation harness this unit's C7 evidence depends on (`scripts/mutation_check.py`)
   already carries the baseline-assertion clause added for exactly this class of risk (AT-307): if
   the flake strikes during a mutation run, `check()` raises `MutationError` on a red baseline
   *before* any mutation is judged, rather than silently reporting corrupted kill counts. That is
   the containment the dispatch asked me to look for, and it already exists and is exercised by
   this unit's own two harness re-runs (both of which I re-ran clean). The manifest's
   non-reproduction record (13 clean attempts including concurrent load) is honest and does not
   overreach into an unfalsifiable "it cannot happen" claim, which C7's unreachability clause would
   refuse. I would not accept this reasoning for a *product-safety* flake, but for a test-harness
   determinism issue with an existing, load-bearing containment mechanism and full disclosure, it
   does not block this unit — it is correctly a standalone high-severity ledger item for its own
   fix.

3. **Self-mutation-testing journey (7/12 → 9/9) — final state matches the narrated
   corrections**, independently confirmed above (exclusion deleted, `panel_site` built and
   exercised, `_replay_discovery` names every exit). Not taken on the maker's word.

## Criteria

- **X1** — PASS. `run_case` unchanged, one call site.
- **X2** — PASS. No stray `playwright`/`.page.` access.
- **X3** — PASS. `structural_signature` deliberately does not exclude `obscured` elements (code +
  docstring read directly); the veiled state and the dashboard behind it are two nodes sharing
  `/`, confirmed by `test_the_modal_state_is_its_own_screen` and by my own browser session
  observing the DOM change on dismissal.
- **X4** — PASS. `MAX_REPLAY_DEPTH = 3` bounds the new recursive replay chain the modal fix
  introduced; no bound in the existing machinery was touched or weakened.
- **X5** — PASS (unaffected). No change to `write_policy`/deny-list logic in this diff; no
  regression evidence found.
- **X16** — PASS. `IssueKind.OVERLAY` is documented and implemented as a PRODUCT observation
  (counted in `issues`, not `tool_failures`), consistent with the existing AT-120/AT-114
  separation; independently observed "1 overlay issue, naming the covered controls" in my own
  browser run.
- **C2** — PASS. `explore_return.py` split from `explore_node.py` at the 300-line cap; `doctor`
  clean.
- **C7** — PASS. Both mutation harnesses independently re-run with correct kill-attribution
  (3/3, 9/9); the sabotage/zero-failure/baseline/kill-attribution/mutation-duty clauses are all
  satisfied by the re-run evidence, not merely the pasted transcript.

## Scoreboard

8/8 criteria met, 0/0 invariants scored separately (folded into the criteria above).

VERDICT: PASS
SCOREBOARD: 8/8 criteria met, 0/0 invariants hold
FAILURES (if any):
- none
LIVE-BROWSER: qa/evidence/browser-at227-first-paint-modal-2026-09-11-checker/report.json
ISSUES-WRITTEN: none (AT-227 and AT-333 status flipped open → fixed in qa/issues.jsonl; AT-334
and AT-335 correctly left open per the manifest's own disclosure)
EXPLANATION: All eight assigned criteria hold on evidence the checker produced itself, including
an independent live-browser session (real Playwright interception timeout + a real post-dismissal
navigation) and two independent mutation-harness re-runs with manual kill-attribution checks. The
manifest's three self-disclosed judgment calls (AT-334 scoping, AT-335 flake, the mutation-testing
journey's final state) were each independently investigated rather than taken on trust, and none
blocks this unit. One minor evidence-staleness note (the pasted `doctor` output predates the
already-committed AT-283 fix) does not affect any criterion.
