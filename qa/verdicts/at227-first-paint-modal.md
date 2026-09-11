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

---

# INDEPENDENT CONCURRENT CHECK — at227-first-paint-modal

**Cycle checked:** 1
**Date:** 2026-09-11
**Checker:** a second fresh subagent, Mode A + Mode D, no builder context, bound to `D:/autoTesting`.

## Why this section exists

This is the accident the protocol's concurrency rule names, not a deliberate dual check: I was
dispatched against the manifest while the check above was already running, and I read the working
tree in its *staged, uncommitted* state. Mid-run the tree changed underneath me — the unit was
committed (`63aef0a`), PASSed (`1ad5496`) and closed out (`4ad6ed8`) by the checker above. I
verified my evidence still applies to the artifact as shipped: every file I read and mutated is
byte-identical to `HEAD`, since `git status` after the commit shows the explore/schema/browser
paths clean and only a later unit's `ui/` files modified. The verdict above is left byte-intact and
its evidence directory untouched; mine is written alongside it at `…-checker-b/`.

**I reach the same verdict on independently produced evidence: PASS.** One new ledger finding
(AT-338, medium) that the check above did not report, and it is not a criterion failure.

## What I re-ran myself

- `uv run pytest -q` — **exit 0**, 2 skipped, 1 warning. Run to completion in isolation *before*
  I started any mutation work, so the temp-dir race the checker above hit is not in my evidence.
- `uv run ruff check src tests scripts` — `All checks passed!`
- `uv run autotester doctor` — **`doctor: clean`, exit 0.** Same observation as above: the
  manifest's pasted `root-clutter: AGENTS.md` is stale evidence predating `dd2ab83`. The real state
  is strictly better than claimed; noted, not charged.
- `uv run python scripts/mutation_check.py …/mutations-safety.json` — **3/3 killed.**
- `uv run python scripts/mutation_check.py …/mutations-crawl.json` — **9/9 killed.**
  Both re-run from scratch. For every one of the 12 I compared the spec's `kills` list against the
  harness's `actually failed` list by hand: each named test is genuinely present in that run's
  `FAILED` set, and each exit code is `1` (tests ran and failed) rather than a collection error
  being read as a kill. Two crawl mutations killed *more* tests than they claimed (the two
  occlusion-probe mutations each also took down `test_no_edge_…` and `test_the_blocked_screen_…`) —
  a superset of the claim, which `expected <= failures` correctly accepts.
- **AT-335 did not fire on my run.** My crawl-mutation baseline came back green, so the flake did
  not corrupt this evidence. One clean observation, consistent with — and not proof against — the
  manifest's ~1-in-14 rate. Recorded as a datum, not as a refutation.
- **Legacy-artifact load check (the `extra="forbid"` question):** loaded every persisted
  `projects/*/crawl/*/nodes.jsonl` node written before this unit through `ScreenNode`. All load;
  their `elements` carry no `obscured` key and default to `False`. Confirmed the mechanism, not
  just the sample: `extra="forbid"` rejects unknown keys, never missing ones, and the field has a
  default. The residual is the known AT-124 shape — a pre-`obscured` artifact displays a defaulted
  `False` as if it were measured — an existing tracked property of this schema, not a new defect.
- **AT-334 probed directly rather than taken on the manifest's word.** `url_template()` on the two
  forms returns `'127.0.0.1:9/'` vs `'127.0.0.1:9/index.html'` (hostless `/` vs `/index.html`) —
  different templates, therefore different node ids, therefore two screens for one page. The
  deferred defect is **real**, so the deferral is honest rather than convenient; and the fixture's
  `./` links genuinely route around it (my own crawl produced 4 nodes over 3 pages, with no
  `/index.html` node), exactly as the manifest discloses.
- Greps for X1/X2/X10 on current `HEAD`: `run_case` one call site (`_bootstrap_login`); no
  `playwright` import or `.page.` access anywhere in `src/autotester/` outside `browser/`;
  `fill|select_option|upload` over `explore*.py` returns nothing.
- C2 line counts on the touched files: `explore_node.py` 238, `explore_return.py` 128,
  `explore.py` 300 (at the cap, not over), `explore_safety.py` 141, `test_explore_modal.py` 220.

## Mode D — my own browser, my own script

Independent of both the maker's script and the checker-above's MCP session: a Python Playwright
script driving **headed** Chromium against a local `http.server` on `tests/fixtures/modal_site`,
evaluating the real `enumerate.js` and then running the real `run_crawl`. **12/12 interactions
pass.** Every step asserts a state change, not a render:

| did | observed |
|---|---|
| first paint, evaluated `enumerate.js` | Reports/Settings/Refresh all `visible: true, obscured: true` |
| checked the veil's own controls | Excited/Focused/Tired/Skip for now all `obscured: false` — the way past the veil stays open |
| clicked the covered `#reports-link`, 1.5s timeout | `TimeoutError` — a covered control really is unclickable by a real pointer |
| re-read the URL | unchanged — no navigation happened |
| clicked `#skip-modal`, re-evaluated | the same three controls now `obscured: false` |
| re-checked the veil's controls | now `visible: false` — gone from the measurement entirely |
| clicked `#reports-link` again | navigated to `/reports.html` — the identical click that timed out seconds earlier now works |
| ran the real crawl from the veiled first paint | `templates=['/', '/reports.html', '/settings.html']`, `screens=4`, `stop_reason='frontier empty'` |
| counted overlay issues | exactly 1 (`kinds=['console','overlay']`) — X16's "not silent" |
| read its detail | `3 control(s) … covered by an in-page overlay and were not tried: Reports, Settings, Refresh. Reachable instead: Excited, Focused, Tired, Skip for now` |
| counted nodes at `/` | 2, distinct signatures (`ae5f1918…`, `08adab5e…`) — X3 holds |
| checked edges from the veiled node | zero `ERRORED` — no edge attributed to a screen the crawl had left |

**Console errors: 1 on `/` at first paint, 0 on `/reports.html`.** The non-zero count is explained,
not waved: the server log records exactly one 404, `GET /favicon.ico`, the browser's own default
request against a fixture directory that has no favicon. No app-originated error.

Evidence: `qa/evidence/browser-at227-first-paint-modal-2026-09-11-checker-b/report.json`.

## The judgement calls I was asked to make independently

1. **AT-333 fixed inside an AT-227 unit — legitimately in scope, not scope creep.** It is a
   blocking dependency, provably: the fixture links `href="reports.html"` (document-relative), and
   under the old guard `host_of` reads `reports.html` as a *hostname*, so the link is refused as
   off-domain and `test_the_crawl_gets_past_the_modal` cannot pass. It is one line of the same
   guard, it carries its own ledger id, and — the part that matters most — it was given its **own
   mutation spec file** (`mutations-safety.json`, its own 3 mutations, its own test block), so a
   checker judges it on its own evidence instead of inheriting the AT-227 verdict. The one thing
   that gives me pause is that this unit edited a HIGH-severity **safety guard** under another
   unit's heading; that is mitigated, not erased, by the separate evidence. The maker also
   explicitly refused to claim the backslash clause was killed by the wrong mutation (manifest
   point 4) — self-correction against its own interest, which raises rather than lowers my
   confidence.
2. **AT-334 deferred — honest.** Verified real above. It changes screen identity (X3/X15) for every
   crawl, and `url_template` is load-bearing for T-135's migration, which sits behind its own
   unanswered gate (`qa/gates/t135-url-pattern-data-migration.md`). Deferring is the correct call;
   the manifest names the fixture work-around as "a scoping choice, not evidence the alias is
   harmless," which is the disclosure that makes it honest rather than convenient.
3. **AT-335 deferred — honest, and its containment is real.** A fix with no reproducible case is
   the unfalsifiable claim C7's unreachability clause explicitly refuses; filing at high severity
   with 13 non-reproductions recorded is the behaviour that clause prescribes. The containment is
   load-bearing and I exercised it: `mutation_check.py` asserts a green baseline before judging any
   mutation, so if the flake strikes mid-run the harness **refuses the run** rather than certifying
   vacuous tests. The failure direction is a false FAIL, never a false PASS — so no verdict,
   including this one, can rest on the flake having been silent.
4. **The `structural_signature` revert — complete in behaviour, INCOMPLETE in documentation.**
   `screen_identity.py` is docstring-only in the diff; `structural_signature()` filters on
   `el.visible` and `not el.in_row` and nothing else, so obscured elements are hashed in, as
   intended. No test claims otherwise — `test_the_modal_state_is_its_own_screen` states in its own
   docstring that it passes with the change reverted and must not be read as evidence for the
   occlusion work, which is exemplary. **But one doc does still assert the reverted behaviour:**
   `schema/screen_graph.py:28-32` describes `obscured` as "never a crawl candidate and **never part
   of the screen's structural signature** (AT-227)" — the exact opposite of what
   `screen_identity.py:34-52` deliberately says, in the file this project's own CLAUDE.md names as
   the single definitive definition of every data shape. That is the re-add trap the
   `screen_identity` docstring was written to prevent, left open in the file a reader consults
   first. Filed as **AT-338 (medium)**. It is **not** a criterion failure: X3 is behavioural and
   holds on my browser evidence, C2's gate is `doctor`, and `doctor` is clean — and a criterion is
   not strengthened mid-verdict to fail an artifact any more than it is softened to pass one.
5. **`isObscured` failing OPEN outside the viewport — the right call, and no test pins it.** The
   direction is correct and the reasoning in the code is sound: `elementFromPoint` returns null for
   any point outside the viewport, so failing closed would mark every below-the-fold control
   obscured and **shrink** the crawl — a silent coverage loss, which is the same failure class
   AT-227 itself is. Failing open can only ever cost a redundant click attempt, which the existing
   machinery already handles. The gap is evidential, not behavioural: **no test and no mutation
   covers the off-viewport branch.** `modal_site` and `panel_site` are both short pages, so the
   `x < 0 || y < 0 || x > innerWidth || y > innerHeight` guard is never exercised — a mutation
   flipping it to `return true` would SURVIVE. C7's mutation duty is scoped to "the branch the test
   claims to defend" and no test claims this one, so it is not a C7 violation; but it is the
   cheapest remaining hole in this unit's evidence (a fixture with a tall page and one
   below-the-fold link would close it). Recorded here as a question for the next unit, deliberately
   **not** filed as a failure — I would not defend it at >80% as a defect, only as missing evidence.

## Observations that are not findings

- **Obscured controls now bypass `_candidate_denial` entirely** (`explore_node.py:220`, Python
  short-circuits before the call), so a covered `Delete` button no longer produces a
  `DENIED_POLICY` edge and no longer increments `rt.denied`. Safety is unaffected in the direction
  that matters — it is *not clicked* either way — and X16's auditability survives, because
  `_report_overlay` names every covered control in the overlay issue. Different accounting, not
  lost information. Raised so the next reader of the denied counter knows.
- The replay recursion adds clicks that are not counted against `max_actions`, bounded by
  `MAX_REPLAY_DEPTH = 3` per `return_to`. The crawl still always terminates (X4 holds), which is
  what the criterion actually requires.
- `qa/gates/next-unit-scope.md` — checked, because building AT-227 while that gate was open would
  have been a bypass. It carries a proper `**Answered:** 2026-09-11 — Option C … — Umesh, in
  conversation` line in this unit's own commit, matching the attribution form the repo's other
  answered gates use. Not a finding.
- Pre-existing ledger id collisions remain at AT-288/289/290/291/298/299 (six duplicated ids). Not
  this unit's doing and not charged to it; noted for a sweep.

## Criteria

| | verdict | on what evidence |
|---|---|---|
| **X1** | PASS | `run_case` one call site, `_bootstrap_login`; `execute.py`/`execute.md` absent from the diff |
| **X2** | PASS | no `playwright` import / `.page.` access outside `browser/` |
| **X3** | PASS | 2 distinct-signature nodes at `/` in my own crawl; `structural_signature` verified to include obscured elements, as intended |
| **X4** | PASS | `MAX_REPLAY_DEPTH = 3` bounds the new recursion; my crawl terminated with `stop_reason='frontier empty'` |
| **X5** | PASS (unaffected) | no `write_policy`/deny-list logic changed; full suite green |
| **X16** | PASS | exactly 1 `OVERLAY` issue naming all 3 covered controls **and** what was reachable instead — a blocked crawl that is no longer indistinguishable from a complete one |
| **C2** | PASS | `doctor: clean` exit 0; every touched file within the 300-line cap; `explore_return.py` split with its reason stated in the manifest (C3) |
| **C7** | PASS | 12/12 mutations re-killed by me, exit code `1` each, kill-attribution matched by hand against `FAILED`; baseline asserted green by the harness |

VERDICT: PASS
SCOREBOARD: 8/8 criteria met, 0/0 invariants scored separately (folded into the criteria)
FAILURES (if any):
- none
LIVE-BROWSER: qa/evidence/browser-at227-first-paint-modal-2026-09-11-checker-b/report.json (my own headed Chromium + my own script; 12/12 interactions; console errors 1 on `/` [a favicon 404] and 0 on `/reports.html`)
ISSUES-WRITTEN: AT-338 (medium, the documentation half of the signature revert left unreverted). AT-227 and AT-333 moved `fixed → verified` — this is the later, independent re-check that transition requires, on my own re-run evidence rather than the verdict above's. AT-334 and AT-335 correctly left `open`.
EXPLANATION: A second, independent check of cycle 1 agrees with the verdict above and adds one finding it did not report. All eight criteria hold on evidence I produced myself: the full suite green in isolation, both mutation specs re-killed 12/12 with kill-attribution verified by hand, and a live headed-Chromium session of my own driving 12 interactions that assert state changes — a covered control that genuinely times out on click, then navigates after dismissal. The three self-disclosed judgement calls survive independent scrutiny: AT-333 was a provable blocking dependency carrying its own mutation evidence rather than scope creep, and AT-334 and AT-335 were both verified to be real defects honestly deferred, not convenient ones. The one gap is documentation: the reverted signature exclusion is still asserted as fact in `ElementRef.obscured`'s schema description, contradicting `structural_signature`'s own docstring in the file this project treats as the definitive source for data shapes (AT-338, medium) — no criterion depends on it, so it is filed rather than charged. The remaining evidential hole, deliberately not filed as a failure, is that `isObscured`'s off-viewport fail-open branch is correct but is exercised by no test and no mutation.
