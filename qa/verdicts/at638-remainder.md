# Verdict — at638-remainder

**Cycle checked:** 1
**Date:** 2026-09-27
**Checker:** fresh claude-sonnet-subagent (Executor of unit: a `/maker` build subagent, per the
manifest's own Executor line, verified against git co-authorship on this branch)
**Status:** COMPLETE (governance gate found — not a build defect).

## Final verdict block

```
VERDICT: FAIL
SCOREBOARD: 17/17 filed criteria (PS1-PS4, EC1-EC4, RR1-RR5, DC1-DC4) reviewed and judged
  buildable-as-worded; 0 refused outright; 1 finding on a criterion's own authority-tag (RR2, see
  below). The FAIL is not against criterion quality -- it is against the unit's deliverable chain
  being unable to complete this cycle: qa/contracts/ is Lab-Protocol-gated, and no
  docs/DECISIONS.md entry authorizes any of the four proposed files. This is the same class of gate
  the manifest itself found and refused to route around; I independently re-derived the same
  conclusion and it holds.
FAILURES:
- [authorization] sev: high · none of permission-surface.md/eval-compiler.md/release-regression.md/
  damage-control-report.md has a docs/DECISIONS.md Changes-authorized line naming it (verified
  against D-040 and D-041's full text, see below) · fix direction: Umesh approves a new DECISIONS
  entry naming the four files as checker-owned deliverables (draft below), written via
  `scripts/append_decision.ps1` · issue: ISS-at638-remainder-1
- [RR2] sev: low · RR2's authority tag claims it "extend[s] CN1/CN5/CN6" but its own stated Verify
  clause only exercises CN1-shaped behaviour (refused-without-approval); it never tests CN5's exact-
  target-match or CN6's bound-shortfall for the release-regression caller, unlike AD2 (the precedent
  it names), whose Verify explicitly runs the four CN5 exactness variants and a CN6 shortfall probe
  against the new caller · fix direction: when release-regression.md is actually authored, either
  add a CN5/CN6-shaped Verify to RR2 or drop the CN5/CN6 tag and keep only CN1/CN9 · not filed as a
  ledger issue (no contract exists yet to attach it to); recorded here for whoever authors the file.
CAPABILITY-COVERAGE: not-applicable (no code, no test added or rewritten; the unit's own manifest
  states this explicitly and I confirm it -- git diff --stat shows only qa/feedback-inbox.md and
  qa/manifests/at638-remainder.md touched, 465 insertions, 0 deletions, no other path).
LIVE-BROWSER: not-applicable (no screen, route, component, schema, or stage changed).
ISSUES-WRITTEN: ISS-at638-remainder-1 (high, approval-required) filed to qa/issues.jsonl on master.
EXECUTOR: a /maker build subagent (checker: claude-sonnet-subagent; self != executor, no
  ANTHROPIC_BASE_URL override in this session).
EXPLANATION: The filed criteria are sound, correctly cross-referenced, and match the conventions
  t150-track-c-governance's checker set. But this unit's own authorization finding is correct and I
  independently re-derived it from docs/DECISIONS.md rather than trusting the paste: D-040's
  Changes-authorized names only crawl-traversal.md and network-assertions.md; D-041's names only the
  seven T-172-178 files (run-trace.md, parallel-run.md, cli-mcp.md, skills.md, script-replay.md,
  agent-fallback.md, failure-bundle.md); T-168 appears in neither D-040 nor D-041 nor D-042. This
  repo's own established practice is unbroken at 5/5 -- ai-target.md + adversarial.md (D-017/D-018),
  catalog.md (D-039), crawl-traversal.md + network-assertions.md (D-040), the seven T-172-178
  contracts (D-041), agent-layer.md (D-042) -- every prior checker-authored contract file was named
  by an Approved-by: Umesh entry BEFORE the checker wrote it. This project's own CLAUDE.md Lab
  Protocol section states the rule generally: "no edit to ARCHITECTURE.md or contracts/ without an
  authorizing DECISIONS entry written FIRST containing the reasoning." Authoring
  permission-surface.md, eval-compiler.md, release-regression.md or damage-control-report.md right
  now would be the first contract file in this repo's history written without that authorization --
  exactly the shortcut the unit's own brief warned against manufacturing. I am not writing that
  entry myself (docs/DECISIONS.md is append-only via scripts/append_decision.ps1, and an
  Approved-by: line requires Umesh, not a checker). Ruling: HUMAN_GATE. The unit cannot PASS this
  cycle on that basis alone, independent of the quality of what was filed.
```

## Ruling on the authorization question (mine, not the maker's, per the dispatch)

**May the checker author these four contract files now? No.** Verified directly against
`docs/DECISIONS.md` (not paraphrased):

- **D-040's `Changes-authorized`** (line 871-874): "docs/ARCHITECTURE.md ... qa/contracts/
  crawl-traversal.md and qa/contracts/network-assertions.md (new, checker-authored DRAFT).
  .goal/goal.json: register T-170 and T-171, and widen T-165's note and done_check." T-171 gets a
  goal-task registration, not a contract file. `crawl-traversal.md`'s own line 164 forward-reference
  to "permission-surface.md (future, T-171)" is a naming hint left by a prior checker, not
  Umesh-approved authority.
- **D-041's `Changes-authorized`** (line 923-928): "New checker-authored DRAFT contracts under
  `qa/contracts/`, as listed in Result." Result (line 917-921) lists exactly: `run-trace.md,
  parallel-run.md, cli-mcp.md, skills.md, script-replay.md, agent-fallback.md, failure-bundle.md`.
  T-166 and T-167 each get a `.goal/goal.json` note appended -- explicitly not a contract file.
- **D-042** authorizes only `qa/contracts/agent-layer.md` (T-179). T-168 is not named by D-040,
  D-041, or D-042, and has existed in `.goal/goal.json` since 2026-09-10 -- before any of them.

This project's own CLAUDE.md (Lab Protocol section) says the rule plainly: **"no edit to
ARCHITECTURE.md or contracts/ without an authorizing DECISIONS entry written FIRST containing the
reasoning."** `qa/contracts/` is this repo's `contracts/` -- every prior checker-authored file
(5 for 5, D-017/D-018/D-039/D-040/D-041/D-042) was named by such an entry before it was written, no
exceptions. Writing any of the four proposed files now would be an unauthorized edit to a
Lab-Protocol-governed path, not a routine amendment I have discretion over. **This is a HUMAN_GATE,
not a judgement call within my normal contract-maintenance authority** (the criticality gate table
in the checker skill reserves "initial contract creation (START)" for human approval always -- this
is exactly that case, applied to four new files at once).

**Draft DECISIONS entry, for Umesh to approve (I did not write this to docs/DECISIONS.md -- that
file is append-only via `scripts/append_decision.ps1` and needs his `Approved-by:` line first):**

> **What:** Authorize `/checker` to author four new checker-owned DRAFT contract files from the
> criteria filed in `qa/feedback-inbox.md` (2026-09-27, at638-remainder unit): `qa/contracts/
> permission-surface.md` (PS1-PS4, T-171, D-040), `qa/contracts/eval-compiler.md` (EC1-EC4, T-166,
> D-041), `qa/contracts/release-regression.md` (RR1-RR5, T-167, D-041), `qa/contracts/
> damage-control-report.md` (DC1-DC4, T-168, previously unauthorized by any decision). Each goes
> DRAFT -> ACTIVE on its own unit's first checker PASS, same as every prior batch.
> **Why:** AT-638 (checker-sweep, high) found these four capabilities have zero checkable contract
> criteria; D-040/D-041 registered the goal tasks but never named contract files for them (T-168 was
> never named by any decision at all). This closes that governance gap the same way D-039/D-040/
> D-041/D-042 closed it for every other checker-authored contract in this repo.
> **Changes-authorized:** the four files named above (new, checker-authored DRAFT).
> **Approved-by:** Umesh -- <pending>.
> **Links:** AT-638; T-166; T-167; T-168; T-171; D-040; D-041; qa/verdicts/at638-remainder.md

## Criteria reviewed (all 17, against D-040/D-041 and the existing contracts they defer to)

- **PS1, PS3** (defer to `consent.md` CN1/CN9 and `coverage.md` V7(a)-(c)): checked against the real
  text of CN1 ("nothing outward-facing starts without approval... judged at every shipped entry
  point"), CN9 ("the gate applies to every crawl, including local fixtures... reversing this is a
  CRITICAL amendment"), and V7(a)-(c) (`controls_discovered`/`controls_exercised`/closed reason set/
  book-balance identity). The deferrals are accurate, not vacuous -- V7 genuinely already computes
  the exact book-balance PS3 needs, and CN1/CN9 genuinely establish an unconditional approval gate
  PS1 can bind to rather than re-deriving.
- **PS2** ("destructive actions ordered last"): the manifest and inbox both tag this `[D-040
  verbatim]`, correctly -- D-040's own "What" section states it in these words. Buildable as worded.
  (Note: the dispatch grouped PS2 with the "freely arguable [maker]" set; on my own read of the
  inbox and D-040, PS2 is direct decision text, not a maker addition -- a minor mischaracterisation
  in the dispatch, not a defect in the filing.)
- **PS4** (`[maker, hardening]`, no second coverage number): reasonable, low-risk, explicitly
  self-voiding if T-171 adds no new surface. Accept.
- **EC1** (KG extends `schema/portal_persona.py`, not a second schema): verified the file exists with
  `PersonaScreen`/`PersonaTransition`/`PersonaRevision` classes already on disk -- extending it for
  screen/control/flow/scenario/case/verdict/API/release nodes is buildable as worded, and mirrors
  `ai-target.md` AI4's Catalog-reuse ruling as claimed.
- **EC2-EC4**: EC3 is checked against `grade.md`/`expand.md` per the inbox's own claim -- neither
  states "component PASS cannot hide workflow FAIL" today (spot-checked both files' criteria lists),
  so EC3 is a genuine new criterion, correctly not mis-tagged as a decision restatement. EC2/EC4
  restate T-166's own goal-task note and the D-041 EXTEND note respectively; buildable as worded.
- **RR1** (LangGraph converts `orchestrate.py` in place; preserves OR2/OR4): checked OR2 ("resume
  never redoes a completed stage") and OR4 ("a crashed stage leaves an honest checkpoint") in full --
  exact match to "resume-without-redo" and "crash-honesty" as characterised. Not vacuous.
- **RR2**: see FAILURES above -- the CN5/CN6 tag is not backed by its own stated Verify, unlike its
  named precedent AD2 (checked: AD2's Verify explicitly runs CN5's four exactness variants and a
  CN6 bound-shortfall probe against the new caller). Low-severity finding, not blocking (no file
  exists yet to be wrong in).
- **RR3** (`[maker]`, named baseline rule): reasonable -- prevents D-041/goal.json's "last trusted
  baseline" language from staying unfalsifiable. Accept.
- **RR4** (exerciser never grades, third instance of the AI5/AD5 family): checked core-invariants.md
  C7 exists and is the right anchor; consistent pattern, not re-derived.
- **RR5** (`langgraph` declared only within this unit): checked core-invariants.md C11 exists
  ("every third-party import is a declared dependency"); consistent, buildable.
- **DC1, DC2, DC4** (defer to V7, CR5, NA1, RE1, RE5): checked all five cited criteria in full text.
  CR5 genuinely covers "skip/blocked never reads as fully explored," NA1 genuinely captures
  first-party network evidence, RE1 genuinely states "reads only existing evidence, never a new
  source of truth" (the exact principle DC2 needs), RE5 genuinely states the no-secrets guarantee
  DC4 needs verbatim. None of the four deferrals is vacuous.
- **DC3** (`[maker]`, genuinely-unified artifact): the word "unified" is literally in T-168's own
  goal-task title ("Unified damage-control report"), so this is closer to a restatement of the
  task's own name than a maker invention -- without it, DC1/DC2/DC4 could be satisfied by four
  unlinked files, which would not be "unified" by any reading. Accept.

## D-042 / T-179 dependency tension (point 5) -- ruling: leave disclosed, do not pick a side

Verified directly against `.goal/goal.json`: T-167's `deps` = `["T-166", "T-110"]` (no T-179).
`docs/plan.md` row 21's dependency column names only `18` (t166-eval-compiler-kg). `src/autotester/
agents/` does not exist (`ls` exits 2, confirmed). D-042's own prose does say "T-167 (release
regression) runs the lead agent on LangGraph checkpoints" -- and that sentence is even echoed in
T-167's own `.goal/goal.json` `note` field ("D-042: runs the lead agent on LangGraph checkpoints"),
so the tension is real and sits inside the ground truth itself, not just in D-042's prose. The unit
correctly wrote no criterion assuming either reading. I make the same call: this is recorded as an
open tension for whoever eventually builds T-167 or amends `release-regression.md`'s scope, not
resolved here.

## Verify commands run (this worktree, live, re-run by me)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ git diff --stat 81054533...HEAD
 qa/feedback-inbox.md            | 235 ++++++++++++++++++++++++++++++++++++++++
 qa/manifests/at638-remainder.md | 230 +++++++++++++++++++++++++++++++++++++++
 2 files changed, 465 insertions(+)

$ grep -rlnE "permission_surface|PermissionSurface" src/   -> exit 1, no matches (reproduced)
$ grep -rlnE "knowledge_graph|KnowledgeGraph|kg_node|KGNode" src/ -> exit 1, no matches (reproduced)
$ grep -n "langgraph" pyproject.toml                        -> exit 1, not declared (reproduced)
$ grep -rlnE "langgraph|interrupt\(" src/                    -> exit 1, no matches (reproduced)
$ grep -rlnE "damage_control|DamageControl|unified_report" src/ -> exit 1, no matches (reproduced)
$ ls src/autotester/stages/orchestrate.py                    -> exists (reproduced)
$ ls src/autotester/agents/                                  -> exit 2, does not exist (reproduced)
```

`uv run pytest` (no CLI `-q`, AT-503): launched live in this worktree; the full suite runs long
(the sibling unit's own check cites "2016 passed, 5 skipped, 32 xfailed" and did not complete inside
a 300s bound either). This unit changes zero files under `src/` or `tests/` -- `git diff --stat`
above is the complete file list -- so there is nothing pytest would newly exercise. `ruff` + `doctor`
+ the full diff-stat are treated as sufficient verification for this contracts-only, no-code unit,
matching the sibling checker's own accepted practice on `t150-track-c-governance`.

## Diff scope (step 4c)

`git diff --stat 81054533...HEAD` shows exactly two paths, both listed in the manifest's "What
changed": `qa/feedback-inbox.md` (235 insertions) and `qa/manifests/at638-remainder.md` (230
insertions, new file). Zero deletions, zero renames, no file outside the manifest's claim. Clean.

## AT-638 -- ruling: stays OPEN

`t150-track-c-governance` closed the Track C slice (`ai-target.md`/`adversarial.md`, now ACTIVE).
This unit's proposals are sound but are **not yet checkable contract criteria** -- they are inbox
entries, gated behind the missing DECISIONS authorization above. AT-638's own title condition
("ZERO checkable contract criteria") is not yet satisfied for T-166/T-167/T-168/T-171: a proposal in
`qa/feedback-inbox.md` is not a `[C*]` criterion in `qa/contracts/`. AT-638 stays `open`. I am
updating its evidence trail (not its status) to record that the remaining work is now fully
specified and blocked only on the DECISIONS entry above, not on any further analysis.

## What I am leaving for Umesh

1. **The DECISIONS entry draft above** -- a yes/no + naming decision, same shape as D-039/D-040/
   D-041/D-042. Once `Approved-by: Umesh` lands via `scripts/append_decision.ps1`, the next checker
   dispatch (Mode A on a fresh manifest, or a direct `/checker` invocation) can author the four files
   from the vetted criteria above with no further analysis needed -- this verdict already did the
   review.
2. **RR2's CN5/CN6 tag** (low severity) -- worth a look when release-regression.md is actually
   authored, not before.
3. **The D-042/T-179 tension** -- whether T-167 depends on the Deep Agents lead agent (T-179) or not
   is still unresolved in the ground truth itself (D-042's prose vs. goal.json's `deps` array).

## Live browser evidence

Not applicable — no screen, route, component, schema, or stage changed. `qa/verdicts/
at638-remainder.md` and `qa/issues.jsonl` (on master) are the only paths this check writes to.
