# Verdict — t126-governance

**Date:** 2026-09-25 · **Checker:** /checker Mode A, sole direct checker (in-session, real re-runs) · **Bound root:** D:/autoTesting/.worktrees/t126-governance
**Cycle checked: 1** (manifest Fix cycle: 1 of 3) · **Dual check:** no (T-126 goal criticality is not `critical`)

## VERDICT: PASS

```
VERDICT: PASS
SCOREBOARD: all stated verify gates green (check_deliverable OK · doctor clean · ruff clean · test_ledger_checks 28 passed · adapter.json valid JSON, 9 read_only_allowlist entries)
CAPABILITY-COVERAGE: 1/1 reproduced (green-before "OK 1 deliverable(s) present" -> single-hunk removal of ONLY the explore_proof entry -> red-after "FAIL ... does not mention 'explore_proof'", the named done_check assertion, not a parse error). The other two manifest rows are CLI-appended data (grep before=0/after=1 per task) + a structural JSON-parse precondition, no separate isolating edit needed.
LIVE-BROWSER: not-applicable (no UI surface changed -- changed paths are qa/adapter.json config, docs/FEATURES.jsonl CLI-appended rows, docs/SNAPSHOT.md generated; none of *.tsx|jsx|vue|svelte|html|css, apps/web/**, routes/**, pages/**, components/**)
ISSUES-WRITTEN: AT-560 (medium -- read_only_allowlist _note overclaims "none write/delete"; regression_proof entry mutates+restores a tracked fixture)
EXECUTOR: claude-sonnet-subagent (manifest's Executor) (checker: claude, sole direct)
EXPLANATION: The maker-side slice of T-126 is correct and in-scope. adapter.json's read-only allowlist names scripts/explore_proof.py exactly as the T-126 done_check requires (grep -c explore_proof == 1; check_deliverable OK; reproduced by falsification). The three missing ledger rows (F-048 T-130, F-049 T-140, F-050 T-141) are appended one-per-task (no duplicates; T-142/T-143 already had F-033/F-034), all --value normal matching goal.json, all reason-prefixed "PREFILLED -- Umesh to confirm or edit." SNAPSHOT.md diff is limited to the generated normal-features line picking up F-048..050. adapter.json verify.commands (the three required gates) is byte-unchanged; the widening is a separate read_only_allowlist block, D-018 + Umesh feedback-inbox 2026-09-24 authorized. Full suite deferred by the maker on a RAM ceiling (0.68 GB free); this unit changes config + CLI-appended ledger rows only (no src/ behaviour), so the targeted test_ledger_checks.py -- the only test file reading adapter.json -- plus doctor + ruff cover it; I re-ran all of them green myself. One finding (AT-560) does not fail any T-126 contract criterion; it is an accuracy defect in the prose the maker added, filed for a follow-up reword.
```

## What I re-ran (2026-09-25, in the bound worktree)

- `uv run python scripts/check_deliverable.py --contains qa/adapter.json explore_proof` -> **OK 1 deliverable(s) present**
- `uv run autotester doctor` -> **doctor: clean**
- `uv run ruff check src tests scripts` -> **All checks passed!**
- `uv run pytest tests/test_ledger_checks.py` -> **28 passed in 32.33s** (the only test file that reads adapter.json, confirmed by the maker's `grep -rl adapter.json tests/`)
- `python -c json.load(qa/adapter.json)` -> valid; `read_only_allowlist.commands` = 9 entries
- `grep -c explore_proof qa/adapter.json` -> **1** (builder's suggested invariant)
- Diff scope base a953bc5..HEAD: 4 paths (qa/adapter.json, docs/FEATURES.jsonl, docs/SNAPSHOT.md, qa/manifests/t126-governance.md), no deletions/renames.

## Capability-coverage (reproduced in a throwaway copy, outside the worktree)

| capability | falsifying edit | red-after (named assertion) |
|---|---|---|
| adapter.json names the explore_proof allowlist entry the done_check requires | removed ONLY the explore_proof entry from verify.read_only_allowlist.commands (9 -> 8) in `$SCRATCH/t126-falsify/adapter.json` | `FAIL <copy>/adapter.json does not mention 'explore_proof'` (green-before was `OK 1 deliverable(s) present`) |

## Ledger rows (no duplicates)

`grep -c '"unit":"T-13x/14x"'`: T-130=1, T-140=1, T-141=1. Before the three `ledger add` calls the maker's grep showed 0 each (pasted in manifest). T-142/T-143 already carried F-033/F-034, correctly left untouched. All three new rows `user_value:normal`, reason prefixed `PREFILLED -- Umesh to confirm or edit.`

## Finding filed (NOT a T-126 contract failure)

- **AT-560** (medium) -- `qa/adapter.json` `verify.read_only_allowlist._note` states "Read-only/inspection ONLY: nothing here may write, push, delete or reach the network", and the manifest asserts "All nine are read-only/inspection: none write, push, delete, or reach the network." That is inaccurate for the `regression_proof.py` entry: `scripts/regression_proof.py` does `shutil.copy(LOGIN_BROKEN, tests/fixtures/regression_site/login.html)` (mutating a **tracked** fixture file) + `store.delete_case(...)`, then restores the canonical good state (line 183). Safe in practice (fixture-scoped, restored, never real/Pathlynks data per its docstring, no push, no network) but a false blanket claim in a committed security-governance file; if interrupted mid-run it could leave the fixture in the broken state. `explore_proof.py` by contrast is clean (writes/deletes only inside its own `tempfile.mkdtemp`). Remedy (maker, follow-up): reword the `_note` to "operate only within a self-created temp dir, or mutate-and-restore a local fixture; never mutate bound source outside tests/fixtures, never push, never reach the network" -- or drop the absolute "none write/delete" phrasing.

## Status: PASS — maker to merge wave/t126-governance and push (D-007).
