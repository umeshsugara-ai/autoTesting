# Verdict — t005-living-ledger

**Date:** 2026-09-03 · **Checker:** /checker (Mode A, fresh subagent, bound to `D:/autoTesting`)
**Contract:** `qa/contracts/living-ledger.md` L1–L7 + `qa/contracts/core-invariants.md` C1–C8
**Manifest:** `qa/manifests/t005-living-ledger.md` · **Cycle checked: 1**

```
VERDICT: FAIL
SCOREBOARD: 7/7 criteria met (L1–L7), 7/8 invariants hold (C2 fails)
FAILURES:
- [C2] docs/ARCHITECTURE.md is 200 lines > the 150-line cap, and doctor has no rule for the cap so `autotester doctor` reports clean · move the two generated sections to a routed sibling doc (docs/MAP.md; checker will fold that as a routine L1 amendment at cycle 2) or compact the prose, AND add a doctor rule for the cap; raising the cap itself is a critical amendment only Umesh can grant · issue: AT-019
ISSUES-WRITTEN: AT-019, AT-020, AT-021, AT-022
EXPLANATION: Every living-ledger criterion reproduced on my own runs — rot test, snapshot staleness after a goal.json edit, hook injection, router removal/dangling, append-only history with the deny hook, confidence-gated relitigation. The unit fails on the project-wide invariant C2: adding ~66 generated lines pushed ARCHITECTURE.md to 200 lines against an explicit 150 cap that the previous check (AT-008) tracked at 121, and nothing in doctor enforces it. Three S3 hardening findings (hand-pasted duplicate id passes doctor; doctor tracebacks instead of reporting `ledger-invalid`; no roll-up for high features) do not fail a criterion today but are logged.
```

## What I re-ran (all from `D:/autoTesting`, working tree as submitted)

| Command | Result |
|---|---|
| `uv run pytest tests/test_ledger.py -q` | 15 passed, exit 0 |
| `uv run pytest -q` | 65 passed, exit 0 |
| `uv run ruff check src tests` | All checks passed! |
| `uv run autotester doctor` | doctor: clean, exit 0 |
| `uv run autotester ledger check` | "every closed high-value task has a row", exit 0 |
| `uv run autotester ledger relitigation "browser session with persistent profile"` | "no gate — no retired features (rule)", exit 0 |
| `uv run autotester snapshot --print \| wc -l` / `wc -l docs/SNAPSHOT.md` | 30 / 29 (≤ 60) |
| `uv run autotester map && uv run autotester snapshot` then doctor | no change to either file; doctor clean (both docs are uncommitted, so `git diff --exit-code` is vacuous — the regenerate-then-compare is the real test) |
| **L1 rot:** first docstring line of `core/ids.py` changed → doctor | `stale-generated: docs/ARCHITECTURE.md — generated sections differ; run autotester map`, exit 1; `git checkout` restored; doctor clean |
| **L1 (goal.json):** T-010 title edited in `.goal/goal.json` → doctor | `stale-generated: docs/SNAPSHOT.md — differs from regeneration`, exit 1; byte-restored; doctor clean |
| **L5:** `powershell -File qa/hooks/mc-sessionstart.ps1` | status line, then `--- docs/SNAPSHOT.md ---` + the full snapshot. The DECISIONS index (D-000..D-006, computed status) is printed by the sibling SessionStart hook `.claude/hooks/lab-session-start.ps1` (ran it with a startup payload) — both are injected, which is the criterion's point |
| **L6:** archive row deleted from the CLAUDE.md router → doctor | `doc-unrouted: docs/archive/INDEX.md`, exit 1; router pointed at `docs/archive/GHOST.md` → `router-dangling` too; restored (cmp-verified) |
| **L6:** `MEMORY.md` | one pointer line to `autotesting-router.md`; nothing else duplicated |
| **L7:** `git log --numstat -- docs/DECISIONS.md` + working tree | 71/0 committed, 12/0 uncommitted — additions only |
| **L7:** `decisions-append-guard.ps1` with an Edit payload on `docs/DECISIONS.md` (also via the exact stdin form in settings.json) | `permissionDecision: deny`; Write on `scripts/append_decision.ps1` → `ask` |
| **C8:** `grep -rE "^(import\|from) (anthropic\|google\|openai)" src/autotester/` | nothing |
| **C5:** `git ls-files \| grep -E "\.env$"` | nothing |

## Adversarial probes

- **(a) Hand-editing FEATURES.jsonl.** Unknown key → doctor fails (extra="forbid"). Retired row with reason `update` → fails. Retro-editing the reason of a `high` row → snapshot goes stale, doctor fails. **But** a hand-pasted duplicate `F-001` line passes doctor and `ledger check` silently (only `append_event` checks ids) → **AT-020**. And the failures above surface as a raw Python traceback from `check_generated_fresh`, not as a `ledger-invalid` violation → **AT-021** (fail-closed, so not a criterion failure). A `retired` row for a feature that was never live, or `supersedes` pointing at a non-existent id, is accepted — noted, not filed (no criterion).
- **(b) Snapshot determinism.** `render_snapshot` reads only the ledger, ARCHITECTURE prose, goal.json, and DECISIONS; the 30-day window anchors on `max(e.date)` in the ledger (render.py:134). Python probe: ledger with an `updated` row 2026-01-10 and latest row 2026-06-01 → the update is outside the window regardless of today's date; adding a row moves the anchor deterministically. No `date.today()` on the read path (only as the default when writing a row). Holds.
- **(c) Relitigation gate.** With a retired "OTP via email link" row: "2FA handling for login" → judge called (mock with no queued response raises `ProviderError`, i.e. the rule never answered "no match"); "re-add F-099" (an id that matches nothing) → judge called, not a rule "no match"; "CSV export" → judge called. Explicit `F-003` in the unit text → rule gate with the retired reason, date, and three choices quoted, exit 2. `supersedes` id also matches deterministically. The CLI with the mock provider and retired rows exits 1 with a traceback rather than a false "no gate" — fail-closed. The paraphrase-gates test (`test_paraphrased_unit_goes_to_the_judge_with_descriptions_and_gates`) asserts the prompt carries the description and reason. Holds.
- **(d) doctor on stale SNAPSHOT after a goal.json change** — fails, see table.
- **(e) Generated sections derived from docstrings** — the `core/ids.py` probe changed one docstring line and doctor flagged ARCHITECTURE stale; the map table row for `core/ids.py` is the docstring's first line. Holds.
- **Snapshot roll-up.** High features have no cap; fixed overhead ≈ 44 lines, so ~16 high live features would make `render_snapshot` raise and take doctor, `ledger add`, and the session hook down with it → **AT-022** (under the cap today; filed, not failed).

## Manifest citations judged

- **AT-009 (bypass 5f83bdb):** the manifest's What-changed claims the `scripts` allowlist token and the "Sweep findings folded" section names the bypass rather than arguing it away — this is the fix direction the sweep asked for. Flipped to `fixed`.
- **Enforcement-path edits under D-000:** `qa/hooks/mc-sessionstart.ps1`, the `.claude/settings.json` merge and `scripts/append_decision.ps1` are each listed in D-000 `Changes-authorized` with `Approved-by: Umesh`; D-006 (session) records the append_decision change specifically. Sufficient for the guard as written. Note for the record: D-000 is a standing authorization for those paths — future enforcement edits will always satisfy the guard literally, so the D-006 habit (a session entry per concrete change) is what keeps the trail honest.
- **T-011 code uncommitted:** user preference, not a bypass — not a finding.
- **AT-010 / AT-016 / AT-017 / AT-018:** confirmed on disk (D-005 present, additions-only; `stalled` notification acked; T-065 high with T-070 dependent; T-045 present). Flipped to `fixed`.
- **AT-013:** folded by this check — L7 backfill line + amendment-log entry in `qa/contracts/living-ledger.md`. Flipped to `fixed`.
- **Inbox (append_decision.ps1 encoding):** fix verified in a scratch copy — the working-tree script appended an entry whose `·`/`—` are clean UTF-8 bytes. Note appended under the entry; status left `unfolded` because the remaining item (the AIOS template copy) is outside this root.
- **Still open, not this unit's claim:** AT-011 (qa/loop.md), AT-012 (tick tz — the newest tick line now carries `+0530`), AT-014 (rubrics), AT-015 (lab hook injects only ARCHITECTURE's H1 — reproduced in my run).

## /goal

FAIL → T-005 stays open; no `goal_cli done`. On the cycle-2 PASS the checker closes T-005 and expects a `FEATURES.jsonl` `live` row for it (`user_value: high`, `--verdict qa/verdicts/t005-living-ledger.md`) at the maker's close-out — `ledger check` will flag its absence.

## Fix cycle 2 must show

1. `docs/ARCHITECTURE.md` ≤ 150 lines with the generated sections still derived and freshness-checked (relocation to a routed `docs/MAP.md` is acceptable — say so in the manifest and the checker folds L1), plus a doctor rule for the cap (AT-019).
2. `load_events` rejects duplicate ids (AT-020) and doctor reports `ledger-invalid` instead of a traceback (AT-021).
3. AT-022 roll-up is optional for the PASS (under cap) but cheap to do in the same cycle.
