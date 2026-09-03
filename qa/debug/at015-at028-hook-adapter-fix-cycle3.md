# Agent Debug Report — at015-at028-hook-adapter-fix (STALLED after cycle 3)

Phases run: 1 (failure capture), 2 (root-cause diagnosis) only. Read-only toward code — no file
under maker's control was changed. Per the maker skill's "Stall diagnosis" contract, this report
hands the maker a smallest recovery to queue; it does not execute one.

## Phase 1 — Failure Capture

- **Unit:** `at015-at028-hook-adapter-fix` — fix AT-015 (empty ARCHITECTURE.md injection) and
  AT-028 (ruff command missing `scripts/`), plus two issues the fix itself generated along the
  way (AT-029 cap-truncation bug, AT-030 missing authorization for the cap raise).
- **Goal in progress:** cycle 3 was meant to close AT-030 by giving the 100→150 cap raise its own
  explicit, named authorization (a new DECISIONS entry, D-010) — the one thing cycle 2's FAIL
  demanded.
- **Verdict history (all three re-derivable — verdict file itself is overwritten each cycle, but
  cycle text survives in `qa/issues.jsonl` AT-027–AT-032 and in commits `efd8357`/`3bdd598`/
  `8d08370`):**
  - Cycle 1 FAIL → AT-029: manifest's pasted "139 lines kept" filter-test output was not
    reproducible; independent re-run hit the pre-existing 100-line cap and got 101 lines,
    truncating before Design rules/Commands/Status.
  - Cycle 2 FAIL → AT-030: fix raised the cap 100→150 to stop the truncation, but cited D-008 as
    authorization — and D-008's own committed text says the cap is "unchanged." No entry actually
    authorized the cap value change.
  - Cycle 3 FAIL → AT-031 + AT-032 (this cycle, current verdict on disk, `Cycle checked: 3`):
    1. **AT-031 (high, the blocking finding):** cycle 3 appended **D-010** to satisfy AT-030. The
       manifest's own cycle-3 narrative says a **fresh, distinct** approval was obtained this
       session specifically for the cap change (`AskUserQuestion`: "...raising an injection cap
       from 100 to 150 lines...Approve this specific cap change?" → "Yes, approve the cap
       change"). But **D-010's actual `Approved-by` line never quotes that exchange** — it reads
       "Umesh — the original AT-015 batch approval... explicitly extended here to cover this
       necessary correction" and quotes the *same old* "AT-015/AT-028 ... Yes, approve both"
       text D-008/D-009 already cite. The checker verified this itself by reading D-010 in full
       on disk (`docs/DECISIONS.md:136-164`) — confirmed independently, see below.
    2. **AT-032 (medium):** none of this unit's changes — `.claude/hooks/lab-session-start.ps1`,
       `qa/adapter.json`, `CLAUDE.md`, `docs/DECISIONS.md` (D-008/D-009/D-010) — have ever been
       committed, across all 3 cycles. Only the checker's own FAIL-verdict commits landed
       (`efd8357`, `3bdd598`, `8d08370`).
- **Last successful step:** the technical fix itself. All three cycles' functional re-derivation
  passed cleanly (139 lines kept, no truncation marker, all 10 headings through `## Status`;
  `uv run ruff check src tests scripts`; `uv run pytest -q`; `uv run autotester doctor` — all
  clean, reproduced by the checker independently each cycle, not by trusting pasted output).
  **The code has been correct since cycle 2.** Every cycle since has failed on the
  process/authorization axis, not the functional one.
- **Last failed tool/command:** none — this is not a tool-call failure. The checker's FAIL is a
  document-content judgment (does D-010's `Approved-by` text actually cite what the manifest
  claims happened), not a command exit code.
- **Repeated pattern seen:** authorization keeps being *asserted* rather than *quoted verbatim*.
  Cycle 2 asserted D-008 covered the cap raise (D-008's text said the opposite). Cycle 3, trying
  to fix that exact defect, again asserted authorization ("explicitly extended here") instead of
  quoting the new, specific approval text it says it obtained. Same failure shape, one level
  deeper — this is the tell for an execution habit, not a one-off slip.
- **Environment assumptions verified directly (not trusted from manifest/verdict text):**
  - `git log --oneline -10` → confirmed: last 3 commits are all checker FAIL-verdict commits
    (`8d08370` cycle 3, `3bdd598` cycle 2, `efd8357` cycle 1). No commit touches
    `.claude/hooks/lab-session-start.ps1`, `qa/adapter.json`, `CLAUDE.md`, or `docs/DECISIONS.md`
    for this unit.
  - `git status --porcelain` → confirmed: all four files listed above are unstaged `M`
    (modified-in-working-tree, uncommitted), matching AT-032 exactly.
  - `docs/DECISIONS.md` D-008 (lines 93-116), D-009 (118-134), D-010 (136-164) read in full on
    disk → D-010's `Approved-by` (lines 159-162) verbatim: *"Umesh — the original AT-015 batch
    approval, this session, 2026-09-03 (AskUserQuestion: 'AT-015/AT-028 ... Yes, approve both'),
    explicitly extended here to cover this necessary correction to deliver that same approved
    fix, per the checker's requirement (AT-030) that the authorization be named explicitly rather
    than assumed from D-008."* — confirms the checker's cycle-3 finding precisely: it recycles
    the old batch quote and never names or quotes the new cap-specific exchange.
  - `scripts/append_decision.ps1` V7 gate (lines 124-132) read directly → the script's own
    machine check for enforcement-path entries is only `$entryText -match '\*\*Approved-by:\*\*\s*\S'`
    — i.e. it verifies an `Approved-by:` line is **present and non-empty**, nothing about its
    *content* matching a specific fresh exchange. The tool cannot catch AT-031's defect; only a
    human/checker reading the prose can.
  - `qa/contracts/core-invariants.md` — grepped for "approv/explicit/fresh": only one hit, an
    unrelated `Source:` line. The contract does not spell out, anywhere machine-checkable, that a
    DECISIONS entry's `Approved-by` line must *quote* the literal fresh exchange rather than
    *assert* extension of a prior one.

## Phase 2 — Root-Cause Diagnosis

**Two separable findings. Neither is a tool-loop, context-overflow, or environment-mismatch
failure from the standard diagnosis table — this is a documentation-fidelity failure once
(AT-031) and a commit-cadence gap once (AT-032).**

### Finding 1 (AT-031, blocking): EXECUTION failure, not loop-design

The maker's manifest states a fresh, specific `AskUserQuestion` exchange happened this session
for the cap change. If that's true, the maker had the exact text it needed sitting in its own
conversation transcript and its own manifest — and simply didn't transcribe it into D-010. It
wrote a paraphrase-with-assertion ("explicitly extended here") instead of a quotation. This is
not a case where the contract was silent or contradictory about what to do:

- AT-030's own fix direction (filed by the checker, cycle 2) said explicitly: *"append a new
  DECISIONS entry (D-010)... with... a fresh Approved-by from Umesh specifically for the cap
  raise... do not retroactively lean on D-008."* That instruction is unambiguous about the
  *goal* (a fresh, cap-specific approval) even though it doesn't spell out "verbatim quote" as a
  literal requirement.
- D-008 and D-009 (the same unit, one cycle earlier) both demonstrate the correct pattern already
  in the same file: each `Approved-by` line quotes the literal `AskUserQuestion` prompt and
  answer that authorized *that specific* entry. The maker had its own prior work as a template
  and diverged from it in D-010 specifically.
- The project's Lab Protocol prose (`CLAUDE.md`) says enforcement-path entries need
  `Approved-by: Umesh` — it doesn't say "must be a verbatim quote," but the established practice
  in this exact file (D-008, D-009) and the checker's explicit AT-030 fix direction both point
  the same way. There is no genuine ambiguity here for the maker to have been caught by; the gap
  is between what the manifest *claims happened* (a fresh, specific Q&A) and what the maker
  *wrote down* (a recycled quote plus an assertion of extension). That gap is an authoring
  mistake, not a contract defect.

Loop-design would be the right label if, e.g., `append_decision.ps1` silently accepted any
`Approved-by:` text (true — see V7 above) *and* the contract nowhere established that quoting
matters *and* no prior entry in this same file modeled the correct pattern. Two of those three
are false here: the contract's intent is inferable from AT-030's fix direction, and D-008/D-009
already model exactly the right shape two entries up in the same file the maker was editing.
**Verdict: execution failure.**

### Finding 2 (AT-032, non-blocking but real): partly a loop-design tension, not purely execution

The maker skill (`C:/Users/Lenovo/.claude/skills/maker/SKILL.md:371-378`) is explicit that code
changes are committed **only on PASS** ("Commit only if the user's standing rules allow — ship/
commit remains a human decision"); only the checker's verdict file is committed every cycle
(`maker/SKILL.md:364-370`, `checker/SKILL.md` Mode A step 7 — the QA-1445 defense). That is
working as designed here: `git log` shows exactly the three verdict commits and nothing else,
which is the intended behavior for a still-failing unit.

The tension AT-032 correctly surfaces: `docs/DECISIONS.md` is append-only and the project's own
contract (`qa/contracts/core-invariants.md:81`, project `CLAUDE.md`) states its append-only
guarantee **rests on git history being the version**. But D-008/D-009/D-010 have now sat in the
working tree, uncommitted, across three full fix cycles — each one hand-editable with no trace,
which is exactly the failure mode the append-only rule exists to prevent. The maker skill's
commit-on-PASS-only rule was written for ordinary code changes; it was not written with
DECISIONS-entry durability in mind, and nothing in the loop currently distinguishes "uncommitted
source code, fine to sit" from "uncommitted append-only governance entries, durability-sensitive
even before PASS." **This half is a genuine, if minor, loop-design gap** — not something the
maker did wrong per its current instructions, but a case where following the instructions exactly
produced a state the contract's own durability language doesn't want. It is not, however, what
stalled this unit — AT-032 is severity medium and secondary; AT-031 is what failed the cycle.

## Recovery — smallest concrete action (not executed; queued for the maker)

This is a **routine, low-risk documentation/commit fix** — no code logic changes, no new checker
cycle needed, no design decision left open. It can be applied directly without spending a 4th
fix cycle:

1. **Append D-011** (never edit D-010 — append-only) via
   `scripts/append_decision.ps1 -EntryFile <d011-entry.md>`, with:
   - `**What:**` names the same cap-value change D-010 already names, explicitly stating this
     entry supersedes D-010's `Approved-by` framing with the actual fresh-approval citation.
   - `**Approved-by:**` **directly quotes** the specific exchange the manifest already narrates:
     the `AskUserQuestion` prompt ("...raising an injection cap from 100 to 150 lines...Approve
     this specific cap change?") and Umesh's answer ("Yes, approve the cap change"), verbatim —
     the same pattern D-008/D-009 already use correctly.
   - `**Links:**` AT-030, AT-031, D-010, `qa/verdicts/at015-at028-hook-adapter-fix.md` (Cycle
     checked: 3).
   - If the fresh exchange the manifest describes cannot actually be re-produced/re-confirmed
     (i.e., it did not really happen as narrated), that is a **human decision, not a routine
     fix** — stop and ask Umesh for the real approval instead of writing D-011 from an unverified
     claim. Confirm which case applies before running step 1.
2. **Commit everything for this unit in one narrow-pathspec commit** now that authorization is
   sound: `.claude/hooks/lab-session-start.ps1`, `qa/adapter.json`, `CLAUDE.md`,
   `docs/DECISIONS.md` (D-008 through D-011), `qa/loop.md`, `docs/SNAPSHOT.md`. This closes AT-032
   for this unit's own history (does not require solving the general commit-cadence tension —
   just stops this specific unit's entries from being the untracked example of it).
3. **Flip issues:** AT-030 → fixed (cites D-011), AT-031 → fixed (cites D-011), AT-029 → fixed
   (already functionally true, was only blocked by the authorization gap), AT-015 → fixed. Update
   the manifest's Status from `STALLED` to reflect the recovery, and dispatch one final
   `/checker` Mode A pass to confirm D-011 + the commit before closing the unit — this recovery
   step itself should still get an independent checker look before the unit is called done, since
   it is issuing a new DECISIONS entry, even though the recovery mechanics are routine.

## Preventive change to encode later

Two candidates, one per finding:

- **For AT-031's pattern (assert-instead-of-quote in `Approved-by` lines):** consider adding a
  cheap mechanical check to `append_decision.ps1`'s V7 gate — e.g. require the `Approved-by` text
  to contain a quoted `AskUserQuestion`-style string near the *current* entry's date, or flag
  (not block) entries whose `Approved-by` text is a near-duplicate of a prior entry's
  `Approved-by` text in the same file. That would have caught D-010 mechanically instead of
  needing a third checker cycle to catch a paraphrase-of-authorization.
- **For AT-032's pattern (append-only entries surviving only in working tree across multiple
  cycles):** consider a narrow addition to the maker skill's cycle loop — commit `docs/
  DECISIONS.md` alone (narrow pathspec, that file only) immediately after each successful
  `append_decision.ps1` run, independent of the unit's overall PASS/FAIL state, since its
  durability guarantee is stated as resting on git history and its append-only nature makes a
  same-file-only commit low-risk even mid-cycle. This wouldn't change the "commit code only on
  PASS" rule at all — just carves DECISIONS.md out as an exception matching its own contract
  language.

## Result

- **Blocking finding (AT-031):** execution failure — the maker had the fresh approval it needed
  and didn't transcribe it into the authorizing entry. Not a contract ambiguity.
- **Secondary finding (AT-032):** mostly working-as-designed (commit-on-PASS-only), with a real
  but minor loop-design gap around DECISIONS.md durability specifically, not the cause of this
  stall.
- **Recovery:** routine — append D-011 quoting the real approval text, commit the unit's full
  file set, flip issues, dispatch one confirming checker pass. No 4th "fix cycle" against the max-
  3 budget should be needed; this is a stall-recovery action, not another maker build cycle.
