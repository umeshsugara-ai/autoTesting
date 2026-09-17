# Verdict — at229-249-pytest-leaves-the-tree-clean

**Cycle checked:** 1
**Date:** 2026-09-17
**Contract:** qa/contracts/core-invariants.md (C7)
**Manifest:** qa/manifests/at229-249-pytest-leaves-the-tree-clean.md

## What I re-ran (independently, not trusting the pasted output)

The manifest's method, reproduced from scratch in my own fresh worktree, never the maker's:

1. `git worktree add --detach .work/checker-at229-249 HEAD` at HEAD (`b4779d7`, one commit ahead of
   the manifest's cited `d2f62ac` — only a `qa/.last-tick` stamp between them, immaterial).
2. `git status --porcelain --ignored --untracked-files=all` → 0 paths (before).
3. `uv run pytest -p no:cacheprovider` → exit 0 (all non-skip/xfail tests passed; pytest's own
   final one-line summary was dropped from the captured log by an apparent buffering quirk under
   `uv run` on this host, but the exit code and the full pass/fail dot-stream are conclusive: no
   `F` anywhere, no error section).
4. `git status --porcelain --ignored --untracked-files=all` → 8614 paths (after). Breakdown by top
   directory: `.venv` 8354, `tests` 136, `src` 115, `scripts` 9 — matching the manifest's numbers
   exactly. All 8614 are `!!` (ignored); zero `??` (untracked-and-not-ignored); zero ` M` (modified).
   After excluding `.venv/` and `__pycache__`/`*.pyc`, **0 paths remain**. Explicit greps for
   `projects/` and `qa/evidence/` — the two paths AT-229 named — both return 0.
5. `git worktree remove --force .work/checker-at229-249`.

**Additional run I performed beyond the manifest's method**, to close the disclosed limit about
live-credential tests being untested without `.env`: copied the repo-root `.env` into the same
worktree (values never read or printed) and re-ran `uv run pytest -q` **without**
`-p no:cacheprovider`. Exit 0. Diff added only `.pytest_cache/` (4 entries — expected, gitignored
tool output, correctly excluded from the question by the manifest) and the `.env` file itself
(which I placed there, not something the suite created). Still zero paths under `projects/` or
`qa/evidence/`. This confirms the property holds even with credentials present and pytest's cache
enabled, which the manifest itself had not tested.

## Ruling

- **AT-229 — does not reproduce.** In a worktree where nothing else is writing, the full suite
  (twice, under two different pytest configurations) leaves the tree clean apart from `.venv/`
  and bytecode. Ledger: **AT-229 → `wontfix`** (not `open`), with the re-measurement recorded on
  the issue.
- **AT-249 — confirmed.** The independent re-measurement is consistent with AT-249's diagnosis
  that AT-229's original evidence (mtimes) was produced by a concurrent checker campaign
  onboarding `saucedemo` and `mkdir -p`'ing Mode D evidence in the same worktree, not by pytest.
  Ledger: **AT-249 → `verified`**. Its second half ("concurrent maker-checker sessions in one
  worktree need isolation") is not re-litigated here — noted on the issue that current practice
  already runs loops in separate `git worktree`s (e.g. `.work/t161-primary-4c09990`, observed live
  during this check), but no criterion pins that as a rule; left open as a smaller residual, not
  re-opened as AT-249's main claim.

## Standing guard

Filed **AT-482** (low): the property this unit measured has no re-runnable instrument going
forward — `tests/test_cli_harness_safety.py::test_running_every_command_leaves_the_repository_
untouched` covers only the CLI surface, and a whole-suite guard structurally cannot live inside
the suite it measures (the manifest says this itself). This is a proposal for the sweep/contract
to weigh, not a criterion change and not a blocker on this unit's ruling.

## Capability coverage

Not applicable — no code changed, no test added or rewritten. The manifest correctly states this
(measurement-only unit; C7's mutation duty does not apply). The slot-1-equivalent instrument here
is the clean-worktree `git status` diff, which I reproduced myself rather than the maker's.

## Known limits carried forward

- Single host (Windows), single point in time. A test that writes conditionally (only under a
  different OS, only under CI, only when some other env var is set) would not show in either of my
  two runs any more than in the manifest's one run.
- `.pytest_cache/` and `.venv/` are deliberately excluded from the question, per the manifest's
  own scoping and C7's intent (tool artifacts, not suite-under-test behaviour).

VERDICT: PASS
SCOREBOARD: 2/2 criteria met, 1/1 invariants hold
FAILURES (if any): none
CAPABILITY-COVERAGE: not-applicable (measurement-only unit, no code/test change)
LIVE-BROWSER: not-applicable (no UI/route/template file in this unit's changed paths — evidence
files under qa/evidence/ and this manifest only)
ISSUES-WRITTEN: AT-482 (low, standing-guard proposal)
EXPLANATION: Independently reproduced the manifest's clean-worktree measurement twice (with and
without pytest cache, and with a real .env present) and got the identical result — no writes
outside .venv/bytecode/pytest-cache, specifically none under projects/ or qa/evidence/. AT-229 is
ruled unreproduced (wontfix) and AT-249 confirmed (verified); a low-severity gap is filed for the
missing standing guard rather than blocking this unit on it.
