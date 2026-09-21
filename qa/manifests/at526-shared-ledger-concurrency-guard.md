# Manifest — at526-shared-ledger-concurrency-guard (AT-526)

**Unit:** AT-526 — is the shared `qa/issues.jsonl` safe under concurrent checkers, and if
not, what is the proportionate remedy? Investigation unit; this brief explicitly allows
ending as a proposal rather than a code change, and that is where this lands.
**Contract:** `qa/contracts/core-invariants.md` C7 (verification is judged on real,
re-runnable output) and C10 (a maker/checker commit names the qa/ files its handshake
writes).
**Goal task:** none (process/governance, issue-driven).
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-526 (medium, NOT fixed here — see "Status" below; a proposal is
recorded, no ledger row is flipped by me, `qa/issues.jsonl` is the checker's write surface
per AT-499 and is also this unit's subject, so I do not touch it).

## Step 1 — how often does this actually happen? (measured, not assumed)

The brief asked me to check whether today's incident (commit `0fe2b6d`, AT-521 checker's
`git commit --only qa/issues.jsonl` sweeping in the at520 checker's uncommitted edits) is
a one-off. `git log --format='%h %ad %s' --date=iso -- qa/issues.jsonl` over the file's
full history (287 commits, `qa/evidence/at526-shared-ledger-concurrency-guard/ledger_commit_log.txt`),
grepped for the incident's own vocabulary (`collision|self-inflicted|dropped|swept|stale
(copy|write)|recurred|reformat`), then each hit read in full:

| Commit | Date | What happened | Damage |
|---|---|---|---|
| `35b3dcb` | 09-09 | two agents independently picked the same new issue id (AT-269) | renumbered to AT-271 |
| `2e0e9c0` | 09-11 | id collisions recurring enough to need a dedicated reconciliation unit (`at319-issue-id-collision-reconcile`) | reconciled |
| `b04d7c9` | 09-11 | a second id collision (AT-335 -> AT-337) | renumbered, called "trivial" |
| `6566441` | 09-17 | a checker's own commit was built from a shared copy that a concurrent loop had just appended to; the checker's own finding was silently overwritten by the other loop's row under the same id | dropped, then found and fixed same day |
| `67a61ec` (AT-496) | 09-18 01:05 | a commit built from a **stale** blob of the ledger dropped a just-appended row (AT-494) and reverted a just-flipped status (AT-401) | real data loss, sat undetected for ~30 minutes until a different checker noticed |
| `a8caf58` | 09-18 06:52 | a PASS commit's own `json.dumps(ensure_ascii=False)` reformatted ~40 unrelated lines of the file | not a concurrency collision, but the same "sloppy shared-file write" family |
| `0fe2b6d` (AT-526, this unit's subject) | 09-18 09:14 | `git commit --only <path>` restricts which files a commit touches, not whose changes within a shared file ride along — it commits the file's current on-disk content wholesale | **no damage this time** — the swept-in edits happened to be correct |

**This is not one incident. It is a recurring pattern — roughly one distinct incident per
day of heavy checker activity, across four different mechanisms, with two confirmed real
data-loss events** (`6566441`'s dropped finding, AT-496's dropped row + reverted status).
The brief's own test for proportionality points toward building something, not "note it
and move on."

## Step 2 — is there damage present right now?

`uv run autotester doctor` -> `doctor: clean`. `check_qa_issue_rows`
(`src/autotester/ledger/checks.py:139`, built under AT-496 specifically for this failure
class) already detects a named-but-missing row (`ledger-row-lost`) and a claimed-fixed-but-
still-open row (`ledger-row-stale`), and neither fires today. The AT-526 incident itself
caused no damage — I did not re-litigate that finding, only confirmed it against the live
tree rather than taking it on trust.

I did not go looking for ids mentioned only in prose (AT-504/AT-509/AT-511 exist precisely
to stop that misreading) — `check_qa_issue_rows`' own marker-line logic is the tool built
and hardened for that distinction, and re-implementing a cruder version of it by hand here
would risk exactly the false-accusation class those three units fixed.

## Step 3 — the brief's option (d), measured against the live corpus

Brief's exact wording: "a doctor rule that detects the symptom — a row at `fixed` whose
unit has no verdict at the matching cycle" — i.e., a `fixed` row should carry a `fixed_by`
naming a real verdict. Measured
(`qa/evidence/at526-shared-ledger-concurrency-guard/fixed_by_sparsity.log`):

```
total rows: 523  fixed rows: 150
fixed rows with NO fixed_by field: 130
fixed rows whose fixed_by names a verdict file NOT present on disk: 0
```

**130 of 150 fixed rows (87%) carry no `fixed_by` field at all.** A rule gating on that
field would flag 87% of legitimately-fixed rows as violations on day one — the same
false-accusation shape the brief itself warned about (the rejected "open row naming a
PASSed manifest" rule, 5/1 false-positive ratio). **I am not building this**, and would
recommend against it in this form to whoever builds a fast-follow: the field is
aspirational, not a load-bearing invariant, and a rule cannot be built on a field 87% of
real rows never populate without first making population of that field itself enforced —
a separate, larger change to the row schema, not in scope here.

## Step 4 — the remedy: drafted, smoke-tested, not merged

I wrote a real, working module — `verify-before-commit` (the brief's option (b)) — and
then hit a hard constraint that stopped me from shipping it:
`tests/test_ledger.py` is 294 lines against `check_file_sizes`'s 300-line cap
(`src/autotester/doctor.py:68`, applies to `tests/` too per AT-419). **Six lines of
headroom is not enough to add real, mutation-tested coverage for a new capability**, and
this unit's authorized file set names `tests/test_ledger.py` specifically, not a new
sibling test file. Shipping the module without shipping tests for it would be exactly the
kind of unverified claim C7 exists to refuse — so I did not merge it. Full writeup,
measurement, and the proposed code are in
`qa/gates/at526-shared-ledger-concurrency-guard.md` and
`qa/evidence/at526-shared-ledger-concurrency-guard/commit_guard.proposed.py`.

**What I verified before proposing it (not merely argued):**
`qa/evidence/at526-shared-ledger-concurrency-guard/smoke_commit_guard.py`, run directly
against the drafted module (typer stubbed out so the pure logic could be exercised without
installing the CLI):

```
PASS: unchanged ledger -> no diff
PASS: reordered rows -> no diff
PASS: reformatted-but-same-content row -> no diff
PASS: added/changed/removed classified correctly: {'AT-1': 'changed', 'AT-3': 'added', 'AT-2': 'removed'}
PASS: reproduces + would have REFUSED the real AT-526 incident: {'AT-520': 'changed', 'AT-525': 'added'}
PASS: no unexpected ids -> clean, would commit
PASS: would ALSO have caught the AT-496 stale-copy drop/revert: {'AT-401': 'changed', 'AT-494': 'removed'}
```

The last line matters most: the guard is not a one-incident patch. Comparing `HEAD`
(re-read fresh at commit time, not cached) against the working tree, row-by-row, by id,
catches both AT-526's mechanism (a concurrent tree edit riding along) and AT-496's
different mechanism (a stale read producing a lossy rewrite) with the same check. It does
**not** address the three id-collision incidents (`35b3dcb`, `2e0e9c0`, `b04d7c9`) — two
agents each treating a freshly-chosen, colliding id as their own intended addition looks
identical to a legitimate add from inside this check. That is disclosed as a gap in the
gate, not silently left out.

I reverted the module and its `cli.py` wiring out of the working tree after drafting and
smoke-testing it (confirmed via `git diff --stat -- src/` showing only the concurrent
subagent's own `doctor.py`/`checks.py` changes, none of mine) — it lives only as an
evidence artifact now, ready for whoever picks up the fast-follow to drop in as-is.

## How to verify (commands + expected)

```
uv run autotester doctor                                    # expect: doctor: clean
uv run ruff check src tests scripts                         # expect: All checks passed!
git diff --stat -- src/                                     # expect: only doctor.py / ledger/checks.py
                                                              # (the concurrent AT-checks subagent's
                                                              # own work), nothing from this unit
git log --format='%h %ad %s' --date=iso -- qa/issues.jsonl  # expect: 287 commits (full history)
uv run python qa/evidence/at526-shared-ledger-concurrency-guard/smoke_commit_guard.py
                                                              # expect: 7 PASS lines, 0 assertion errors
```

## Actual outputs (from my own run)

```
$ uv run autotester doctor
doctor: clean
$ uv run ruff check src tests scripts
All checks passed!
$ git diff --stat -- src/
 src/autotester/doctor.py         | (concurrent subagent's own change)
 src/autotester/ledger/checks.py  | (concurrent subagent's own change)
```

Full suite was **not** re-run: the final state of this unit touches no `src/` file (the
draft was written, smoke-tested, and reverted; only `qa/manifests/`, `qa/gates/`, and
`qa/evidence/` under this unit's own slug changed), matching the brief's "run the full
suite once only if you touch src/."

## Capability coverage (each claim -> its isolating check)

| capability | check | falsifying condition | observed |
|---|---|---|---|
| the AT-526 incident is not a one-off | full ledger-commit history grepped for the incident's own vocabulary, each hit read in full | fewer than 2 real hits besides `0fe2b6d` | 6 other hits, 2 with confirmed real data loss |
| no damage is currently sitting in the ledger | `uv run autotester doctor` (uses AT-496's `check_qa_issue_rows`) | any `ledger-row-lost`/`ledger-row-stale` violation | clean |
| option (d) as literally specified is a false-accusation machine | direct count of `fixed` rows missing `fixed_by` | fewer than, say, 20% missing | 130/150 = 87% missing |
| the proposed guard would have refused the real incident | smoke script constructs the exact `0fe2b6d` working-tree state and calls `unexpected_ledger_changes` | the flagged set is empty or wrong | `{'AT-520': 'changed', 'AT-525': 'added'}`, matching the two rows the checker's own report named as not-its-own |
| the guard generalizes beyond AT-526's specific mechanism | same smoke script, AT-496's stale-read scenario reconstructed from its own manifest's numbers | the flagged set is empty or wrong | `{'AT-401': 'changed', 'AT-494': 'removed'}`, matching AT-496's own two named losses exactly |
| nothing of mine is left in `src/` | `git diff --stat -- src/` | any hunk outside `doctor.py`/`checks.py` | none |

**NO ISOLATING FALSIFICATION for the "recurring, not one-off" framing itself**
(`revert_op: none`) — it is a historical fact about the git log, not a behavior a revert
could re-test; the isolating check is the grep + manual read already shown.

## Live browser evidence

Not UI-touching — no `src/` file remains changed, no `ui/` route, no browser surface.
Changed paths at close: `qa/manifests/at526-shared-ledger-concurrency-guard.md`,
`qa/gates/at526-shared-ledger-concurrency-guard.md`,
`qa/evidence/at526-shared-ledger-concurrency-guard/*`.

## Known limits (disclosed, not claimed)

- **The remedy is proposed, not shipped.** It requires its own unit with an authorized
  `tests/test_commit_guard.py` (the `check_file_sizes` budget on `tests/test_ledger.py`
  leaves 6 lines of headroom — not enough for real coverage) and, to actually take effect,
  a change to `~/.claude/skills/checker/SKILL.md`'s commit step (outside this repo, and a
  change to the maker-checker handshake contract that is not this unit's to make
  unilaterally).
- **The proposed guard does not address the id-collision family** (3 of the 7 measured
  incidents) — two agents choosing the same new id both look, from inside this check, like
  a legitimate intended addition. A different remedy (id allocation, not commit-time
  content diff) would be needed for that class.
- **`qa/contracts/core-invariants.md` is unedited** — no criterion changed; this unit found
  no gap in the contract itself, only in the mechanics of how the checker's own commit is
  made.
- **`qa/issues.jsonl`'s AT-526 row is not flipped by this manifest** — that ledger is the
  checker's write surface (AT-499) and this unit's subject; the checker should judge
  whether "measured, proposed, gated" constitutes progress worth a status note, or whether
  it should stay `open` until the gate is answered.

## Status: ready-for-check (proposal, not a code change)

This is a completed investigation ending in a gate
(`qa/gates/at526-shared-ledger-concurrency-guard.md`) and a ready-to-adopt but unmerged
module (`qa/evidence/at526-shared-ledger-concurrency-guard/commit_guard.proposed.py`), per
the brief's explicit allowance for that outcome. The measured finding — this is a real,
recurring pattern (7 incidents / 9 days, 2 with confirmed data loss), not a single
orchestrator mistake — argues for building the proposed guard as a fast-follow unit rather
than treating today's near-miss as isolated; the file-budget wall is what stopped this unit
from doing that itself, not a judgment that it isn't worth doing.
