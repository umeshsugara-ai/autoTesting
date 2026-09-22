# Verdict — at550-empty-config

**Date:** 2026-09-22
**Cycle checked:** 1
**Project root (bound):** D:/autoTesting/.worktrees/at550-empty-config
**Base commit:** 0cc0df5 · **Unit commit:** 2ae9bd4 (branch wave/at550-empty-config)

## What I re-ran myself

- `PYTHONUTF8=1 uv run pytest tests/test_schema.py tests/test_ensemble_honesty.py tests/test_analyze_video.py tests/test_adjudicate.py -v`
  → `54 passed, 1 warning in 1.11s` (matches manifest exactly).
- `uv run pytest` (full suite, bare, no `-q`, AT-503) → `1538 passed, 5 skipped, 32 xfailed, 1 warning in 633.60s`, exit 0. Whole-log scan for `FAILED`/`ERROR`/`^E` — none. No regression anywhere else in the tree.
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `git diff 0cc0df5..HEAD --stat` and the full diff for every changed file (4c).
- `grep -rn "DEFAULT_VISION_PROVIDER\|_configured_vision_providers\|def vision_ensemble"` over `src/` to confirm single definition.
- Capability row 1 reproduced in a throwaway `git archive HEAD` copy at
  `<scratch>/at550ec-row1` (outside the bound tree, `uv sync`'d its own venv — never edited
  the bound working tree).

## Criteria judged

**VL3 (`qa/contracts/video-learning.md`)** — MET. The fix is pure observability: no hard
error, no non-empty-config requirement was introduced. `ProviderConfig.vision_ensemble()`'s
return value for an empty config is still `self._configured_vision_providers() or
[DEFAULT_VISION_PROVIDER]` — byte-identical to before (confirmed in the diff and by
`tests/test_schema.py::test_vision_ensemble_empty_config_falls_back_to_gemini`, unchanged and
still green). `vision_config_defaulted` is the additional field that makes a substituted
default distinguishable from an explicit `vision="gemini"` on the persisted `VideoAnalysis`,
extending the same AT-550-CORE conduit (`requested_providers`/`degraded_providers`) with one
more `bool = False` field — safe default for every pre-existing persisted analysis. This is
the "default-with-note" remedy named in the open AT-550 (checker-sweep) ledger row, the second
of its two accepted options; single-credential degrade-never-die policy is untouched.

**VL4 (adjudication purity)** — MET, unaffected. `adjudicate` gained one more plain-data
keyword (`vision_config_defaulted: bool = False`) threaded straight onto the constructed
`VideoAnalysis`; no provider, clock, or randomness touches it. The sort key and merge logic
are untouched (diff shows only docstring reflow in that region, content preserved).

**core-invariants C9 (a control value is honoured, never silently substituted with a weaker
default)** — MET. This is the exact shape the unit closes: an empty `vision` config used to
silently substitute a default with nothing recording that it happened; now the substitution is
recorded.

**core-invariants C1/C2/C3 (schema-first, size caps, one-concept-one-place)** — MET.
`DEFAULT_VISION_PROVIDER` and `_configured_vision_providers()` are each defined exactly once
(`schema/project.py:10`, `:67`); both `vision_ensemble()` and `vision_ensemble_defaulted()`
call the one parser rather than duplicating split/strip/dedupe logic — confirmed by reading
both bodies. `adjudicate.py` sits at exactly 300/300 lines and `adjudicate()` at 47/50;
`analyze_video.py` at 189/300 and `analyze()` at 48/50 — under caps, and `doctor` independently
confirms clean. The docstring reflow in both files preserves content (compared old vs. new
prose in the diff line by line) rather than deleting it.

## Capability coverage — 1/1 rows reproduced (row 2 is a documented non-isolating mirror)

| row | check | result |
|---|---|---|
| 1 | `test_vision_ensemble_defaulted_distinguishes_empty_from_explicit_gemini` + `test_analyze_route_records_the_default_when_vision_config_is_empty` | **Reproduced.** In throwaway copy: GREEN before (`3 passed` on the three named tests) → falsifying edit (`vision_ensemble_defaulted()` body → `return False`) → **RED for the right reason** (`2 failed, 1 passed`; both failures are `assert False is True` on the exact two named tests, i.e. the assertion the check is named for, not a parse/import cascade) → GREEN after revert (`3 passed`). |
| 2 | `test_analyze_route_records_no_default_when_vision_is_explicitly_gemini` | Manifest discloses this row cannot isolate the defect alone (it asserts `False`, which the falsifying edit also produces) — confirmed: it is the one test that stayed green through row 1's red step above, exactly as claimed. Included honestly as the honesty mirror, not misrepresented as an independent isolator. Not a coverage gap: row 1 is what actually falsifies the capability.

No capability was claimed with zero rows, and no row's edit survived.

## Diff scope (4c)

`git diff 0cc0df5..HEAD --stat`: `qa/manifests/at550-empty-config.md`,
`src/autotester/cli_video.py`, `src/autotester/schema/analysis.py`,
`src/autotester/schema/project.py`, `src/autotester/stages/adjudicate.py`,
`src/autotester/stages/analyze_video.py`, `src/autotester/ui/routes_sources.py`,
`tests/test_ensemble_honesty.py`, `tests/test_schema.py` — every path is named in the
manifest's "What changed" or capability-coverage table; nothing else touched. Read every `-`
line of the full diff: no function, class, export, route, test, or config key was deleted or
renamed — every removed line is a docstring/signature line immediately replaced by the
rewritten version of the same function (`vision_ensemble()`, `adjudicate()`, `analyze()`),
not a deletion.

## Issues addressed

`qa/issues.jsonl` line 547, `AT-550` (checker-sweep, `feature: living-ledger`) — flipped
`open → fixed` in this check. Its cycle-1 checker_note already left the empty-config half
explicitly open ("the empty-config half remains"); this unit closes exactly that half via the
"default-with-note" remedy the row itself names as accepted. Appended a checker_note citing
the independent reproduction above rather than trusting the manifest's claim. (Distinct from
the unrelated `AT-550` at line 553, a checker-unit capability-coverage finding on
`at540-assertion-layer` — not touched.)

## Live browser

**Not applicable.** Changed paths this cycle are schema/record layer
(`schema/project.py`, `schema/analysis.py`) plus two pure-pipeline stages
(`stages/adjudicate.py`, `stages/analyze_video.py`) plus two callers
(`ui/routes_sources.py::analyze_source`, `cli_video.py::analyze_cmd`). Verified the UI claim
myself rather than taking the manifest's word: read `routes_sources.py:220-256` — the route
decorator, refusal branches, and final `RedirectResponse(..., status_code=303)` are all
byte-identical to before; the only change is one new kwarg into the existing `analyze(...)`
call. No new route, no template touched (`grep` over `src/autotester/ui` for
`vision_config_defaulted`/`degraded_providers` finds only `routes_sources.py`, no `.html`).
`test_analyze_route_records_the_default_when_vision_config_is_empty` and its mirror already
drive the real route end-to-end via `TestClient` (not mocked) and assert on the persisted
artifact and the real 303 status — adequate independent coverage for a route that renders
nothing new. Judged honestly per the dispatch's own steer: persistence-layer-only claim holds.

## VERDICT

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met (VL3, VL4, C9, C1/C2/C3), 0/0 invariants newly at risk
FAILURES (if any): none
CAPABILITY-COVERAGE: 1/1 rows reproduced (row 2 is a disclosed non-isolating honesty mirror, not a coverage gap)
LIVE-BROWSER: not-applicable (schema/record layer + thin route pass-through, verified against the diff; route-level TestClient tests exercise the real route)
ISSUES-WRITTEN: none new; AT-550 (qa/issues.jsonl line 547) flipped open -> fixed
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: The empty-vision-config silent-default gap (AT-550's second, disclosed-open half) is now observable on the persisted VideoAnalysis via vision_config_defaulted, sourced from a single shared parser with no behavior change to the fallback value itself. Independently reproduced the falsification in a throwaway copy outside the bound tree (green -> red-for-the-right-reason -> green), full suite stays green (1538 passed, 0 failed), doctor and ruff are clean, and the diff touches only the files the manifest names with no deletions.
```
