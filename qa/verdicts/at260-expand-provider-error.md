# Verdict — at260-expand-provider-error

**Date:** 2026-09-09
**Cycle checked:** 1
**Checker mode:** Mode A (bound to `D:/autoTesting`)
**Commit checked:** `945cf56`

## What I re-ran myself

Isolated extract: `git archive 945cf56` into a scratch dir, own `uv sync` venv,
`cli.__file__` confirmed resolving inside the extract before trusting anything.

1. `uv run pytest tests/test_expand_cli.py -v` → 9 passed (matches manifest).
2. `uv run pytest` → 0 failures (943 `.`/`s` characters, no `F`/`E`; exit 0 —
   matches manifest's "929 passed, 2 skipped").
3. `uv run ruff check src tests scripts` → `All checks passed!`
4. `uv run autotester doctor` → `doctor: clean`

## Sabotage confirmation (independent, own extract)

Removed the entire new `except ProviderError as exc: ...` block from
`src/autotester/cli.py::expand_cases` by hand (not `git checkout`). Re-ran
`tests/test_expand_cli.py -v`: **exactly 1 failure**,
`test_a_provider_failure_mid_expand_is_a_clean_refusal_not_a_traceback`, with
`AssertionError: assert 'no cases persisted' in ''`. All 8 other tests in the
file still passed. Restored the saved original, re-ran (9 passed), and
confirmed the live tree (`D:/autoTesting/src/autotester/cli.py`) was never
touched (`grep -c "no cases persisted"` → 1, unchanged).

## The CliRunner-empty-output discrepancy — investigated, not just repeated

The manifest is right that `result.output` comes back `''` under
`typer.testing.CliRunner` on the sabotaged build rather than containing the
literal string `"Traceback"` — I reproduced that exact empty string myself in
the sabotage run above. Judged it a non-vacuous guard for two reasons: (1) the
test's actual assertion is `"no cases persisted" in result.output`, which is
false in exactly the buggy case (empty string) and true in exactly the fixed
case — it is not vacuously true either way; (2) I did not stop at CliRunner. I
added a throwaway, extract-only provider (`providers/_raiser.py`, never
touching the live tree, deleted with the extract) that always raises
`ProviderError`, seeded a real project + APPROVED FlowSpec on disk, and ran
`uv run autotester expand demo --provider checker-raiser` as a genuine
subprocess (not CliRunner). Result: exit 1, stdout carried exactly
`demo: model call failed, no cases persisted — checker-probe: synthetic
mid-call failure (role=agent)`, **stderr was completely empty** (no raw
traceback anywhere, not even to stderr), and `projects/demo/` held only
`flowspec.json`/`project.json` — no `cases.jsonl`. The fix holds identically
outside the test harness. No real gap: the CliRunner quirk is cosmetic to the
test's internals, not a hole in the shipped behavior.

## X1 (review gate) and X4 (no-fire on refusal)

- **X1** — `stages/expand.py::expand` line 124 calls `require_reviewed(spec)`
  before any flow loop runs; unaffected by this unit (pre-existing), confirmed
  by reading the file directly. Not what AT-260 touched, but still true.
- **X4 / manifest's own added claim** (`expand`'s all-or-nothing, partial
  results discarded by construction) — confirmed by reading
  `stages/expand.py::expand` (lines 120-128): it builds a plain in-memory
  `list[Case]` via `cases.extend(expand_flow(...))` inside a normal `for`
  loop and only `return`s once every flow has succeeded. A `ProviderError`
  raised inside `expand_flow` propagates before the function returns
  anything, so `cli.py`'s `for case in cases: store_.add_case(case)` is
  structurally unreachable on failure — not merely untested, unreachable by
  construction. Matches the manifest's claim exactly.

## UI-touching

Confirmed via `git show --stat 945cf56`: only `src/autotester/cli.py` and
`tests/test_expand_cli.py` changed. No UI/route/template files. Mode D
(live-browser) correctly not invoked — manifest's "not UI-touching" claim
holds.

## Result

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met (X1, X4), 0/0 additional invariants checked (none named beyond X1/X4)
FAILURES (if any):
- none
LIVE-BROWSER: not-applicable (src/autotester/cli.py, tests/test_expand_cli.py — CLI-only, no UI surface changed)
ISSUES-WRITTEN: none (AT-260 marked fixed in qa/issues.jsonl by this verdict's committer step)
EXPLANATION: All four verify commands reproduced independently in an isolated git-archive extract with __file__ confirmed
inside it. Sabotage removed the fix and failed exactly the one named test, restored cleanly, live tree untouched. The
manifest's CliRunner-empty-output discrepancy was independently investigated with a real subprocess invocation
(uv run autotester expand demo --provider checker-raiser against a throwaway extract-only raising provider) — exit 1,
clean one-line stdout message, empty stderr, no cases.jsonl written, confirming the fix holds outside the test harness too.
expand()'s all-or-nothing behavior confirmed by reading stages/expand.py directly. Diff confirmed CLI-only via git show --stat.
```

---

## INDEPENDENT CONCURRENT CHECK

**Date:** 2026-09-09
**Cycle checked:** 1
**Checker mode:** Mode A (bound to `D:/autoTesting`)
**Commit checked:** `945cf56`

This check began before the primary verdict appeared and did not read it until after completing its
own commands, code inspection, and sabotage. Both checks agree on PASS. The only presentational
difference is scoreboard scope: this check records all six criteria in `expand.md` and all nine
project-wide core invariants, while the primary block counts only the two criteria named by the unit.

### Evidence independently produced

- `uv run pytest tests/test_expand_cli.py -v` → 9 passed in 1.61s.
- `uv run pytest` → 929 passed, 2 skipped, 1 warning in 93.72s.
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`.
- Read `stages/expand.py`: review precedes generation; HAPPY is copied once from the observed flow;
  applicability is deterministic for input/auth and model-judged for eight universal classes; empty
  expansions are dropped; and both expansion functions materialize lists before returning.
- Read `prompts/expand_case_v1.md`: wrong credentials must be obviously fake, while genuine secret
  placeholders remain unchanged.
- Read `cli.py::expand_cases`: `ProviderError` is caught before the persistence loop, emits a clean
  one-line refusal, and exits 1.
- `git show --stat 945cf56` confirms only `src/autotester/cli.py` and
  `tests/test_expand_cli.py` changed, so Mode D is not applicable.

### Independent C7 sabotage

Extracted `945cf56` with `git archive` under `.work`, removed only the new `except ProviderError`
block, and asserted before execution that the live file contained the anchor once, the mutant zero
times, and their bytes differed. `autotester.cli.__file__` resolved inside the extract. The named
regression test reported `FAILED`; a direct `CliRunner` probe against the same mutant reproduced
`EXIT 1`, `OUTPUT ''`, `EXCEPTION ProviderError truncated`, and `CASES 0`. The live tree was never
modified, and the temporary archive/probe files were removed afterward.

AT-260 was already moved `open → fixed` by the concurrent primary checker while this run was in
progress, so this check did not race or advance it to `verified`. No new issue was found.

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met, 9/9 invariants hold
LIVE-BROWSER: not-applicable (src/autotester/cli.py, tests/test_expand_cli.py)
ISSUES-WRITTEN: none (AT-260 already flipped open -> fixed by concurrent primary check)
EXPLANATION: All four manifest commands pass independently, and an archived mutant reproduces the uncaught ProviderError with empty CLI output while retaining zero persisted cases. The shipped handler converts that failure into the required clean refusal, and the materialized-list boundary prevents partial persistence; the CLI-only changed paths do not trigger Mode D.
```
