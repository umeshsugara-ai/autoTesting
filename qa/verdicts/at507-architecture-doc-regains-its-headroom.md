# Verdict — at507-architecture-doc-regains-its-headroom

**Cycle checked:** 1
**Date:** 2026-09-18
**Checker:** fresh subagent, bound to `d:/autoTesting`
**Commits under check:** `d7298b5` (the ARCHITECTURE.md trim + D-027/D-028) and `dfcacd6` (the
maker folding in the full-suite result and correcting a provenance error in the manifest prose).

## What I re-ran / re-derived myself (not trusted from the manifest)

1. **Line count.** `wc -l docs/ARCHITECTURE.md` = 144. `ARCHITECTURE_MAX_LINES` in
   `src/autotester/ledger/render.py:20` = 150. 6 lines of real headroom, matching the manifest.
2. **The deletion itself.** `git show d7298b5 -- docs/ARCHITECTURE.md`: exactly 6 lines removed
   (blank separator + `## Status` heading + `**Built:**` line + two-line `**Next:**` paragraph),
   nothing else touched in that file. `git show d7298b5 --stat` confirms the commit's only other
   content changes are `docs/DECISIONS.md` (+68, the two new entries), `docs/SNAPSHOT.md`
   (regenerated tail), the unit's own evidence dir and manifest.
3. **Was the deleted claim actually false?** `.goal/goal.json` carries **20** `pending` tasks
   today (T-122, T-123, T-136, T-145, T-125, T-126, T-150–T-155, T-162–T-164, and others), not the
   "10+" the manifest/D-027 cite but unambiguously not zero. The deleted line's claim ("the P0–P5
   goal backlog is closed") was false. Confirmed independently, not taken on the manifest's word.
4. **Was anything actually load-bearing lost?** Cross-checked every fact in the deleted `Built`/
   `Next` prose against `docs/SNAPSHOT.md`, `docs/MAP.md`, `docs/FEATURES.jsonl`, and the surviving
   Concept→file table:
   - Most of the `Built:` line's components (schema, provider seam, doctor, CLI, browser/,
     store/, Pathlynks onboarding, the stages/, ui/) are still named in the surviving Concept→file
     table, which I independently re-verified: extracted all 39 backtick file-path references in
     that table and confirmed every one resolves on disk — **0 missing**, matching the manifest's
     own claim.
   - **One concrete loss found:** the deleted line cited `scripts/bench_trial.py` by name as
     evidence of "a real bench trial." That path does not appear anywhere in the surviving
     `docs/ARCHITECTURE.md`, `docs/MAP.md` (its generated Directory map covers `src/autotester/`
     modules only — zero `scripts/` rows, a pre-existing, unrelated gap, not something this unit
     introduced), `docs/SNAPSHOT.md`, or `docs/FEATURES.jsonl`. The underlying *feature* (bench
     scorecard, its human-oracle-baseline honesty caveat) is still discoverable via F-017 and the
     surviving `stages/bench.py::scorecard` row, so this is a narrow loss — one script's file path,
     not the feature or its limitation — but it does concretely falsify the manifest's own
     capability-coverage row 3 claim of "no information was actually lost." Filed as **AT-520**
     (low, documentation).
   - The two "Next: … open for later" items (a Pathlynks demo video for `ingest.py`'s golden test;
     a live timed human trial) are **not** newly lost: both gaps are already independently
     documented as follow-on notes in `docs/FEATURES.jsonl` (F-008's reason: "No Pathlynks demo
     video exists in this repo yet … the recall bar is a follow-on task"; F-017's reason: "No live
     human tester was available this session"), predating this unit. Not a finding.
5. **A second, uncaught miscount.** D-027 (and the manifest's own "Measure before deciding" §3)
   state the Concept→file table has **34 rows**. I counted it directly: 32 pipe-delimited lines in
   that table minus the header row and the `|---|---|` separator = **30 data rows**, not 34. D-028
   already exists to correct one arithmetic slip in this same entry (145 vs 144 total lines) but
   does not cover this second one. Zero live consequence — the conclusion the count supports (no
   literal duplication with `docs/MAP.md`'s 117-row module map) holds at the correct count either
   way — but it is exactly the kind of unverified number the dispatch asked not to take on trust.
   Filed as **AT-519** (low, documentation).
6. **Lab Protocol compliance.** `docs/DECISIONS.md` D-027 and D-028 exist, both `type: fix`,
   `status: ACTIVE`. `.claude/hooks/decisions-append-guard.ps1` is wired into `PreToolUse` in
   `.claude/settings.json` and hard-denies any direct Edit/Write to `docs/DECISIONS.md` — the only
   legitimate write path is `scripts/append_decision.ps1`, which the manifest's process narrative
   is consistent with and which the hook makes bypass technically implausible (this checker cannot
   independently prove intra-commit ordering from git history alone, since both entries landed in
   the same commit as the prose edit, but the mechanism forecloses a direct edit having produced
   them). D-027's `**Changes-authorized:**` names exactly `docs/ARCHITECTURE.md` (the `## Status`
   section), `docs/MAP.md` and `docs/SNAPSHOT.md` (regenerated), and the manifest — matching the
   diff exactly. Neither entry's `Changes-authorized` touches an enforcement path
   (`.claude/hooks/*`, `append_decision.ps1`, `.claude/settings.json`), so no `Approved-by` was
   required, and none is present — correct per `append_decision.ps1`'s own V7 rule. D-028 is a
   genuine append (new `## D-028` header) and does not edit D-027's text.
7. **Doc still does its job.** `uv run autotester doctor` → `doctor: clean`. `uv run ruff check
   src tests scripts` → `All checks passed!`. `uv run pytest -q -o addopts= tests/test_ledger.py
   tests/test_doctor.py` → `34 passed`. Read `check_docs_routed` (`doctor.py:170-190`) directly:
   it checks header presence + router listing, not completeness of any one doc's prose, so it has
   no opinion on the AT-520/AT-519 findings above.
8. **Full-suite provenance table.** The manifest's corrected three-run table exactly matches
   independently checkable evidence: `.work/at507_full_suite.log` is present on disk and its tail
   (`1484 passed, 2 skipped, 32 xfailed, 1 warning in 870.11s (0:14:30)`, `EXIT:0`) plus a
   whole-file `grep -c "FAILED\|ERROR"` = 0 matches the manifest's "this unit's run" row exactly.
   `qa/verdicts/at513-the-block-tests-leave-the-row-tests.md` independently records `1 failed,
   1483 passed, 2 skipped, 32 xfailed … in 1078.94s`, the failure being
   `test_run_once_kills_a_real_hung_process_and_its_real_grandchild`, re-ran alone → `2 passed` —
   matching the manifest's "at513 checker's full suite" row exactly. The "coordinator's full
   suite, ~1h earlier" row has no surviving log file to re-derive independently, but it is not
   load-bearing (this unit touches no `src/`/`tests/` file, so the full-suite result is
   belt-and-suspenders per the manifest's own framing) and is not contradicted by anything found.
   `dfcacd6`'s diff is confirmed to touch only the manifest file (`git show dfcacd6 --stat`: 1 file
   changed), consistent with it being a pure fold-in/correction commit, not a scope violation.
9. **Diff scope (4c).** `git diff <base>..d7298b5 --stat` (already captured above) touches only
   `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/SNAPSHOT.md`, the unit's own evidence dir and
   manifest — nothing outside "What changed," no function/class/test/config-key deleted.

## Capability coverage

Re-verified independently: line-count claim (item 1), no-other-section-touched claim (item 2),
39/39 path-existence claim (item 4), doctor/ruff/targeted-tests claims (item 7), append-only
DECISIONS claim (item 6). All hold. The one capability-coverage row that does **not** fully hold
as stated is row 3 ("No information was actually lost") — see AT-520 above; the loss found is real
but narrow (one script path, not a feature or its documented limitation) and does not overturn the
row's substance.

## Live browser evidence

Not applicable — no `src/` file, no UI surface, no browser-reachable path changed. Changed paths:
`docs/ARCHITECTURE.md`, `docs/SNAPSHOT.md` (regenerated), `docs/DECISIONS.md` (D-027, D-028),
`qa/evidence/at507-architecture-doc-regains-its-headroom/*`, this manifest. Confirmed via `git
diff` scope in item 9.

## Issues addressed

The manifest names no `qa/issues.jsonl` row as fixed (its own convention — "not a filed
qa/issues.jsonl row"). Nothing to check off.

---

VERDICT: PASS
SCOREBOARD: 5/5 criteria met (C2 budget + concept-table accuracy, C10 commit-path scoping,
Lab Protocol append-only compliance, doc still routed/clean, full-suite provenance table accurate),
all invariants hold
FAILURES (if any): none — see EXPLANATION for two low-severity findings recorded to the ledger
rather than charged against the unit
CAPABILITY-COVERAGE: 6/7 rows fully reproduced as stated; 1/7 (row 3, "no information lost")
holds in substance but not in absolute terms — narrowed by AT-520, not falsified
LIVE-BROWSER: not-applicable (no src/ or UI-reachable path changed; changed paths listed above)
ISSUES-WRITTEN: AT-519 (low, documentation — D-027 cites 34 rows, actual is 30), AT-520 (low,
documentation — scripts/bench_trial.py's path is undiscoverable in any routed doc after the trim)
EXPLANATION: The trim is real, correctly measured, and legitimately recovers headroom without
gaming the line-count proxy or raising the budget past what was justified; the deleted claim was
genuinely false (20 pending goal tasks today, not zero); D-027/D-028 are genuine, correctly-scoped,
append-only entries with no enforcement-path overreach; doctor/ruff/targeted tests are clean; and
the corrected three-run full-suite provenance table checks out exactly against the surviving log
file and the at513 verdict. Two low-severity findings temper but do not overturn the "nothing was
lost" argument: one script's file path (scripts/bench_trial.py) is now undiscoverable via any
routed doc, and the manifest's own row-count claim for the surviving Concept→file table (34) is
off by 4 (actual 30) — a second miscount in the same DECISIONS entry that D-028 already had to
correct once for a different number. Neither affects the substance of the decision or any core
contract criterion (C2 governs the table's accuracy, not its exhaustiveness), so both are recorded
to the ledger rather than failing an otherwise well-measured, correctly-authorized unit.
