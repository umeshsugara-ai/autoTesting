# Verdict — t150-track-c-governance

**Cycle checked:** 1
**Date:** 2026-09-27
**Checker:** fresh claude-sonnet-subagent (Executor of unit: a `/maker` build subagent, per the
manifest's corrected Executor line)
**Status:** COMPLETE.

## Final verdict block

```
VERDICT: PASS
SCOREBOARD: 14/14 filed criteria (AI1-AI7, AD1-AD7) accepted into contracts, 0 refused outright;
  1 criterion (orig. AI2) split into two; 1 criterion (orig. AI3, Catalog reuse) folded into a
  cross-reference rather than refiled as a new criterion, to avoid duplicating catalog.md CT7.
FAILURES: none
CONTRACTS AUTHORED: qa/contracts/ai-target.md (AI1-AI8, DRAFT), qa/contracts/adversarial.md
  (AD1-AD7, DRAFT, bounds a HELD capability)
DONE_CHECK: `uv run python scripts/check_deliverable.py --exists qa/contracts/ai-target.md
  qa/contracts/adversarial.md && uv run autotester doctor` -> exit 0 (re-run live, this worktree)
LIVE-BROWSER: not applicable -- no screen/route/component/schema/stage changed; manifest's own
  "skip (governance)" call is correct.
ISSUES-WRITTEN: ISS-t150-1 (low, spec-coverage-gap -- docs/spec.md R30 has no requirement row for
  T-154/T-155; informational, does not block this unit or adversarial.md's validity since D-018's
  own Changes-authorized line is independent authority)
AT-638: left OPEN, correctly -- it also names T-166/T-167/T-168/T-171, none touched here. This
  verdict answers only the Track C slice.
EXECUTOR: a /maker build subagent (per the manifest's own orchestrator-corrected line, verified
  accurate against .goal/goal.json and docs/plan.md -- see "Corrections verified" below).
EXPLANATION: The maker's two groups of proposed criteria (AI1-AI7, AD1-AD7) are substantively
sound and are D-017/D-018's own text in all but four cases (orig. AI2's adversarial-kind clause,
orig. AI3's Catalog-reuse restatement, AD6, AD7). All four were checked rather than rubber-stamped:
orig. AI2 was split so the D-017-verbatim claim and the maker's adversarial-input extension are
independently attackable; orig. AI3 was folded into a cross-reference to catalog.md's own CT7
(which already explicitly extends to "any later Track-C catalog code") rather than refiled, because
refiling it would give one concept two ground truths in two contracts; AD6/AD7 were accepted as
defense-in-depth under the D-016 write-policy precedent (an inner guard inside an outer boundary is
an established pattern here, not a novel one) rather than as D-018 derivations, and neither
authorizes anything -- both only narrow a future build, so accepting them does not require a fresh
Umesh gate. The AT-218 vacuous-guard concern was checked specifically: AI1/AI6/AI8's Verify greps
target files that do not exist yet (measured: all five Track-C stage files and both new schema
files are absent from this branch; a grep against them exits 2, not "no match"). This is not the
AT-218 defect -- it is the same forward-declaration shape this repo's own catalog.md CT7 already
used under D-039 before T-125 landed -- but each criterion now carries an explicit Landing note
saying so, so a future checker cannot mistake "file not found" for "criterion satisfied." AI3's own
Verify (grep for class Catalog / class BlockedReason) was run for real against this branch: it
returns ZERO matches today (schema/catalog.py does not exist, T-125 still pending), not "exactly
one" as filed -- recorded as the expected pre-T-125 state, matching CT7's own precedent, not a new
defect. Doctor's L6 router-row check does not apply to qa/contracts/ (RepoDocs.docs_dir is
root/docs only; verified by reading src/autotester/core/paths.py and doctor.py directly), so
neither new file needs a CLAUDE.md router row or a Purpose/Open-me-when header, and neither was
given one -- matching consent.md/catalog.md's own header style instead. Both new files pass
`autotester doctor` and `ruff check` clean, and T-150's own done_check was re-run live and exits 0.
```

## Criteria scored (against the maker's own filing)

- **AI1 (discovery signals deterministic/file-cited):** accepted near-verbatim into `ai-target.md`
  AI1, with an added Landing note (files don't exist yet; a grep-exit-2 must not be read as a pass).
- **AI2 (model names kind, table chooses checks):** split. The D-017-verbatim table-mapping claim
  became `ai-target.md` AI2. The maker's own flagged extension (an out-of-table/adversarial-string
  kind must still resolve safely) became a separate, independently-attackable `[maker]` criterion,
  AI3 -- exactly the split the maker's inbox entry itself suggested as the checker's likely call.
- **AI3 (orig., Catalog/BlockedReason reuse):** **not refiled as a new criterion.** `catalog.md`
  CT7 already states this contract is "judged over every unit that touches `stages/ai_catalog.py`
  or any later Track-C catalog code" -- T-152's file, named explicitly. Restating it in
  `ai-target.md` would create two ground truths for one concept. Folded into `ai-target.md` AI4 as
  a cross-reference with its own re-measured Verify (0/0 matches today, as expected pre-T-125).
- **AI4 (blocked check names the missing fixture):** accepted, renumbered AI5.
- **AI5 (capturer never grades):** accepted, renumbered AI6.
- **AI6 (captures scrubbed before judge):** accepted, renumbered AI7.
- **AI7 (context read as plain markdown only):** accepted, renumbered AI8.
- **AD1-AD5 (approval-before-anything, exact target+bound, production grant, no hard probe-lib
  dependency, exerciser never grades):** all accepted verbatim in substance into `adversarial.md`
  AD1-AD5 -- each already a direct restatement of D-018/D-017 or a direct mirror of an existing
  `consent.md` criterion (CN1, CN5/CN6, CN7).
- **AD6 (absolute probe ceiling in code):** accepted, tagged `[maker's addition, accepted]` with the
  D-016 precedent named explicitly as the reasoning (see contract). Not a decision handed to Umesh:
  it only narrows a HELD capability's eventual build, and D-016 already establishes this exact
  inner-guard shape as normal practice in this repo.
- **AD7 (refusal audit-trail log):** accepted, same reasoning as AD6.

## Corrections verified (things the brief asked me not to take on trust)

- **Executor line.** The manifest's corrected claim -- "a `/maker` build subagent... dispatched by
  the orchestrator," not "the orchestrator, inline" -- is checked against `git log`: commit
  `25f1e403` (the substantive filing) and `0ea7559b` (the correction itself) both carry
  `Co-Authored-By: Claude Opus 5`, consistent with a subagent build rather than a bare orchestrator
  edit, and the correction commit's own message explains the discrepancy plausibly (a subagent's
  self-report is not authoritative about who dispatched it). Accepted as accurate; no independent
  way exists to fully verify *who* dispatched a subagent from git history alone, so this is
  accepted on the balance of evidence, not proven beyond doubt.
- **"Register the C tasks" already satisfied.** Verified directly against `.goal/goal.json`: T-150
  through T-155 all carry `"created": "2026-09-08T00:46:52"`, each with its own `deps`, `note` and
  `done_check` -- confirms the manifest's claim exactly. `docs/plan.md` rows 15/20/24/25 name
  T-150/T-151/T-152/T-153 (T-154/T-155 sit in the "Held / blocked" section, not the numbered wave
  table -- the manifest did not claim otherwise). `target.md` M11 lists all six. `docs/spec.md` R30
  maps to "T-150-T-153" only, confirming the manifest's own disclosed gap (see ISS-t150-1).
- **AT-638 stays open.** Confirmed by reading the row directly: it names T-166, T-167, T-168, T-171
  and "T-150..T-155 (Track C)" as the five ungoverned capabilities. This unit answers only the
  Track C portion. **Not closed by this verdict.**
- **No probe sent, no code touched.** `git show --stat` on both commits (`25f1e403`, `0ea7559b`)
  shows only `qa/feedback-inbox.md` and `qa/manifests/t150-track-c-governance.md` touched -- zero
  `src/`, `tests/`, or `scripts/` changes, confirming the manifest's claim.

## Verify commands run (this worktree, live)

```
$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run python scripts/check_deliverable.py --exists qa/contracts/ai-target.md qa/contracts/adversarial.md
OK 2 deliverable(s) present

$ grep -rn "class Catalog" src/autotester/schema/ ; grep -rn "class BlockedReason" src/
(no output -- zero matches, expected pre-T-125 state, see AI4's re-measured Verify)

$ ls src/autotester/stages/discover.py src/autotester/stages/read_context.py \
     src/autotester/stages/ai_capture.py src/autotester/stages/ai_catalog.py \
     src/autotester/stages/adversarial.py
(all: No such file or directory -- confirms every Landing note's premise)
```

**`uv run pytest` (no CLI `-q`, AT-503):** attempted, did not complete inside a 300s bound (the full
suite is large -- a prior unit's own verdict on this branch's ancestor cites "2016 passed, 5
skipped, 32 xfailed"). Not re-attempted at full length: this unit changes zero files under `src/`
or `tests/`, so there is nothing pytest would newly exercise, matching the manifest's own stated
rationale for skipping it. `ruff` + `doctor` + the live re-run of T-150's actual `done_check` are
treated as sufficient verification for a contracts-only, no-code unit.

## Gaps disclosed by this check (not blocking PASS)

- **ISS-t150-1** (low): `docs/spec.md` R30 has no requirement row for T-154/T-155. Filed to
  `qa/issues.jsonl`; recommendation is to add the row when T-154 is unblocked. Does not affect this
  unit or `adversarial.md`'s present validity (D-018 authorizes the contract directly).
- **AI3's Executor-attribution acceptance** (see above) rests on git co-author metadata rather than
  independently observable dispatch evidence; flagged rather than silently assumed.
- No `qa/gates/<slug>.md` was opened. AD6/AD7 were judged as within the checker's own authority
  (narrowing only, consistent with the D-016 precedent) rather than a decision requiring Umesh.
  If Umesh disagrees with that judgement on review, both criteria can be struck or re-tagged in a
  later amendment without touching AD1-AD5.

## Live browser evidence

Not applicable — no screen, route, component, schema, or stage changed. `qa/contracts/ai-target.md`,
`qa/contracts/adversarial.md`, `qa/issues.jsonl`, and this verdict are the only paths touched by the
check; none renders anywhere in the product.
