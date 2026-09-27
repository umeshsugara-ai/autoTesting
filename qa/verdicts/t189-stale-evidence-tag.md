# Verdict — t189-stale-evidence-tag

**Unit:** T-189 (at516-c). **Cycle checked:** 1. **Date:** 2026-09-27.
**Checker:** fresh Claude Sonnet subagent, `D:/autoTesting/.claude/worktrees/agent-aac03d021e1145e8d`,
branch `wave/t189-stale-evidence-tag`, unit commit `d2e8ebe1` + bring-up merge `e6b0126b` of master
on top. `self != executor` (executor: build subagent, same Claude session family, fresh context;
no `ANTHROPIC_BASE_URL` override; no external delegation involved in this unit).

## VERDICT: PASS

## What I re-ran myself (never trusted pasted output)

- `uv run pytest` (no `-q`): **3 failed, 2047 passed, 6 skipped, 14 xfailed, 15 warnings in 870.08s**
  — reproduces the manifest's `3 failed, 2047 passed` exactly. The 3 failures are exactly the ones
  named in advance and nothing else:
  `test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`
  (AT-627), `test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail` and
  `::test_revised_goal_contract_is_registered` (both `ISS-at638-remainder-2`, pre-existing on master,
  caused by the orchestrator's own `.goal/goal.json` growth — confirmed neither test file is in this
  unit's own commit diff). **No fourth failure.**
- `uv run ruff check src tests scripts` → `All checks passed!` (re-run twice, including after my
  own contract/ledger edits).
- `uv run autotester doctor` → `doctor: clean` (re-run twice, same).
- `uv run pytest tests/ -k evidence` (T-189's registered `done_check`) → 49 passed. Per the
  manifest's own disclosure and `ISS-at638-remainder-2`, this keyword match is Goodhartable and is
  **not** treated as the unit's real evidence — the capability-coverage table and the mutation-kill
  proof below are.
- The C7 mutation-kill proof, re-run independently:
  `uv run python scripts/mutation_check.py qa/evidence/t189-stale-evidence-tag/mutations.json` →
  **3/3 mutations killed**, each attributed to exactly the test it claims. `git status --porcelain`
  before and after the run is byte-identical — the sandboxed harness left the bound tree untouched.

## AT-218 vacuous-guard row — attacked directly, not read

Built two lying tombstones myself in a clean-room fixture (a separate temp root outside the bound
tree, importing the shipped `check_stale_evidence_specs` directly — never a sabotage of the bound
tree):

1. **Well-formed but nonexistent function.** `moved_to` names a real file, a function that does not
   exist in it. Result: **flagged**, with the exact message the code produces —
   `tagged moved to '...::test_does_not_exist' but that does not resolve either`. The mechanism does
   not trust the tombstone's presence; it re-resolves, exactly as claimed.
2. **Real function, wrong one (the case the dispatch asked me to be honest about).** `moved_to`
   names a function that genuinely exists in the named file but is a decoy, not the actual moved
   test. Result: **silently accepted (0 violations)**. This is a real, structural limit — resolution
   proves existence, not semantic correctness — and it is not something the unit overclaims. The
   manifest's own language ("the check never trusts a tombstone's mere presence... for an
   unresolvable kills id it looks up the tombstone and then re-resolves moved_to") describes exactly
   this mechanism and nothing more; it never claims to detect a real-but-wrong target. I folded this
   limit explicitly into the C7 amendment below so it is recorded as contract text, not left as an
   unwritten caveat.

Also confirmed independently: a bare (non-`::`) `kills` name is resolved only against the spec's own
declared `tests` scope, matching `scripts/mutation_check.py::collected_tests()`'s real behavior
(`--collect-only` scoped to the spec's own `tests` argument) — the false-positive fix claim in the
manifest is correct, re-derived from `mutation_check.py` itself, not taken on its word.

## Byte-intactness

Re-derived the same way the manifest specifies (`git rev-parse HEAD:<path>` vs
`git hash-object <path>`) for all 7 files independently — all 7 **MATCH**. Also reproduced the
documented CRLF/`core.autocrlf=true` trap myself: a naive `sha256sum` of the working file vs
`sha256sum` of `git show HEAD:<path>` output mismatches (`7b8245e7...` vs `b50d4695...`) for a file
the rev-parse/hash-object pair proves is untouched. The manifest's caveat is accurate, not a
convenient excuse.

## Diff scope (C7's own scope-boundary discipline, 4c)

`git diff --name-status d2e8ebe1^..d2e8ebe1` (the unit's own commit, excluding the bring-up merge of
master) matches the manifest's "What changed" list exactly: `docs/MAP.md`, 7 new
`mutations.stale.json` sidecars, `qa/evidence/t189-stale-evidence-tag/mutations.json`,
`qa/manifests/t189-stale-evidence-tag.md`, `src/autotester/doctor.py`,
`src/autotester/ledger/evidence_specs.py`, `src/autotester/schema/evidence_tombstone.py`,
`tests/test_evidence_spec_tombstones.py`. No deletion or rename of an existing function, test, or
config key. The broader `3e232fea...HEAD` diff (which also touches `qa/.last-tick`, `qa/QUEUE.md`,
and an unrelated T-192 manifest) is entirely the disclosed bring-up merge of master, not this unit's
own change.

## Retroactive audit of the 27 stale entries

Independently recomputed the pre-tombstone stale count from the 7 spec files using the shipped
`_load_spec`/`_scope_files`/`_resolves` functions directly: **27**, exact match to the manifest's
figure (per-file: at469=1, at496=6, at500=5, at504=5, at506=1, at509=5, at511=4 — collapsing into 24
tombstone entries because several cover every parametrize id of one moved function).

Rather than a partial sample, I traced **every** tombstone entry attributed to a named unit back to
that unit's actual commit diff:
- `git show 3546a28c -- tests/test_ledger_checks.py` (AT-506's split): every `+def test_...` name in
  this commit's diff matches an at506-attributed tombstone entry, 1:1.
- `git show 9ed3833b -- tests/test_marker_blocks.py` (AT-513's split): every `+def test_...` name in
  this commit's diff matches an at513-attributed tombstone entry, 1:1.

23 of 24 entries are fully corroborated this way. The 24th (at469, honestly marked
`moved_by_unit: "unknown"`) I traced by hand: `git log -S` on both node-id names shows they were
**both introduced in the same original commit** (`f7e83cdc`, AT-469's own fix), not one renamed into
the other — the old one was later **deleted**, not renamed, by an unrelated rewrite (`07428a76`,
AT-478/479, which replaced text-based failure parsing with structured pytest reports; the surviving
test was never touched by that commit). The tombstone's note calling this a "rename" is imprecise,
though not harmful: the 3 stale mutations targeted a code path (`known`-nodeid text parsing) that no
longer exists at all, so there is no live regression signal being silenced, and the honestly-unknown
attribution already flagged this entry as uncertain. **Filed `ISS-t189-stale-evidence-tag-1`,
severity low** (documentation precision, not a functional defect) rather than silently letting it
pass — this is exactly the kind of thing item 3 of the dispatch asked me to be suspicious of, and it
turned out to be real but minor.

Also independently audited the scope boundary (gap 5 in the manifest): listed every directory under
`qa/evidence/` and confirmed no directory outside the `browser-*` naming convention carries a file
literally named `mutations.json` in a shape `check_stale_evidence_specs` would misread — the
boundary holds for the current repo, not just by assumption.

## Live browser / persona

Not applicable — confirmed from the unit's own isolated commit diff (see Diff scope above), not
from the manifest's claim: every changed path is `schema/`, `ledger/`, `doctor.py`, `docs/MAP.md`,
`tests/`, or a `qa/evidence/*.json` sidecar. No UI surface, no persona walk required. (Minor,
non-blocking: the manifest does not carry a literal `Persona walk:` line in the format the checker
skill's 5bb expects for a 2026-09-27 manifest; its "Live browser evidence: not UI-touching" section
covers the same substance. Noted, not filed — zero risk given the changed-paths audit above.)

## Contract fold-in (mine to do, per the maker/checker split)

D-048 authorized "the at516 tagging rule, in the contract that owns evidence specs" as an
authorized-but-unwritten change; the manifest correctly left it to me rather than editing
`qa/contracts/` itself. **Adopted the mechanism into `qa/contracts/core-invariants.md` C7** as a new
bullet (resolution-not-presence discipline, the disclosed real-but-wrong-function limit, and the
bare-name scope fix), extended C7's `Verify:` line to name `check_stale_evidence_specs` via
`uv run autotester doctor`, and appended a routine amendment-log entry citing D-048 and this unit.
Tightening only — no existing criterion weakened, no enforcement-path file touched, so no
`Approved-by` gate applies to this fold-in itself.

## Ledger

- `AT-516`: `open` → `fixed`, `fixed_date: 2026-09-27`,
  `regression_check: "uv run pytest tests/test_evidence_spec_tombstones.py"` (a `verify.shell.commands`
  base — `uv run pytest` — plus a test-file argument, per the allowed regression_check forms).
- New: `ISS-t189-stale-evidence-tag-1` (low, tombstone-narrative-inaccuracy, at469) — see above.
- `ISS-at638-remainder-2` untouched — correctly out of scope for this unit; already queued
  separately by the orchestrator.

## SCOREBOARD

7/7 criteria met (C7 mutation-independence, byte-intactness, AT-218 resolution discipline, bare-name
scope correctness, retroactive-audit accuracy, diff-scope discipline, full-suite regression floor),
0/0 additional invariants beyond C7 itself violated.

## CAPABILITY-COVERAGE

3/3 rows reproduced independently (own mutation-check run, tree unchanged before/after) plus 2/2
of my own clean-room falsifications (lying-tombstone nonexistent-function case caught; real-but-wrong
case honestly does not catch, as disclosed).

## LIVE-BROWSER

not-applicable (changed paths: `src/autotester/{schema,ledger}/*.py`, `src/autotester/doctor.py`,
`docs/MAP.md`, `tests/test_evidence_spec_tombstones.py`, `qa/evidence/**/mutations*.json` — no UI
surface, confirmed from the unit's own isolated commit diff, not the manifest's assertion)

## ISSUES-WRITTEN

ISS-t189-stale-evidence-tag-1 (low)

## EXECUTOR

build subagent (manifest's own label) (checker: fresh Claude Sonnet subagent, this session)

## EXPLANATION

Every claim in the manifest reproduced under independent re-derivation, including the two claims
most worth distrusting (byte-intactness, given the CRLF trap it itself documents; and the
27-stale-entry retroactive audit, given how much a wrong `moved_to` could quietly cost). The one
genuine imperfection found — at469's "rename" language not matching git history — does not weaken
the mechanism's actual guarantee and is filed, not swept aside. PASS.
