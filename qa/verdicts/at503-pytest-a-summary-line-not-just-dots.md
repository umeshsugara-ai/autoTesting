# Verdict — at503-pytest-a-summary-line-not-just-dots

**Cycle checked:** 1
**Date:** 2026-09-18
**Commit under check:** e15c1f1
**Checker:** fresh /checker subagent, bound to `d:/autoTesting`

## What I re-ran myself (never trusted the pasted logs)

- Re-derived the mechanism from scratch on `tests/test_ledger_checks.py` (19 tests), each run
  redirected to a file and read whole:
  - `uv run pytest tests/test_ledger_checks.py` (bare) → `...................  [100%]` +
    `19 passed in 0.63s`, exit 0. **Summary present.**
  - `uv run pytest -q tests/test_ledger_checks.py` → dots + `[100%]` only, **no summary**, exit 0.
  - `uv run pytest -qq tests/test_ledger_checks.py` → identical to the `-q` row, **no summary**,
    exit 0.
  - This matches the manifest's own table exactly. The unit's central premise holds in my own
    hands, not just the maker's.
- Confirmed `pyproject.toml:62` is the only config source of `-q` (no `pytest.ini`/`setup.cfg`/
  `tox.ini` in the repo).
- Additionally ran `uv run pytest -o addopts= tests/test_ledger_checks.py` (addopts cleared
  entirely, not just CLI `-q` omitted) — see Findings below.
- `uv run ruff check src tests scripts` → `All checks passed!`, exit 0.
- `uv run autotester doctor` → `doctor: clean`, exit 0.
- `git show e15c1f1 -- CLAUDE.md`: the diff is exactly 4 lines (1 removed, 3 added) inside the
  `## Commands` block only — no permissions, hooks, `.claude/settings.json`, secrets handling, or
  Lab-Protocol enforcement path touched.
- `git show --stat e15c1f1`: touches only `CLAUDE.md`, `qa/adapter.json`, the four evidence logs,
  `qa/feedback-inbox.md`, and the manifest itself — exactly the manifest's declared "What changed"
  file set. No deletion of any existing function/test/config key; no file touched outside that set.

## Judgement per the dispatch's five falsification points

1. **Re-derived the doubling myself** — confirmed above, identical result to the manifest's table.
2. **Is bare `uv run pytest` the right verify command?** Yes, with one caveat filed as a finding
   (AT-523): the manifest's stated reason for not touching `pyproject.toml`'s `addopts` includes an
   inaccurate claim — "a fully un-quieted pytest prints one line per test." I tested this directly
   (`-o addopts=`, clearing addopts entirely): output is still dots + `[100%]` + a few header lines,
   **not** one line per test (that needs `-v`, which nothing here proposes). This does not change the
   unit's decision — its other, independently sufficient reason (touching `addopts` would change
   every invocation in the tree, not just this one command) stands on its own and is correct — so
   it is a documentation-accuracy finding, not a functional defect, and does not fail the unit.
   `expect: exit 0` is unchanged and confirmed still true. No parser depends on the adapter's verify
   command's stdout format (checked: nothing in `src/`/`tests/`/`scripts/` parses
   `qa/adapter.json`'s `cmd` strings for their output shape, only their exit code).
3. **This is the checker's own verify command too** — confirmed via `qa/adapter.json`'s content:
   only the `cmd` string changed, `expect` unchanged. Future checkers running Mode A step 3 now get
   a readable summary line for free. Disclosure in the manifest's "Known limits" is accurate and
   complete.
4. **The partial fix and its residual** — folded the six affected `qa/contracts/*.md` Verify
   clauses myself (checker-owned surface, routine amendment — see below), and filed the remainder
   (`AGENTS.md`, `qa/loop.md`, two `CLAUDE.md` prose spots outside the Commands block, and
   `.goal/goal.json`'s per-file `cmd` rows) to the ledger as AT-521/AT-522, since those files are
   outside the checker's contract write-surface. Independently re-counted the `.goal/goal.json`
   claim: 43 of 50 `cmd` rows carry `-q` — matches the dispatch's own count exactly.
5. **No test added** — accepted the manifest's reasoning (the property under test is pytest's own
   `-q`/`addopts` combination semantics, not `autotester` code; asserting it in `tests/` would test
   a third-party library's CLI parsing). I do think a narrow, project-owned guard is worth
   suggesting — asserting `qa/adapter.json`'s verify `cmd` strings never stack a CLI `-q` on top of
   `pyproject.toml`'s own `addopts` — because that asserts this repo's own config consistency, not
   pytest's internals, sidestepping the manifest's objection. Filed as part of AT-523, not a
   blocker.

## Contract maintenance performed (checker-owned surface, routine gate)

Folded `qa/feedback-inbox.md`'s 2026-09-18 AT-503 entry: corrected the stale `uv run pytest -q` →
`uv run pytest` in the Verify clauses of `qa/contracts/core-invariants.md` (C7), `ui.md`,
`explore.md`, `living-ledger.md`, `browser-and-secrets.md` (both B1-B4 and B5-B9 clauses), and
`pathlynks-onboarding.md`. No criterion text weakened — same invariant (exit 0, real pasted output),
only the stale shell string corrected to match the fixed adapter command. Added one new
append-only amendment-log entry to `core-invariants.md` (2026-09-18) documenting the fold and
naming the residual filed to the ledger instead. This is a routine tightening/correction, not a
criticality-gated change (no goal-direction reversal, no safety/data invariant touched, nothing
irreversible enabled) — applied without a human gate per the contract-maintenance table.

## Ledger

- **AT-503** flipped `open → fixed` (this unit fixes it; a later re-check would move it to
  `verified`).
- **AT-521** (low, documentation) — filed: `CLAUDE.md` (two prose spots outside the Commands
  block), `AGENTS.md` (three lines), `qa/loop.md` (slot-1 Verify line) still name the doubled
  `uv run pytest -q`.
- **AT-522** (low, tooling) — filed: 43 of 50 per-file `cmd` rows in `.goal/goal.json` carry the
  same doubling.
- **AT-523** (low, documentation) — filed: the manifest's "one line per test" rationale is
  inaccurate (independently disproved), though it doesn't change the unit's correct decision; plus
  an optional regression-guard suggestion.

## Diff scope (4c)

No function/class/export/route/test/config key removed beyond the single intended `cmd` string
change. No file touched outside the manifest's declared "What changed" set. Clean.

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met, 1/1 invariants hold
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 2/2 claims independently re-derived (config/CLI-flag behaviour, no code
  mutation applicable — consistent with the manifest's disclosed no-test rationale; both rows
  reproduced in my own run, not read from the maker's logs)
LIVE-BROWSER: not-applicable (changed paths: qa/adapter.json, CLAUDE.md Commands block,
  qa/feedback-inbox.md, manifest/evidence — no src/, no UI surface)
ISSUES-WRITTEN: AT-503 (open→fixed), AT-521, AT-522, AT-523
EXPLANATION: The unit's central claim (pytest's -q is additive; CLI -q stacks on
  pyproject.toml's addopts="-q" to reach -qq and suppress the summary line) was independently
  re-derived on the same subset with identical results, and the fix (qa/adapter.json's verify cmd
  → bare `uv run pytest`) is narrow, correctly scoped, and confirmed live (ruff/doctor green,
  CLAUDE.md diff confined to the Commands block). Folded the same correction into six
  qa/contracts/*.md Verify clauses (checker-owned, routine). Filed the disclosed residual
  (AGENTS.md, qa/loop.md, two CLAUDE.md prose spots, ~43 .goal/goal.json cmd rows) to the ledger
  as AT-521/AT-522, plus one low finding (AT-523) on an inaccurate secondary rationale in the
  manifest's Decision section that does not change the unit's correct outcome.
```
