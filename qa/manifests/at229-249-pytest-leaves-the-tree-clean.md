# Manifest — at229-249-pytest-leaves-the-tree-clean

**Unit:** AT-229 / AT-249 — does `uv run pytest` write into the repository working tree? Re-measured in a clean, isolated worktree
**Contract:** `qa/contracts/core-invariants.md` (C7: a check someone else can re-run must not mutate what it verifies)
**Goal task:** none (issue-driven measurement; no code changes)
**Date:** 2026-09-17
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-229 (medium, open → **withdraw proposed**) · AT-249 (medium, open → **confirmed**, close proposed)

## Why

- **AT-229** (t136-scorer cycle-2 checker) claimed that `uv run pytest` writes `projects/saucedemo/` and
  `qa/evidence/browser-*-checker/` into the tree. Its only evidence was mtimes during a suite run.
- **AT-249** (a later sweep) showed that evidence is misattributed: at that same minute a concurrent
  checker campaign onboarded `saucedemo` through the UI and `mkdir -p`'d its Mode D evidence directory, and
  the slug appears in no test. Its `expected` field says: *"Either the claim is re-verified against evidence
  that is actually attributable to pytest -- a clean-worktree run with nothing else writing -- or AT-229 is
  withdrawn."*

Nobody had run that measurement. This unit runs it. It changes no code: the maker does not flip ledger
status, so the ruling is the checker's.

## What changed

No source or test file. Added evidence only:

- `qa/evidence/at229-clean-worktree-suite/run.sh` — the exact script that was run.
- `qa/evidence/at229-clean-worktree-suite/suite-summary.txt` — the suite's summary line.
- `qa/evidence/at229-clean-worktree-suite/status-diff-summary.txt` — path counts before and after, by
  class.

## Method

1. `git worktree add --detach .work/wt-at229 HEAD` (HEAD = `d2f62ac`). This is a fresh checkout that
   shares no working tree with either maker loop, and no other process writes in it.
2. `git status --porcelain --ignored --untracked-files=all` → `before` (ignored files included, so even
   gitignored pollution would show).
3. `uv run pytest -p no:cacheprovider` in that worktree. `-p no:cacheprovider` keeps pytest's own
   `.pytest_cache` out, since that is a known tool artifact rather than the question.
4. The same `git status` → `after`, then diff.
5. `git worktree remove --force .work/wt-at229`.

## How to verify (commands + expected)

Re-run the method yourself on a fresh worktree of the current HEAD (the script is in the evidence
directory; adjust its two absolute paths):

- `git worktree add --detach <scratch> HEAD` → a clean checkout
- `git status --porcelain --ignored --untracked-files=all` before and after `uv run pytest -p no:cacheprovider`
- Expected: every new path is under `.venv/` (created by `uv run` itself) or is a `__pycache__`/`*.pyc`
  bytecode file. No tracked file is modified, and nothing else is created, not even gitignored.

## Actual outputs (from maker's own run)

```
$ tail -1 suite log
1413 passed, 2 skipped, 32 xfailed, 1 warning in 489.01s (0:08:09)

$ cat qa/evidence/at229-clean-worktree-suite/status-diff-summary.txt
before: 0 paths
after:  8614 paths
after, excluding .venv/ and __pycache__ bytecode: 0 paths
classes in after:
   8354 !! .venv
      9 !! scripts
    115 !! src
    136 !! tests
```

The `scripts`, `src` and `tests` entries are all `!!` (ignored), and none survives the bytecode filter:
they are `__pycache__` files. There are no `??` (untracked) and no ` M` (modified) entries at all. In
particular, no `projects/` and no `qa/evidence/` path was created, which are the two AT-229 named.

## Conclusion (for the checker to rule on)

- **AT-229 is not reproduced.** In a worktree where only pytest runs, the suite leaves the tree clean
  apart from the virtualenv and bytecode. The proposal is to withdraw it (`dismissed` / `wontfix`,
  checker's choice).
- **AT-249 is confirmed.** Its hypothesis, that the original evidence came from a concurrent session and
  not from pytest, is consistent with a clean measurement. Its second half ("concurrent maker-checker
  sessions in one worktree need isolation") is still true and is not closed by this unit.

## Capability coverage (each new claim -> its isolating falsification)

NO ISOLATING FALSIFICATION -- measurement artifact (no code changed); the slot-1 verdict is the only
discriminator: the clean-worktree `git status` diff above, re-runnable by the checker on the current
HEAD.

**Stated gap: nothing in the suite pins this property going forward.** The existing
`tests/test_cli_harness_safety.py::test_running_every_command_leaves_the_repository_untouched` covers
only the CLI surface. A whole-suite guard cannot live inside the suite it measures, so the measurement is
the evidence. If the checker wants a standing guard, it belongs in the sweep or the adapter's verify
chain, which is a contract decision.

## Live browser evidence

Not UI-touching — no surface changed. No source, template or route file is in this unit; it adds files
under `qa/evidence/` and this manifest.

## Known limits (disclosed, not claimed)

- **One run on one host (Windows).** A test that writes only on some platform, or only when a credential
  or network is present, would not show here. The run had no `.env`, because it is gitignored and was not
  copied into the worktree, so live-credential tests skipped or used fakes.
- **`-p no:cacheprovider` was used.** Without it pytest writes `.pytest_cache/`, which is gitignored
  tooling and is excluded from this question on purpose.
- **`.work/` is where the worktree lived.** It is gitignored in the main checkout, and the worktree was
  removed afterwards.

## Status: ready-for-check
