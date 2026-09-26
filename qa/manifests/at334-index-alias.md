# Manifest — at334-index-alias

**Unit:** A directory index reached two ways (`/` and `/index.html`) must be one screen identity,
not two — `core.urls.url_template` kept the path as served, so `/` and `/index.html` produced
different `(url_template, signature)` node ids.
**Contract:** no `qa/contracts/` criterion number names this directly; judged against X15
(`qa/contracts/explore.md` — `Screen.url_pattern` / `ScreenNode.url_template` must reduce to one
identity) and `qa/contracts/ingest.md`'s "url_template is the ONE place a URL is normalised"
invariant. Flagged for the checker to decide whether a dedicated criterion is warranted.
**Date:** 2026-09-26
**Fix cycle:** 1 of 3
**Dual check:** no
**Persona walk:** skip (pure identity-normalisation fix, no persona/UI surface touched)
**Issues addressed:** AT-334
**Executor:** claude-opus-subagent

## The gap (AT-334, as filed)

Measured on a real browser crawl of `tests/fixtures/modal_site`: six nodes for a three-page site.
`NODE a80f79 /` and `NODE 49083d /index.html` were the SAME page in the same veiled state
(identical reachable controls), and likewise for the dismissed-veil pair — but `core/urls.py::
url_template` kept the path as served, so the two forms produced different node ids. Both pairs
also filed their own OVERLAY issue for the same veil, so the duplication inflated screen counts,
coverage percentages, the bench scorecard, and a `max_screens`-bounded crawl's budget.

## What changed

- `src/autotester/core/urls.py::url_template` (`:83`) — new keyword-only parameter
  `fold_index: bool = False`. When `True`, a trailing `index.html`/`index.htm` PATH SEGMENT is
  dropped from `segments` *before* templating, so `/index.html` -> `/` and `/docs/index.html` ->
  `/docs` (matching whatever `/docs/` itself already normalises to under the pre-existing
  trailing-slash-drop rule — **not** `/docs/`, which would be a third, never-otherwise-produced
  shape and would break the function's own documented idempotence). The match is exact and
  case-sensitive: `myindex.html`, `index.html.bak`, `index.php` and `/Index.html` are all
  untouched. New module constant `_INDEX_SEGMENTS = {"index.html", "index.htm"}` (`:23`).
- **Default is `False`, not `True` — a mid-build discovery, not the original design.** Building
  this the way the brief first described (fold unconditionally inside `url_template`) broke two
  currently-passing tests in `tests/test_migrate_url_patterns.py`:
  `test_a_pattern_carrying_a_port_matches_a_host_declared_without_one` and
  `test_a_pattern_without_a_port_matches_a_host_declared_with_one`, both of which pin
  `repair("/127.0.0.1:46661/index.html", ...)` == `"/index.html"` (never `/`).
  `scripts/migrate_url_patterns.py::repair` (`:90`) calls `url_template` directly on the path
  remaining after it strips a project-declared host, and that script sits behind its own separate,
  unanswered gate (`qa/gates/t135-url-pattern-data-migration.md`) — the brief explicitly forbids
  touching it or its behaviour. Making the fold opt-in resolves this with **zero changes** to
  `scripts/migrate_url_patterns.py`: every caller that never asks for `fold_index=True` (including
  `repair`) keeps behaving exactly as it did before this unit.
- `src/autotester/core/urls.py::screen_url_pattern` (`:170`) — now calls
  `url_template(absolute_url(raw), keep_host=False, fold_index=True)`. This is the X15 boundary
  (`Screen.url_pattern`, used by `stages/ingest.py`, `stages/product_map.py`, and
  `stages/explore_status.py::login_template`) that must agree with `ScreenNode.url_template` for
  coverage to compare a video-taught screen against a crawl-observed one at all — both now fold.
- `src/autotester/stages/screen_identity.py::node_from` (`:64`) — now calls
  `url_template(observation.url, keep_host=False, fold_index=True)`, the actual site of the filed
  bug (`ScreenNode.id` is a hash of `(url_template, signature)` — `schema/screen_graph.py:79-82`).
- `tests/test_urls.py` — 15 tests added: the fold itself (root, nested-directory, `.htm`,
  query/fragment survival, host-kept forms), the `fold_index` default-off safety net tied directly
  to the discovered `migrate_url_patterns` conflict, four non-fold pins (`myindex.html`,
  `index.html.bak`, `index.php`, case-sensitivity) run *with* `fold_index=True` so the guard is
  proven under the condition where it actually matters, and `screen_url_pattern`'s own fold.
- `tests/test_screen_identity.py` — 1 test added,
  `test_index_html_and_directory_root_collapse_to_one_node_identity`, reproducing the exact AT-334
  measurement (identical controls at `/` and `/index.html`) at the `node_from` boundary — pure,
  no browser.
- No `docs/MAP.md` regeneration needed — no new module, `autotester doctor`'s generated-doc
  freshness check passed clean (see below).

## How to verify (commands + actual outputs)

```
$ uv run pytest tests/test_urls.py tests/test_screen_identity.py tests/test_migrate_url_patterns.py
..................................................................       [100%]
66 passed in 1.38s

$ uv run pytest tests/test_urls.py tests/test_screen_identity.py tests/test_explore.py \
    tests/test_explore_merge.py tests/test_coverage.py tests/test_coverage_wiring.py \
    tests/test_crawl_coverage.py tests/test_crawl_coverage_bounds.py tests/test_store_crawl.py \
    tests/test_migrate_url_patterns.py tests/test_ingest_persist.py
........................................................................ [ 43%]
........................................................................ [ 86%]
......................                                                   [100%]
167 passed

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

**RAM-gated deviation from the literal verify command (disclosed):** `uv run pytest tests/ -k "url
or explore or crawl"` as specified collects ~380 tests, including 7 files that drive a real
headless Chromium (`test_browser*.py`, `test_crawl_inventory_live.py`, `test_explore_live.py`,
`test_explore_login_spa_live.py`) plus `test_explore_modal.py`. Both the literal command and a
version with the seven live-browser files excluded were run and each hit a 100-120s timeout with
zero output in this sandboxed environment before being terminated — consistent with the brief's
own repeated "RAM is tight" warning. Ran instead: the exact two commands shown above, covering
every non-browser file whose name matches `url`/`explore`/`crawl` plus `test_ingest_persist.py`
(the other X15 producer) and `test_migrate_url_patterns.py` (the file this unit's own fold-safety
decision is about). `test_explore_modal.py` (the one file that would exercise the actual
`tests/fixtures/modal_site` fixture named in AT-334, live) was attempted once and also timed out
at 100s with no output — not retried a second time per the "at most once or twice" instruction.
Live-crawl confirmation against that fixture is left to the checker's Mode D, as the brief
permits.

## Capability coverage (each claim -> its isolating falsification)

Falsified in a throwaway copy OUTSIDE the tracked worktree, using plain stdlib `importlib`
(`core/urls.py` has zero third-party dependencies, so no `uv`/venv setup was needed —
cheaper on RAM than spinning up a second environment):
`C:/Users/Lenovo/AppData/Local/Temp/claude/d--autoTesting/dd410a44-7522-428c-9b91-fda96de822cd/scratchpad/at334-falsify/`
(`urls_fixed.py` + `falsify_driver.py`). Never used `git stash`; the tracked worktree's `git
status` before and after showed only the 4 intended files, both times.

| claim | falsifying edit (in the throwaway copy) | check | observed |
|---|---|---|---|
| The fold is load-bearing — `/index.html` really does depend on the new `if fold_index and segments and segments[-1] in _INDEX_SEGMENTS` guard | Removed the two-line fold block entirely (commented out) | `url_template("/index.html", keep_host=False, fold_index=True)` | Baseline (fixed file): `'/'`. Mutated: `'/index.html'` — RED, exactly the filed duplicate-identity bug reproduced |
| The exact-match guard (`_INDEX_SEGMENTS`, not a suffix check) is load-bearing — it is what stops the fold from over-broadening | Changed the condition to `segments[-1].endswith(".html")` | `url_template("/myindex.html", keep_host=False, fold_index=True)` | Baseline (fixed file): `'/myindex.html'`. Mutated: `'/'` — RED, `myindex.html` incorrectly swallowed exactly as the brief warned against |

```
== baseline: fixed urls.py, unmodified ==
fold /index.html -> '/' (expect '/'): PASS
non-fold /myindex.html -> '/myindex.html' (expect '/myindex.html'): PASS

== mutation 1: remove the fold entirely ==
fold /index.html -> '/index.html' (fixed gives '/'): RED as expected -- fold is load-bearing

== mutation 2: over-broaden -- strip ANY segment ending in .html ==
non-fold /myindex.html -> '/' (fixed gives '/myindex.html'): RED as expected -- exact-match guard is load-bearing

== re-check the real fixed file is untouched by either mutation file ==
fixed file still folds correctly: PASS
fixed file still guards correctly: PASS
```

Tracked worktree `git status --porcelain` immediately after, confirming the falsification never
touched it:
```
 M src/autotester/core/urls.py
 M src/autotester/stages/screen_identity.py
 M tests/test_screen_identity.py
 M tests/test_urls.py
```
(exactly the 4 files this unit intended to change.)

**Not separately falsified (mutation-style):** the `fold_index` default-off behaviour and the
`screen_url_pattern` opt-in are exercised directly by
`test_fold_index_defaults_to_off_so_migrate_url_patterns_repair_is_unaffected` and
`test_screen_url_pattern_folds_trailing_index_html_like_node_identity_does`, and by the full
`test_migrate_url_patterns.py` suite passing unmodified (66 passed, above) — the discovery that
the default-off design was *necessary* (not just convenient) was itself found by running that
suite against the first, unconditional-fold version of the code and watching it go red; that red
run is reported under "How the fold_index design was found" in Gaps below rather than repeated
here as a separate mutation, since it was the actual TDD signal that produced the current design.

## Live browser evidence

Attempted once against `tests/test_explore_modal.py` (the real fixture named in AT-334,
`tests/fixtures/modal_site`) — timed out at 100s with no output in this environment, not retried.
No other live-browser test was run. See "RAM-gated deviation" above.

## Known limits / gaps (disclosed, not claimed)

- **Persisted-id consequence (asked for explicitly).** `ScreenNode.id` is `content_id("node",
  {"t": url_template, "s": signature})` (`schema/screen_graph.py:79-82`). Any already-stored
  `crawl.json`/`portal_persona.json` node whose `url_template` ends in `/index.html` or
  `/index.htm` will get a **different id** the next time that page is templated with
  `fold_index=True` (i.e. every future `node_from` call, and every future `screen_url_pattern`
  call for `Screen.url_pattern`). Checked the real committed project data under `projects/` for
  any current impact: `grep -rl "index.html\|index.htm" projects/` finds only navigate-step
  targets and one `project.json` `base_url` (`projects/regression-demo`), never a stored
  `url_pattern` value — `projects/checkerdemo/flowspec.json` has zero `"url_pattern"` occurrences
  today, and no `portal_persona.json` exists anywhere in the repo. **So this cycle changes nothing
  on disk; the consequence is prospective**, and would first show up as a persona/screenmap
  `key()` miss (`schema/portal_persona.py:74-77`) the first time a project with a stored
  `index.html`-suffixed pattern is re-crawled or re-ingested after this fix ships. Not migrated —
  out of this unit's scope and `projects/` data is explicitly off-limits.
- **How the `fold_index` design was found, for the checker's benefit:** the brief's own design
  section described an unconditional fold inside `url_template`. Building it that way and running
  `tests/test_migrate_url_patterns.py` (part of the "-k explore or crawl or url" verify surface)
  surfaced the two failures described above — a real, measured conflict with the frozen
  `scripts/migrate_url_patterns.py::repair`, not a hypothetical one. The opt-in parameter is the
  resolution; flagged in case the checker judges a different resolution (e.g., a T-135-gate answer
  that explicitly permits touching `repair`) preferable — that gate remains unanswered and this
  unit does not touch it either way.
- RAM-gated: neither the literal `-k "url or explore or crawl"` verify command nor a live crawl of
  `tests/fixtures/modal_site` completed in this environment (both timed out); see "How to verify"
  above for exactly what ran instead and why it is judged equivalent coverage for a pure
  identity-normalisation change.
- `qa/gates/t135-url-pattern-data-migration.md` was read and is otherwise untouched — its own
  unresolved question (whether to run the migration on `projects/erp/screenmap.json`) is unrelated
  to and unaffected by this fix.
- No `qa/contracts/` file names this exact criterion; flagged above for the checker to decide
  whether X15 should gain an explicit index-alias clause or a new criterion is warranted.

## Status: ready-for-check
