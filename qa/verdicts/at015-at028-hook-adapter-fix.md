# Verdict — at015-at028-hook-adapter-fix

**Cycle checked:** 2
**Date:** 2026-09-03
**Checker:** fresh subagent, Mode A, no builder context, bound to `d:/autoTesting`

## What I re-ran myself (never trusted the pasted manifest output)

1. **Read `.claude/hooks/lab-session-start.ps1` on disk in full.** Confirmed line 126 now reads
   `if ($keep.Count -ge 150) { ... }` — genuinely raised from 100, not still 100 and not some
   other number.
2. **Extracted the literal ARCHITECTURE-filter block (lines 115-129) from the real file via
   `Get-Content` + array slicing** (not hand-retyped), closed the one dangling `if` brace the
   slice cut off, appended a capture line, and ran it with `Invoke-Expression` against the real
   current `docs/ARCHITECTURE.md`. Proof this wasn't a simplification: the first attempt (without
   the extra closing brace) threw a genuine PowerShell parse error ("Missing closing '}'"),
   confirming the extracted text really does contain the file's own nested `if/elseif/if` control
   flow, not a paraphrase.
   - **Result: kept = 139 lines, no `"excerpt capped"` marker present, all 10 `## ` headings
     present through `## Status`** (`## What it does` … `## Design rules` … `## Commands` …
     `## Status`), `## Directory map and schema summary` correctly absent. This matches the
     manifest's claim exactly and directly refutes cycle 1's finding (AT-029) — the cap raise did
     fix the truncation.
3. **Re-ran `grep -n "uv run ruff check" qa/adapter.json CLAUDE.md qa/loop.md`** — all three read
   `uv run ruff check src tests scripts`, byte-for-byte identical. AT-028 stays fixed.
4. **Re-ran `uv run pytest -q`** → clean (one skip, rest pass, matches manifest).
5. **Re-ran `uv run ruff check src tests scripts`** → "All checks passed!"
6. **Re-ran `uv run autotester doctor`** → "doctor: clean"
7. **Read `docs/DECISIONS.md` in full** to independently confirm D-008/D-009 exist, are ACTIVE,
   carry `Approved-by: Umesh`, and were appended (not hand-edited) — `wc -l` = 134 lines, D-009
   is the last entry, no D-010.

## New finding this cycle: AT-030 (authorization gap, not a reproducibility gap)

Re-reading D-008 while confirming its authorization scope, its own **Result** paragraph says
verbatim: *"The existing 100-line cap and `[... capped ...]` message are unchanged."* But this
cycle's actual fix changed that same cap from 100 to 150 — and the manifest justifies the edit
by citing D-008's `Changes-authorized` line ("the cap line is part of the ARCHITECTURE excerpt
filter only"). D-008 does not authorize this change; it explicitly documents the cap as
untouched, which is now false. No new DECISIONS entry (there is no D-010) exists with the actual
reasoning for 100→150 or a fresh `Approved-by` naming that specific edit. The Umesh
AskUserQuestion approval both D-008 and D-009 cite ("AT-015/AT-028 ... Yes, approve both")
predates and does not name a cap-value change — it covered the cycle-1 scope only.

This is exactly the class of defect this repo's Lab Protocol exists to catch: docs/DECISIONS.md
is the sole authorization path for enforcement-path edits (`.claude/hooks/lab-session-start.ps1`
is explicitly listed as an enforcement path in `CLAUDE.md`), it is append-only, and an existing
entry cannot be silently reinterpreted to cover something it factually disclaims. Filed as
**AT-030** (severity: high) in `qa/issues.jsonl`.

Note: this is a **process/authorization** defect, not a technical one — the cap raise itself
works correctly (see re-run above) and is a reasonable choice (matches ARCHITECTURE.md's own C2
150-line ceiling). The fix is procedural: append a real D-010 with the reasoning and get
Umesh's `Approved-by` specifically for the cap change, before treating the hook edit as
authorized.

## AT-015 / AT-029 / AT-028 status

- **AT-028** (ruff command): independently reproduced fixed. Stays `fixed` (already flipped
  cycle 1; not re-flipped here).
- **AT-029** (cycle-1 reproducibility gap: pasted "139 lines, all headings" was not actually
  reproducible against the real 100-line-capped code): independently reproduced **now genuinely
  true** against the real 150-cap code. The narrow functional claim is fixed. **Left `open`**,
  not flipped to `fixed`, because this unit's overall verdict is FAIL this cycle (protocol:
  only a PASS cycle flips these) and because the underlying hook edit that fixes it is itself
  unauthorized per AT-030 — flipping it to fixed would credit a change that isn't yet
  legitimately landed.
- **AT-015** (original empty-injection defect): same reasoning — the injection is no longer
  empty and no longer truncated early (confirmed), but left `open` for the same reason as AT-029.

## Scoreboard

- Contract: `qa/contracts/core-invariants.md` (general) + `docs/DECISIONS.md` D-008/D-009.
- Functional re-verification (filter logic, ruff command, pytest, ruff, doctor): 5/5 pass.
- Process/authorization criterion (enforcement-path edit needs a DECISIONS entry that actually
  authorizes what was done, per `CLAUDE.md` Lab Protocol "Update authorization" + "Enforcement
  paths" rules): **fails** — the cap-raise edit is unauthorized as committed.

```
VERDICT: FAIL
SCOREBOARD: 5/6 criteria met, 1/2 invariants hold
FAILURES (if any):
- [Lab Protocol — enforcement-path authorization] .claude/hooks/lab-session-start.ps1's cap
  raise (100->150) is cited to D-008, which explicitly states the cap is unchanged; no D-010
  exists authorizing the actual edit made · fix direction: append a new DECISIONS entry with the
  real reasoning + a fresh Approved-by: Umesh naming the cap-value change specifically, before
  the edit is considered landed · issue: AT-030
ISSUES-WRITTEN: AT-030
EXPLANATION: The technical fix is genuinely correct and independently reproduced this cycle
(139 lines kept, no truncation, all 10 headings present, ruff/pytest/doctor clean) — cycle 1's
AT-029 finding is resolved on the merits. But verifying the authorization chain surfaced a new
defect: the enforcement-path edit that makes it work (raising the truncation cap) is justified
by misciting D-008, which on its own committed text disclaims exactly this change. That is an
unauthorized enforcement-path edit under this repo's own Lab Protocol, so the unit fails on
process grounds even though the code now behaves correctly.
```
