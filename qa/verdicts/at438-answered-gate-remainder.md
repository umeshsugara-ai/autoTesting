# Verdict — at438-answered-gate-remainder

**Checker:** /checker (fresh, isolated context, bound to
`D:/autoTesting/.claude/worktrees/agent-abbe17c7593b44730`, branch `wave/at438-answered-gate-remainder`)
**Date:** 2026-09-27
**Manifest:** `qa/manifests/at438-answered-gate-remainder.md` (Status: ready-for-check, Fix cycle: 1 of 1)
**Cycle checked: 1**
**Code under check:** commit `76bc6e93` (merge `1af10659` brings master in on top; unit's own diff
verified against `76bc6e93^..76bc6e93`)

```
VERDICT: FAIL
SCOREBOARD: 0/1 criteria met (the unit's own stated job — an accurate bookkeeping close-out —
  is not met), 2/2 checked invariants hold (C2 doctor, C3 no drift filenames)
FAILURES:
- sev: high · qa/manifests/at438-display-contents.md's own "Issues addressed" line, edited by this
  unit's commit, states AT-442, AT-443 and AT-445 are "fixed", while qa/issues.jsonl records all
  three status: "open" at the time of the commit, D-049's authorized Result section never mentions
  them, and this SAME commit's OTHER file (qa/manifests/at438-answered-gate-remainder.md, "Where to
  attack this") explicitly argues the unit correctly left their ledger status untouched because
  flipping it "is a /checker call, not mine." One commit asserts a status in prose that its other
  half says was deliberately not authorized — a bookkeeping unit's entire job is textual accuracy,
  and this is a self-contradiction inside its own diff · issue: see "New/updated ledger rows" below,
  now resolved by this verdict
- sev: medium · the manifest's flipped header states unqualified "**Status:** checked-PASS", but the
  checker verdict it cites for authority (qa/verdicts/at438-display-contents.md, "Re-ruling of cycle
  3") explicitly scopes itself: "VERDICT: PASS (re-ruled; supersedes the cycle-3 FAIL above for
  U14(b) only)". Folding AT-453 (separately verified via t186-details-content) and AT-454 (wontfix)
  into one blanket "checked-PASS" overstates what the cited re-ruling actually says
- sev: medium · the unit's claim "this project's gate convention has no separate Status: closed
  header field to flip" is false: `qa/gates/at106-hook-architecture-path.md`,
  `qa/gates/at110-approval-forgery.md` and `qa/gates/at355-guard-shape.md` all carry
  `Status: ANSWERED` (at110: `Status: ANSWERED -> built and merged`). The unit checked four gates
  that happen not to use the convention (at147, at520, commit-before-verdict, at610) and concluded
  the convention does not exist, rather than checking whether it exists elsewhere (it does). The
  actual gate this unit is named after, `qa/gates/at438-u14b-baseline.md`, still reads
  `**Status: OPEN**` in its own header, 25+ hours after being fully answered and acted on — the most
  visible unresolved field on the one artifact this unit's title promises to close out. Precedent
  `qa/manifests/at400-gate-premise-corrected.md` (AT-400, severity high) establishes exactly this
  principle for this project: "a gate is open until its file says otherwise" — a stale gate record
  is not a cosmetic gap here, it has been rated high before
CAPABILITY-COVERAGE: not-applicable (bookkeeping unit, no capability rows)
LIVE-BROWSER: not-applicable
ISSUES-WRITTEN: none new; AT-442/AT-443/AT-445 ledger status resolved below by this checker,
  independent of the unit's own (correct, as far as it went) restraint
EXPLANATION: see below
```

## The premise, independently re-derived (not trusting the manifest or the sweep)

I re-walked this from `git log`, `docs/DECISIONS.md`, `qa/contracts/ui.md` and `qa/issues.jsonl`
myself, without reading the unit's narrative as evidence.

- `qa/gates/at438-u14b-baseline.md` was answered `a + b + c` at `2026-09-26T22:34:22+05:30`.
- `6d2eb0bd` (2026-09-26 23:16:38 +0530, ~42 min later, commit message
  `qa(checker): re-rule at438 cycle 3 PASS under D-048/D-049; amend U14(b)/(c)`) is a real checker
  commit. It touches `docs/DECISIONS.md` (+D-049), `qa/contracts/ui.md` (U14(b)/(c) amended),
  `qa/issues.jsonl` (AT-438/449/450 → fixed, AT-454 → wontfix), and appends a
  "Re-ruling of cycle 3" section with `VERDICT: PASS` to `qa/verdicts/at438-display-contents.md`.
  I confirmed the section exists at line 410, is scoped to U14(b), and is written under a checker
  commit, not a maker self-attestation.
- `580fd3a7` (2026-09-27 17:59:39 +0530, `qa(checker): t186-details-content cycle 1 -- PASS`) is
  also a real, independent checker verification (byte-comparison, own falsification copy, own
  headed-Chromium run) that closes AT-453 as `verified`.
- `docs/DECISIONS.md` D-049's `Result` section: "AT-438, AT-449 and AT-450 flip to fixed... AT-454
  becomes wontfix... AT-453 stays open for its own unit" — matches `qa/issues.jsonl`'s current state
  exactly for those five ids.

**The premise survives independent checking: the sweep note (`bd69565d`, "an answered gate nobody
acted on") was indeed stale by the time it was written** — it postdates both `6d2eb0bd` and
`580fd3a7` by 40+ minutes and reads `AT-438: "status": "fixed"` as evidence of inaction, when
`"fixed"` is D-049's own stated target string. On this specific point, both the maker unit under
review and my own independent re-derivation reach the same conclusion. Agreement is not proof, so
I re-verified from primary sources (commit content, not the manifest's summary of it) rather than
trusting either party — the finding holds.

## Where this unit actually falls down

**1. The manifest flip's authority is real, but the unit oversold it.** The "Re-ruling of cycle 3"
section is a genuine checker verdict, and a maker mechanically transcribing an existing checker PASS
into a manifest's terminal status is legitimate — that is what happened at
`qa/manifests/at015-at028-hook-adapter-fix.md` ("Recovery confirmed — checked-PASS", following a
dispatched confirming checker pass). But that precedent's confirming pass was a full re-verification
across every open concern (technical fix, approval-quote authority, uncommitted changes) before the
unqualified `checked-PASS` was written. Here, the cited authority says "for U14(b) only" in its own
text, and the manifest header drops that qualifier. A reader of the manifest header alone — which is
exactly what a session-start hook or loop-status parser reads — now believes this unit is
unconditionally closed.

**2. The self-contradiction on AT-442/443/445 is the harder problem.** In the same commit
(`76bc6e93`):
- `qa/manifests/at438-display-contents.md`'s "Issues addressed" line says: "AT-442 (...; fixed) ·
  AT-443 (...; fixed) · AT-445 (...; fixed)".
- `qa/manifests/at438-answered-gate-remainder.md`'s "Where to attack this" section says: "I left
  them alone deliberately... Flipping a ledger row to fixed/verified on my own reading, without a
  checker-run falsification, is exactly the unverified-status-change the project's own sweep
  convention forbids... If these three should also close, that is a /checker call, not mine."

  Both cannot be true. The restraint described in the second file is the *correct* instinct — it
  matches this project's own P2 rule (`qa/QUEUE.md`'s AT-648 write-up: "promoting on someone else's
  already-embedded note rather than a falsification run... is exactly the unverified-status-change
  P2 forbids"). But the prose written into the first file oversteps that same restraint the unit
  claims to be honoring. A bookkeeping-only unit whose sole deliverable is textual accuracy cannot
  ship two files that disagree with each other about the same three ids.

**I did the falsification the unit declined to do, since the brief asked me to rule on it rather
than merely note it, and I have checker authority over the ledger:**
- `src/autotester/browser/visual_order.js:60`: `// never its tag: authors restyle it (AT-449).
  NEVER insert a probe (AT-442/443).` — the shipped detector (walk-up to nearest box) structurally
  does not insert a probe node into author DOM. AT-442 (probe restarts author animations), AT-443
  (author `:empty` hides the probe) and AT-445 (page-controlled `appendChild`/`remove` override
  breaks the probe) are all consequences of the abandoned cycle-1 probe-insertion approach. They
  cannot occur by construction against the code that is actually on master.
- The `appendChild` still present at `visual_order.js:189` is the unrelated form-control mirror path
  (masked/placeholder text measurement), not the display:contents probe path AT-445 was about —
  checked directly, not assumed.
- Both the cycle-2 and cycle-3 checker verdicts (`qa/verdicts/at438-display-contents.md` lines 233
  and 400/401) already state, independently of each other and of this unit, "AT-442, AT-443 and
  AT-445 do not reproduce" against `9fc937d` — the exact commit that is byte-identical to what is on
  master today (D-049).
  - I re-ran `uv run pytest tests/test_browser_visual_order.py -k display_contents` myself in this
    worktree (post-merge with master): `1 passed, 31 deselected in 1.85s`, including the AT-442
    animation-clock-never-regresses assertion.

That is a real falsification chain (structural code guarantee + two independent prior checker
verdicts + my own fresh re-run), not a third party's unverified note. **Ruling: AT-442, AT-443 and
AT-445 are fixed.** I did not flip them in `qa/issues.jsonl` from this worktree/branch, because
`qa/contracts/core-invariants.md` C10 restricts a unit's commit to its own manifest's named paths,
and this checker-ledger correction is not part of `at438-answered-gate-remainder`'s own scope — it
belongs on a standalone `chore(qa)` commit to master (the project's own established pattern for
ledger/contract housekeeping, e.g. `6d2eb0bd`, `bd69565d`), which this worktree cannot make without
leaving the branch under review. Handing this to the orchestrator to apply directly against
`D:/autoTesting` main checkout:
`qa/issues.jsonl` AT-442/AT-443/AT-445 → `"status": "fixed"`, `"fixed_date": "2026-09-27"`,
`"source": "checker at438-answered-gate-remainder cycle-1 review"`,
`"fixed_by": "9fc937d (probe-insertion approach removed; visual_order.js:60 comment 'NEVER insert a
probe (AT-442/443)'); independently confirmed via qa/verdicts/at438-display-contents.md lines
233/400-401 and a fresh uv run pytest tests/test_browser_visual_order.py -k display_contents run"`,
`"regression_check": "uv run pytest tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor"`.

**3. The gate file itself was never touched, and the unit's claim about gate-status convention is
wrong.** See FAILURES above. `qa/gates/at438-u14b-baseline.md` still reads `**Status: OPEN**`. This
project has precedent (AT-400, severity high) for treating a stale gate record as a real defect, not
a cosmetic one, and three other gates in this same repo use `Status: ANSWERED` once dealt with. This
unit's entire premise was "collect the remainder of the answered gate" — the gate's own header field
is squarely inside that remit and was missed.

## What I confirmed independently and did not fault

- **Diff discipline:** `git diff --numstat 76bc6e93^ 76bc6e93` → exactly two files,
  `qa/manifests/at438-answered-gate-remainder.md` (142 insertions, new file) and
  `qa/manifests/at438-display-contents.md` (24 insertions, 2 deletions). No touch to
  `qa/issues.jsonl`, `qa/contracts/`, `docs/DECISIONS.md`, `.goal/`, `src/` or `tests/` — matches the
  manifest's claim exactly.
- **Ruff:** `uv run ruff check src tests scripts` → `All checks passed!`.
- **Doctor:** `uv run autotester doctor` → one violation, `stale-generated: docs/SNAPSHOT.md differs
  from regeneration`. Traced this to the merge (`1af10659`) bringing in master's `.goal/goal.json`
  changes from `c0a60e2f` (T-191 close-out, landed after this unit's own commit) without a
  `autotester snapshot` regeneration — not caused by this unit's own diff, which never touches
  `.goal/` or `docs/SNAPSHOT.md`. Not held against this unit.
- **Pytest:** ruff/doctor and a targeted re-run of the display-contents test are independently
  confirmed clean (above). A full bare `uv run pytest` re-run was attempted twice from this worktree
  but the shared machine had 4+ concurrent pytest processes running from other live sessions at
  verification time (`Get-Process pytest` showed processes from 19:34, 19:38, in addition to mine) —
  the same contention class the manifest itself named for its unexplained
  `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` failure. I did not force a clean
  solo run given that contention (would mean competing with other live sessions for the process
  table, which the manifest itself correctly declined to do for the same reason). The manifest's
  reported `3 failed, 2068 passed` is plausible and not disputed, but not independently
  byte-reproduced by me. This does not change the verdict — the FAILURES above are document-
  consistency defects, verified directly from file contents, independent of the suite result.
- **at015-at028 precedent:** real, and the mechanical-transcription-of-an-existing-checker-verdict
  pattern is sound in principle — the defect here is in what got transcribed (unqualified vs.
  scoped), not in the pattern itself.
- **AT-438 `fixed` vs AT-453 `verified` asymmetry:** intentional, not a loose end. D-049's Result
  section names `fixed` as the explicit target string for AT-438/449/450; AT-453 reached `verified`
  through a separate, later, fully-independent checker PASS (`580fd3a7`) on its own capped unit. Two
  different paths to two different (correct) ledger states.

## Ruling on the zero-code-unit verify-cost question

Two independent sightings (this unit's own note, and `qa/verdicts/t192-url-pattern-heal.md`'s C10
scope observation) both point at the same friction: a markdown-only diff pays the same `uv run
pytest` cost as a full feature unit. **I am not relaxing `qa/contracts/core-invariants.md` C7's
Verify clause.** The full-suite run is not there to re-prove behavior the unit didn't touch — it is
there to confirm the tree being merged is not broken by *concurrent* drift, which is exactly what it
caught here (the two `test_goal_done_checks` reds are real, live, tracked separately). A carve-out
that let zero-code units skip it would blind exactly the class of unit most likely to be merged
quickly and least likely to get a second look. What I will note as a documentation gap, not a rule
change: C7 does not currently say in words that a zero-code unit's pre-existing/concurrent failures,
correctly named and not touching the affected files, do not block its own PASS — this unit and
`t192-url-pattern-heal` both had to reason that out from first principles. I am not amending
`qa/contracts/core-invariants.md` from this branch, for the same C10 reason AT-442/443/445 isn't
being ledger-fixed here: it is out of this unit's own path scope. Recommending the orchestrator or a
routine checker sweep add one sentence to C7 confirming this reading, citing this verdict and
`t192-url-pattern-heal.md`.

## Required for cycle 2

1. Fix the self-contradiction: either (a) get the ledger fixed first (now ruled on above — cite this
   verdict) and then word "Issues addressed" to match, or (b) if the fix lands first, reword the
   line to not assert "fixed" ahead of the ledger.
2. Qualify the `checked-PASS` status line to name what it actually re-rules (U14(b)), rather than an
   unqualified blanket close.
3. Flip `qa/gates/at438-u14b-baseline.md`'s header `Status: OPEN` to reflect its answered/acted-on
   state, consistent with `at106-hook-architecture-path.md` / `at355-guard-shape.md` /
   `at110-approval-forgery.md`'s `Status: ANSWERED` convention, and correct the manifest's claim that
   no such convention exists in this project.

## Status: not passed — cycle 2 required
