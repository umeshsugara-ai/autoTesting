# Verdict — at015-at028-hook-adapter-fix

**Date:** 2026-09-03
**Cycle checked:** 1
**Checker mode:** A (unit check), fresh subagent, no builder context
**Bound project root:** d:/autoTesting

## What I re-ran myself (not trusted from the manifest)

1. Read `docs/DECISIONS.md` D-008 and D-009 in full (lines 93-134). Both have What/Why/Result/
   Links/Changes-authorized/Approved-by (Umesh, this session, AskUserQuestion batch). Confirmed
   sequential IDs (D-007 → D-008 → D-009) and that `git diff docs/DECISIONS.md` is a pure
   append at the end of the file (no bytes before D-008 touched) — consistent with
   `scripts/append_decision.ps1`'s `AppendAllText` write path (read the script in full,
   `scripts/append_decision.ps1:136-141`), not a hand-edit. Note: the working tree has this
   diff as **uncommitted** (`git status --short` shows `M docs/DECISIONS.md` along with every
   other file this unit touches) — the append path itself is not in question, but nothing in
   this unit has been committed to git yet.
2. Independently re-simulated `.claude/hooks/lab-session-start.ps1`'s new filter (lines
   111-129, read in full) against the actual current `docs/ARCHITECTURE.md` (143 lines,
   confirmed via `wc -l`), using the exact same `Get-Content -Encoding UTF8` + inKeep/keep +
   100-line-cap logic, executed via `powershell -NoProfile -Command`.
   - **Result: `kept lines: 101`** (100 content lines + the `[... ARCHITECTURE excerpt capped
     at 100 lines ...]` message), with only these headings present: H1 title, What it does,
     Pipeline, Concept → file, Data model, Execution model, Security, Storage. The loop hits
     the pre-existing 100-line cap (unchanged by this unit, per D-008's own text) partway
     through the "Storage" section and breaks — **Design rules, Commands, and Status are never
     reached**, and `## Directory map and schema summary` is correctly excluded (as intended).
   - This **contradicts** the manifest's "Actual outputs" section, which claims `kept lines:
     139` with all 9 non-excluded headings present (including Design rules, Commands, Status)
     and no mention of a cap. That claimed output is not reproducible against the code and file
     actually on disk — ran it a second time with an independent script to rule out a
     transcription slip on my end; both runs agree (101, capped, missing 3 headings).
   - **AT-015's core defect (fully empty ARCHITECTURE injection every session) IS genuinely
     fixed** — session start now receives substantive real prose instead of nothing. But the
     manifest's specific verify-command evidence for this fix is false/unreproducible, and the
     actual current behavior has an unclaimed residual: three of the file's real sections
     (Design rules, Commands, Status) are silently dropped every session by the pre-existing
     cap, a narrower instance of the same "session start doesn't see real ground truth" defect
     class AT-015 was filed against.
3. Read `qa/adapter.json:10`, `CLAUDE.md:68` and `:90`, `qa/loop.md:15` directly. All four read
   `uv run ruff check src tests scripts`, byte-for-byte identical. Matches the manifest's claim
   for this item.
4. Re-ran commands myself, none pasted-only:
   - `uv run pytest -q` → exit 0, all pass (1 skipped, matches manifest)
   - `uv run ruff check src tests scripts` → `All checks passed!`
   - `uv run autotester doctor` → `doctor: clean`
   All three match the manifest's claims.

## Verdict

```
VERDICT: FAIL
SCOREBOARD: 3/4 verify items reproduced as claimed, 1/4 (ARCHITECTURE filter re-run) contradicted by independent re-execution
FAILURES (if any):
- [D-008 verify] Manifest's pasted ARCHITECTURE.md filter test ("kept lines: 139", all 9 headings) is not reproducible: independent re-run of the exact new filter code against the exact current docs/ARCHITECTURE.md yields 101 lines, capped mid-"Storage", missing Design rules/Commands/Status entirely · fix direction: raise or remove the pre-existing 100-line cap (or split the excerpt), then re-paste a verify output that is actually reproduced, not assumed · issue: AT-029
ISSUES-WRITTEN: AT-029 (new, medium); AT-028 updated open->fixed (independently reproduced, see below)
EXPLANATION: D-009/AT-028 (adapter.json ruff command) checks out cleanly on every axis I re-ran myself — DECISIONS entry, byte-for-byte command match across three files, and a clean pytest/ruff/doctor run. D-008/AT-015's underlying fix is real progress (the injection is no longer empty), but the manifest's own verify evidence for it — the specific thing this dispatch asked me to independently confirm rather than trust — does not reproduce. Per Mode A's core rule ("a pasted output you cannot reproduce = FAIL on that item, stated plainly"), that alone fails the unit even though AT-028's half is solid and the Lab Protocol paperwork (D-008/D-009 headers, Approved-by, append-only diff shape) is in order.
```

## Ledger changes made

- **AT-028** — `qa/issues.jsonl`: `open → fixed`. Verifiably fixed by this unit: D-009 authorizes
  it, `qa/adapter.json`/`CLAUDE.md`/`qa/loop.md` agree byte-for-byte, `ruff check src tests
  scripts` passes. (Not `verified` — that requires a later independent re-check per this
  project's ledger discipline.)
- **AT-015** — left `open`. The empty-injection symptom is gone, but the manifest's own claimed
  verification of the fix is false, and the fix as it stands still silently drops 3 of 9 real
  sections every session (the cap issue below is the concrete remaining defect). Not safe to
  mark fixed on unreproduced evidence.
- **AT-029** (new, medium, `open`) — the pasted-evidence discrepancy + the residual 100-line-cap
  truncation, filed with the exact independent re-run steps and output above.

## Scope note

No goal task to close — this unit is infra (AT-015/AT-028 process issues), not a `.goal/goal.json`
task, per the dispatch instructions.

## Next step for the maker

Re-open cycle 2: either raise/remove the ARCHITECTURE excerpt's 100-line cap (or otherwise ensure
Design rules/Commands/Status survive the cut) so the injected ground truth actually covers what
D-008 claims it covers, or narrow D-008's claim to match reality and re-paste a verify output that
is actually reproduced — then re-submit with `Fix cycle: 2`.
