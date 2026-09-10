# Manifest — t135-coverage-merge-expand

**Contract:** qa/contracts/ingest.md (I6 + its no-fire list, which defers "merging into an
existing `FlowSpec`" to **A6** — this unit) · qa/contracts/coverage.md (V1, V3, V6) ·
qa/contracts/expand.md (X6, the door rule) · qa/contracts/review-gate.md (R1)
**Goal task:** T-135 — Track A6: coverage/merge/expand loops reconnected + ARCHITECTURE update
**Date:** 2026-09-11
**Fix cycle:** 2 of max 3
**Dual check:** required  ← `.goal/goal.json` T-135 carries `criticality: critical`
**Issues addressed:** AT-287 (root cause, fix REPLACED in cycle 2) · AT-288 · AT-289 · AT-290 (both rows) · AT-291 (both rows) · AT-293 (new, filed by this unit) · reconciles AT-286 (the in-flight work the
2026-09-11 sweep flagged is this unit; it is now a manifest, not an untracked tree)

## Why this unit exists

The self-extension loop was open at exactly one joint. COVERAGE notices an unknown route and
queues a `VideoRequest`; a human records the video; INGEST produces a **fresh** `FlowSpec` — and
the answer had nowhere to land. `persist_ingest` refuses to overwrite an APPROVED spec (I6), and
its own error text names the missing piece: *"or merge instead once merge_flowspec exists."*
`RequestStatus.FULFILLED` and `fulfilled_by_source` were declared in the schema and **written by
nothing anywhere in src/ or tests/**, so every request the system ever made stayed OPEN for life.

## What changed

- `src/autotester/stages/merge_flowspec.py` (new, 159 lines) — `merge_flowspec` folds an ingested
  spec into the reviewed one without rewriting a single existing screen or flow; `resolve_requests`
  closes the requests the merged spec can now answer; `open_requests` surfaces the ones it cannot.
- `src/autotester/core/urls.py` — **AT-287.** ~~Added `_split`, a host-shape heuristic.~~
  **Superseded in cycle 2:** the heuristic is deleted and all four `url_pattern` producers are
  canonicalised to `keep_host=False`. See "Cycle 2" below.
- `src/autotester/stages/ingest.py`, `src/autotester/stages/product_map.py` (cycle 2) — store
  `url_pattern` host-less, matching `explore_merge.py` and `screen_identity.py`.
- `src/autotester/ui/routes_crawls.py` (cycle 2) — `resolve_requests` on the UI merge seam (AT-289).
- `projects/erp/screenmap.json` (cycle 2) — 3 mangled rows repaired (AT-290).
- `src/autotester/cli_video.py:151-200` — `autotester ingest run --merge`, the door (X6/V6), plus a
  `--merge`/`--replace` mutual-exclusion refusal and `_merge_into_reviewed`.
- `src/autotester/store/request_store.py` (new) + `project_store.py` — `update_request` (the ask
  had no status-transition path at all). Adding it pushed `project_store.py` to 303 lines, so the
  request methods moved to a `RequestStoreMixin`, exactly as `crawl_store.py` was split at the same
  cap. Public API unchanged.
- `src/autotester/stages/explore_merge.py` — `_disagreement` → public `disagreement`, and its
  `crawl_id` param renamed `source_id` now that a second seam calls it. **Behaviour unchanged**;
  this exists so the video seam and the crawl seam cannot drift apart (C1: one concept, one place).
- `tests/test_merge_flowspec.py` (merge semantics) + `tests/test_merge_flowspec_requests.py`
  (the ask lifecycle) + `tests/test_merge_flowspec_cli.py` (the door) — split at the 300-line cap
  the way `test_expand.py`/`test_expand_cli.py` are.
- `tests/test_urls.py`, `tests/test_coverage.py`, `tests/test_ingest_persist.py`,
  `tests/test_coverage_wiring.py` — regression tests (see Cycle 2 for what each defends).
- `docs/ARCHITECTURE.md` (concept→file row for the new stage) · `docs/MAP.md` (regenerated).
- `qa/issues.jsonl` — AT-287 filed.

## The defect found on the way — AT-287 (high)

`core/urls.py`'s docstring promised `url_template(url_template(u)) == url_template(u)`. **It was
false.** `urlsplit("demo.test/x")` has no `//`, so the HOST lands in `.path` and becomes a path
segment. `stages/ingest.py` stores `url_pattern` **host-ful** (I7) while `explore_merge` stores it
host-less; `stages/coverage.py::_known_paths` re-templates every stored pattern to compare, so a
video-learned `demo.test/students/{id}` became `/demo.test/students/{id}` and matched no observed
path. **Reproduced against production code before the fix:** a `FlowSpec` containing a screen for
precisely the URL a run visited still reported `CoverageGap ['/students/{id}']`.

This is coverage.md V1's own trap in a second disguise — V1 made both sides use one normaliser but
did not notice the normaliser is lossy when fed its own output.

**It is on this unit's critical path, which is why it is fixed here and not deferred:**
`resolve_requests` could never close a video-answered gap, because the pattern the recording taught
never matched the path the request was raised on.

**~~Blast radius, measured rather than assumed~~ — THIS CLAIM WAS FALSE.** I wrote that no project
on disk was affected. I had measured `projects/*/flowspec.json` **only**. Checker A found
`projects/erp/screenmap.json` carrying **3 video-derived rows** mangled to
`/vidysea.com/erp/trainers` — produced by `product_map.py`, an artifact my measurement never looked
at — and **rendered to a human today** on `/projects/erp/product-map`. Repaired in cycle 2. The
lesson is the one this manifest got wrong: "measured" means measuring every producer, not the one
you happened to think of.

## How to verify (commands + expected)

- `uv run pytest -q` → expected: exit 0
- `uv run ruff check src tests scripts` → expected: exit 0
- `uv run autotester doctor` → expected: exit 1 with **exactly one** violation, the pre-existing
  untracked root `AGENTS.md` (AT-283). This unit adds none and removed the `stale-generated
  docs/MAP.md` one.
- `uv run python scripts/check_deliverable.py --exists src/autotester/stages/merge_flowspec.py tests/test_merge_flowspec.py && uv run pytest tests/test_merge_flowspec.py tests/test_coverage.py -q` → expected: exit 0 (the goal task's own `done_check`)

**Sabotage the fix must survive (please re-derive, do not trust this) — cycle 2 set:**
1. Revert `stages/ingest.py`'s `url_template(observed.url, keep_host=False)` to the host-ful call →
   `tests/test_ingest_persist.py::test_a_video_screen_and_a_crawled_screen_of_one_url_produce_one_pattern`
   and `::test_an_observed_url_is_templated_the_same_way_the_crawler_templates_it` must fail.
2. Replace `resolve_requests`' body with `return []` → 5 tests fail (checker A measured 5 in cycle 1,
   not the 3 I predicted).
3. Delete the `resolve_requests` call in `ui/routes_crawls.py::merge_crawl` →
   `tests/test_coverage_wiring.py::test_the_merge_button_closes_the_request_the_crawl_answers` must fail.
4. Make `_learned_url_patterns` return `{}` →
   `tests/test_merge_flowspec.py::test_a_re_recording_teaches_a_url_pattern_the_spec_lacked` must fail.

## Actual outputs (from maker's own run)

**Superseded — this block was captured before the last cycle-1 edit and was wrong on two counts
(doctor showed 2 violations, not 1; the subset was 28 passed, not 27). Both were checker findings.
The authoritative, freshly re-run outputs are in "Cycle 2 verify" below.**

Pre-fix reproduction of AT-287, run against production code:

```
url_template(u)               = 'demo.test/students/{id}'
url_template(url_template(u)) = '/demo.test/students/{id}'
IDEMPOTENT? False
spec has a screen for exactly the URL the run visited.
  gaps found : ['/students/{id}']      EXPECTED: []
>>> A video-learned screen is INVISIBLE to coverage.
```

## Live browser evidence

`qa/evidence/browser-t135-coverage-merge-expand-2026-09-11/report.json`

No file under `ui/` changed, but D-024 demands honesty about indirect surfaces: the AT-287 fix
changes what `coverage.py` reports, and `ui/routes_crawls.py:150` renders that in the coverage
card. Real uvicorn + Playwright Chromium over 4 pages, **0 console errors on every page**; the
checkerdemo crawl page's "Against the FlowSpec" card renders correctly and unregressed (crawl
patterns are host-less, so AT-287 never touched them).

**The interaction that matters ran for real:** `autotester ingest run demo <src> --merge` in a real
process against a real on-disk store →
`demo: v4, 2 screens, 0 flows after merging the answer video (review status draft, 1 request(s) closed)`,
exit 0. On disk: the human-reviewed screen survived **verbatim**, the recording's screen was added,
v3→v4, review APPROVED→draft, and `requests.jsonl` shows `status=fulfilled,
fulfilled_by_source=src_2a9dbdd46186`.

**Declared gaps (a SKIP is a stated gap, never a pass):**
1. No subprocess run against a REAL video with a live vision provider — no suitable recording
   exists in-repo, and a fake mp4 fails the model call rather than the merge. Only the observation
   is stubbed; everything this unit owns ran for real.
2. The UI has **no ingest route at all** (`persist_ingest`/`ingest_video` appear only in
   `cli_video.py`), so the CLI is this stage's only real entry point — there is no second call site
   to wire, unlike coverage.md V6's two.

## Judgements offered to the checker (please rule)

1. **Was fixing AT-287 inside this unit correct, or scope creep?** Argued above as on the critical
   path. If ruled scope creep, it should split into its own unit rather than be reverted — the loop
   does not close without it.
2. **`explore_merge._disagreement` → `disagreement` is a rename of a contract-referenced private
   helper** (explore.md X12 territory). Behaviour is identical and no test referenced it, but the
   contract's prose names `_disagreement`.
3. **The `_LOOKS_LIKE_HOST` heuristic** (first segment carries `.` or `:`) is a judgement call. A
   relative path whose first segment contains a dot (`v1.2/foo`) would be misread as a host. I
   judged that shape absent from this system's URLs; that is an assumption worth attacking.
4. **AT-287 filed by the maker, not the checker** — the ledger is checker-owned, but the id is
   cited in shipped code comments, so leaving it unfiled would dangle. Re-file or re-word freely.

---

# Cycle 2 — what the two FAIL verdicts changed

Both checkers FAILed cycle 1 (`t135-coverage-merge-expand.md`, `.b.md`), and a
`senior-software-engineer` review returned **Warning** on the same seam. Their union, and what
each got:

### AT-288 — the doctor baseline I declared was not the baseline I produced (both checkers)
My one-line `docs/ARCHITECTURE.md` row took the file 150 → 151 against the repo's own C2 budget,
and the `doctor` output I pasted was captured **before** that edit. Fixed by folding the new stage
into the existing self-extension row. **All outputs below were re-run after the last edit.**
My cycle-1 manifest also pasted "27 passed" where the real number was 28 — checker A caught it.

### AT-289 — the loop was only closed on the CLI path (checker A charged it; B found it too)
Checker A clicked the product's own "Merge these screens into the FlowSpec" button, watched the
coverage gap go to zero, and read the ask back **still OPEN**. Against T-100's no-CLI goal that is
the only door an operator has. `resolve_requests` is now called from
`ui/routes_crawls.py::merge_crawl`, exactly as `queue_requests` is called from both entry points
(coverage.md V6). Defended by two button-driven tests in `tests/test_coverage_wiring.py` — the file
whose docstring already warns that a test calling the helper directly "would pass just as well with
both call sites deleted".

### AT-287 fix REPLACED — the parser was never the root cause
Checker A: `url_template` was still not idempotent for a **dotless host** (`localhost`, `erp`), and
my heuristic silently **dropped** a dotted first segment. The engineering review went further:
`url_template("settings.json", keep_host=False)` returned `"/"` — total path loss — and named the
exposed caller as `stages/ingest.py`, which templates **vision-model transcribed text**, not
validated URLs.

They are right, and the guess is unwinnable **in principle**: `settings.json` and `example.com` are
the same shape. So the heuristic is **deleted**.

The actual root cause, found while fixing it: **the two seams stored different shapes.**
`ingest.py` and `product_map.py` stored `url_pattern` host-ful; `explore_merge.py` and
`screen_identity.py` stored it host-less. So `ingest.md` **I7's own stated purpose** — *"a screen
learned from a video and the same screen found by a crawl collapse to one row instead of two"* —
**was defeated**: the two sides could never produce the same pattern. I7 asserted that each side
calls `url_template`, and never once tested that they **agree**. AT-287 was a symptom of that.

Cycle 2 canonicalises all four producers to `keep_host=False`. Re-templating a path is idempotent
with no guessing, and the new
`tests/test_ingest_persist.py::test_a_video_screen_and_a_crawled_screen_of_one_url_produce_one_pattern`
is the cross-seam assertion I7 always required.

### AT-290 (checker A) — my blast-radius claim was FALSE, and I must own it
I claimed "measured rather than assumed: no false gap has actually been produced yet". I measured
`projects/*/flowspec.json` **only**. `projects/erp/screenmap.json` carries **3 video-derived rows**
mangled to `/vidysea.com/erp/trainers`, produced by `product_map.py` — an artifact my measurement
never looked at — and **rendered to a human today** on `/projects/erp/product-map`. My fix did not
heal them either (a leading slash short-circuited it). Repaired in cycle 2 to `/erp/trainers`;
backup at `.work/screenmap.json.bak`. The AT-287 ledger note is corrected, not softened.

### AT-290 (checker B) — a merge could never TEACH a url_pattern
`Screen.id` is content-addressed on `(name, signals)` only, so a re-recording of an already-named
screen was dropped whole by `_new_screens`. Since I7 makes `url_pattern=None` the **normal** outcome
for a video with no visible address bar, that was the **common** case: ask for a video, get one,
learn nothing, leave the ask open forever. `_learned_url_patterns` now fills a `None` — and only a
`None`; an existing pattern is still never overwritten, because that would be rewriting reviewed
truth.

### AT-291 (checker B) — false attribution
A no-op merge stamped `fulfilled_by_source` with an unrelated recording's id. Attribution is now
derived from the **answering screen's own** `source_ref`, so it is correct by construction rather
than by assumption; `source_id` is only a fallback.

### AT-293 — filed by me, against the process itself
The two checkers ran concurrently and **both allocated AT-288–AT-291**, for eight different
defects. I did not renumber their rows — the ledger is checker-owned and rewriting another
checker's ids would destroy the audit trail the dual check exists to create. Remedy proposed in the
row; `adapter.json` already declares an apparently-unused `tools.reserve_id`.

## Cycle 2 verify (every command re-run after the final edit)

```
$ uv run pytest -q
1032 passed, 2 skipped, 1 warning in 86.49s        exit=0

$ uv run ruff check src tests scripts
All checks passed!                                  exit=0

$ uv run autotester doctor
root-clutter: AGENTS.md - scratch and evidence belong in .work/, not the repo root
1 violation(s)                                      exit=1   (AT-283 only — the certified baseline)

$ uv run python scripts/check_deliverable.py --exists src/autotester/stages/merge_flowspec.py tests/test_merge_flowspec.py
OK 2 deliverable(s) present                         exit=0
$ uv run pytest tests/test_merge_flowspec.py tests/test_coverage.py -q
24 passed                                           exit=0
```

Test files were re-split at the C2 cap as they grew: `test_merge_flowspec.py` (merge semantics,
194) · `test_merge_flowspec_requests.py` (the ask lifecycle, new) · `test_merge_flowspec_cli.py`
(the door).

## What cycle 2 does NOT claim

- **No live-browser re-run by me this cycle.** Both checkers ran their own Mode D in cycle 1 and
  must do so again; mine was only ever a smoke check and is not this release's validation.
- **The screenmap repair is data, not code.** It is a one-off repair of 3 rows, verified by reading
  the file back; nothing regression-tests stored-data repair, and I did not add a migration.
- **`_GAP_KINDS` still hardcodes `("route","screen")`.** The engineering review confirmed only those
  two are ever constructed today; it remains a latent trap if a stage starts emitting
  `field`/`class` gaps. Not fixed, deliberately — out of this unit's scope.

## Status: ready-for-check
