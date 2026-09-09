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
