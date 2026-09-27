# Manifest — t189-stale-evidence-tag

**Unit:** T-189 (at516-c) — a stale `mutations.json` evidence spec stays byte-intact and gets a
"stale on purpose, test moved to `<node>`" tag a CHECK can tell apart from neglect.
**Contract:** `qa/contracts/core-invariants.md` C7 (mutation-evidence rules) is the contract that
owns evidence specs; **no criterion in it currently states the at516 tagging rule** — D-048 names
"the at516 tagging rule, in the contract that owns evidence specs" as authorized-but-not-yet-written.
Per the maker/checker split, `qa/contracts/` is checker-owned and I have not edited it. See "Gaps
stated, not hidden" below — I judge this does NOT need a `qa/feedback-inbox.md` entry, because
D-048(c) plus the mechanism below fully answers the design question; the remaining step (folding
the rule into C7's prose) is squarely the checker's to do, the same way x18a-login-both-directions
left its own proposed contract wording for the checker to adopt.
**Authority:** `qa/gates/at516-evidence-spec-splitting-policy.md`, answered (c), recorded in
**D-048** (`docs/DECISIONS.md`): *"A stale evidence spec stays byte-intact and gets a 'stale on
purpose' tag."*
**Executor:** build subagent, isolated worktree `D:/autoTesting/.claude/worktrees/agent-aac03d021e1145e8d`,
branch `wave/t189-stale-evidence-tag` from master `3e232fea` (rebased once — see "Base branch"
below).
**Goal task:** T-189, `.goal/goal.json` — "at516-c: stale evidence spec stays byte-intact and gets
a 'stale on purpose, test moved to `<node>`' tag a check can tell apart".
**Date:** 2026-09-27
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-516 (medium, open -> fixed)

## The tension and the mechanism

D-048(c) requires two things that cannot both live in one place: (1) **byte-intact** — the stale
`mutations.json` file's existing bytes never change, proven below by hash, not by "I didn't mean
to touch it"; (2) **a tag a check can tell apart** from an unexplained (neglected) staleness. Since
the tag cannot live inside the byte-intact file, it lives in a **sidecar**:
`qa/evidence/<slug>/mutations.stale.json`, one JSON document per stale spec, validated by a new
Pydantic model.

- `src/autotester/schema/evidence_tombstone.py` (52 lines, new) — `EvidenceTombstoneEntry`
  (`old_nodeid`, `moved_to`, `moved_by_unit`, `note`, `extra="forbid"`) and `EvidenceTombstone`
  (`entries: list[...]`). Both `old_nodeid` and `moved_to` are validated `file::function` — a bare
  name is rejected, because a bare `moved_to` would reopen exactly the "which file?" ambiguity the
  tombstone exists to remove.
- `src/autotester/ledger/evidence_specs.py` (156 lines, new) — `check_stale_evidence_specs(root)`:
  for every `qa/evidence/<unit>/mutations.json` (skipping `browser-*` checker-evidence dirs, whose
  artifact shape is a sabotage-row list, not a mutation spec), for every `kills` node-id that does
  **not** resolve against the spec's own declared `tests` scope, look up a tombstone entry keyed by
  that node-id. **The check does not trust the tombstone's presence — it resolves `moved_to` the
  same way it resolved the original id.** A tombstone whose `moved_to` does not resolve either is
  flagged with a *different* message ("tagged moved to X but that does not resolve either") than
  the no-tombstone case ("no mutations.stale.json entry tags this as deliberate") — this is the
  distinguishing mechanism the dispatch asked for: **deliberate-and-honest** passes,
  **deliberate-but-lying** and **neglected** both fail, distinguishably.
- Wired into `uv run autotester doctor` (`src/autotester/doctor.py`, 279 lines after the addition,
  under the 300-line cap) alongside the other 12 checks.

## Byte-intactness proof

**Method:** `git rev-parse HEAD:<path>` (the committed blob SHA) vs `git hash-object <path>` (the
current working-tree content re-hashed through git's own clean filters) — these two are directly
comparable and immune to `core.autocrlf`. This project's `core.autocrlf` is `true`, which means a
naive `sha256sum` of the on-disk file will **never** equal a naive `sha256sum` of `git show
HEAD:<path>`'s output, even for a byte-identical, completely untouched file, because Windows
materializes CRLF on checkout while git's blob storage and `git show`/`cat-file -p` always emit LF.
Demonstrated on one of the seven files below, so a checker re-deriving this the naive way is not
misled by an apparent mismatch:

```
$ git config core.autocrlf
true
$ sha256sum qa/evidence/at469-mutation-ids-with-spaces/mutations.json
7b8245e77ed87144762ee02eb5ae441808295135828dbd0c3a38d1ccc6fab981 *qa/evidence/at469-mutation-ids-with-spaces/mutations.json
$ git show HEAD:qa/evidence/at469-mutation-ids-with-spaces/mutations.json > /tmp/at469_head_blob.json
$ sha256sum /tmp/at469_head_blob.json
b50d46952ee6146adcfd6039cd19752f3ace7b79ff22580c5a280e677889361c */tmp/at469_head_blob.json
```
These differ (CRLF vs LF) despite the file being byte-for-byte what HEAD already had — a false
alarm if used as the proof method. The `rev-parse`/`hash-object` pair below is the correct one:

| evidence spec | `git rev-parse HEAD:<path>` | `git hash-object <path>` | match |
|---|---|---|---|
| at469-mutation-ids-with-spaces/mutations.json | `3b625ef7c5eff757a94243bf89efcd6c45c7a939` | `3b625ef7c5eff757a94243bf89efcd6c45c7a939` | yes |
| at496-the-ledger-never-loses-a-row/mutations.json | `348580dfce35b50921547d4e0c1df9236c911468` | `348580dfce35b50921547d4e0c1df9236c911468` | yes |
| at500-a-letter-suffixed-id-is-an-id/mutations.json | `9cf4e245e015b704d2745b1b9e4e96ec20235ed3` | `9cf4e245e015b704d2745b1b9e4e96ec20235ed3` | yes |
| at504-prose-about-the-marker-is-not-a-claim/mutations.json | `64146bf185530408318e485851f825ba8672e79b` | `64146bf185530408318e485851f825ba8672e79b` | yes |
| at506-record-rules-leave-the-source-rules/mutations.json | `350b4ed96fa0d5cde0c6ad4f8874eaf01b70cd3c` | `350b4ed96fa0d5cde0c6ad4f8874eaf01b70cd3c` | yes |
| at509-the-claim-block-is-a-block-not-a-line/mutations.json | `e827d393eeeb93642f47cea1adf939df3231dbe9` | `e827d393eeeb93642f47cea1adf939df3231dbe9` | yes |
| at511-a-field-label-may-carry-a-parenthetical/mutations.json | `fae875aec343ede841b8e42df110262120a09b0f` | `fae875aec343ede841b8e42df110262120a09b0f` | yes |

All seven `mutations.json` files this unit tags are, right now, byte-identical to what HEAD already
carried before this unit touched anything — I never opened them for writing, only for reading
(`_load_spec`) and existence checks.

## What changed

- `src/autotester/schema/evidence_tombstone.py` (new, 52 lines) — the tombstone shape.
- `src/autotester/ledger/evidence_specs.py` (new, 156 lines) — `check_stale_evidence_specs`,
  `_resolves`, `_scope_files`, `_bare`, `_defines`, `_tombstone_key`, `_load_spec`, `_load_tombstone`.
- `src/autotester/doctor.py` — one import + one entry in `run()`'s check tuple.
- `docs/MAP.md` — regenerated (`uv run autotester map`) to list the two new src files; a legitimate,
  non-destructive maintenance run, not scope creep (`check_generated_fresh` requires it).
- Seven new sidecar files, `qa/evidence/<slug>/mutations.stale.json` — the retroactive tagging of
  every evidence spec in the repo that this unit's own check found genuinely stale (audited all 35
  directories under `qa/evidence/` that carry a `mutations.json`; see next section).
- `qa/evidence/t189-stale-evidence-tag/mutations.json` (new) — this unit's own C7 mutation-kill
  proof, 3 mutations against the two new modules.
- `tests/test_evidence_spec_tombstones.py` (new, 175 lines, 14 tests).

## Retroactive audit (why seven, and which test each one names)

`check_stale_evidence_specs` does not just exist for future staleness — run cold against the real
repo it immediately flagged 27 already-stale `kills` entries (spread across 7 spec files) that
`autotester doctor` had never been able to see before this unit. I resolved every one of the seven
by hand-verifying, via direct `grep`, where the named test actually lives today, before writing its
tombstone entry — not by trusting a guess:

```
$ grep -n "def test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id" tests/test_mutation_check.py
177:def test_a_mutation_is_attributed_to_a_parametrized_test_with_spaces_in_its_id(
$ grep -n "def test_a_field_label_carrying_a_parenthetical_still_ends_the_block|def test_an_issue_id_with_a_parenthetical_is_not_a_field_label" tests/test_marker_blocks.py
118:def test_a_field_label_carrying_a_parenthetical_still_ends_the_block(tmp_path: Path) -> None:
132:def test_an_issue_id_with_a_parenthetical_is_not_a_field_label(tmp_path: Path) -> None:
```

Six of the seven tombstones attribute the move to `at506-record-rules-leave-the-source-rules` or
`at513-the-block-tests-leave-the-row-tests` (real prior units that split `test_doctor.py` ->
`test_ledger_checks.py` -> `test_marker_blocks.py`, visible in git history). **One, at469, has an
honestly-unknown `moved_by_unit`** — the rename (not a split) predates any unit slug I could find
that claims it — recorded as `"unknown -- renamed after AT-469 shipped; found stale by T-189's
audit (2026-09-27), no unit slug attributes the rename"` rather than guessed. This is flagged again
under Gaps.

## How to verify (commands + expected, each run separately per the dispatch)

- `uv run pytest` (no `-q`) → exit 0, only pre-existing failures
- `uv run pytest tests/ -k evidence` (T-189's `done_check`) → exit 0
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`

## Actual outputs (from maker's own run, all four separate)

```
$ uv run pytest
...
========================== short test summary info ===========================
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
3 failed, 2047 passed, 6 skipped, 14 xfailed, 15 warnings in 1256.24s (0:20:56)
```

```
$ uv run pytest tests/ -k evidence
.................................................                        [100%]
49 passed, 2021 deselected, 1 warning in 4.38s
```

```
$ uv run ruff check src tests scripts
All checks passed!
```

```
$ uv run autotester doctor
doctor: clean
```

**All three full-suite failures are pre-existing and already documented — none are new:**
- `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` = **AT-627**, open, low
  severity, load-sensitive (flagged in the dispatch in advance).
- `test_no_pending_task_has_a_done_check_that_cannot_fail` and
  `test_revised_goal_contract_is_registered` = the two failures **`ISS-at638-remainder-2`**
  (severity high, filed 2026-09-27) already names, pre-existing on master, unrelated to any file
  this unit touches (`.goal/goal.json` growth to 81 tasks / five Goodhartable `done_check`s —
  see Gaps below, since one of the five named tasks is **T-189 itself**).
  `ISS-at638-remainder-2`'s own cited baseline ("3 failed, 2033 passed, 6 skipped, 14 xfailed")
  plus this unit's 14 new tests reconciles exactly to this run's `2047 passed`.

## Capability-coverage table (new tests -> the specific capability each guards)

| capability | covering test | falsifying edit (this unit's own C7 mutation spec) | GREEN before / RED after |
|---|---|---|---|
| a tombstone's `moved_to` is RESOLVED, never trusted by presence (AT-218 — a lying tombstone must still fail) | `test_a_tombstone_whose_moved_to_does_not_resolve_is_still_flagged` | `evidence_specs.py`: `if entry is not None and _resolves(...)` → `if entry is not None:` | KILLED — pytest exit 1, attributed exactly to this test |
| a bare `kills` name resolves only against the spec's OWN declared `tests` scope, not the whole repo (the false-positive bug this build hit against real at311/at520/at523 specs) | `test_a_bare_kills_name_outside_the_specs_tests_scope_is_stale` | `evidence_specs.py`: `any(_defines(f, name) for f in scope)` → `any(_defines(f, name) for f in root.joinpath("tests").rglob("*.py"))` | KILLED — pytest exit 1, attributed exactly to this test |
| the tombstone schema refuses a bare (non `file::function`) `moved_to` | `test_the_tombstone_entry_refuses_a_bare_moved_to` | `evidence_tombstone.py`: validator body → `return value` (no-op) | KILLED — pytest exit 1, attributed exactly to this test |

Real pasted mutation-kill run (`uv run python scripts/mutation_check.py qa/evidence/t189-stale-evidence-tag/mutations.json`):

```
KILLED  AT-218: the tombstone check trusts an entry's mere PRESENCE instead of resolving its moved_to -- a lying tombstone would silently pass  (pytest exit 1)
    claims to kill : tests/test_evidence_spec_tombstones.py::test_a_tombstone_whose_moved_to_does_not_resolve_is_still_flagged
    actually failed: tests/test_evidence_spec_tombstones.py::test_a_tombstone_whose_moved_to_does_not_resolve_is_still_flagged
KILLED  a bare kills name resolves against the WHOLE tests tree instead of the spec's own declared tests scope  (pytest exit 1)
    claims to kill : tests/test_evidence_spec_tombstones.py::test_a_bare_kills_name_outside_the_specs_tests_scope_is_stale
    actually failed: tests/test_evidence_spec_tombstones.py::test_a_bare_kills_name_outside_the_specs_tests_scope_is_stale
KILLED  the tombstone entry's path-qualified validator becomes a no-op, so a bare moved_to is accepted  (pytest exit 1)
    claims to kill : tests/test_evidence_spec_tombstones.py::test_the_tombstone_entry_refuses_a_bare_moved_to
    actually failed: tests/test_evidence_spec_tombstones.py::test_the_tombstone_entry_refuses_a_bare_moved_to

3/3 mutations killed
```

`scripts/mutation_check.py` sandboxes every mutation in a temp dir OUTSIDE the repo (it copies only
`scripts/`, `tests/`, `src/`, `pyproject.toml`, `conftest.py` via its own pre-existing
`shutil.copytree`-based sandboxing — not `git archive`, since this is the project's existing
mutation harness, not something built fresh for this unit). I confirmed the bound worktree was
untouched by the run: `git status --porcelain` before and after the mutation-check invocation is
identical (no new modifications beyond the ones already listed under "What changed").

**Other new tests, not separately mutation-falsified** (regression coverage exercising the same
`check_stale_evidence_specs` / `_resolves` code path the three rows above already isolate
line-by-line): `test_a_spec_whose_kills_still_resolve_is_not_stale`,
`test_a_stale_path_qualified_id_with_no_tombstone_is_flagged`,
`test_a_tombstone_whose_moved_to_actually_resolves_is_accepted`,
`test_a_tombstone_covers_every_parametrize_id_of_the_moved_function`,
`test_a_bare_kills_name_resolves_against_the_specs_own_tests_scope`,
`test_browser_evidence_directories_are_never_treated_as_mutation_specs`,
`test_a_non_dict_mutations_json_is_never_crashed_on`,
`test_no_qa_evidence_directory_is_not_an_error`,
`test_the_tombstone_entry_forbids_an_unknown_key`,
`test_the_check_is_wired_into_autotester_doctor`,
`test_the_repos_own_evidence_specs_are_clean_or_honestly_tombstoned` (the real-repo anti-regression
test — this one is exactly what disclosed the 27 pre-existing stale entries in the first place, and
now that all seven specs are tagged, it passes green against the live tree, not a fixture).

## Live browser evidence: not UI-touching

This unit is a `doctor`/schema-level static check over `qa/evidence/*/mutations.json` files. It
changes no runtime code path, no crawl, no report, no UI surface. Changed paths: `src/autotester/
schema/evidence_tombstone.py`, `src/autotester/ledger/evidence_specs.py`, `src/autotester/
doctor.py`, `docs/MAP.md`, `tests/test_evidence_spec_tombstones.py`, seven `mutations.stale.json`
sidecars, one new `mutations.json`. No persona walk applies.

## Base branch (stale-worktree note)

My worktree's default branch base was ~10 commits behind true current master when I started. I
confirmed via `git diff --name-only <old-base> localcheck/master` that the divergent files
(`qa/.last-tick`, `qa/QUEUE.md`, several `qa/gates/*.md`, `qa/issues.jsonl`, `qa/verdicts/
at638-remainder.md`) do not overlap any file this unit touches, then created
`wave/t189-stale-evidence-tag` from the true current master and carried my uncommitted work forward.
The branch is one commit behind the very latest master (`4016f82a`, unrelated T-192 work) as of
this manifest — confirmed no file overlap.

## Gaps stated, not hidden

1. **The at516 tagging rule is not yet written into `qa/contracts/core-invariants.md` C7.** D-048
   authorizes it there; I did not write it myself because `qa/contracts/` is checker-owned. The
   checker should fold the mechanism above into C7's prose (or amend it) before this unit can be
   considered fully closed at the contract level — same pattern as x18a-login-both-directions'
   "Proposed wording" section.
2. **`at469`'s `moved_by_unit` is honestly `"unknown"`** — I could not find a unit slug that claims
   the rename in git history or `docs/FEATURES.jsonl`; recorded as such rather than guessed.
3. **T-189's own `done_check` (`uv run pytest tests/ -k evidence`) is independently documented as
   Goodhartable** — `ISS-at638-remainder-2` (filed by a checker session, 2026-09-27, pre-existing on
   master, not something I introduced) names T-189 by number among five pending tasks whose
   `-k <keyword>` `done_check` passes on a clean repo regardless of whether the task was ever
   started, because unrelated pre-existing tests already match the keyword. **This means the
   generic done_check is NOT the real evidence for this unit — the capability-coverage table above
   (14 new named tests + the 3-mutation kill proof, both pasted) is.** The checker should not accept
   `-k evidence` passing as sufficient; it should independently confirm the specific tests above
   exist, pass, and are killed by their named mutations. I have not fixed `ISS-at638-remainder-2`
   itself (it also names four other tasks and a stale test-count pin unrelated to T-189, and fixing
   the goal-schema issue is not this unit's contract) — flagging it here rather than silently
   letting a generic `-k evidence` PASS stand in for real verification.
4. **CRLF/`core.autocrlf` hashing confound** — documented above with a real pasted demonstration;
   a checker re-deriving byte-intactness with a naive `sha256sum`/`git show` comparison will see an
   apparent mismatch that is not a real content difference. Use `git rev-parse HEAD:<path>` vs
   `git hash-object <path>` instead.
5. **Scope boundary: one level deep under `qa/evidence/`, `browser-*` dirs excluded.** This mirrors
   the real shape of the repo's two evidence artifact kinds (maker mutation specs vs checker
   sabotage-row lists) but is itself an assumption `[ASSUMPTION]` about the boundary being stable —
   the checker should confirm no other evidence-directory naming convention exists that this check
   would either wrongly ingest or wrongly skip.

## What a checker should attack hardest

- Whether folding the D-048/at516 rule into C7 is required before PASS, or can be a follow-on.
- The lying-tombstone AT-218 proof (row 1 of the capability table) — the single most important
  guarantee in this unit; try a tombstone whose `moved_to` looks plausible but resolves to the
  wrong function name in the right file.
- The at469 unknown-attribution gap — is "unknown, found by T-189's audit" acceptable, or does
  policy require blocking until the original renaming unit is identified?
- The Goodhartable-done_check disclosure (#3 above) — confirm the checker verifies via the
  capability-coverage table and mutation proof, not the generic `-k evidence` gate.
- The CRLF hashing caveat — verify a checker session on the same Windows checkout reproduces the
  `rev-parse`/`hash-object` match, not a `sha256sum` mismatch mistaken for a real change.

**Status: checked-PASS (cycle 1)**

Verdict `qa/verdicts/t189-stale-evidence-tag.md`, **Cycle checked: 1**, verdict commit `7eb8a712`,
merged `52c7ff2c`, pushed to `origin/master`. `T-189` is `done`; `AT-516` moves open -> fixed with
`regression_check: uv run pytest tests/test_evidence_spec_tombstones.py`.

**The checker attacked the AT-218 lying-tombstone class directly rather than reading the claim**,
in a clean-room temp root outside the bound tree, importing the shipped
`check_stale_evidence_specs`. Two fixtures: a well-formed but nonexistent target is correctly
flagged with the exact "tagged moved to ... but that does not resolve either" message; a *real but
wrong* function (a decoy) is correctly **not** caught. That second result is the honest structural
limit of this unit — **resolution proves existence, not semantic correctness** — and the checker
folded it into the contract text so it is recorded rather than implied. It also re-ran the mutation
proof independently (3/3 killed, `git status --porcelain` identical before and after) and traced
`scripts/mutation_check.py::collected_tests()` to confirm the bare-name scope fix genuinely matches
the spec's own declared `tests` field.

**Byte-intactness re-derived, including the trap:** all 7 tagged specs MATCH on
`git rev-parse HEAD:<path>` vs `git hash-object <path>`, and the checker reproduced the
`core.autocrlf=true` CRLF trap itself (a naive `sha256sum` mismatches an untouched file) rather
than taking this manifest's caveat on trust.

**The retroactive audit went further than sampling.** All 24 tombstone entries were traced to the
commits that split the test files (`3546a28c` for at506, `9ed3833b` for at513) — every
`+def test_...` in those diffs matches an entry 1:1. The 24th (at469, honestly recorded as
`"unknown"`) was traced by hand and its "renamed" narrative is **imprecise**: the old and new names
were both created in the same commit `f7e83cdc`, and the old was later *deleted*, not renamed, by
an unrelated rewrite `07428a76`. No live regression is at risk — the old mutations targeted code
that no longer exists — so it is filed as `ISS-t189-stale-evidence-tag-1` (low), not a blocker.

**Contract fold-in was the checker's to do and it did it:** D-048 authorized folding the at516
tagging rule into C7 but deliberately left it unwritten, since `qa/contracts/` is checker-owned.
C7 now carries the resolution-not-presence discipline, the disclosed real-but-wrong-function limit,
and the bare-name scope fix, plus an amendment-log entry. Tightening only; no enforcement path
touched, so no `Approved-by` gate was needed.

**Concurrency, recorded because it touched shared state:** master advanced under the checker while
it worked, and it watched `.goal/goal.json`'s done count move 54 -> 55 on its own. It stashed the
live uncommitted `.goal/` work, merged (two conflicts, both correctly resolved — an append-only
ledger row and a timestamp), then found its stash conflicted against still-newer live writes and
**discarded its own redundant copy rather than forcing a resolution into another session's
in-flight state.** I verified that call: the current uncommitted `.goal/` diff is exactly the
progress recompute from T-189's own close (54 -> 55 done, 27 -> 26 pending), which is what
`goal_cli.py done` produces. Nothing was lost.

`ISS-at638-remainder-2` was correctly left untouched — it is queued as its own unit.

