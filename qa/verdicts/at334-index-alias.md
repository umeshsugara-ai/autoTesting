# Verdict — at334-index-alias

**Date:** 2026-09-26
**Cycle checked:** 1
**Checker:** /checker (standing checker session, orchestrator plus 2 fresh-context lenses; the decisive finding was reproduced by the orchestrator itself)
**Contract:** qa/contracts/explore.md (screen identity), qa/contracts/coverage.md V1 (both sides of a coverage diff normalised the same way); issue AT-334
**Branch / code commit:** at334-index-alias · 78a144d (manifest aece107)

```
VERDICT: FAIL
SCOREBOARD: 1/2 criteria met (AT-334 node identity folds: met; one identity across the Screen/coverage seams: NOT met), 2/3 invariants hold (C2 caps and C7 sabotage rows hold; coverage.md V1 same-normalisation broken)
FAILURES:
- [coverage.md V1 / AT-334] sev: high · the fold is applied at node identity only (screen_identity.node_from, urls.screen_url_pattern). explore_merge.screen_from:73, coverage._path_of:30 and merge_flowspec:172 still call url_template unfolded, so an index-first crawl persists Screen.url_pattern '/index.html', and a run visiting '/' is reported as a false CoverageGap. That is a regression: on master both paths were known screens · pass fold_index=True at every call that produces or compares a screen identity (or derive Screen.url_pattern from the already-folded node template without its host), and add a test where an index-first crawl plus a '/' visit gives no gap, in both orders · issue: AT-618
CAPABILITY-COVERAGE: 2/2 manifest rows reproduced + 1 extra checker row (node_from with fold_index=False turns test_index_html_and_directory_root_collapse_to_one_node_identity red, so the second site is pinned)
LIVE-BROWSER: SKIP (deferred to cycle 2: the unit already fails on a reproduced code-level regression, and Mode D on tests/fixtures/modal_site runs against the fixed cycle)
ISSUES-WRITTEN: AT-618
EXECUTOR: maker builder (checker: claude-opus orchestrator + sonnet subagents)
EXPLANATION: The fold itself is correct and well-pinned: 16 tests, the edge cases behave, both sabotage rows kill, and the opt-in default that protects scripts/migrate_url_patterns.py::repair is a reasonable disclosed choice. But folding identity at 2 of the 5 seams creates exactly the disagreement coverage.md V1 forbids, and the reproduction shows it turns a covered page into a reported gap.
```

## Reproduction (orchestrator, real functions; master vs branch, same venv)

```
node_from(http://127.0.0.1:8765/index.html) then node_from(.../), dedupe by node id (first seen wins),
screen_from each, coverage._known_paths, then ask whether a run visiting '/' is a gap:
master  nodes: 2 screen patterns: ['/', '/index.html'] | run visits '/': gap = False
at334   nodes: 1 screen patterns: ['/index.html'] | run visits '/': gap = True
```

`grep -rn "url_template(" src/ scripts/` on the branch lists these callers:
- They pass `fold_index=True`: urls.py:170 and screen_identity.py:70.
- They do NOT: coverage.py:30, explore_merge.py:73 and merge_flowspec.py:172.
- The disclosed exception: scripts/migrate_url_patterns.py:101.

## What passed

- Targeted: `tests/test_urls.py tests/test_screen_identity.py tests/test_migrate_url_patterns.py` gave 66 passed. ruff reported `All checks passed!` and doctor reported `doctor: clean`.
- Row 1 (fold removed) gave 8 red on the named index assertions. Row 2 (over-broadened to `*.html`) gave 3 red, including `test_myindex_html_is_not_folded` and the case-sensitivity test.
- Edge cases: `/index.html?x=1`, `#frag`, `/INDEX.HTML` (not folded, case-sensitive), `/docs/index.htm`, `/index.html/`, `/a/index.html.bak` and `/myindex.html` all follow the documented rule.
- 4c: only urls.py, screen_identity.py, two test files and the manifest changed, with no deletions and the caps held.
- The full suite was started on the tip. Its result is appended below when it lands; it cannot change this FAIL.

- **Addendum:** the full-suite run was stopped by the checker after the FAIL was established, to free RAM for the next unit in the queue. Cycle 2 re-runs the full suite and Mode D.
