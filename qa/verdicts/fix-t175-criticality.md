# Verdict — fix-t175-criticality

**Date:** 2026-09-24
**Cycle checked:** 1
**Checker:** claude-sonnet-subagent (fresh context, Mode A unit check)
**Bound root:** D:/autoTesting/.worktrees/fix-t175-criticality (branch wave/fix-t175-criticality, head 9c78eb0)
**Contract:** qa/contracts/core-invariants.md + authority D-041 (docs/DECISIONS.md) + tests/test_goal_criticality_vocabulary.py

## What I re-ran myself

- `PYTHONUTF8=1 uv run --project . --directory . pytest tests/test_goal_criticality_vocabulary.py tests/test_goal_done_checks.py`
  → `10 passed in 0.09s` (matches manifest's pasted output).
- `PYTHONUTF8=1 uv run --project . --directory . ruff check src tests scripts` → `All checks passed!`
- `PYTHONUTF8=1 uv run --project . --directory . autotester doctor` → `doctor: clean`
- Independently re-scanned all 64 `.goal/goal.json` task rows in Python (`base_criticality not in {"low","medium","high","critical"}`) → `bad rows: []`. Confirms the manifest's claim that T-175 was the only offender and no other row is now out of vocabulary.
- `git diff 82ef224 9c78eb0 --stat` → exactly three paths: `.goal/dashboard.html` (2 +-, timestamp-only), `.goal/goal.json` (12 +-: T-175's `base_criticality`/`criticality` + top-level `updated`/`analytics.velocity_per_day`/`analytics.eta_days`/`last_deterministic_tick`), `qa/manifests/fix-t175-criticality.md` (new, 49 lines). Full diff of `.goal/goal.json` confirms no other task row's block is touched. Diff-scope claim holds.
- Confirmed a concurrent full-suite pytest was running from the sibling `t170-network-assertions` worktree at check time (`Get-CimInstance Win32_Process` showed live `uv run pytest` / `pytest.exe` processes rooted there). Independently judged the full suite is **not required** for this unit: the only two test modules in the tree that read real `.goal/goal.json` content for `base_criticality`/`criticality` are the two named and already re-run (`test_ledger_checks.py` only writes a synthetic goal.json to a tmp dir; `test_goal_done_check_shapes.py`'s own docstring says the real-file scanning tests live in `test_goal_done_checks.py`). The manifest's declared gap (RAM-driven, full suite deliberately skipped) is accepted; no full-suite run was needed or attempted by this check either, avoiding a second concurrent pytest process on the same machine.
- D-041 read in full: its `Changes-authorized` line explicitly covers "`.goal/goal.json`: register T-172 to T-178" with `Approved-by: Umesh`. This unit corrects a value within that same authorized registration (T-175's row), not a new or out-of-scope edit — authority holds.
- `qa/issues.jsonl` scanned for any row referencing goal task T-175 (exact-match, not substring): none found (`AT-175` is an unrelated pre-existing video-learning issue). Manifest's "Issues addressed: none" is accurate — no ledger row to flip.

## Judgement on the three questions posed

(a) **"medium" is in the classifier vocabulary** (`{"low","medium","high","critical"}`, confirmed against `tests/test_goal_criticality_vocabulary.py:31`) **and is a reasonable mapping.** T-175 is a behaviour-preserving refactor (moving prompts to `SKILL.md` under the provider seam, D-041) — not touching production data or an irreversible/outward-facing action (ruling out `high`/`critical`), but grouped under D-041's considered set of seven new units rather than being a cosmetic no-op (ruling out `low`). `user_value: "normal"` on the same row is confirmed untouched and is correctly a separate field. Reasonable.

(b) **Re-scanned all rows myself** (Python, independent of the manifest's claim) — zero out-of-vocabulary `base_criticality` values remain anywhere in the file. T-175 was the only offender, now fixed.

(c) **Manifest's declared gap (full suite not run, RAM/concurrency reason) is accepted** — I independently verified a full-suite pytest actually was running concurrently from another worktree, and independently judged (not merely deferred to the manifest) that the full suite is not required for this change's blast radius. No full suite was run by this check.

## Capability coverage — reproduced independently

Reproduced in a throwaway copy **outside** the bound root (`C:\Users\Lenovo\AppData\Local\Temp\claude\...\scratchpad\fix-t175-repro`, containing only `tests/test_goal_criticality_vocabulary.py` + `.goal/goal.json` copied from the bound tree — never edited in place):

- **Green before** (copy of the current, post-fix `.goal/goal.json`): `pytest tests/test_goal_criticality_vocabulary.py::test_every_base_criticality_is_a_value_the_classifier_recognises` → `1 passed in 0.07s`. Proves the copy is real.
- **Falsifying edit** (single-hunk, scripted, applied only to the copy): T-175's `base_criticality` → `"normal"`, `criticality` → `"low"`.
- **Red after**: same test → `1 failed` — `AssertionError: ... downgrading them to 'low': {'T-175': 'normal'}`. Isolates exactly T-175, exactly the vocabulary assertion named in the manifest's row. Matches the manifest's claimed before/after exactly.

The bound working tree was never edited.

## Verdict

```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (C9 — declared control value honoured, applied to this correction), 0/0 other invariants at issue
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 1/1 rows reproduced
LIVE-BROWSER: not-applicable (changed paths: .goal/goal.json [data], .goal/dashboard.html [regenerated by monitor.py, not hand-edited], qa/manifests/fix-t175-criticality.md — no *.tsx/jsx/vue/svelte/html/css application UI, route, page, or component touched)
ISSUES-WRITTEN: none
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: A single-value data correction to T-175's registration row (base_criticality/criticality "normal"/"low" -> "medium"/"medium"), scoped exactly as D-041's Changes-authorized permits, re-verified by re-running the two named test modules plus ruff and doctor (all green, matching the manifest), an independent re-scan of all 64 rows confirming no other out-of-vocabulary value remains, and an independent reproduction of the capability-coverage row in a throwaway copy outside the bound root. No UI surface touched; full test suite correctly judged unnecessary for this change's blast radius and correctly not run given a concurrent full-suite process elsewhere on the machine.
```
