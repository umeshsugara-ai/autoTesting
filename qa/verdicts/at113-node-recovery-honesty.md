# Verdict — at113-node-recovery-honesty

**Date:** 2026-09-08
**Unit commit:** `ea7e25d` (tree checked at `dd60161`; `src/`, `tests/`, `scripts/` byte-identical since)
**Contract:** `qa/contracts/explore.md` — X11, X13
**Cycle checked:** 1
**Checked by:** /checker (fresh subagent, Mode A), bound to `D:/autoTesting`
**Environment note:** the Docker daemon was DOWN, so every `docker compose exec -T autotester …`
command in the manifest was re-run **natively** (`uv run …`) instead. Host reports **584 passed,
2 skipped**; the container reports 585/1. Verified, not assumed: `uv run pytest -rs` names the two
skips as `tests/test_db.py:93` (live Mongo opt-in) and `tests/test_ui.py:163` ("POSIX permission
bits don't apply on Windows"). The second is the Windows-only skip; same 586 collected, no missing
test. The delta is fully explained.

**This is a retry.** Two earlier checkers on this unit died mid-run (ENOTFOUND; account rate
limit) and wrote nothing. This check started from zero evidence; nothing from those runs was used.

---

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met (X11, X13), 6/6 unit claims independently reproduced
FAILURES (if any): none
ISSUES-WRITTEN: AT-113 open -> fixed; AT-117 (new, low)
EXPLANATION: Both failure paths were forced with the checker's own probe reading the raw on-disk
JSONL, and both now land aborted_error with a NAVIGATION issue and a non-zero crawl.issues. Each
branch, reverted independently in a git-archive scratch copy, fails its own matching test. The
maker's write-policy explanation is exactly right (measured: return_to fires once on /settings
under READ_ONLY, three times under ALLOW_WRITES) and the pill tone is distinct on a really
rendered page. One low-severity finding (AT-117): the manifest's pasted sabotage transcript shows
an assertion message that the entry-path sabotage cannot actually produce — the claim is true, the
quoted output is reconstructed rather than run.
```

---

## What I re-ran myself

| Command | Result |
|---|---|
| `uv run pytest` | **584 passed, 2 skipped**, 1 warning (74s) — both skips explained above |
| `uv run pytest -rs` | skip reasons: `test_db.py:93` live-Mongo opt-in · `test_ui.py:163` POSIX bits on Windows |
| `uv run ruff check src tests scripts` | `All checks passed!` (exit 0) |
| `uv run autotester doctor` | `doctor: clean` (exit 0) |
| `uv run python scripts/explore_proof.py` | **11/11 invariants held** — B5's approval gate still first (`no approval => nothing runs, nothing written`, CLI exit 2, no crawl dir, no browser profile) |
| `wc -l` on the touched files | `explore_node.py` 219 · `crawl_view.py` 179 · `test_explore_node_recovery.py` 89 — all under the 300 cap |
| `ls ./C:` | no stray `C:` directory at the repo root |
| `git status --porcelain src tests scripts` | empty (clean, before and after this check) |

No `git stash` / `checkout` / `restore` was used at any point (AT-101). All sabotage ran in a
`git archive HEAD` extract under the session scratchpad, PYTHONPATH-pinned to that copy.

---

## 1. The original defect, reproduced and both paths confirmed fixed

I wrote my own probe rather than reading the maker's tests: it runs the real `run_crawl` against
`tests/crawl_fake`, monkeypatches `explore_node.return_to` to fail at the exact point, and then
**reads `nodes.jsonl`, `issues.jsonl` and `crawl.json` off disk** — so the evidence is the
persisted artifact X11 talks about, not an in-memory object.

**(a) Entry failure — `return_to` fails before any candidate is tried** (`READ_ONLY`):

```
disk node statuses:            ['aborted_error']
aborted_error count:           1        explored count: 0
navigation issues on disk:     1  -> "could not return to this screen before exploring it — abandoned unexplored"
crawl.issues (envelope, disk): 1        status: completed   stop: frontier empty
```

**(b) Mid-loop failure — `return_to` fails after at least one candidate was tried**
(`ALLOW_WRITES`, failure scoped to `/settings`):

```
disk node statuses:            ['aborted_error', 'explored', 'explored', 'explored', 'explored']
aborted_error count:           1        explored count: 4
navigation issues on disk:     2  -> "off-domain link refused: External"
                                  -> "lost this screen mid-exploration — remaining controls not tried"
crawl.issues (envelope, disk): 2        status: completed   stop: frontier empty
```

Both paths satisfy all three requirements: on-disk status is `aborted_error` (never `explored`),
a `CrawlIssue` of `kind=navigation` is filed, and `crawl.issues >= 1`. The mid-loop case is the
sharper proof — the lost node is `aborted_error` while its four healthy siblings stay `explored`,
so the fix is discriminating, not a blanket downgrade. This is the X11 claim precisely: *a node's
final status must reach disk*, and it now reaches disk **truthfully**.

Note on the sweep's original symptom: the crawl still ends `status=completed` /
`stop_reason='frontier empty'`. That is correct and not a residual defect — the frontier genuinely
did empty; what was broken was that `issues=0` and the node looked explored. Both are now false.

## 2. Sabotage — each branch, reverted independently, fails its own test

Scratch copy from `git archive HEAD`; the live tree was never modified.

| Sabotage | Result |
|---|---|
| baseline (unmodified scratch copy) | `2 passed` |
| **A** — entry branch back to pre-fix (`_mark(ABORTED_ERROR); return`, no `add_issue`) | `1 failed, 1 passed` — `test_a_node_the_crawl_cannot_return_to_files_an_issue_and_is_marked_aborted` fails at line 49 on `assert any("could not return" in i.detail for i in issues)` |
| **B** — mid-loop branch back to pre-fix (`break` instead of issue + `ABORTED_ERROR` + `return`) | `1 failed, 1 passed` — `test_a_node_lost_mid_exploration_is_marked_aborted_not_explored` fails with `- aborted_error / + explored` |
| restored | `2 passed` |

Each sabotage fails **exactly one** test, and the one that defends it. Neither test is decorative,
and neither is a duplicate of the other. This is what X13's "the gate must be load-bearing"
discipline asks for, applied to X11's status-honesty claim.

## 3. The maker's write-policy claim — independently measured, and correct

The manifest says the mid-loop test needs `ALLOW_WRITES` because under `READ_ONLY` every candidate
on `/settings` is denied or skipped, so `return_to` fires only once and the second path cannot be
exercised. I instrumented `return_to` with a per-node call counter and ran a clean crawl at each
policy:

```
read_only    return_to calls per node: {'/': 3, '/students': 3, '/settings': 1, '/students/{id}': 2}
allow_writes return_to calls per node: {'/': 3, '/students': 3, '/settings': 3, '/students/{id}': 2,
                                        '/deleted': 1, '/saved': 1}
```

Exactly one call on `/settings` under `READ_ONLY`, three under `ALLOW_WRITES`. The claim holds
literally, and the test therefore does test what it says it tests — under the default policy it
would have passed vacuously. The maker's honesty about how it found this (by running it, after two
wrong guesses) is worth more than the fact itself.

## 4. The visual fix — on a really rendered page, not the dict

I ran a crawl with a genuinely aborted `/settings` node, passed the real nodes and edges through
`crawl_view.screen_tree`, and grepped the emitted HTML for the badge classes:

```
rendered aborted_error   -> badge classes ['badge-fail'] (x1)
rendered explored        -> badge classes ['badge-pass'] (x4)
distinct? True
```

The pill tone is genuinely different on the page a human reads, not merely present in
`_NODE_STATUS_TONE`. `ABORTED_DIALOG` maps to the same `danger` tone; any status not in the dict
falls back to `neutral`, which is the correct conservative default.

## 5. Regressions

`explore_node.py` and `crawl_view.py` both changed, and both are load-bearing for the explore
stage. `scripts/explore_proof.py` is **11/11** (counted line by line, not from a summary — `-q`
suppresses it in this repo), including B5's approval gate as the first invariant and X6's
destructive-control denials. Full suite 584/2 with the delta explained. No file crossed the
300-line cap. `git status --porcelain src tests scripts` is empty.

## 6. On the bundling — acceptable, with a note

Three things rode along with the AT-113 fix:

- **the stray `C:` root directory** — untracked junk from a mangled `--junitxml` path; it never
  appeared in the commit at all (the diff stat has no such file), so this was cleanup of the
  working tree, not a code change. Zero risk.
- **`docs/FEATURES.jsonl` F-036** — one appended line for T-124, which `autotester doctor` was
  flagging. The alternative was to leave `doctor` dirty and check this unit against a failing
  gate, or to make a one-line commit to clear it first. The row cites T-124's own
  `qa/verdicts/t124-consent-gates.md`, so its provenance is not muddied by the vehicle that
  carried it.
- **the test-file split** at the 300-line cap — forced by `doctor`, not a choice.

All three are doctor-driven, small, and reviewable at a glance; separating them would have cost
more ceremony than it bought. Judged **reasonable**. The line I would hold: this stays acceptable
because each was mechanically forced by a gate the unit had to pass. A behavioural change to
another feature bundled the same way would not be.

## 7. The one finding — AT-117 (low)

The manifest's sabotage block (lines 43-51) shows **both** tests failing with
`AssertionError: assert 'explored' == 'aborted_error'`. That cannot be what the entry-path
sabotage produces: the pre-fix entry path already marked `ABORTED_ERROR` (its bug was the *missing
issue*, not the status), so reverting it fails on the `issues` assertion at line 49, which is what
I measured. Only the mid-loop sabotage yields the quoted message.

The substantive claim — each revert fails its matching test — is **true**, and I reproduced it
independently, which is why this is a low-severity ledger note rather than a FAIL. But a manifest
is evidence, and evidence is pasted from a run, never reconstructed from memory. Filed as
**AT-117**.

## Contract judgement

- **X11 — artifacts incremental, human-readable, survive a crash: MET.** X11's own words are that
  a node's final status must reach disk and that a status transition requires `update_node`.
  `_mark` does exactly that, and I confirmed the transition on the persisted `nodes.jsonl` for both
  failure paths. Before this unit the on-disk record was *present but false* for the mid-loop path,
  which is the worse half of the same guarantee: a graph that loads and lies is not better than one
  that fails to load. The crash-scope caveat in X11 (a torn line during a single append is not
  covered) is untouched by this unit and not re-litigated here.
- **X13 — a crawl proposes screens, never approves them: MET, and materially strengthened.**
  `explore_merge.py` is byte-unchanged, so the DRAFT reset and the never-rewrite guarantee are
  intact. The AT-113 relevance is upstream of the merge: `merge_screens` consumes
  `store.list_nodes(crawl_id)` with no status filter, so an unexplored node used to enter the
  FlowSpec as an ordinary screen with no actions, indistinguishable from a genuine leaf. The
  proposal was honest about being a proposal but dishonest about what it had seen. A human now has
  a filed navigation issue, a non-zero `crawl.issues`, and a red pill in the screen tree before
  they approve anything.

**Ledger:** `AT-113` `open -> fixed` with the reproduction recorded (`verified` awaits a later
re-check, per the ledger's own rules). `AT-117` opened, low. No goal task matches this unit
(issue-fix unit; it gates T-145), so no `/goal` close was performed.

**Not judged here (correctly excluded by the maker):** AT-108/AT-114, the swallowed-cause pattern
in `capture()`'s blind `except Exception` and `_recover`'s `pass`. Both are visible in the code I
read and both are real, but they are queued as their own shape-level sweep of every `except` in
`stages/explore*.py`. Folding them in here would have been scope creep on a unit that gates T-145.
