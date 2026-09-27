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

## CHECK — cycle 2

**Checker:** /checker (fresh, isolated context, bound to
`D:/autoTesting/.claude/worktrees/agent-abbe17c7593b44730`, branch `wave/at438-answered-gate-remainder`)
**Date:** 2026-09-27
**Cycle checked: 2**
**Code under check:** commit `a9357439` (reviewed SHA). `a8cee3b9` (`Merge: a9357439 e1414fec`) is a
clean sync-merge of master with no manual changes beyond the two parents own content -- the C10
exception ("a `Merge branch master` sync commit that brings in nothing but masters own history")
applies, so it needed no new cycle; I verified against it anyway (see Verify below) because that is
the tree the merge would actually ship.

```
VERDICT: PASS
SCOREBOARD: 3/3 required cycle-2 fixes verified genuine, 0 new self-contradictions, 1 new low-severity
  inaccuracy found (self-disclosed, non-substantive) -- doctor clean -- ruff clean -- the two pytest
  reds named in the manifest are confirmed real-at-commit-time and already fixed on the tree this unit
  actually merges into
CAPABILITY-COVERAGE: not-applicable (bookkeeping unit, no capability rows)
LIVE-BROWSER: not-applicable
ISSUES-WRITTEN: none new
EXPLANATION: see below
```

### The three required cycle-2 fixes, each independently re-derived from primary sources

**1. Self-contradiction on AT-442/443/445 -- fixed, genuinely.** `qa/issues.jsonl` at HEAD reads
`"status": "fixed"` for all three, `fixed_by` citing exactly `qa/verdicts/at438-answered-gate-remainder.md
(3ae87a54)` (confirmed by direct parse of the ledger, not the manifest's summary of it). I confirmed:
- `3ae87a54` is a real commit, `qa(checker): FAIL at438-answered-gate-remainder cycle 1 --
  self-contradictory close-out` -- the cited authority genuinely exists and genuinely did the
  falsification (its own text, read directly, shows the `visual_order.js:60` reasoning and the fresh
  pytest re-run).
- `4bba329b` (`chore(qa): apply the checker's AT-442/443/445 ruling to the ledger`) is a real,
  separate commit on master, authored by the orchestrator applying the checker's ruling, as the
  manifest claims, and is an ancestor of this branch's HEAD (`git merge-base --is-ancestor 4bba329b
  HEAD` -> yes) -- reached via merge, not written from this worktree.
- `a9357439` itself (the unit's own cycle-2 commit) does **not** touch `qa/issues.jsonl` --
  `git show --stat a9357439` confirms only the three manifest/gate paths. The unit's claim that it
  "did not touch qa/issues.jsonl myself" and that the fix "arrived via `git merge master`" is literally
  true, not a rationalization.
- D-049's `Result:` section (`docs/DECISIONS.md`, read directly) names only AT-438/AT-449/AT-450
  (-> fixed), AT-454 (-> wontfix), AT-453 (stays open) -- AT-442/443/445 do not appear in `Result:` at
  all, only in the unrelated `Links:` line. The manifest's claim that D-049 "never names them" is
  correct.
- Both files (`at438-answered-gate-remainder.md`, `at438-display-contents.md`) now cite `3ae87a54` as
  the explicit authority for AT-442/443/445 and do not attribute them to D-048/D-049. No contradiction
  remains between the two files -- verified by reading both in full, not by trusting the manifest's own
  claim that it fixed this.

**2. Overstated `checked-PASS` -- fixed, and accurately scoped.** `at438-display-contents.md`'s header
now reads `**Status:** checked-PASS **for U14(b) only**`, names AT-453 (`t186-details-content`,
`580fd3a7`) and AT-454 (`wontfix`) as resolved elsewhere, and the closing `## Status:` line matches. I
confirmed `580fd3a7` (`qa(checker): t186-details-content cycle 1 -- PASS...`) and its merge `336433d1`
are both real commits reachable from HEAD, and that the qualifier matches exactly what
`qa/verdicts/at438-display-contents.md`'s "Re-ruling of cycle 3" section says ("for U14(b) only") --
neither broader nor narrower than that scope.

**3. False convention claim + stale gate -- fixed, and the correction itself is accurate.** I
independently re-checked all seven named gates:
`grep -n "Status:" qa/gates/{at147-expiry-end-of-day,at520-scripts-line-cap,commit-before-verdict,
at610-strict-out-of-order}.md` -> none use the field (confirming the cycle-1 sample was accurately
described, just wrongly generalized), and `at106-hook-architecture-path.md` / `at110-approval-forgery.md`
/ `at355-guard-shape.md` do use `Status: ANSWERED` (at110: `Status: ANSWERED -> built and merged`). The
gate this unit is named after, `qa/gates/at438-u14b-baseline.md`, now reads `**Status: ANSWERED -> acted
on**` -- `git diff a9357439^ a9357439 -- qa/gates/at438-u14b-baseline.md` shows exactly `+4/-1`, only
the header line changed. The new form follows the `at110` style (arrow + what happened) rather than
inventing a fourth spelling -- consistent with the existing two-form convention (bare `ANSWERED`, or
`ANSWERED -> <outcome>`), not a new one.

### Did correcting the prose introduce new inaccuracies? Yes -- one, low severity, self-disclosed

The manifest's own pasted "Cycle-2 `git diff --stat` before commit" table reads:
```
qa/gates/at438-u14b-baseline.md               |   5 +-
qa/manifests/at438-answered-gate-remainder.md | 150 ++++++++++++++++++++++----
qa/manifests/at438-display-contents.md        |  40 ++++++-
3 files changed, 170 insertions(+), 25 deletions(-)
```
The actual `git diff --stat a9357439^ a9357439` (re-run fresh by me) is:
```
qa/gates/at438-u14b-baseline.md               |   5 +-
qa/manifests/at438-answered-gate-remainder.md | 153 ++++++++++++++++++++++----
qa/manifests/at438-display-contents.md        |  40 ++++++-
3 files changed, 173 insertions(+), 25 deletions(-)
```
150 vs 153, 170 vs 173 -- a 3-line undercount on the remainder manifest's own insertion count. This is
real: the pasted table is stale relative to the file's own final committed state. The manifest's own
caveat ("the count includes this very table's own addition, which is expected for a self-describing
manifest") correctly anticipates that this kind of drift is structurally possible for a
self-describing file, but the actual number pasted still doesn't match -- tracing it, the trailing
paragraph after the table ("Exactly the three paths...", "No touch to...", the `## Status:` line) was
written after the `git diff --stat` was captured, adding the missing lines. **I am not failing the unit
over this**: it does not misstate which files changed, does not change the file count, does not affect
any of the three required fixes' substance, and is an order of magnitude smaller than the kind of
misrepresentation cycle 1 FAILed on (a self-contradiction about ledger status, an overstated scope, a
false convention claim). It is, however, exactly the class of thing the brief asked me to hunt for, and
I record it here rather than let a fifth instance of "asserting without looking" pass unnoted -- a
manifest citing an exact `git diff --stat` table should run it *after* all prose is final, or caveat
the specific number, not just the general phenomenon.

### Doctor / pytest staleness -- ruled acceptable, and here is why with evidence

The manifest's cycle-2 Verify table reports `uv run autotester doctor` -> 1 violation
(`stale-generated: docs/SNAPSHOT.md`) and `uv run pytest` -> `2 failed` (`test_goal_done_checks.py`,
T-190 waiver + 81==70 count). Re-running both fresh against this worktree's actual HEAD
(`a8cee3b9`, which includes the sync-merge of master bringing in `bae9568e` "stamp the tick -- waves
15-18; recompute goal progress" and the merged `at638-done-check-repair` PASS):
- `uv run autotester doctor` -> `doctor: clean` (run twice for consistency).
- `uv run ruff check src tests scripts` -> `All checks passed!`.
- `uv run pytest tests/test_goal_done_checks.py tests/test_goal_contract_registration.py` ->
  `8 passed`.

Both reds the manifest reported are real at the manifest's own commit time (`a9357439`) and have since
been fixed by commits that landed on master *after* `a9357439` (`bae9568e` for the SNAPSHOT
regeneration; `4a580f2c`/`0b79ab1b` merging the already-PASSed `at638-done-check-repair` for the two
test reds) and reached this branch only via the later sync-merge `a8cee3b9` -- confirmed via
`git merge-base --is-ancestor bae9568e a9357439` -> **no** (i.e. it postdates the unit's own commit).
`git diff --numstat a9357439^ a9357439` confirms the unit's own diff never touches `.goal/*` or
`docs/SNAPSHOT.md`, so it did not cause either red.

**Ruling: acceptable, not a defect, and not the same question as the manifest's own diff-stat staleness
above.** `qa/contracts/core-invariants.md` C10 explicitly distinguishes the "reviewed SHA" (what a
manifest's Verify table describes) from a subsequent "`Merge branch master` sync commit that brings
in nothing but master's own history," which needs no new cycle precisely because the checker is
expected to re-verify against the merged tree before relying on it -- which is what I just did, fresh,
and it is green. Requiring a manifest to predict and paste evidence for commits that land on master
*after* its own commit, while it waits in the check queue, would be a moving target with no fixed
point; the sync-merge exception exists so that job falls to the checker instead. This is a different
disposition from the diff-stat mismatch above only in that the diff-stat table describes the unit's
*own* content, fully within its control at commit time, whereas the suite/doctor state describes the
wider repo, which explicitly is not.

### Item 8 -- the two deliberate omissions

- **`qa/QUEUE.md`'s stale sweep note, left unedited.** Verified: a correction already exists in the
  file at "## Correction -- the `at438-display-contents` answered-gate finding was mostly wrong" (the
  orchestrator's entry, dated 2026-09-27, naming the sweep's three false claims and filing
  `ISS-sweep-unverified-negative`). The manifest's claim that "the orchestrator has since appended a
  correction there" is accurate. **Ruling: acceptable** -- `qa/QUEUE.md` is a live, concurrently-written
  log with no established in-place-edit convention for past rows (checked: no other row in the file is
  retroactively marked resolved), and the correction the unit points to already discharges the concern
  independently.
- **`qa/contracts/` left untouched by the unit.** Correct restraint -- `qa/contracts/` is checker-owned.
  See the C7 amendment below, which I made myself in this cycle rather than leaving the cycle-1
  verdict's recommendation dangling a second time.

### The C7 amendment -- made, not just recommended again

The cycle-1 verdict recommended, but declined to write (correctly, for C10 reasons), one sentence for
`qa/contracts/core-invariants.md` C7 confirming that a zero-code unit's correctly-named
pre-existing/concurrent failure does not block its own PASS. The brief asked this cycle's checker to
settle it rather than pass the recommendation forward a second time. **I amended it.** Added to C7 (new
bullet after the existing Verify clause) and logged in the Amendment log, both dated 2026-09-27, citing
this verdict and `qa/verdicts/t192-url-pattern-heal.md`'s independent identical observation. The
addition is deliberately narrow: it requires the manifest to name the failing test(s) individually and
*show*, not assert, the cause outside its own diff, and it does not excuse a failure the unit caused,
misnamed, or did not actually verify -- so it tightens the reading into words without weakening the
underlying Verify duty. `uv run autotester doctor` and `uv run ruff check src tests scripts` both stay
clean after this edit (re-run above, post-edit).

### What I did not fault, confirmed independently

- **Diff discipline**: `git diff --numstat a9357439^ a9357439` -> exactly the three paths the manifest
  and this unit's brief name, matching `qa/gates/at438-u14b-baseline.md` (+4/-1),
  `qa/manifests/at438-answered-gate-remainder.md` (+134/-19), `qa/manifests/at438-display-contents.md`
  (+35/-5) exactly as given in the dispatch brief.
  Cycle-1's own diff (`76bc6e93^..76bc6e93`) numstat re-confirmed too: `142/0` (new file) and `24/2` --
  matching both manifests' own claims about their cycle-1 change sizes.
- **Every commit SHA cited by the cycle-2 prose** (`3ae87a54`, `4bba329b`, `6d2eb0bd`, `580fd3a7`,
  `336433d1`, `76ceb4d4`) resolves to a real commit with the claimed subject line.
- **`qa/contracts/ui.md`** grep claims ("branch point", "AT-454") both present as claimed.
- **`at015-at028-hook-adapter-fix.md`** precedent text ("Recovery confirmed -- checked-PASS.") verified
  present, supporting the manifest's citation of it as prior art for a STALLED-unit resolution flip.
- **AT-627** is a real, previously-documented flaky-test tag (`test_flake_probe_real_process.py`
  grandchild test) -- the manifest's framing of its clean pass this cycle as "supporting contention, not
  regression" is a reasonable, non-overstated reading, not a fifth new claim needing correction.

## Status: checked-PASS -- cycle 2
