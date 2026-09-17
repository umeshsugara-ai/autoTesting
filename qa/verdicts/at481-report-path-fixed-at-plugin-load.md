# Verdict — at481-report-path-fixed-at-plugin-load

**Date:** 2026-09-17
**Cycle checked:** 1
**Mode:** A (unit check)
**Checker root:** D:/autoTesting (bound)
**Unit commit:** 627bd8b (base 03cc8a9)

## What I re-ran myself

- `uv run pytest -q tests/test_mutation_check.py tests/test_mutation_check_judgement.py tests/test_mutation_sandbox.py`
  → `.....................................` **37 passed**, exit 0. Matches manifest.
- `uv run ruff check src tests scripts` → `All checks passed!`. Matches manifest.
- `uv run autotester doctor` → `doctor: clean`. Matches manifest.
- `uv run python scripts/mutation_check.py qa/evidence/at481-report-path-fixed-at-plugin-load/mutations.json`
  → `KILLED  AT-481 reopens: the report path is read from the environment at session end again
  (pytest exit 1)` naming both `[reassigned]` and `[removed]` as `actually failed`, `1/1 mutations
  killed`, exit 0. Matches manifest exactly (mutation_check.py sandboxes this run itself, outside
  the bound tree, per its own design).

## Diff scope (step 4c)

`git show --stat 627bd8b`: 5 files — `scripts/mutation_check.py` (+3/-1 net, single hunk),
`tests/test_mutation_check.py` (+16, one new parametrised test), the unit's own
`qa/manifests/at481-report-path-fixed-at-plugin-load.md`, and its own
`qa/evidence/at481-report-path-fixed-at-plugin-load/{mutations.json,mutations.out}`. All five are
inside the manifest's "What changed" + its own evidence dir. No function/class/test/route/config
key was deleted or renamed; no file outside the declared set was touched. (`git diff 03cc8a9 627bd8b
--stat` additionally shows `qa/.last-tick`, `qa/issues.jsonl`, `qa/token-ledger.jsonl`,
`qa/QUEUE.md`, and the at468 verdict — all of those land in the two intervening commits `2e4d9b0`
and `c8be82b`, not in 627bd8b itself; confirmed by the isolated `git show --stat 627bd8b` above.)
Clean — no finding.

## Capability coverage (step 4b) — reproduced by ME, in a throwaway copy

Threw away `git archive HEAD` into a scratch dir outside the bound root
(`…/scratchpad/at481-row1`), ran pytest against that copy with the repo's own venv
(`D:/autoTesting/.venv/Scripts/python.exe -m pytest`), never touching the bound tree.

| capability | check | before (copy, unedited) | falsifying edit applied (single hunk, `scripts/mutation_check.py`, in the COPY only) | after |
|---|---|---|---|---|
| a test that reassigns or removes `MUTATION_REPORT` cannot redirect or break the report | `test_a_test_that_touches_the_report_variable_cannot_hide_a_kill[reassigned,removed]` | **GREEN** — `..` (2 passed) | `with open(_REPORT, ...)` → `with open(os.environ["MUTATION_REPORT"], ...)` (exact manifest cell) | **RED**, right reason — `[reassigned]`: `assert result["killed"] is True` fails on `killed: False` (the hidden-kill defect, reproduced live); `[removed]`: `MutationError: baseline is NOT green (pytest exit 1)` from a `KeyError: 'MUTATION_REPORT'` raised inside `pytest_sessionfinish` (the refuse-to-run defect, reproduced live). `-k` selection shows `2 failed, 19 deselected` — nothing else in the suite reddened, so the edit isolates exactly the claimed capability, not a broken import. |

Row VERIFIED — 1/1.

## Ledger

AT-481 (low): claimed `open → fixed`. Verified — the capability-coverage reproduction above is
independent, direct evidence the fix closes the defect described in AT-481's `evidence`/`expected`
fields (same two failure shapes: hidden kill via reassignment, refusal via KeyError on removal).
Flipped `qa/issues.jsonl` line for AT-481 to `"status": "fixed", "fixed_date": "2026-09-17"` (a
later re-check would move it to `verified`, per protocol — not done by the same checker run that
just fixed it).

## Known limits (manifest's disclosure, judged)

Both disclosed limits are real and correctly out-of-scope: (1) a conftest/sitecustomize that runs
before `-p` plugin import is a different attack surface than "a test under measurement," and (2) a
test writing the report file directly is the same trust boundary as any test deleting files —
neither is what AT-481 named. No new finding raised from these.

## Not UI-touching

Changed paths: `scripts/mutation_check.py`, `tests/test_mutation_check.py`. No UI surface, direct
or indirect (no retrieval/ranking/render path touched). Mode D not applicable.

## Not external-data-collection

Tooling fix to the mutation-check harness itself; no scope/source claim in this manifest. Step 5c
not applicable.

## Scoreboard

Contract-wide (`core-invariants.md`, C-numbered, no separate I-series):
- **C7** (verification independent / mutation instrument's verdict is the tests', not
  redirectable) — MET, primary criterion, evidenced above.
- **C2** (readable — file/function size, docstrings) — MET (`doctor: clean`).
- **C3** (one concept one place / anti-drift, no new files) — MET (`doctor: clean`; no new files
  introduced).
- **C4** (repo root stays clean) — MET (`doctor: clean`).
- **C10** (unit's commit carries only its own paths) — MET (`git show --stat 627bd8b`, above).
- C1, C5, C6, C8, C9 — not applicable (no schema/secret/artifact/provider/`.goal` control-value
  change in this unit); per contract's no-fire list this is not charged.

5/5 applicable criteria met, 0 violations.

```
VERDICT: PASS
SCOREBOARD: 5/5 applicable criteria met (C2, C3, C4, C7, C10), 0 invariants violated
FAILURES (if any): none
CAPABILITY-COVERAGE: 1/1 rows reproduced
LIVE-BROWSER: not-applicable (scripts/mutation_check.py, tests/test_mutation_check.py — no UI surface)
ISSUES-WRITTEN: none (AT-481 flipped open -> fixed, no new issues)
EXPLANATION: Re-ran all four verify commands myself and every output matched the manifest exactly, including the mutation harness's own 1/1-killed run. Independently reproduced the manifest's single capability row in a throwaway copy outside the bound tree (green before, red after, for the exact two failure shapes AT-481 named — hidden kill via reassignment, refusal via KeyError on removal — with nothing else in the suite reddening). Diff scope for commit 627bd8b is exactly the manifest's "What changed" plus its own evidence/manifest files; no deletions or out-of-scope files. Not UI-touching, not external-data-collection.
```
