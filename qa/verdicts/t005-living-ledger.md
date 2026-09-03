# Verdict — t005-living-ledger

**Date:** 2026-09-03 · **Checker:** /checker (Mode A, fresh subagent, bound to `D:/autoTesting`)
**Contract:** `qa/contracts/living-ledger.md` L1–L7 + `qa/contracts/core-invariants.md` C1–C8
**Manifest:** `qa/manifests/t005-living-ledger.md` · **Cycle checked: 2**

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met (L1–L7), 8/8 invariants hold (C1–C8)
FAILURES: none
ISSUES-WRITTEN: none new · AT-019, AT-020, AT-022 → fixed · AT-013 → verified · AT-021 stays OPEN (claimed fixed, not reproduced)
EXPLANATION: The cycle-1 failure (C2) is closed on my own runs: ARCHITECTURE.md is 135 lines, the generated sections live in a routed, self-describing docs/MAP.md whose staleness doctor catches, and check_architecture_budget fires on a 155-line scratch copy. Contract L1 folded as a routine, non-weakening amendment (cap untouched). AT-021 is NOT fixed at the user-facing surface: `autotester doctor` still prints a traceback on a broken or duplicate FEATURES.jsonl row because run() calls check_generated_fresh (→ render_snapshot → load_events) before check_ledger gets to catch it; the maker's test asserts check_ledger in isolation. No criterion depends on it (fail-closed), so it stays an open S3, not a FAIL.
```

## What I re-ran (all from `D:/autoTesting`, working tree as submitted)

| Command | Result |
|---|---|
| `uv run pytest -q` | 69 passed, exit 0 |
| `uv run pytest tests/test_ledger.py -q` | 19 passed, exit 0 |
| `uv run ruff check src tests` | All checks passed! |
| `uv run autotester doctor` | doctor: clean, exit 0 |
| `wc -l docs/ARCHITECTURE.md docs/MAP.md docs/SNAPSHOT.md` | 135 / 73 / 29 |
| `uv run autotester snapshot --print \| wc -l` | 30 (≤ 60) |
| `uv run autotester ledger check` | "every closed high-value task has a row", exit 0 |
| `uv run autotester ledger relitigation "browser session with persistent profile"` | "no gate — no retired features (rule)", exit 0 |
| **L1 rot:** first docstring line of `core/ids.py` changed → doctor | `stale-generated: docs/MAP.md — generated sections differ; run autotester map`, exit 1; `map` → clean; `git checkout` + `map` restored; doctor clean |
| **L1 (goal.json):** T-010 title edited → doctor | `stale-generated: docs/SNAPSHOT.md`, exit 1; byte-restored (cmp), doctor clean |
| **L6:** MAP.md row removed from the CLAUDE.md router → doctor | `doc-unrouted: docs/MAP.md`, exit 1; byte-restored (cmp), doctor clean; router has 8 rows for 7 `docs/**/*.md` + archive index |
| **L6:** `MEMORY.md` | one pointer line to `autotesting-router.md` |
| **L5:** `powershell -File qa/hooks/mc-sessionstart.ps1` | status line, then `--- docs/SNAPSHOT.md ---` + full snapshot (32 lines total) |
| **L7:** `git log --numstat -- docs/DECISIONS.md` + working tree | 71/0 committed, 12/0 uncommitted — additions only; D-000..D-006 present; `decisions-append-guard.ps1` wired in `.claude/settings.json` |
| **C8:** `grep -rE "^(import\|from) (anthropic\|google\|openai)" src/autotester/` | nothing |
| **C5:** `git ls-files \| grep -E "\.env$"` | nothing |
| **C2 budget (AT-019):** scratch copy of ARCHITECTURE.md padded to 155 lines → `doctor.check_architecture_budget` | `architecture-too-long: docs/ARCHITECTURE.md — 155 lines > 150; move detail to a routed doc` |
| **AT-020:** copy of line 1 (F-001) appended to FEATURES.jsonl | `load_events` raises `FEATURES.jsonl:3: duplicate id F-001 (rows are append-only)`; `ledger check` exit 1; restored (cmp) |
| **AT-022:** scratch ledger with 11 high live features → `render_snapshot` | 8 shown + `+3 more high-value features → docs/FEATURES.jsonl`; 37 lines, no raise |
| **AT-021:** duplicate-id row / broken-JSON row / retired-with-`update` row → `uv run autotester doctor` | full Python traceback each time, 0 `ledger-invalid` lines (exit 1, fail-closed). `check_ledger(root)` alone returns `ledger-invalid: … duplicate id F-001`; `check_generated_fresh(root)` raises ValueError. **Not fixed at the CLI.** |

Every probe edit restored; `git status` after the check shows the same modified/untracked set as at the start of the check plus only the checker-owned files below.

## Contract maintenance (this check)

- `qa/contracts/living-ledger.md` L1 amended (routine, pre-declared at cycle 1): generated sections in `docs/MAP.md`; doctor fails when MAP.md or SNAPSHOT.md differ from regeneration; ARCHITECTURE.md ≤ 150 doctor-enforced. Reason in the amendment log. Nothing weakened; the C2 cap is untouched.

## Manifest citations judged

- **AT-019 (S2):** fixed and reproduced — relocation + doctor rule + 135 lines. Flipped.
- **AT-020 (S3):** fixed at the load level (the fix direction asked for exactly this). Flipped.
- **AT-022 (S3):** roll-up present and exercised past the cap. Flipped.
- **AT-021 (S3):** claim not reproduced — stays `open` with the cycle-2 evidence appended. The test `test_doctor_reports_a_broken_ledger_instead_of_raising` targets `check_ledger`, not `doctor.run()`; the issue text already named the ordering (`check_generated_fresh` before `check_ledger`). Fix: guard `render_snapshot` in `check_generated_fresh` (skip freshness when the ledger is invalid) or run `check_ledger` first; assert on `run()`.
- **AT-013:** re-read the L7 backfill line against `docs/DECISIONS.md` → `verified`.

## /goal

PASS → **T-005 closed** via `goal_cli.py done --task-id T-005`. T-005 is `user_value: high`: **the maker must append the `FEATURES.jsonl` `live` row at close-out** (`autotester ledger add … --verdict qa/verdicts/t005-living-ledger.md`, prefilled reason confirm-or-edit) — `ledger check` / doctor `ledger-row-missing` will flag its absence, and the next sweep flags it under L3.

## Next unit should carry

- AT-021 (open S3): make `doctor.run()` report `ledger-invalid` instead of tracebacking — one guard, one test on `run()`.
