# Manifest — at227-first-paint-modal
**Contract:** qa/contracts/explore.md (X3, X4, X5, X16) · qa/contracts/core-invariants.md (C2, C7)
**Goal task:** AT-227 (ledger issue; no `.goal` task id — the unit is an issue-fix batch)
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no (no `.goal` task with this slug; no `criticality: critical`)
**Issues addressed:** AT-227 (fixed) · AT-333 (filed and fixed this cycle) · AT-334, AT-335 (filed, NOT fixed — reasons below)

## The unit in one line

A modal on first paint made the crawl learn ONE screen and still report
`status=completed, issues=0`. Three distinct defects were in that path; two are fixed here, the
third is filed with its evidence and deliberately left for its own unit.

## What changed

- `src/autotester/browser/enumerate.js`:19-39,140 — new `isObscured(el)`: `document.elementFromPoint`
  at the control's centre decides whether the control is the thing a click would actually hit. Fails
  OPEN for any point outside the viewport (`elementFromPoint` returns null off-screen, so a
  below-the-fold control would otherwise be called "obscured" and the crawl would SHRINK). Emitted as
  a new `obscured` field.
- `src/autotester/schema/screen_graph.py`:29-35 — `ElementRef.obscured`, defaulting False so every
  existing artifact still loads under `extra="forbid"`.
- `src/autotester/schema/enums.py`:270-275 — `IssueKind.OVERLAY`. A PRODUCT observation, not a tool
  failure (contrast `EVIDENCE`, AT-114/AT-120): the screen really was uninteractable in the state the
  crawl met it, so it must not be filed as a crawler fault and must not be silent either.
- `src/autotester/stages/screen_identity.py`:34-52 — **docstring only.** An earlier version of this
  unit excluded obscured elements from the structural signature; its mutation SURVIVED and the change
  was removed (see "What the mutation run changed about this unit", point 3). What remains is a
  comment recording why identity deliberately does NOT use `obscured`, so the next reader does not
  re-add it.
- `src/autotester/stages/explore_node.py` — `_report_overlay` files ONE issue per covered screen
  naming what was hidden and what was reachable instead; obscured controls are skipped as candidates;
  `_enqueue` now takes the `ScreenEdge` so the runtime can replay it.
- `src/autotester/stages/explore.py`:58-61 — `ExploreRuntime.discovery` (node id → the edge that
  found it).
- `src/autotester/stages/explore_return.py` — **new file**, split from `explore_node.py` at the
  300-line cap (C2). Holds the whole "find my way back to this exact screen" ladder, which grew a
  fourth rung: back → the node's URL → **replaying the edge that discovered it** → the base URL.
  `MAX_REPLAY_DEPTH = 3` bounds the recursion (X4: a crawl must always terminate).
- `src/autotester/stages/explore_safety.py`:93-112 — `link_is_safe` takes the page's URL and resolves
  the href with the same `urljoin` the navigation uses (AT-333).
- `tests/fixtures/modal_site/` — **new fixture**: a dashboard under a first-paint modal, with the
  modal dismissed client-side (no navigation, no history entry, same URL). The committed
  `crawl_site` fixture has no modal, which the AT-227 note names as exactly why a self-authored
  fixture could not surface this.
- `tests/fixtures/panel_site/` — **new fixture**: a first-run panel that opens ONCE per browser, so
  the screen it reveals can be discovered and then genuinely cannot be returned to. Built because a
  mutation survived without it (point 2 below).
- `tests/test_explore_modal.py` — **new**, 6 tests. `tests/test_explore_safety.py`:160-215 — the
  link-safety block rewritten for the new signature, +3 tests. `tests/test_explore_error_causes.py`
  — repointed at the moved `_recover`.

## The three defects, separated

1. **AT-227, the reported half — a covered control looks clickable.** `isVisible` asks CSS; CSS says
   a control under a veil is visible. Fixed by the occlusion probe.
2. **AT-227, the half that only appeared after fixing the first.** Once the crawl clicked "Skip for
   now" and found the dashboard, it could not get BACK to either screen: `return_to` returned True on
   a URL match alone (so it went on questioning the dismissed screen as if it were still veiled), and
   once that was tightened, the dashboard-behind-the-modal had no URL that reaches it at all — it was
   enqueued and then abandoned unexplored. Fixed by the fingerprint check plus edge replay. **Without
   this, the occlusion fix alone does not deliver the issue's "expected".**
3. **AT-333, found by this unit's own fixture.** `host_of` force-prefixes `//` because it was written
   for the absolute URL the browser will use; fed a bare relative href it reads `reports.html` as a
   *hostname*, so every document-relative link was refused as off-domain. Root cause is a check/act
   divergence — `_perform` navigated `urljoin(current_url, href)` while the guard judged the raw
   string, so the guard's verdict was about a URL the browser would never visit. The same line also
   failed OPEN on anything `host_of` fails CLOSED on (a backslash, AT-007). Fixed here because the
   AT-227 test cannot pass without it and it is the same guard; the backslash clause is called out
   separately in the ledger so the checker judges it on its own evidence rather than inheriting mine.

**AT-334 is filed and NOT fixed:** `/` and `/index.html` are counted as two screens (six nodes for a
three-page site, each veiled state filing its own overlay issue). It is a change to screen identity
(X3/X15) affecting every crawl, and `url_template` is load-bearing for T-135's migration, which is
itself behind an unanswered gate. The fixture was changed to link `./` so the two concerns do not
ride on one test — a scoping choice, not evidence the alias is harmless.

## How to verify (commands + expected)

- `uv run pytest -q` → expected: exit 0, no failures
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: only the pre-existing `root-clutter: AGENTS.md` (untracked,
  not from this unit — present at session start, from the `.codex/` tooling)
- `uv run pytest tests/test_explore_modal.py -q` → expected: 6 passed, against a real Chromium
- `uv run python scripts/mutation_check.py qa/evidence/at227-first-paint-modal/mutations-safety.json`
  → expected: `3/3 mutations killed`
- `uv run python scripts/mutation_check.py qa/evidence/at227-first-paint-modal/mutations-crawl.json`
  → expected: `9/9 mutations killed` (C7). **Re-run it if the baseline comes back red — see AT-335.**

## Actual outputs (from maker's own run)

```
$ uv run pytest -q
1097 passed, 2 skipped, 1 warning in 194.47s (0:03:14)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)
   ^ pre-existing and NOT from this unit: AGENTS.md is untracked, arrived with the
     .codex/ tooling, and was already present at session start.

$ uv run python scripts/mutation_check.py .../mutations-safety.json
KILLED  link safety judges the raw href instead of the resolved URL (AT-333)
KILLED  an empty host is waved through again (AT-333's fail-open)
KILLED  the allowed-domain check is dropped, keeping only 'has a host'
3/3 mutations killed

$ uv run python scripts/mutation_check.py .../mutations-crawl.json
KILLED  occlusion probe disarmed - every element reports reachable
KILLED  occlusion probe removed entirely from the emitted element
KILLED  covered controls are tried again instead of skipped
KILLED  the overlay is passed over silently (the original AT-227 failure)
KILLED  the overlay issue no longer names what was covered
KILLED  return_to short-circuits on the URL alone (AT-227 first half)
KILLED  the discovering edge is never replayed - a stateful screen is unreachable
KILLED  the replay does not verify where it landed
KILLED  a failed replay stops naming WHICH control it replayed (the AT-108 shape)
9/9 mutations killed
```

Full logs: `qa/evidence/at227-first-paint-modal/mutations-{safety,crawl}.out`.

## What the mutation run changed about this unit (C7 worked)

The first run came back **7/12**. Five survivors, and chasing each one changed the unit:

1. **`return_to` short-circuits on the URL alone — SURVIVED.** My test asserted the crawl
   *reaches* every page, which it does either way. What the bug actually produced was a graph with
   invented failures: the browser sat on the dismissed dashboard while the crawl tried the veiled
   screen's remaining controls, each hidden there, each recorded as an ERRORED edge against a
   screen it was not on. New test asserts edge attribution, not reachability.
2. **The replay's landing check — SURVIVED**, because in the modal fixture the replay always lands
   correctly, so nothing separated it from `return True`. C7 forbids discharging that with "no
   mutation can reach it" (and two such claims of mine have already been falsified here), so the
   `panel_site` fixture was built: a first-run panel that opens ONCE per browser, whose revealed
   screen has no URL *and* cannot be restored by replay.
3. **The signature exclusion — SURVIVED, and the right answer was to DELETE it.** Excluding
   obscured elements from `structural_signature` is not what makes the veiled and dismissed states
   two screens — they differ anyway, because dismissing the veil makes its own controls
   `display:none` under the pre-existing `visible` rule. What the exclusion *did* change was
   collapsing ONE modal shown over TWO different pages into a single node, which would claim one
   screen has two outcomes for the same action. Removed rather than justified with a fixture.
   `test_the_modal_state_is_its_own_screen` says so in its own docstring, so nobody reads it as
   evidence for the occlusion work.
4. **One survivor was my error, not a test hole.** I claimed the "judge the raw href" mutation
   kills the backslash tests. It does not: with `target = el.href`, `host_of` still returns `""`
   for a backslash and the guard still refuses. The harness was right; the claim was mine.
5. **And re-reading `explore_return.py` before submitting found a defect in it**, unprompted by any
   mutation: `_replay_discovery` ended `except Exception: return False` — the AT-114 shape, where
   "the panel only opens once" and "the browser died" become the same answer — returning a bare
   `False` from four places while `return_to` overwrote the nested cause (AT-108's class). It now
   returns `str | None` and every exit names itself. The first mutation I wrote for that fix
   targeted the `except` branch, which this fixture never reaches, so it could only ever have
   SURVIVED; a mutation with no way to die is decoration, not evidence, and it was replaced with
   one on the branch the fixture does reach.

## Live browser evidence

`qa/evidence/browser-at227-first-paint-modal-2026-09-11/report.json` — real Chromium, local HTTP
server, **6/6 interactions pass, 0 console errors**. It asserts state changes, not rendering:

| did | observed |
|---|---|
| loaded the dashboard with the modal on first paint | Refresh, Reports, Settings reported obscured |
| checked the modal's own controls | Skip for now reachable |
| clicked the covered "Reports" link, short timeout | **intercepted** — a covered control really is unclickable |
| clicked "Skip for now" | Reports no longer obscured |
| ran the full crawl from the veiled first paint | /reports.html and /settings.html reached |
| looked for the blocked screen in the report | 1 overlay issue, naming the covered controls |

Two interactions first reported `pass: false` on behaviour that was correct — a sorted-order
mismatch and a literal `(s)` — both bugs in the evidence script's comparison, repaired there
rather than by relaxing the expectation.

**This is the maker's smoke pass and is NOT this unit's validation.** The checker runs its own,
with its own script.

## Known gap the checker should weigh

**AT-335 (filed, high, NOT fixed):** the modal crawl is non-deterministic — 1 red in 14 runs,
observed once as a red BASELINE inside `mutation_check.py`, which refused the run (correctly,
AT-196). Could not be reproduced in 13 further attempts including 3 concurrent pytest processes.
Deliberately not "fixed": with no reproducible case, any fix would be the unfalsifiable claim C7
forbids. It matters beyond this unit — a test the mutation harness needs green, failing 1 run in
14, silently invalidates future mutation evidence.

## Status: ready-for-check
