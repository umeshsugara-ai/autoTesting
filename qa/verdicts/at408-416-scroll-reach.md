# Verdict — at408-416-scroll-reach

**Cycle checked:** 1 (manifest's `Fix cycle: 1 of 3`)
**Date:** 2026-09-27
**Checker:** fresh-context Mode A + mandatory Mode D, `D:/autoTesting/.worktrees/at408-416-scroll-reach`
**Commits reviewed:** `553e8fac` (original), `15e14023` (this cycle's fix + merge), branch `wave/at408-416-scroll-reach`

```
VERDICT: PASS
SCOREBOARD: 13/14 criteria met, 5/5 invariants hold
FAILURES (if any):
- [C7] sev: medium · the manifest's "strict generalization... a chain of N segments" claim is backed only by prose reasoning and a committed corpus capped at DEPTHS=(1,2,3) (max 2 genuine scroller crossings, one non-trivial clip segment) — no committed test exercises N>=3 scroller crossings or 2+ simultaneous non-trivial clip segments · fix direction: add 2 fixture-based regression tests (3-scroller-under-one-clip; 2-independent-clip-boundaries) at the depth the corpus caps out before · issue: ISS-at408-416-1
- [manifest accuracy] sev: low · capability-coverage table row 3's "RED after" cell reads "4 failed, 50 passed, 14 xfailed"; the reproduced number is "4 failed, 32 passed, 14 xfailed" (4+32+14=50 is the corpus total; "50" was pasted where "32" belongs) · fix direction: correct the cell text next edit · issue: ISS-at408-416-2
CAPABILITY-COVERAGE: 4/4 rows reproduced (throwaway copy outside the bound root, own venv, green-before/red-after/reverted-identical for every row)
LIVE-BROWSER: qa/evidence/browser-at408-416-scroll-reach-2026-09-27-checker/report.json
ISSUES-WRITTEN: ISS-at408-416-1, ISS-at408-416-2
EXECUTOR: not stated in manifest (checker: claude-sonnet-subagent)
EXPLANATION: The gate (qa/gates/at416-clip-vs-reach-direction.md, Answered B, D-048) is implemented
as shipped — outer clips test against the box of the scroller that opened their segment, never the
glyph's moving rect or an inner scroller's box — not drifted to A or C. All 4 capability-coverage
rows reproduced independently in an isolated throwaway copy. My own real-Chromium Mode D run (own
probes, not the maker's) confirms the shipped fixture is scroll-invariant and, using two novel
fixtures I built outside the bound root, that the segment-chain algorithm also holds at N=3 scroller
crossings and at 2 independent clip boundaries — geometries the committed suite never enumerates
(filed as ISS-at408-416-1, medium, a coverage gap, not a live defect since I found none). The
bare `uv run pytest` full suite showed 4 failures, not the manifest's 1: the known AT-627 flake plus
three more (test_mutation_check_judgement's hung-baseline test, test_redact_wrap_perf's 3.0s wall-clock
bound at 3.18s, and test_crawl_inventory_live hitting its own wall_clock_s bound) — all four are
timing/wall-clock-bound tests, none touch this unit's changed files (git diff confirms), and all four
pass cleanly in isolation (1.97s / 22.80s / 186.07s), so this is concurrent-session load in a shared
environment (my run: 1941s vs the manifest's 1299s), not a regression from this unit.
```

## Detail

### 1. Gate direction (Answered B, D-048)

`src/autotester/browser/visual_order_reach.js` implements exactly option B, generalized: `reachOf`
returns `{segments, scrollX, scrollY}` where each segment's `clip` is tested (`isReachable`) against
`seg.refBox || rect` — `null` (the glyph's own rect) for the first segment, and the box of the
scroller that opened each subsequent segment otherwise, discarding any earlier/inner scroller's box.
This is the checker's originally-suggested mechanism from the gate file, not option A (which would
stop the clip from accumulating past a scrollable ancestor and re-open AT-393) and not option C
(disclosure only — no fix). Traced by hand through N=0 (no scroller: one segment, `refBox: null`,
identical to pre-AT-379 behaviour for non-scrolling ancestors), N=1 (two segments — reduces exactly
to the previous cycle's `innerClip`/glyph, `outerClip`/scrollerBox design) and N=2/3 (chain of 3/4
segments, each referenced on its own opening scroller). No drift from B found.

### 2. Mode D — checker's own live-browser run (mandatory, this unit's job, not the maker's)

Driven myself via the Playwright MCP tool against real headless Chromium, reading the ACTUAL spliced
`visual_order.js` + `visual_order_reach.js` text out of this worktree (never the maker's screenshots,
never curl):

- **This unit's own fixture** (`tests/fixtures/bidi_site/at416_card.html`): glyph set at rest and
  after scrolling both `overflow:hidden`-wrapped `overflow:auto` bodies to their end is the same
  sorted multiset; `CARD3_HIDDEN_SENTINEL` (the non-overflowing negative-control card) never appears.
  Matches the shipped tests' claim.
- **Novel probe 1** (`checker_probe_3scroller.html`, built in the session scratchpad, never written
  into this worktree): `L0 (hidden, 40px clip) > L1 (auto) > L2 (auto) > L3 (auto)` — 3 genuine
  scroller crossings under one hard clip, a geometry absent from the committed corpus (`DEPTHS`
  caps at 3 total ancestors, i.e. at most 2 scrollers). Scroll-invariant under real Chromium.
- **Novel probe 2** (`checker_probe_2clip.html`, same scratchpad): `L0 (hidden) > L1 (auto) > L2
  (hidden) > L3 (auto)` — 2 independent hard-clip boundaries, each adjacent to its own scroller, the
  harder case the manifest's "chain of N segments" claim actually needs to be tested against (the
  shipped hidden-auto-auto fix only ever has one non-trivial clip segment). Scroll-invariant under
  real Chromium.

Both novel probes hold, so the shipped code is correct beyond N=2 by my own live measurement — but
neither geometry is covered by a committed test, so the manifest's "strict generalization" claim is
unenumerated by the artifact itself (see ISS-at408-416-1). Full detail:
`qa/evidence/browser-at408-416-scroll-reach-2026-09-27-checker/report.json`.

### 3. The claimed newly-found defect (this cycle) and its generalization

Verified the single-scroller case reduces to the previously-verified two-segment design (2 above) and
that the specific N=2 `hidden-auto-auto` family (the actual defect this cycle fixed) is proven both by
the committed corpus and by my own falsification (4 below, row 3). The further claim — that this is a
*strict* generalization holding for arbitrary N — is analytically sound (traced by hand) and confirmed
by my own live probes at N=3 and at 2 clip segments, but is not proven by anything committed to the
unit. This is exactly the "generalization claimed but only tested at N=2" gap named in my dispatch;
filed as ISS-at408-416-1, medium (a test-coverage gap in a credential-visibility-relevant module, not
a live defect — my own independent evidence found none).

### 4. Capability coverage — independently reproduced (4/4)

Throwaway copy at `scratchpad/falsify-at408416` (own venv via `uv sync --frozen`, real Playwright/
Chromium), confirmed green (**54 passed, 14 xfailed**) before any edit. Every row applied as a single
hunk to `src/autotester/browser/visual_order_reach.js`, run, then reverted and diffed byte-identical
against the worktree original before the next row:

| row | expected | observed | match |
|---|---|---|---|
| AT-408 accumulation (`if (scrollsX) scrollX += ...` gated off after first segment) | 13 failed incl. named regression | 13 failed, 24 passed, 14 xfailed, named test present | yes |
| AT-416 core (`const box = seg.refBox \|\| rect` → `const box = rect`) | 20 failed incl. both named fixture tests | 20 failed, 18 passed, 14 xfailed, both named tests present | yes |
| AT-416 nested/this cycle (`refBox = box` → lock to first scroller only) | 4 failed, 14 xfailed | 4 failed, 32 passed, 14 xfailed — exactly the 4 predicted shapes | yes (manifest's "50 passed" is a typo for 32 — ISS-at408-416-2) |
| AT-393 negative control (drop the overflow-amount check) | 3 failed, named leak assertion | 3 failed, `NESTCLIP_BELOW_SENTINEL_F2` leaked as predicted | yes |

### 5. Full-suite run — re-run myself, real numbers

```
$ uv run pytest
4 failed, 2025 passed, 6 skipped, 14 xfailed, 15 warnings in 1941.00s (0:32:20)
FAILED tests/test_crawl_inventory_live.py::test_a_logged_in_crawl_maps_every_route_and_names_the_one_it_refused
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
FAILED tests/test_mutation_check_judgement.py::test_a_hung_baseline_is_refused_even_when_a_child_holds_the_output_open
FAILED tests/test_redact_wrap_perf.py::test_redact_scan_stays_under_a_generous_bound_on_a_500kb_corpus
```

The manifest claims exactly 1 (`test_flake_probe_real_process`, the known AT-627 flake) in 1299.25s;
my run found 4 in 1941.00s — 50% slower, consistent with heavier concurrent session load in this
shared environment (this project runs a live maker-checker swarm; several other units' checkers were
active at the same time). Root-caused, not assumed:

- `test_crawl_inventory_live`: fails with `crawl.status is CrawlStatus.STOPPED_BOUND`,
  `stop_reason='wall_clock_s'` — its own internal wall-clock bound tripped under load. Re-run in
  isolation: **PASSED in 186.07s**.
- `test_flake_probe_real_process` (AT-627): the known pre-existing real-subprocess-kill timing flake,
  unrelated to this unit (confirmed by the 2026-09-25/27 manifests and by `git diff` — this test file
  is untouched by this unit's commits).
- `test_mutation_check_judgement`: same class as AT-627 (a second real-hung-process-kill timing test,
  AT-487). Re-run in isolation: **PASSED in 22.80s**.
- `test_redact_wrap_perf`: a 3.0s wall-clock performance bound, observed 3.18s (6% over) under full-
  suite load — its own in-file comment predicts exactly this failure mode ("not a tight target that
  would flake on a loaded machine"). Re-run in isolation: **PASSED in 1.97s**.

`git diff` confirms none of these four test files were touched by this unit's commits
(`553e8fac`..`15e14023` vs. `git merge-base master wave/at408-416-scroll-reach`). All four are
timing/wall-clock-bound tests that pass cleanly outside full-suite contention. None regress from this
unit's change to `observe.py` (which `test_crawl_inventory_live` exercises indirectly via
`PageObserver` — its isolated pass proves the splice mechanism is unaffected).

`uv run ruff check src tests scripts` → `All checks passed!` (re-run myself).
`uv run autotester doctor` → `doctor: clean` (re-run myself).
File sizes: `visual_order_reach.js` 164 lines, `visual_order.js` 228 lines — both under the 300-line
C2 cap.

### 6. Commit-before-verdict (C10)

`15e14023` (this cycle's fix, HEAD) and its ancestor `553e8fac` are both committed on
`wave/at408-416-scroll-reach` before this check; the merge of master (`3095c3f4`) is clean and, per
`git diff`, touches none of this unit's own files.
