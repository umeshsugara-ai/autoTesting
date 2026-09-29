# Contract — release-regression (run the whole suite on a release, and compare honestly)

**Status:** **DRAFT** (authored by /checker 2026-09-28 under **D-054**, `Approved-by: Umesh`).
Goes **ACTIVE** on T-167's first checker PASS.
**Feature:** T-167 — convert the orchestrator to LangGraph, gate consent/review with `interrupt()`,
and compare a release run against the last trusted baseline.
**Code:** does not exist yet (T-167 `pending`). The module it converts is
`src/autotester/stages/orchestrate.py` (T-163, done). No LangGraph usage exists in `src/` and
`langgraph` is not in `pyproject.toml`.
**Dependencies:** **T-166 and T-110 only** — settled by **D-055**. See the disclosure below.
**Grounding:** D-041 (names RR1 verbatim; it is the superseding entry `orchestrator.md`'s no-fire
list was waiting for) · D-055 · `orchestrator.md` OR2/OR4 · `consent.md` CN1/CN9 ·
`core-invariants.md` C7 and C11 · AT-638.

## Why it exists

A regression suite that silently compares against "whatever ran last" will call a release clean
because the previous release was already broken. The point of T-167 is that the comparison has a
**named, testable** baseline rule, and that converting the orchestrator to LangGraph does not quietly
cost the resume-without-redo and crash-honesty guarantees `orchestrator.md` already won.

## Criteria

### RR1 — LangGraph converts `orchestrate.py` IN PLACE, and must not weaken OR2/OR4 [D-041 verbatim]

It is a conversion, **not a second orchestrator**. `orchestrator.md`'s own no-fire list declined
LangGraph "in this unit" (T-163) pending a superseding entry; **D-041 is that entry**, scoped to
T-167. Edit in place — this repo's standing anti-drift rule, and here it is also a contract term.

OR2's resume-without-redo and OR4's crash-honesty must be **preserved, not merely re-implemented**.

**Verify:** OR2/OR4's own falsification shapes, reproduced against the LangGraph checkpointer
substrate instead of the filestore `RunState` — mark a stage done, re-run, assert it is not redone;
force a raise, assert `failed` status and the correct resume point.

### RR2 — `interrupt()` LAYERS ON TOP OF `RunApproval`; it never replaces it [D-041 explicit]

A release run needs its own valid `RunApproval` **before it starts**, exactly as every other
outward-facing entry point does. `interrupt()` is a human-in-the-loop pause inside the graph; it is
not an approval mechanism.

**Scope correction carried from D-054, and it narrows this criterion deliberately:** the filed
version of RR2 claimed authority from `consent.md` CN5/CN6, and that claim is **overstated against
RR2's own stated Verify**. What RR2 actually tests is CN1's shape (nothing outward-facing starts
without approval) and CN9's unconditionality. CN5/CN6 are not cited here. A unit must not import
CN5/CN6 obligations from this file.

**Verify:** a release run with no `RunApproval` is refused **before** the LangGraph graph is invoked
— CN1-shaped: no run directory, no navigation. A run *with* approval reaches the `interrupt()` point,
and a resume without human input never proceeds past it.

### RR3 — "The last trusted baseline" is ONE named, testable rule — never "whatever ran last"

D-041 and `.goal/goal.json` name the *property*; they do not specify its mechanics. This criterion
does not assert a particular rule. It requires the build to **pick one, name it, and test it.**

**Verify:** a fixture with three release runs — good, bad, good. Whichever "trusted" rule the build
adopts must be named and exercised. For example, if a flagged-bad run is excluded, the third run's
diff must compare against the **first good** run and skip the bad one — not silently against the
immediately-prior run.

### RR4 — The release trigger never grades [C7; third instance of one family]

The mechanism that starts a release run does not also judge its outcome. This is the same shape as
`ai-target.md` AI5 and `adversarial.md` AD5, and it is **cited, not re-derived**.

**Verify:** the AI5/AD5 test shape, applied to the release-trigger module.

### RR5 — `langgraph` is declared in `pyproject.toml` only within this unit [D-041, C11]

**Verify:** `grep -n "langgraph" pyproject.toml` returns a real line, and `uv run autotester doctor`'s
`check_dependencies_declared` reports clean.

### RR6 — Per-flow validation plans are stitched into ONE release run that ends in ONE issues log

*(Added 2026-09-29 from Umesh's verbatim 2026-09-24 meeting direction, `qa/feedback-inbox.md`
2026-09-24T16:10, 09:28-09:47: "jab yeh ek flow poora complete ho jayega next time woh ek hamara plan
ban jayega ... woh stitch ho jate hain ek ke upar ek. Toh jab aap badi release karte ho toh yeh saare
flow automatic check karke aapko last me log de dega ki yahan yeh yeh issues hain.")*

Each completed flow leaves a persisted validation plan. A release run executes **all** of them and
terminates in a **single** issues log naming each issue's flow. A flow with no plan is reported as
**not run**, never omitted from the log.

**Verify:** a fixture with 3 flows, each with a persisted plan and one seeded failure in two of them —
one release run produces one log containing both failures with their flow ids, and the third flow
appears as passed. Remove one flow's plan — it appears in the log as `not run`. Sabotage: run only the
first plan — the two-failures assertion goes red.

## Disclosed dependency tension — RESOLVED, recorded so it is not re-opened

D-042 says *"T-167 runs the lead agent on LangGraph checkpoints"*, which would tie T-167 to the Deep
Agents lead agent (T-179). The maker who filed these criteria declined to pick a side and flagged it
instead — correctly, because `.goal/goal.json` T-167 `deps` are `["T-166", "T-110"]`, `docs/plan.md`
row 21 names only T-166, and `src/autotester/agents/` does not exist.

**D-055 settles it: T-167 depends on T-166 and T-110 only, and this contract encodes no T-179
dependency.** D-042's sentence describes a later integration, not T-167's own build. No criterion
here assumes the lead agent.

## No-fire list

- Building T-167 itself.
- The Deep Agents lead-agent integration — not this contract's job (D-055).
- The concrete webhook / CI trigger mechanism — named by no decision read.

## Amendment log (append-only; git history is the version)

- 2026-09-28 · init · authored by /checker under D-054 from the criteria filed in
  `qa/feedback-inbox.md` (2026-09-27, `at638-remainder`). Cause: AT-638 — T-167 had zero checkable
  criteria. Two things carried in rather than copied: **RR2 is narrowed**, dropping the filed CN5/CN6
  authority claim that D-054 records as overstated against RR2's own Verify; and the **T-179
  dependency tension is closed by D-055** rather than left flagged, so a future unit does not
  re-litigate it. DRAFT until T-167's first PASS. **Changes-authorized:** this file (named by D-054).
  No enforcement-path file touched. **Links:** AT-638; D-041; D-042; D-054; D-055; T-167; T-163.

- 2026-09-29 · routine (add) · RR6 added: per-flow validation plans stitch into one release run that
  ends in one issues log, and a planless flow is `not run`, never omitted. Cause: Umesh's verbatim
  2026-09-24 meeting direction ("the product's own north star as the customer states it"), tagged
  "unfolded pending T-167's contract" since 2026-09-24; RR1-RR5 govern the substrate, the approval,
  the baseline rule, the grading boundary and the dependency, and none states the stitching.
  Adds a criterion, weakens none. **Changes-authorized:** this file (D-054). No enforcement-path file
  touched. **Links:** AT-666; D-054; T-167; qa/feedback-inbox.md 2026-09-24T16:10.