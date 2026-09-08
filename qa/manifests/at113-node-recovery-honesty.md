# Manifest — at113-node-recovery-honesty
**Contract:** `qa/contracts/explore.md` X11 (artifacts are incremental, human-readable, and
survive a crash) and X13 (a crawl proposes screens, never approves them — the same "the system
knew something and did not say it" shape as AT-104/AT-098, which this batch's design continues).
**Goal task:** none (issue-fix unit — gates T-145)
**Date:** 2026-09-08
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** **AT-113** (high — sweep-found, gates T-145)

## The defect, as the sweep proved it
`explore_node.py::visit_node` had two paths where a node the crawl could not return to was marked
`ABORTED_ERROR` **with no issue filed**, and one of those two paths did not even reach
`ABORTED_ERROR` — it fell through to `EXPLORED` anyway:

1. **Entry failure.** `return_to(rt, node)` fails before any candidate is tried →
   `_mark(rt, node, NodeStatus.ABORTED_ERROR)` and `return`. No `add_issue` call at all. The sweep
   forced this and got `screens=2, issues=0` with one node silently unexplored — the crawl still
   ended `status=completed`, `stop_reason='frontier empty'`.
2. **Mid-loop failure.** `return_to` fails after at least one candidate was tried → an edge **was**
   recorded (`ERRORED`, "could not return to this screen"), but the loop then `break`s into the
   unconditional `_mark(rt, node, NodeStatus.EXPLORED)` at the bottom of the function. A node
   visited **halfway** was marked as if it had been visited completely.

Neither node's problem reached `crawl.issues`, and the crawl page rendered every node's status pill
in the same neutral gray regardless of value — so even a human reading `ABORTED_ERROR` in the
screen tree would not see it flagged as a problem.

## What changed
- `stages/explore_node.py::visit_node` — both paths now call `add_issue(..., IssueKind.NAVIGATION,
  ...)` before marking the node, and the mid-loop path now marks `ABORTED_ERROR` and returns
  immediately instead of falling through to `EXPLORED`.
- `ui/crawl_view.py` — `_NODE_STATUS_TONE` maps `ABORTED_ERROR`/`ABORTED_DIALOG` to `danger` and
  `EXPLORED` to `positive`, so the screen tree's status pill is visually distinct rather than a
  uniform neutral gray regardless of what actually happened to the node.
- **New** `tests/test_explore_node_recovery.py` (split from `test_explore.py` at its 300-line
  cap): two tests, one per failure path, each monkeypatching `explore_node.return_to` to fail at
  the exact point the sweep forced it.
- `docs/FEATURES.jsonl` — F-036, the missing ledger row `autotester doctor` was flagging for T-124
  (unrelated to AT-113 itself, fixed because doctor caught it while verifying this unit).

## Sabotage — each branch reverted independently, real output pasted

**AT-117 (checker-found): the block that was here before was WRONG, and it was wrong in the way
that matters — I reconstructed it from memory instead of pasting a run.** It showed both tests
failing with `assert 'explored' == 'aborted_error'`. That is impossible for the entry path: its
pre-fix form *already* marked `ABORTED_ERROR`, so the defect there was the **missing issue**, not
the status, and the test fails on the `any(...)` issue assertion. The substantive claim held and
the checker reproduced it — but a transcript written from memory is not evidence, and it is
exactly the failure this manifest format exists to prevent. Re-run properly, one branch at a time:

```
$ SABOTAGE: entry path only -- issue-filing removed, status left as-is
E   assert False
E    +  where False = any(<generator object test_a_node_the_crawl_cannot_return_to_files_an_issue...>)
FAILED tests/test_explore_node_recovery.py::test_a_node_the_crawl_cannot_return_to_files_an_issue_and_is_marked_aborted
1 failed, 1 passed in 0.38s

$ SABOTAGE: mid-loop path only -- reverted to break + fall through to EXPLORED
E   AssertionError: assert 'explored' == 'aborted_error'
E     - aborted_error
E     + explored
FAILED tests/test_explore_node_recovery.py::test_a_node_lost_mid_exploration_is_marked_aborted_not_explored
1 failed, 1 passed in 0.41s

$ RESTORE
2 passed in 0.29s
```

Each branch fails **exactly one** test, and the one that defends it — which is a stronger result
than "both fail", because it proves the two tests are not redundant.
The second test needed `WritePolicy.ALLOW_WRITES` rather than the default `READ_ONLY`: under
READ_ONLY every candidate on the fixture's `/settings` node is denied or skipped, so `return_to`
is only ever called once (on entry) and the mid-loop path can never be exercised at all — a fact
found by running it, not by reading the code, after two failed attempts at the wrong write policy
and the wrong `url_template` string (host-included vs host-less; `node_from` templates host-less).

## Corrected in the same cycle, unprompted
`autotester doctor` flagged three things while I verified this unit, none of them the defect
itself: a stray `C:` directory at the repo root (my own `--junitxml` path was mangled by the shell,
same failure mode the cycle-2 checker hit and reported on itself), the new test file crossing the
300-line cap once the AT-113 tests were added, and T-124's missing ledger row. All three fixed
here rather than left for the next unit to trip over.

## How to verify (commands + expected)
- `docker compose exec -T autotester uv run pytest -q` → all pass, includes the 2 new tests
- `docker compose exec -T autotester uv run ruff check src tests scripts` → `All checks passed!`
- `docker compose exec -T autotester uv run autotester doctor` → `doctor: clean`
- `docker compose exec -T autotester uv run python scripts/explore_proof.py` → `11/11` —
  `explore_node.py` changed and must not regress B3/B5.
- Sabotage worth re-running: revert either branch in `visit_node` to its pre-fix form and confirm
  the matching test in `test_explore_node_recovery.py` fails.

## Not fixed here, deliberately
AT-108/AT-114 — the "cause was swallowed" pattern in `capture()`'s blind `except Exception` and
`_recover`'s last-ditch `pass` — is queued as its own sweep of every `except` in
`stages/explore*.py`, not folded into this unit, per the standing plan to treat that as a shape
rather than a location.

## Status: checked-PASS

Verdict: `qa/verdicts/at113-node-recovery-honesty.md` (**Cycle checked: 1**, PASS, 2/2 criteria,
6/6 unit claims independently reproduced). **AT-113 closes.** The checker read raw on-disk JSONL
with its own probe rather than running my tests, and confirmed the fix is *discriminating* rather
than a blanket downgrade: on the mid-loop path `/settings` is `aborted_error` while all four of
its siblings stay `explored`.

It also verified the claim I could most easily have been wrong about — that the mid-loop test
needs `ALLOW_WRITES` — by instrumenting the call counter: `return_to` fires **once** on
`/settings` under `READ_ONLY` and **three times** under `ALLOW_WRITES`. Under the default policy
that test would have passed vacuously.

**AT-117 (low) is the finding that matters and it is mine:** the sabotage transcript in this
manifest was reconstructed from memory rather than pasted from a run, and was internally
impossible. Corrected above with real output from two separate runs. The checker was right to file
it even though the underlying claim was true — the whole point of pasting output is that it was
not written by me.

**One correction back to the checker, verified on disk rather than assumed:** its closing note says
AT-093 (punctuation-separated logout labels, X6) is still open and must close before the explorer
meets a real product. `qa/issues.jsonl` records AT-093 as **`verified`** — it was fixed at T-143
and independently re-probed under three policies by the 2026-09-08 sweep. X6's gate on T-145 is
already satisfied on that axis.
