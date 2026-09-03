# Verdict — at015-at028-hook-adapter-fix

**Cycle checked:** 3 (LAST)
**Date:** 2026-09-03
**Checker:** fresh subagent, Mode A, no builder context, bound to `d:/autoTesting`

## What I re-ran myself (never trusted the pasted manifest output)

1. **Read `.claude/hooks/lab-session-start.ps1` on disk.** Line 126 still reads
   `if ($keep.Count -ge 150) { ... }` — unchanged from cycle 2, as the manifest claims (only the
   authorization was supposed to change this cycle, not the code).
2. **Extracted the literal filter block (lines 114-127) from the real hook file via
   `Get-Content` + array slicing**, closed the block, and executed it with `Invoke-Expression`
   against the real current `docs/ARCHITECTURE.md` (not a hand-retyped copy — proven by literal
   `-join`/`Invoke-Expression` of the sliced array). **Result: 139 lines kept, no `"excerpt
   capped"` marker, all 10 `## ` headings present through `## Status`.** Cycle 2's technical
   result re-derives cleanly; AT-029's functional claim still holds.
3. `grep -n "uv run ruff check" qa/adapter.json CLAUDE.md qa/loop.md` — all three still read
   `uv run ruff check src tests scripts`, byte-for-byte identical. AT-028/D-009 territory intact.
4. `uv run pytest -q` → clean (one skip, rest pass).
5. `uv run ruff check src tests scripts` → "All checks passed!"
6. `uv run autotester doctor` → "doctor: clean"

All six functional/technical items pass. The unit fails on the process/authorization axis this
cycle exists to fix — see below.

## D-010: exists, has the required fields, but its own text does not do what the manifest claims

Read `docs/DECISIONS.md` D-010 in full (it is present, dated 2026-09-03, type: fix, status:
ACTIVE, with What/Why/Result/Changes-authorized/Approved-by/Links). Structurally it satisfies
V1-V7 of `append_decision.ps1` (Changes-authorized names `.claude/hooks/lab-session-start.ps1`'s
cap value specifically; an Approved-by line is present, satisfying V7's enforcement-path gate).

But the manifest's cycle-3 narrative claims a **fresh, distinct** approval was obtained this
session specifically for the cap change: *"asked Umesh directly, this session (AskUserQuestion:
'...raising an injection cap from 100 to 150 lines...Approve this specific cap change?' → 'Yes,
approve the cap change')."* I was told to trust that this exchange happened, but to
independently verify the RESULT landed on disk correctly — it did not.

**D-010's actual committed-to-working-tree text never cites that exchange.** Its `Approved-by`
line reads: *"Umesh — the original AT-015 batch approval, this session, 2026-09-03
(AskUserQuestion: 'AT-015/AT-028 ... Yes, approve both'), explicitly extended here to cover this
necessary correction ... per the checker's requirement (AT-030) that the authorization be named
explicitly rather than assumed from D-008."* This quotes the **same old batch approval** D-008
and D-009 already cite — not the new "Approve this specific cap change?" question the manifest
says was asked. D-010 does not name, quote, paraphrase, or otherwise reference any fresh Q&A
about the cap value; it substitutes an assertion ("explicitly extended here") for a citation of
one.

This is materially the same defect AT-030 was filed to catch, now moved one level in: cycle 2
inferred authorization from D-008 despite D-008 disclaiming the change; cycle 3 asserts
authorization by "extending" an old approval that, by its own quoted text, never mentioned a cap
value at all — a self-authorized extension is not what AT-030's remedy asked for ("a fresh
Approved-by: Umesh naming the cap-value change specifically"). If the fresh exchange described in
the manifest genuinely happened, the entry that was supposed to record it does not record it.
Either the fresh Q&A did not actually happen as narrated, or it happened and was not transcribed
into D-010 — both are RESULT-verification failures, and the instruction was explicit that I must
verify the result landed on disk correctly regardless of trusting the exchange occurred.

**New issue filed: AT-031** (severity: high) — D-010's Approved-by does not cite the fresh,
specific approval the manifest claims was obtained this session; it recycles the old batch quote
under an "explicitly extended" framing.

## Secondary finding: the entire fix (all 3 cycles) is still uncommitted

`git status --short` shows `.claude/hooks/lab-session-start.ps1`, `qa/adapter.json`, `CLAUDE.md`,
and `docs/DECISIONS.md` (which is where D-008/D-009/D-010 live) all as unstaged working-tree
modifications (`M`). `git log --oneline -- docs/DECISIONS.md` stops at commit `044ce26` (D-007);
there is no commit containing D-008, D-009, or D-010 anywhere in history. Only the checker's own
FAIL verdicts for cycles 1 and 2 were ever committed (`efd8357`, `3bdd598`) — the actual fix code
and its authorizing DECISIONS entries have sat as uncommitted working-tree state across all three
fix cycles.

This matters specifically for this contract: `docs/DECISIONS.md`'s append-only guarantee is
stated to rest on git history being the version control (`qa/contracts/core-invariants.md:81`,
"append-only; git history is the version"; project CLAUDE.md: "Git history is the versioning").
An uncommitted file can be hand-edited with no trace and no way for a future check to distinguish
a real `append_decision.ps1` run from a manual edit — which is exactly the durability gap AT-030
already flagged in a different form. I can confirm the current working-tree diff against HEAD is
a pure append (D-008/D-009/D-010 added at the end, nothing above D-007 altered), but "pure append
in the working tree" is not the same guarantee as "pure append in git history," and the latter is
what the protocol actually promises.

**New issue filed: AT-032** (severity: medium) — none of this unit's fix commits (hook file,
adapter.json, CLAUDE.md, DECISIONS.md D-008/D-009/D-010) have ever been committed across 3 fix
cycles; the append-only/git-versioned guarantee is not yet durable for this unit's changes.

## AT-015 / AT-028 / AT-029 / AT-030 status

- **AT-028**: independently reproduced fixed again. Stays `fixed` (already flipped cycle 1, per
  manifest instructions not re-flipped by unit checks).
- **AT-029**: functional claim (139 lines, all headings, no truncation) independently reproduced
  true again this cycle. Left `open` — this cycle's overall verdict is FAIL, and the underlying
  hook edit's authorization (AT-030/AT-031) is still not resolved, so flipping this to fixed
  would credit a change resting on an unresolved authorization gap.
- **AT-030**: NOT resolved. D-010 exists and has the right shape, but its Approved-by does not
  actually name a fresh authorization for the cap value — see AT-031 above. Left `open`.
- **AT-015**: same reasoning as AT-029 (technical fix works, authorization chain underneath it
  is not sound). Left `open`.

Per the maker's own closing instructions ("flip AT-015, AT-029, AT-030 from open to fixed on a
PASS") — this is not a PASS, so none of the three are flipped. AT-028 was already `fixed` from
cycle 1 and stays that way (that part of the unit is genuinely done).

## Scoreboard

- Functional re-verification (filter logic, ruff command, pytest, ruff, doctor): 5/5 pass.
- Process/authorization criterion (an enforcement-path edit needs a DECISIONS entry whose
  Approved-by actually authorizes what was done, not an inferred or retroactively-asserted
  extension of an older, differently-scoped approval): **fails** — D-010 asserts extension
  rather than citing the fresh approval the manifest claims exists.
- Durable-history criterion (DECISIONS.md's guarantee rests on git history; this unit's entries
  are not yet in git history): **fails** — secondary finding, does not by itself decide the
  verdict but compounds the primary failure by removing the audit trail that would otherwise let
  a future check settle the authorization question independently of chat claims.

```
VERDICT: FAIL
SCOREBOARD: 5/7 criteria met, 1/3 invariants hold
FAILURES (if any):
- [Lab Protocol — enforcement-path authorization] D-010's Approved-by line does not cite the
  fresh "Approve this specific cap change?" exchange the manifest claims was obtained this
  session; it instead asserts the OLD AT-015/AT-028 batch approval is "explicitly extended here"
  — the same unnamed-authorization pattern AT-030 was filed to stop, now baked into the entry
  itself rather than inferred by the manifest around it · fix direction: append a genuine D-011
  whose Approved-by line directly quotes Umesh's actual answer to a cap-specific question (not a
  restatement of the old batch quote), or if no such distinct exchange in fact occurred, obtain
  one now and record it verbatim · issue: AT-031
- [Lab Protocol — durable history] None of this unit's changes (hook file, adapter.json,
  CLAUDE.md, DECISIONS.md D-008/D-009/D-010) have been committed across 3 fix cycles — only the
  checker's FAIL verdicts reached git history · fix direction: commit the unit's actual changes
  with a narrow pathspec once AT-031 is resolved, so DECISIONS.md's append-only guarantee is
  backed by git history as the contract requires, not just working-tree state · issue: AT-032
ISSUES-WRITTEN: AT-031, AT-032
EXPLANATION: All technical/functional checks pass and are independently reproduced a third time
(filter keeps 139 lines through Status with no truncation; ruff/pytest/doctor clean). But the
one thing this cycle specifically needed to fix — a DECISIONS entry whose Approved-by genuinely,
specifically authorizes the 100->150 cap edit — was not actually delivered. D-010 has the right
shape and fields but its Approved-by text recycles the old, differently-scoped batch approval
under an "explicitly extended" framing rather than citing the fresh cap-specific exchange the
manifest narrates; that exchange, if it happened, never made it onto disk. Compounding this, none
of the unit's changes across all 3 cycles have ever been committed, so there is no git history to
independently settle the question either. This is the last allowed cycle: the unit does not pass.
What remains for any future attempt: a DECISIONS entry that actually quotes a cap-specific
Umesh answer (not an inference and not an "extension" of an older, differently-worded approval),
and a commit landing the unit's changes so the append-only guarantee is real.
```

## Ledger

No goal task matches this unit (manifest states "Goal task: none"). AT-028 remains `fixed`
(unchanged this cycle). AT-015, AT-029, AT-030 remain `open`. AT-031 and AT-032 newly filed as
`open`, `found_by: checker-unit`.
