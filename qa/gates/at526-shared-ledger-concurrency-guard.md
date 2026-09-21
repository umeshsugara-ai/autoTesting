# Gate — AT-526: should the checker's `qa/issues.jsonl` commit go through a
# verify-before-commit guard, and who builds it?

**Why this is a gate, not a shipped fix:** the remedy is small and already drafted
and smoke-tested (below), but landing it needs a sibling test file
(`tests/test_commit_guard.py`) and this unit's authorized file set names only
`tests/test_ledger.py` — which has **6 lines of headroom** against C2's 300-line
cap (294 lines today; `check_file_sizes` in `src/autotester/doctor.py:68`). There is
no way to add real, mutation-tested coverage for a new capability inside that
budget. Shipping the code without shipping tests for it would itself be the kind
of unverified claim `qa/contracts/core-invariants.md` C7 exists to refuse, so it is
proposed here instead, exactly as `at520`'s own gate did for a different reason
(a decision the pair should not make silently) — this one is a real file-budget
constraint, not a judgment call, but the effect (not landing in this unit) is the
same.

## The measurement that changes the brief's framing

The brief asked whether today's incident (commit `0fe2b6d`) was a one-off. It is
not. `git log --format='%h %ad %s' -- qa/issues.jsonl` (287 commits, full history,
`qa/evidence/at526-shared-ledger-concurrency-guard/ledger_commit_log.txt`) contains
**seven** distinct shared-ledger concurrency incidents across nine days
(2026-09-09 -> 2026-09-18), in four different mechanisms:

| Commit | Date | Mechanism | Damage |
|---|---|---|---|
| `35b3dcb` | 09-09 | two agents picked the same new issue id | renumbered (AT-269->AT-271) |
| `2e0e9c0` | 09-11 | id collisions, enough of them to need a dedicated unit (`at319-issue-id-collision-reconcile`) | reconciled |
| `b04d7c9` | 09-11 | a second id collision (AT-335->AT-337) | renumbered, "trivial" |
| `6566441` | 09-17 | stale-copy commit picked up a concurrent loop's row instead of its own | **one checker's finding silently dropped until fixed same day** |
| `67a61ec`/AT-496 | 09-18 01:05 | a commit built from a stale blob dropped a row and reverted a status | **real data loss, undetected until a later checker noticed and filed AT-496** |
| `a8caf58` | 09-18 06:52 | a PASS commit's own `json.dumps(ensure_ascii=False)` reformatted the whole file | not concurrency, but the same "sloppy shared-file write" family |
| `0fe2b6d`/AT-526 | 09-18 09:14 | `git commit --only` swept a concurrent checker's uncommitted edits into its own commit | **no damage this time** — pure luck, not a property of the mechanism |

**This is not one incident; it is a recurring pattern at roughly one per day of
heavy checker activity**, with two confirmed real data-loss events (AT-482's
dropped finding, AT-496's dropped row + reverted status). The brief's own
proportionality test ("if today's incident is the only one, say so") points the
other way: a real remedy beyond detection is warranted.

## Current health (measured, not assumed)

`uv run autotester doctor` is **clean right now** — `check_qa_issue_rows`
(`src/autotester/ledger/checks.py:139`, built under AT-496) already detects the
"row lost" and "row claimed-fixed-but-still-open" shapes and neither fires today.
No open damage from the AT-526 incident itself; the checker's own account (no
row wrong, just fortunate timing) checks out.

## Option (d) from the brief — measured, and it does not survive contact with the corpus

The brief's exact wording — "a row at `fixed` whose unit has no verdict at the
matching cycle" — cashes out as: a `fixed` row should have a `fixed_by` field
naming a real verdict. Measured directly
(`qa/evidence/at526-shared-ledger-concurrency-guard/fixed_by_sparsity.log`):

```
total rows: 523  fixed rows: 150
fixed rows with NO fixed_by field: 130
```

**130 of 150 fixed rows (87%) have no `fixed_by` at all.** A rule built on that
field would flag 87% of legitimately-fixed rows on day one — precisely the
false-accusation machine the brief warned this option might already be, in the
same family as the rejected "open row naming a PASSed manifest" rule. **Do not
build this.** (The zero rows whose `fixed_by` names a missing verdict file is not
evidence for the rule — it only shows the 13% that DO populate the field are
honest, not that the field is reliable enough to gate on.)

## The proposed remedy (drafted, smoke-tested, not merged)

`qa/evidence/at526-shared-ledger-concurrency-guard/commit_guard.proposed.py` — a
~140-line module (`src/autotester/ledger/commit_guard.py`, if adopted) with two
pure functions and one CLI command:

- `diff_ledger_ids(old_text, new_text) -> {id: "added"|"changed"|"removed"}` —
  compares `qa/issues.jsonl` row-by-row **by id**, using
  `json.dumps(row, sort_keys=True)` for the comparison so a pure reformat
  (whitespace, key order, `ensure_ascii` escaping — the `a8caf58` incident) is
  never mistaken for a content change, and reordering rows is never mistaken for
  a change either.
- `unexpected_ledger_changes(old_text, new_text, intended_ids)` — the guard
  itself: every id that changed between `HEAD` and the working tree that the
  caller did NOT declare it intended to touch.
- `autotester qa-ledger commit --expect AT-521,AT-522,AT-524 -m "..."` — replaces
  a bare `git commit --only qa/issues.jsonl`; reads `HEAD`'s copy fresh via
  `git show HEAD:qa/issues.jsonl` (not a cached read), refuses with the exact
  foreign ids named if anything outside `--expect` changed, and only then runs
  the commit.

**Smoke-tested against the real incident shapes**
(`qa/evidence/at526-shared-ledger-concurrency-guard/smoke_commit_guard.py`, run
output confirms all six assertions pass):

- Reproduces `0fe2b6d` exactly: given the at520 checker's uncommitted flip+append
  sitting in the shared working tree and the at521 checker's own intended
  `{AT-521, AT-524}`, the guard reports `{'AT-520': 'changed', 'AT-525': 'added'}`
  as unexpected — it would have **refused** that commit.
- **Also generalizes to AT-496's stale-copy drop** (a different mechanism —
  reading an old blob, not a shared-tree race): given the true `HEAD` at the time
  of `1688da3` and that checker's actual stale-based rewrite, the guard reports
  `{'AT-401': 'changed', 'AT-494': 'removed'}` as unexpected. **One remedy, two of
  the seven measured incidents directly prevented**, plus AT-526's own.
- Does **not** address the id-collision mechanism (`35b3dcb`, `2e0e9c0`,
  `b04d7c9`, 3 of 7 incidents): if two agents independently choose the same new
  id, each treats it as its own intended addition, so neither is "unexpected" to
  the other. That needs a different remedy (an id-allocation step, not a
  commit-time content diff) — named here as a gap, not solved by this proposal.

## Options

1. **Adopt the drafted module as-is**, as its own small unit with an authorized
   `tests/test_commit_guard.py` (the AT-506 precedent: `checks.py` was split out
   of `doctor.py` for exactly this file-budget reason). Requires the checker's
   own workflow (`~/.claude/skills/checker/SKILL.md`, outside this repo) to
   actually call `autotester qa-ledger commit` instead of a bare
   `git commit --only qa/issues.jsonl` — a change to the maker-checker handshake
   contract, which is why this is named as a decision rather than silently done.
2. **Orchestration-only, no code**: never let two checkers hold concurrent
   uncommitted edits to `qa/issues.jsonl` — serialize the *commit* step only
   (each checker's analysis/build work can still run in parallel; only the
   moment of writing+committing the shared ledger is single-file-at-a-time).
   Costs nothing to build, fixes `AT-526`'s exact mechanism and `6566441`'s, does
   **not** fix `AT-496` (a stale read can still happen even serialized, if the
   read and the commit are far apart in time) or the id-collision family.
3. **Both** — option 2 as the immediate, zero-cost orchestration fix, option 1 as
   a fast-follow unit once Umesh confirms the handshake-contract change. This is
   the recommendation (see manifest).
4. **Do nothing further** — accept that `check_qa_issue_rows` (AT-496) already
   detects the two damaging shapes after the fact, and treat a 7-incidents-in-9-days
   rate as an acceptable cost of running checkers concurrently. Not recommended:
   two of those seven were real, silently-dropped findings, caught only because a
   later, unrelated checker happened to notice.

**Blocks:** any change to `~/.claude/skills/checker/SKILL.md`'s commit step
(outside this repo, needs its own review); a possible id-allocation fix for the
three collision incidents (separate mechanism, not designed here).

**Opened:** 2026-09-18 (AT-526 build unit, measured before proposing).

**Answered:** 2026-09-21 — **Option 3: Both** (Umesh in chat: *"3. Both — orchestration now,
guard as fast-follow"*):
- **Immediate (this week):** orchestration-only serialization — no two agents may hold
  concurrent uncommitted edits to `qa/issues.jsonl`; the commit step of the shared ledger is
  single-file-at-a-time (analysis/build work stays parallel). Fixes AT-526's exact mechanism
  and `6566441`'s.
- **Fast-follow (one unit):** adopt the drafted module (`qa/evidence/at526-shared-ledger-
  concurrency-guard/commit_guard.proposed.py` → `src/autotester/ledger/commit_guard.py`) with
  its own authorized `tests/test_commit_guard.py` (AT-506 file-budget precedent), then update
  `~/.claude/skills/checker/SKILL.md`'s commit step to `autotester qa-ledger commit --expect …`
  — Umesh authorized the handshake-contract change in the same reply, and asked that the
  result be validated by the /checker skill before it is trusted.
- Named gaps stay named: the id-collision family (3 of 7 incidents) needs a separate
  id-allocation remedy — not designed in option 3 and not silently dropped.
