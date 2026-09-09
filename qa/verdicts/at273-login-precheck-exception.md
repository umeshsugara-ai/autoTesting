# Verdict — at273-login-precheck-exception

**Date:** 2026-09-09
**Checked by:** /checker (Mode A, standalone dispatch)
**Cycle checked:** 1
**Contract:** `qa/contracts/explore.md` (login bootstrap, X10)
**Commit:** `ad6259c`

## What I re-ran myself (live tree, `D:/autoTesting`)

```
$ uv run pytest tests/test_explore_login_bypass.py -q
....                                                                     [100%]
(4 passed)

$ uv run pytest -q
928 dot markers ('s' x2, rest '.'), no F, warnings summary only
(matches manifest's "924 passed, 2 skipped" plus the 4 new tests in this unit)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

## Independent sabotage-confirmation (own isolated extract)

`git archive HEAD | tar -x` into
`C:/Users/Lenovo/AppData/Local/Temp/claude/d--autoTesting/.../scratchpad/checker_extract`,
`uv sync` its own venv. Verified `autotester.stages.explore.__file__` resolved
inside the extract path before trusting any result.

Reverted `_already_past_login`'s two named-exception branches
(`except NavigationRefused as exc: ... / except Exception as exc: ...`) back to a
bare `except Exception: return False`, then ran
`tests/test_explore_login_bypass.py tests/test_explore.py tests/test_explore_blocked.py`
(25 tests total):

```
...F.....................                                                [100%]
FAILED tests/test_explore_login_bypass.py::test_a_transient_precheck_failure_is_named_not_swallowed
AssertionError: assert 'precheck also failed' in 'login case did not complete'
```

Exactly 1 failure — the named test, with the exact predicted assertion mismatch.
Restored the file from a saved copy (never `git checkout`); the restored file diffed
byte-identical to the pre-sabotage copy, and `git diff --stat` against the live tree
(outside the extract, never touched) showed no changes to `explore.py` — the sabotage
never left the isolated extract.

## Fallback-unchanged claim — own constructed case (item 3)

The manifest claims the "precheck also failed" cause only surfaces in
`stop_reason` when the login case *also* genuinely fails afterward — i.e. a
transient/spurious precheck exception followed by a normally-succeeding login
case should leave `crawl.status` healthy with no spurious noise. No existing test
covered this branch, so I wrote my own probe in the isolated extract
(`tests/test_at273_checker_probe.py`, not part of the maker's submission,
deleted after use): `_already_past_login`'s own `goto` raises
`RuntimeError("net::ERR_CONNECTION_RESET")` exactly once for the SIGNIN url;
`run_case`'s subsequent NAVIGATE+FILL then succeeds normally (fillable staged).

Result: **PASS.** The FILL side-effect (`(IDENTIFIER, "someone") in page.fills`)
confirms the case genuinely ran (not an always-skip regression), and
`crawl.status is CrawlStatus.COMPLETED`, `crawl.stop_reason == "frontier empty"`,
with `"precheck also failed" not in stop_reason`. The fallback is genuinely
unchanged — only the cause's visibility on the failure path changed, exactly as
claimed.

## Line cap / doctor / scope

- `run_crawl` (`src/autotester/stages/explore.py:248-296`) is 49 lines including
  its docstring — under the 50-line cap. `uv run autotester doctor` is clean, no
  new violation.
- `git diff ad6259c^ ad6259c --stat` touches exactly
  `src/autotester/stages/explore.py` (+32/-3) and
  `tests/test_explore_login_bypass.py` (+30) — no route, template, or rendered
  surface changed. Confirmed independently from the diff, not from the manifest's
  assertion: this unit is **not UI-touching**.

## Contract judgment

This unit does not itself carry a numbered X-criterion (it is issue-driven
hardening on top of X1/AT-226's login bootstrap, matching X10's discipline that
the explorer's only typing happens through the human-authored login case via
`run_case`). Judged against the explore.md contract as a whole:
- X1 (single-invention-site / one `run_case` call site inside `_bootstrap_login`) —
  unaffected; no new call site added.
- X10 (nothing is typed by the explorer itself) — unaffected; the fix only adds a
  diagnostic string field and an exception-naming branch, no `fill`/`select_option`/
  `upload` call anywhere in the diff.
- X11-style incremental-artifact discipline — unaffected; no new disk write path.
- No criterion is weakened; the change is strictly additive diagnostics with an
  unchanged fallback value (`False`), which I independently re-verified above.

`Issues addressed`: AT-273 (high) — verifiably fixed; ledger row flipped
`open → fixed` below.

## VERDICT

```
VERDICT: PASS
SCOREBOARD: 4/4 verify commands reproduced, 1/1 sabotage-defended assertion holds, 1/1 constructed fallback-unchanged case holds
FAILURES (if any): none
LIVE-BROWSER: not-applicable (src/autotester/stages/explore.py, tests/test_explore_login_bypass.py — no route/template/component/rendered-output changed)
ISSUES-WRITTEN: none (AT-273 flipped open -> fixed in qa/issues.jsonl)
EXPLANATION: Every manifest claim reproduced independently in an isolated git-archive extract with its own venv: the 4 named tests pass, the full suite (928 tests) is clean, ruff and doctor are clean, and sabotaging the two named-exception branches back to a bare except fails exactly the one predicted test with the exact predicted message. A self-constructed case (not in the maker's submission) confirms the fallback truly is unchanged: a transient precheck exception followed by a genuinely successful login case leaves status COMPLETED with no "precheck also failed" noise. run_crawl stays at 49/50 lines and the diff touches only explore.py + its test file, confirming the no-UI claim from the diff itself.
```
