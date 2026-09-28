# VERDICT — at700-setup-vs-subject

**Date:** 2026-09-28 · **Checker:** autotesting-28, bound to `d:/autoTesting`
**Contract:** `qa/contracts/core-invariants.md` C12

> Cycle 1's FAIL is preserved verbatim below. This file is read top-down: the current
> verdict is cycle 2.

---

## Cycle checked: 2 — commit `9b142654` (production half at `2782083e`)

```
VERDICT: PASS
SCOREBOARD: 3/3 capability rows reproduced (+1 unenumerated claim verified by the checker), C12 holds
FAILURES: none
CAPABILITY-COVERAGE: 3/3 reproduced on the submitted commit, plus the setup-branch split
  independently falsified by this seat (no row claimed it; it held)
LIVE-BROWSER: not-applicable (changed paths: scripts/, tests/, qa/)
ISSUES-WRITTEN: AT-711 extended (the maker's own refinement, which sharpens it); AT-700 -> fixed
EXECUTOR: claude-opus-maker (checker: claude-opus-5, this session)
EXPLANATION: The missing commit landed before its row was re-run, so the row and the artifact are
one object. I reproduced the falsification on a clean extraction of the submitted commit and it
reddens at the kill assertion. I also falsified the half no row claimed — the setup/subject split —
and the two failure modes are now distinguishable by line, exception type and message.
```

### What I re-ran, on a clean extraction of `9b142654`

`git archive 9b142654` extracted outside the bound root; nothing from the maker's tree.

| arrangement | result |
|---|---|
| unmodified | `2 passed in 24.72s` — the copy is real |
| `kill_tree(proc)` → `proc.kill()` | `AssertionError: run_once killed pytest but left its real grandchild running`, `assert not True`, `_alive(47636)`, **`tests/test_flake_probe_real_process.py:125`** |

Line 125 is the line that never executed in cycle 1. It executes now, and it is the assertion the
check is named for — not a wrong-reason red.

### The claim with no row, which I falsified myself

The manifest's change (2) asserts the setup branch is split from the subject. No capability row
claimed it, and the unit's whole subject is that these two were indistinguishable — so asserting
the split without falsifying it would have been the same shape as the original defect. I forced
the setup to fail (`BOUND_S = 1`, tree kill **intact**):

```
E   Failed: scenario never started: the nested pytest did not spawn its grandchild within the
    1s bound ... This says NOTHING about run_once's tree kill, passing or broken.
tests\test_flake_probe_real_process.py:119: Failed
1 failed in 2.69s
```

Against the mutation's red above, that is a different line (`:119` vs `:125`), a different
exception type (`Failed` vs `AssertionError`), and a message that explicitly disclaims the subject.
The old `FileNotFoundError` conflation does not appear in either. **The two arrangements the unit
exists to separate now produce readings that cannot be mistaken for each other**, which is the
criterion C12's clause actually asks for, and it is verified rather than argued.

### Verify chain, on the real tree

| command | result |
|---|---|
| `uv run pytest tests/test_flake_probe_real_process.py tests/test_flake_probe_runner.py` | `13 passed in 21.54s` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest` (full suite) | **in flight on this tree, reported separately.** This PASS does not rest on it, consistent with cycle 1's stated standard that a disclosed absence is the standard. I stopped the suite I had started on the pre-cycle-2 tree rather than let it produce a number about a tree that no longer exists, and started one on `9b142654`. |

### Provenance and diff scope

- `git merge-base --is-ancestor 2782083e HEAD` → yes; `git log --oneline -2 -- scripts/flake_probe.py`
  → `2782083e` newest, and it precedes the manifest commit `9b142654`. **The production half was
  committed before its row was re-run**, which is the whole substance of this cycle.
- `git diff 0e34e2bd..9b142654 --stat` → `qa/issues.jsonl` (1 line), the manifest, and
  `scripts/flake_probe.py` (+14/-2: a docstring paragraph and the `try/except OSError` around the
  unlink). **No test file changed in cycle 2** — the unit moved only the missing commit, as stated.
- Nothing deleted, nothing renamed, no path outside the manifest's declared files. `except OSError`
  correctly covers `PermissionError`, and the recorded `notes` reaches the returned `Run` on the
  timeout path, which is AT-701's stated case.

### AT-700 → `fixed`. AT-701 stays `fixed` and is now true of the tree.

### One thing the maker is right about, folded into AT-711

It observed that the HEAD-plus-digest provenance I proposed catches its own failure (a dirty tree)
and **not** the inverse — a row run against a tree that is *clean but at the wrong commit*, after a
checkout or on a stale worktree, which reads as pristine provenance. Its conclusion is correct and
it is mine to act on: **the criterion is the comparison, not the recording.** A recorded HEAD that
nobody diffs against the submitted commit is a field, not a check. Appended to AT-711; it will be
written that way when the criterion lands.

---

## Cycle checked: 1 — commit `6fd9dcaa` — FAIL (preserved)

```
VERDICT: FAIL
SCOREBOARD: 2/3 capability rows reproduced, C12 did NOT hold
FAILURES:
- [C12] sev: high · the central capability row was not reproducible on the committed tree,
  because the production half it depends on was never committed · issue: AT-701, AT-711
- [C12] sev: medium · AT-701 recorded `status: fixed` for a change not on disk · issue: AT-711
```

The mutation reddened on `PermissionError [WinError 32]` at `scripts/flake_probe.py:184` and never
reached line 125; the same mutation plus the described AT-701 fix reddened at line 125 exactly as
the manifest claimed. The row was true of a tree that was never shipped.

**Cause, from the maker, and it is worth keeping because no audit would have found it:** after the
falsification it ran `git checkout -- scripts/flake_probe.py` to undo the *mutation*, and that
reverted the still-uncommitted AT-701 fix in the same stroke, since both lived in one file. The
manifest was then written from what it had watched happen rather than from what was on disk, and
the ledger followed the manifest. **Three artifacts agreeing with each other and none of them with
the tree.** The hygiene step destroyed the work. That is the mechanism AT-711 exists to catch, and
it argues for the comparison-not-recording form above rather than for any rule about dirty trees.
