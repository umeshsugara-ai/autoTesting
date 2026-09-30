# Verdict - at710-decision-citation-resolver

**Date:** 2026-09-30
**Cycle checked:** 2
**Bound to:** D:/autoTesting/.worktrees/at710-citations (branch wave/at710-citations, HEAD 63624313; master merged in at 16df87a6)
**Contract:** qa/contracts/living-ledger.md L9 AS IT NOW READS after D-060 (commit 38930b1f) + CLAUDE.md doctor design rules
**Checker:** claude-sonnet-subagent (manifest names no Executor; self != executor)

VERDICT: PASS

SCOREBOARD: 1/1 criteria met (L9: every sub-clause and all three Verify fixtures evidenced), 1/1 invariants hold (doctor design rules)

FAILURES: none against L9. One close-out condition for the maker, not a criterion failure: see "Doctor state" below (regenerate `docs/SNAPSHOT.md` after merge).

CAPABILITY-COVERAGE: 5/5 re-run rows reproduced (rows 1, 3, 5, 6, 9 of the manifest's 9; rows 2, 4, 7, 8 reproduced in cycle 1 on identical code and are carried, not re-run)
LIVE-BROWSER: not-applicable (src/autotester/ledger/citations.py, src/autotester/doctor.py, tests/test_citations.py; no UI surface)
ISSUES-WRITTEN: none (ISS-at710-1 moved open -> wontfix, moot: obligation now L10)
EXECUTOR: not stated in manifest (checker: claude-sonnet-subagent)

EXPLANATION: Cycle 1 failed on exactly one thing, the wrong-subject bullet. D-060 moved that bullet verbatim into L10 (status "not yet buildable", own unit), and L9 now carries only a one-line pointer, so the unit closes against L9's Verify clause, which the unchanged code already satisfied. I re-read L9 line by line: no residual subject-match, `**What:**`-comparison or "necessary and not sufficient" wording remains in L9 or its Verify. The unit's code is byte-identical to what I verified in cycle 1.

## Judged against L9 as it now reads

- **No residual subject-match clause.** `qa/contracts/living-ledger.md` L9 (lines 115-165): the bullets are failing-shape, cost, both-directions, why-nothing-caught-it, foreign id space, non-claiming declared, no whole-file exemption, Verify, and a single pointer line ("Subject match is not part of this criterion's Verify: ... L10, split out under D-060"). The former bullet appears only under L10 (lines 168-180), quoted verbatim, with its own Verify and "Status: not yet buildable". L10's obligation is preserved, weakened nowhere. The 2026-09-30 amendment-log entry names D-060 as its authority. This is a split, not a softening: no L9 sub-clause other than the moved bullet changed.
- **Verify clause, each item** (evidence unchanged from cycle 1, table below in the history): violation names file, line and id; resolves across DECISIONS.md and docs/archive/; header-matching never substring; foreign id space exempt at entry granularity in docs/DECISIONS.md only; non-claiming occurrences declared per occurrence with a reason; no whole-file exemption; fixtures (a), (b), (c) each built (fixture (c): precondition asserted at run time that the id is not in `appended_ids`, then 7 citations fire).
- **Code unchanged:** `git diff 24d6323b..HEAD --stat -- src/autotester/ledger/citations.py src/autotester/doctor.py tests/test_citations.py` is empty. `git diff b385910f..HEAD -- src tests` is NOT empty, but the only entries are two test files that arrived through the master merge (`tests/test_goal_contract_registration.py`, `tests/test_mc_sessionstart_unclosed.py`, from other units' merges), none in this unit's files and none under `src/`. Nothing this unit added or removed changed.

## What I re-ran (bound worktree, output redirected to .work/ files, no CLI -q, no piping)

| command | result |
|---|---|
| `uv run pytest tests/test_citations.py tests/test_doctor.py tests/test_ledger_checks.py` (first run, before I neutralised quoted ids in the cycle-1 verdict) | 79 passed, 1 failed: `test_the_real_tree_has_no_dangling_citation`, caused by MY cycle-1 verdict, not by the code (next section) |
| same three files, after neutralising | 80 passed in 64.53s (EXIT 0), including `test_the_real_tree_has_no_dangling_citation` |
| `uv run ruff check src tests scripts` | All checks passed (EXIT 0) |
| `uv run autotester doctor` | first run 5 violations (stale SNAPSHOT + 4 from my cycle-1 verdict); after the verdict fix, 1 violation (stale SNAPSHOT), zero `decision-citation-dangling` |
| full `uv run pytest` | NOT RUN (RAM; another checker is on T-171). The maker runs it once after merge. Not evidence for this verdict either way. |

**A finding about the resolver in use, not a failure of L9 (needs the maker's awareness).** My own committed cycle-1 verdict tripped the new check: it is a `qa/verdicts/*.md` file, one of the five citation globs, and it quoted a foreign-log id twice, a synthetic test id once, and a truncated-id fragment once. So the doctor went red (4 violations) the moment the verdict was on the tree, and the real-tree test with it. That is L9 working as written (a verdict is a citing source and its quotations are undeclared), and the exemption design is per occurrence by intent, so I did not ask for a whole-file exemption. What I did: reworded those quoted ids in the cycle-1 history below to plain descriptions (meaning unchanged), and wrote this verdict with no unresolvable literal id. Consequence for future checkers and makers: a verdict or manifest that quotes a phantom, foreign or synthetic decision id verbatim turns `autotester doctor` red unless a `NON_CLAIMING` row is added in `citations.py` (a code change, so a maker unit). Describe such ids in words instead.

## Doctor state (maker close-out condition, not a criterion failure)

After the verdict fix, `uv run autotester doctor` reports exactly one violation: `stale-generated: docs/SNAPSHOT.md differs from regeneration`. It is merge-induced: `docs/DECISIONS.md` gained 75 lines from master (the D-059 and D-060 entries) since this branch regenerated SNAPSHOT in cycle 1, and SNAPSHOT's "Last decisions" section still ends at D-058. No file this unit changed causes it, and the cycle-1 verdict already said to regenerate after merge rather than hand-merge. I did not regenerate it (a generated artifact, not mine to edit). Close-out: after merging to master run `uv run autotester snapshot` (and `map` if it reports drift), then `uv run autotester doctor` must print `doctor: clean`; the merge is not finished until it does. This is the one place I could be wrong to call it a non-failure: if the maker reads "doctor clean" in the manifest as a standing claim for this branch tree, it no longer reproduces here until the regeneration.

## Capability coverage (step 4b): 5 of 9 re-run this cycle, all reproduced

Per the dispatch ("at least 3"), I re-ran five, each in its own throwaway copy under the scratchpad (outside the worktree): `src/`, `docs/`, `pyproject.toml`, `tests/test_citations.py` and the four qa globs, with `PYTHONPATH=<copy>/src`, `AUTOTESTER_ROOT=<copy>`, `--noconftest`. The import path was confirmed to be the copy for every row (`autotester.ledger.citations.__file__` printed the copy path). The named check ran green IN the copy before the edit (11 passed) for every row.

| # | edit (single hunk, single file named in "What changed") | before (copy) | after | check that fired |
|---|---|---|---|---|
| 1 | `if cid in appended or` -> `if True or` in citations.py | 11 passed | 6 failed | dangling-id, header-vs-substring, word-bounded pattern, foreign-entry, non-claiming per-occurrence, seven-fire (assertion-level, not import errors) |
| 3 | header regex `^##\s+(D-\d+)\b` -> `(D-\d+)\b` in citations.py | 11 passed | 2 failed | `test_matching_is_by_header_not_by_substring`, `test_a_foreign_id_is_exempt_across_its_whole_entry_only` |
| 5 | `or (line_no, cid) in foreign or` -> `or False or` in citations.py | 11 passed | 2 failed | `test_a_foreign_id_is_exempt_across_its_whole_entry_only`, `test_the_real_tree_has_no_dangling_citation` |
| 6 | `or _declared(rel, line, cid)` -> `or False` in citations.py | 11 passed | 2 failed | `test_a_non_claiming_row_is_per_occurrence_never_per_file`, `test_the_real_tree_has_no_dangling_citation` |
| 9 | drop `check_decision_citations` from the `run()` tuple in doctor.py | 11 passed | 1 failed | `test_doctor_run_includes_the_citation_check` (wiring, not just the function) |

Row 1 note: with the whole check disabled, the real-tree test still passes (an empty result is what it asserts), so row 1 is isolated by the six synthetic-tree tests, not by the real-tree one. Traps checked: no row reddens on import or parse; no row asserts a state the bug also produces.

## Ledger

ISS-at710-1 (`qa/issues.jsonl`) moved `open -> wontfix` with a `resolution` note: the obligation was moved to L10 by D-060 (not yet buildable, own unit) and is preserved there. It is moot for this unit, not fixed by it, so it is not `fixed` or `verified`.

## Diff scope (step 4c)

Unchanged from cycle 1 for this unit's files (above): `citations.py` (new), `tests/test_citations.py` (new), three lines of `doctor.py`, and generated docs; nothing deleted or renamed by this unit. The merge brought in master's own changes, which are not this unit's diff.

## Non-blocking observations (questions, not failures)

- The cycle-1 observation stands: the manifest still carries a stale upper half (HUMAN_GATE status, 7 dangling citations, 131-line scratch module). `NON_CLAIMING` row 3 is keyed to a phrase on that stale half, so rewording it turns the doctor red; if the maker retires the stale half, re-key that row in the same change.
- `check_decision_citations` returns `[]` when `appended_ids` is empty (an unreadable or header-less authority file passes silently on the real tree). Guarded today only by the real-tree test's assertion that four known ids are appended. Candidate follow-up, not a defect against L9's text.

---

## CYCLE 1 (history, kept verbatim except quoted ids neutralised - see note in cycle 2)

**Date:** 2026-09-30
**Cycle checked:** 1
**Bound to:** D:/autoTesting/.worktrees/at710-citations (branch wave/at710-citations, commit 24d6323b; base 9daa5a02)
**Contract:** qa/contracts/living-ledger.md L9 (incl. the 2026-09-28 "resolution is necessary and not sufficient" bullet and the 2026-09-29 fixture-(c) tightening) + CLAUDE.md doctor design rules
**Checker:** claude-sonnet-subagent (manifest names no Executor; self != executor)

VERDICT: FAIL

SCOREBOARD: 0/1 criteria met (L9: 8 of 9 sub-clauses evidenced, 1 not implemented), 1/1 invariants hold (doctor design rules)

FAILURES:
- [L9 wrong-subject bullet] sev: high - a resolving id is treated as clean on its own; no claim-vs-`**What:**` comparison exists - either (a) maker files the request in qa/feedback-inbox.md proposing a DECLARABLE shape (for example a `cites-for: D-NNN - <subject>` marker) and /checker folds it into L9, then the maker builds it, or (b) checker splits the bullet into its own criterion so this unit closes against the Verify clause only. This is a contract-shape decision for the checker seat, not something the maker can settle by building - issue: ISS-at710-1

CAPABILITY-COVERAGE: 9/9 rows reproduced
LIVE-BROWSER: not-applicable (src/autotester/ledger/citations.py, src/autotester/doctor.py, tests/test_citations.py, generated docs; no UI surface)
ISSUES-WRITTEN: ISS-at710-1
EXECUTOR: not stated in manifest (checker: claude-sonnet-subagent)

EXPLANATION: The resolver is sound where it is implemented: every Verify-clause behaviour is evidenced, the real tree is clean for the right reason, and all nine falsifying edits reproduce red on the named check. It fails only because L9's own text says the check "may not treat a resolving id as clean on its own", and the unit builds exactly that check (resolution by `## D-NNN` header, nothing more). The manifest discloses the gap honestly, which is why this is one narrow failure rather than a broad one.

## What I re-ran (all in the bound worktree, output redirected to files, no CLI -q)

| command | result |
|---|---|
| `uv run pytest tests/test_citations.py` | 11 passed (EXIT 0) |
| `uv run pytest tests/test_doctor.py tests/test_ledger_checks.py` | 69 passed (EXIT 0) |
| `uv run ruff check src tests scripts` | All checks passed (EXIT 0) |
| `uv run autotester doctor` | `doctor: clean` (EXIT 0) |
| full `uv run pytest` | **NOT RUN - deferred evidence gap** (RAM ~0.6 GB free, per dispatch). One full suite runs after merge. The manifest's 2170-passed figure belongs to an earlier cycle on a different tree and is not evidence for this one. |

## L9 criterion by criterion

| L9 clause | evidence | met |
|---|---|---|
| Violation names file, line and unresolved id | `test_a_dangling_id_fires_naming_file_line_and_id` -> `qa/gates/g.md:2`, id in detail | yes |
| Resolves across DECISIONS.md AND docs/archive/ (archiving is not deletion) | `test_an_archived_entry_resolves`; row 4 falsification | yes |
| Header-matching, never substring | `test_matching_is_by_header_not_by_substring`; row 3 falsification | yes |
| Foreign id space out of scope at ENTRY granularity, not reported, not a whole-file exemption | `test_a_foreign_id_is_exempt_across_its_whole_entry_only` (the foreign-log id in prose on one line, qualified by a log path on another; a later unqualified entry still fires); scoped to `docs/DECISIONS.md` only (`_scan`, `rel == "docs/DECISIONS.md"`) | yes |
| Non-claiming occurrence declared with a reason, per occurrence, never per file | `NON_CLAIMING` keys are (file, line text, id) -> reason; `test_a_non_claiming_row_is_per_occurrence_never_per_file` | yes |
| No whole-file exemption anywhere, DECISIONS.md least of all | no per-file exemption in the module; DECISIONS.md :623/:638 are handled by the entry rule, not the allow-list | yes |
| Fixture (a): "D-056 did not exist" sentence must not fire | declared `NON_CLAIMING` rows for living-ledger.md :137/:229 and the manifest :129 each match exactly one real line (my probe printed hits [137], [229], [129]) | yes |
| Fixture (b): cross-log citation qualified only elsewhere in its entry must not fire | same test as the foreign-id row; on the real tree DECISIONS.md:623 and :638 do not fire | yes |
| Fixture (c) as amended 2026-09-29: seven citations fire while the entry is unwritten, precondition asserted at run time, not tied to a real id | `test_seven_citations_of_an_unwritten_entry_all_fire` asserts `"a synthetic id" not in appended_ids` then 7 fire. Only the "absent" branch of the fixture's precondition is built; the "present with a non-matching What:" branch is not. | partial (see below) |
| "Resolution is necessary and not sufficient": a citation stating what an entry authorizes is compared against the entry's `**What:**`, mismatch is a violation | **not implemented** - `check_decision_citations` never reads a `**What:**` field. The maker discloses this ("Known gap, disclosed not claimed"). | **no** |

Why this fails rather than passes with a disclosed gap: the bullet was written because the exact defect it names happened twice (D-056 then D-057 each resolved while being wrong), and L9 says in terms that the check "may not" go green on resolution alone. PASS requires every criterion evidenced; a disclosed hole in a criterion is still a hole. Confidence above 80%.

Why it is one narrow failure: the maker's reason for not building it is real - L9 also says exemptions and claims are "declared, not inferred", and free-text authorization claims have no machine shape in this tree. So the missing piece is a shape decision (contract side), and the fix direction says so. Nothing else in this unit needs to change for the bullet to be the only open item.

## Current-tree finding (re-derived independently, not from the manifest)

I ran the module over the worktree with `NON_CLAIMING` emptied (raw resolver): exactly 3 hits, all `the foreign-log id` quotations (living-ledger.md:137 and :229, manifest :129). I also wrote a second, independent scan (own regex, own header parse, the five globs, 1671 occurrences): the only unresolved ids are `the foreign-log id` (7 occurrences: those three lines plus DECISIONS.md:623/:638, foreign log) and a truncated-id artefact of my looser regex (placeholder text with letters after the digit, in at638-done-check-repair.md:101 and at283-agents-md-root-clutter.md:77), which the module's `\b` correctly does not match. 59 headers resolve (D-056, D-057, D-058 present). **True dangling citations in the tree: 0. `autotester doctor` reports none, so this is not a resolver bug and there is no finding to file against the tree.** The write-policy gates were repointed off D-057 in 9daa5a02, so the seven-citation shape no longer exists live; the real-tree test therefore proves "clean" and fixture (c) proves "would fire", which is the right split.

## Capability coverage (step 4b) - 9/9 reproduced

Each row in its own throwaway copy under the scratchpad (outside the worktree), `PYTHONPATH=<copy>/src`, `AUTOTESTER_ROOT=<copy>`, `--noconftest` (the repo conftest needs `tests_mutation_fixtures`; test_citations.py uses only tmp_path and monkeypatch). Import path confirmed to be the copy (`autotester.ledger.citations.__file__`). Green before the edit in the copy for every row (11 passed). Every edit is single-hunk, single file, and in a file named in "What changed".

| # | edit | before (copy) | after | named check fired |
|---|---|---|---|---|
| 1 | `if cid in appended or` -> `if True or` | 11 passed | 6 failed | yes: dangling, header, boundary, foreign, per-file, seven-fire |
| 2 | `r"\bD-\d+\b"` -> `r"D-\d+"` | 11 passed | 2 failed | yes: `test_the_citation_pattern_is_word_bounded` (+ real tree) |
| 3 | `r"^##\s+(D-\d+)\b"` -> `r"(D-\d+)\b"` | 11 passed | 2 failed | yes: `test_matching_is_by_header_not_by_substring` (+ foreign-entry test) |
| 4 | `glob("*.md")` -> `glob("*.nomatch")` | 11 passed | 1 failed | yes: `test_an_archived_entry_resolves` |
| 5 | `or (line_no, cid) in foreign or` -> `or False or` | 11 passed | 2 failed | yes: `test_a_foreign_id_is_exempt_across_its_whole_entry_only` (+ real tree) |
| 6 | `or _declared(rel, line, cid)` -> `or False` | 11 passed | 2 failed | yes: `test_a_non_claiming_row_is_per_occurrence_never_per_file` (+ real tree) |
| 7 | `and snippet in line for` -> `and True for` | 11 passed | 1 failed | yes: same per-occurrence test |
| 8 | `"docs/*.md")` -> `"docs/*.md", "qa/*.md")` | 11 passed | 1 failed | yes: `test_only_the_five_named_globs_are_citation_sources` |
| 9 | drop `check_decision_citations` from the `run()` tuple in doctor.py | 11 passed | 1 failed | yes: `test_doctor_run_includes_the_citation_check` |

One small discrepancy with the manifest: row 8 shows 2 failures there and 1 in my copy, because my copy omitted top-level `qa/*.md` files. The named check fired either way; not a finding. Traps checked: no row reddens on import/parse; the row-1 edit reddens only assertion-level checks; the wiring test (row 9) monkeypatches the function and asserts the marker appears in `doctor.run`, so it proves wiring, not just the function.

## Diff scope (step 4c) - `git diff 9daa5a02...HEAD`

Files: `docs/MAP.md` (+1), `docs/SNAPSHOT.md` (+2/-2), `qa/manifests/at710-decision-citation-resolver.md`, `src/autotester/doctor.py` (+2/-1), `src/autotester/ledger/citations.py` (NEW, 101 lines), `tests/test_citations.py` (NEW). All listed in "What changed".
- Removed lines: doctor.py one line (the tuple's last line, rewrapped to add the name - no function or export removed); SNAPSHOT.md two generated "Last decisions" lines (D-053 rolled off, D-057 status changed to SUPERSEDED by D-058) - regenerated content, not authored.
- New modules: exactly `ledger/citations.py` and `tests/test_citations.py` - matches D-058 point 1. `tests/test_doctor.py` untouched (still 300 lines). doctor.py 280/300.
- Duplicate definitions: `check_decision_citations`, `appended_ids`, `foreign_ids_by_line` are defined once, in `citations.py` (grep over src and scripts).
- Design rules: citations.py 101 lines, every function well under 50, module docstring states one job, `Violation` imported from `autotester.doctor` with doctor importing citations lazily inside `run()` (no import cycle; same pattern as `checks.py`). No `*_v2` / `*_new`.

## Non-blocking observations (questions, not failures)

- **Silent green if the authority file is unreadable.** `check_decision_citations` returns `[]` when `appended_ids` is empty. Correct for tmp trees; on the real tree a header-format change would disable the check quietly. It is guarded today only by `test_the_real_tree_has_no_dangling_citation` asserting D-055..D-058 are appended. Consider whether an existing but header-less `docs/DECISIONS.md` should itself be a violation.
- **The manifest carries two contradictory Status lines.** The upper block (line 15) still says "HUMAN_GATE ... not ready-for-check" and its measured section still lists 7 dangling citations and a 131-line scratch module; only the last `## Status: ready-for-check` block describes this unit. The cycle-2 close-out should retire the stale half. `NON_CLAIMING` row 3 is keyed to a phrase on manifest line 129 (in that stale half): rewording that line un-declares the row and doctor goes red. That fails safe, but the maker should re-key it if the manifest is edited.
- **Merge friction:** master has an uncommitted `docs/SNAPSHOT.md` change (git status at session start); this branch also regenerated it. Regenerate after merge rather than resolving by hand.
- The manifest says the wrong-subject bullet needs a checker decision on a declarable shape. That decision is outside this bound seat (the contract lives on master and is checker-maintained); it is raised here as the fix direction of ISS-at710-1.
