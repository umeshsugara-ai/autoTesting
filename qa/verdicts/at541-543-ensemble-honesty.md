# Verdict — at541-543-ensemble-honesty

**Date:** 2026-09-22 · **Cycle checked:** 1 · **Mode:** A (unit check)
**Project root (bound):** `D:/autoTesting/.worktrees/at541-543-ensemble-honesty`
**Base commit for diff scope:** 6b0e744 · **Unit commit:** 7c3626b (branch `wave/at541-543-ensemble-honesty`)
**Contract:** `qa/contracts/video-learning.md` VL3 (extended to per-provider coverage) ·
`qa/contracts/core-invariants.md` C1, C2, C3, C7

## What I re-ran (all real, all fresh)

- `uv run pytest tests/test_expand.py tests/test_schema.py tests/test_analyze_video.py tests/test_adjudicate.py tests/test_ensemble_honesty.py` → **61 passed, 1 warning in 1.08s** (matches manifest).
- `uv run ruff check src tests scripts` → **All checks passed!**
- `uv run autotester doctor` → **doctor: clean**
- `uv run pytest` (bare, `PYTHONUTF8=1`, no CLI `-q` per AT-503) → **1534 passed, 5 skipped, 32 xfailed, 1 warning in 670.38s** — matches the manifest's claimed full-suite line exactly, 0 failures.
- Targeted re-runs by name: `tests/test_expand.py -k REGRESSION_ANCHOR` → 2 passed; `tests/test_schema.py -k vision_ensemble` → 2 passed; `tests/test_bench.py -k oracle_human_trial` → 2 passed.
- Read the real diff (`git diff 6b0e744..HEAD`, `git show --name-only 7c3626b`) and the real code at `schema/analysis.py`, `stages/adjudicate.py`, `stages/analyze_video.py`, `ui/routes_sources.py`, `stages/expand.py`, `schema/project.py`, `stages/bench.py`, `cli_video.py`.

## Capability coverage — independently reproduced (3/3), own throwaway copies

Used `git archive HEAD` into three scratch dirs outside the bound tree (junctioned the existing
`.venv` in rather than reinstalling — same interpreter/site-packages, no code difference), confirmed
**green-before** in each (`6 passed` in `tests/test_ensemble_honesty.py`), applied each single-hunk
edit exactly as the manifest's table names it, and re-ran:

| row | edit applied | my result | manifest claimed |
|---|---|---|---|
| `degraded_providers` set-difference | `schema/analysis.py:93` `return sorted(...)` → `return []` | **3 failed, 3 passed** — `assert [] == ['anthropic']` | 3 failed, 3 passed — same assertion |
| `adjudicate()` threads `requested_providers` | `adjudicate.py:291` → `requested_providers=labels,` | **3 failed, 3 passed** — `assert ['gemini'] == ['anthropic', 'gemini']` | 3 failed, 3 passed — same assertion |
| **THE AT-550 regression shape**: route forwards `ready` not `ensemble` | `routes_sources.py:252` → `requested_providers=[p.label for p in ready]` | **1 failed, 5 passed** — `test_analyze_route_records_the_shrink_when_one_configured_provider_has_no_credential` fails on `assert ['gemini'] == ['anthropic', 'gemini']` | 1 failed, 5 passed — same test, same assertion |

All three isolate exactly what they claim to; the third row's fired assertion is the named
route-level regression, not a collateral failure. No row survived. No UNVERIFIED rows in the
manifest to judge as debt.

## Diff scope (4c)

`git diff 6b0e744..HEAD --stat`: `docs/SNAPSHOT.md` (1/1, decision rolling-window line, auto-regenerated —
consistent with the pre-existing `AT-557` finding that `doctor` wanted a snapshot regen; my own
`doctor` run is clean, confirming this is the expected side effect, not an undisclosed touch),
`qa/manifests/...` (new), `schema/analysis.py` (+21), `stages/adjudicate.py` (+15/-15, docstring
trims to hold the 300-line cap), `stages/analyze_video.py` (+14/-3), `ui/routes_sources.py` (+8/-1),
`tests/test_ensemble_honesty.py` (new, +219). No existing function, class, route, test, or config
key was deleted or renamed. Commit `7c3626b` carries only these paths (C10 — `git show --name-only`
confirmed).

## Retro-coverage — AT-541/542/543 (bare commits df529f2/a5e5b81), independently re-verified

No code changed for these three this cycle; I read the shipped code directly, not the manifest's
description of it.

- **AT-541** — `expand.py:33` `CLASS_DESCRIPTIONS[CaseClass.REGRESSION_ANCHOR]` present; `applicable_classes()` appends it at `:76`. Real. Ledger flipped `open → fixed`.
- **AT-542** — `project.py:61-70` `ProviderConfig.vision_ensemble()` present and wired at both call sites (`routes_sources.py:245`, `cli_video.py:248`). Real. Ledger flipped `open → fixed` (code-wiring claim only — the `projects/erp` stale-data evidence in that ledger row describes old artifacts, not something new code retroactively changes).
- **AT-543** — `bench.py:52` `oracle_human_trial(..., duration_s: float | None = None)`, scores `0.0` when unset, never a hardcoded literal; sole caller in `bench_trial.py` passes a real measured value. Real. Ledger flipped `open → fixed`.
- **AT-547 (bypass, governance)** — its own `expected` field asked for exactly this: a retro-manifest + a dispatched Mode A check. Both now exist (this manifest, this verdict). Ledger flipped `open → fixed`.

## AT-550 — the new defect, judged directly

**Genuinely fixed, half of it.** `VideoAnalysis.requested_providers`/`degraded_providers`
(`schema/analysis.py:59-93`) are threaded through `adjudicate()` → `analyze()` →
`routes_sources.py:252` exactly as the manifest describes, mutation-verified above. A degraded run
now persists, on disk, a field pair that distinguishes "asked for 2, 1 answered" from "asked for 1,
1 answered" — something the pre-fix artifact could not do at all. That is real and is what VL3
(extended to per-provider coverage) asks for: "in a field, not a log line."

**Not fully fixed — the ledger's own `AT-550` (the `checker-sweep` row, distinct per AT-553's
discriminator convention from an unrelated `checker-unit` AT-550 elsewhere in the same file) asked
for two things, and only one is done:**

1. *Record the shrink* — DONE, verified above.
2. *"Make the empty-config default explicit (refuse, or default-with-note) instead of a silent
   `['gemini']`"* — **NOT done.** `project.py:70` still reads `return seen or ["gemini"]`,
   byte-identical to before this cycle. The manifest never claims to touch this, but its "Issues
   addressed" line lists bare `AT-550 (new, this cycle)`, which reads as full closure of that
   ledger row. It is not. I left that row **open** (not `fixed`) in the ledger and recorded exactly
   which half remains, so a future unit inherits an accurate row rather than a falsely-closed one.

**Also found, not blocking:** nothing downstream reads `degraded_providers` yet. `cli_video.py:262`'s
green/PARTIAL indicator and `routes_sources.py:213`'s `remove_missing=analysis.is_complete` are both
still driven by `observations_expected`, which for the **UI route specifically** is computed from
`ready` (the credential-filtered list), not the newly-added `requested_providers`. So a UI-triggered
degraded run still shows *complete*, not *PARTIAL*, in the one place a human currently sees this
number (the CLI's own coverage line, when re-run against the same project). This mirrors the
project's own already-accepted `AT-207` pattern — a field is written and true, but not yet consumed
by any display — and I judge it the same way: **not a VL3 violation** (VL3's letter, "in a field,"
is satisfied), but a real residual, now recorded in `AT-550`'s ledger note rather than silently
dropped. The manifest's own "Known limits" section partially discloses the opt-in-caller risk but
does not name this specific gap; I've made it explicit.

**Net judgement:** the criterion the contract actually states (VL3, extended) is met and
independently verified. The broader ask a *different* document (the sweep-filed ledger row) bundled
alongside it is half-done and now accurately tracked as such — this is a disclosed residual, not a
criterion failure, so it does not fail the unit.

## Mode D — UI surface, judged not to require a live browser

`ui/routes_sources.py` is a UI surface by path, but the diff itself is not a UI-behaviour change:
`_refusal()` (the error path) is untouched, and the success path is still a bare `303` redirect —
identical response shape before and after, confirmed by reading the route in full, not just the
diff hunk. The only change is one added keyword argument to an internal call. The two new
`TestClient` tests (`test_analyze_route_records_the_shrink_when_one_configured_provider_has_no_credential`,
its mirror) exercise the real ASGI route end-to-end and assert on the persisted artifact, which is
what actually changed. I judge a live browser unnecessary here and the integration tests adequate —
there is no rendered HTML difference to observe with one.

## Ledger

Flipped `open → fixed`: **AT-541, AT-542, AT-543, AT-547**. Left open with a detailed partial-fix
note: **AT-550** (`checker-sweep` row, line 547 pre-edit) — see its `checker_note` for exactly what
remains. No new issue ids minted (folded the residual into the existing row per AT-553's
already-established discriminator convention, avoiding further id churn in a file that already
documents twelve colliding rows). `qa/issues.jsonl` re-validated line-by-line as valid JSON after
edits (560 lines, unchanged count).

## Capability coverage / invariants not otherwise in scope

I-VL5/I-VL6 (severity merge, no model in adjudication) are untouched by this diff — `adjudicate`'s
merge logic is unchanged; only its signature grew a keyword-only parameter. Not scored, not claimed.

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met (VL3-extended, C1, C2, C3, C7), 0/0 invariants in scope
FAILURES (if any):
- none at >80% confidence severity
CAPABILITY-COVERAGE: 3/3 rows reproduced
LIVE-BROWSER: not-applicable (ui/routes_sources.py:239-252 — response shape unchanged, TestClient integration adequate, confirmed by reading the full route)
ISSUES-WRITTEN: none new (updated: AT-541, AT-542, AT-543, AT-547 -> fixed; AT-550 checker-sweep row annotated partial-fix, left open)
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All required verify commands, the full 1534-test suite, and all three capability-coverage mutations reproduced exactly as the manifest claimed, in my own throwaway copies. AT-541/542/543's retro-fixes are real, independently re-read in the shipped code and re-tested by name. AT-550's core claim (a degraded run now persists a visible requested-vs-actual record) holds under mutation. The unit's own "Issues addressed" line overclaims AT-550 as fully closed when the ledger row's second ask (explicit empty-config handling) is untouched and no consumer yet renders the degradation signal to a human -- both now recorded in the ledger rather than passed over, consistent with this project's AT-207 precedent for a written-but-unconsumed field. Neither gap violates the stated VL3 criterion, so the unit PASSes with the residuals disclosed.
```
