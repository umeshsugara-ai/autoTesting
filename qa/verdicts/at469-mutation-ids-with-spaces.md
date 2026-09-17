# Verdict — at469-mutation-ids-with-spaces

**Date:** 2026-09-17
**Checker:** /checker Mode A (fresh subagent, bound to `d:/autoTesting`)
**Manifest:** `qa/manifests/at469-mutation-ids-with-spaces.md` (Fix cycle: 1)
**Cycle checked: 1**
**Unit commit:** f7e83cd (HEAD eb909eb only adds `qa/.last-tick`; `scripts/mutation_check.py` and `tests/test_mutation_check.py` clean against HEAD)

```
VERDICT: FAIL
SCOREBOARD: 0/1 criteria met (C7 attribution clause), invariants otherwise hold
FAILURES (if any):
- [C7] sev: medium · the AT-469 fix's "longest known nodeid wins" rule creates a FALSE KILLED that the pre-fix instrument did not have: a failure of nodeid A whose message starts with the rest of a collected sibling B = A + " - " + ... is attributed to B, which passed · treat a FAILED line matched by >1 collected nodeid as ambiguous (attribute to none, fail closed) or read failures from a structured source (--junitxml / a report plugin) instead of the short summary; add a test where the SHORTER nodeid is the one that failed · issue: AT-473
CAPABILITY-COVERAGE: 4/4 rows reproduced
LIVE-BROWSER: not-applicable (scripts/mutation_check.py, tests/test_mutation_check.py, qa/evidence/at469-*/, qa/manifests/at469-* — a verification CLI and its tests; confirmed from `git show f7e83cd --stat`)
ISSUES-WRITTEN: AT-473
EXPLANATION: The spaced-id defect itself is fixed and every row of the capability table dies for the right assertion in a throwaway copy, but the gate's worst failure direction was attacked as asked and it broke: a real pytest run in which only test_amb[a] failed was reported KILLED for test_amb[a] - Failed: boom] (which passed) and SURVIVED for test_amb[a]. The pre-fix instrument got both right, the unit's own test pins "longest wins" as correct for exactly this shape, and Known limits claims errors only toward SURVIVED — so the regression is undisclosed. The reachable shape needs an id containing "] - <message text>", so it is contrived, hence medium not high; AT-469 stays open until the fix is fail-closed.
```

## What I re-ran (my own runs, not the manifest's paste)

| command | result |
|---|---|
| `uv run pytest tests/test_mutation_check.py tests/test_mutation_sandbox.py` | `22 passed in 70.91s` — matches |
| `uv run ruff check src tests scripts` | `All checks passed!` — matches |
| `uv run autotester doctor` | `doctor: clean` — matches |
| `uv run python scripts/mutation_check.py qa/evidence/at469-mutation-ids-with-spaces/mutations.json` | `4/4 mutations killed` — matches |
| `uv run pytest` (full) | 5 FAILED, none in this unit: 4 in `tests/test_crawl_coverage.py` (untracked, the other maker loop's mid-edit — `TypeError: compute_coverage() got an unexpected keyword argument 'stop_reason'`) and `test_cli_harness_safety.py::test_running_every_command_leaves_the_repository_untouched`, which passes alone (`4 passed`) — the shared tree was being edited concurrently. Not charged to this unit. |

## Capability coverage (Mode A 4b) — reproduced in a throwaway copy

Copy: working tree minus `.git/.venv/.work/projects/qa/evidence/caches`, tarred to the session scratchpad
(outside the bound root). Named check run with the root venv's python from the copy's cwd; the test file
inserts its own `parents[1]/scripts`, so `mutation_check` is the copy's (row 1's edit, made only in the
copy, changed the result — proof). Each cell is a single-hunk edit to `scripts/mutation_check.py`, a file
named in "What changed" → admissible. Anchor asserted to match once, file asserted changed, restored after.

| row | before (copy) | after edit | assertion that fired |
|---|---|---|---|
| 1 `failed_tests(out, set().union(...))` → `failed_tests(out)` | 1 passed | exit 1 | `test_mutation_check.py:207` `assert result["killed"] is True` — `'killed': False, 'expected': ['tests/test_spaced.py::test_small[one small value]']` |
| 2 `whole = [...]` → `whole = []` | 1 passed | exit 1 | `:183` set equality — left has `test_x[a`, `test_z[q]` |
| 3 `max(whole…)` → `min(whole…)` | 1 passed | exit 1 | `:183` — left has `test_z[q]` instead of `test_z[q] - r]` |
| 4 `startswith(n + " - ")` → `startswith(n)` | 1 passed | exit 1 | `:188` stranger case — `{'test_y'} == {'test_yz'}` |

All four die for the assertion they are named for. No row is a load/import failure.

## Adversarial probes (real pytest 9.1.1, scratch repo, `check()` from the bound tree's committed instrument)

Raw mutated-run summary lines, verbatim:
```
FAILED tests/test_probe.py::test_amb[a] - Failed: boom] - z
FAILED tests/test_probe.py::test_dash[x - y] - assert not True
FAILED tests/test_probe.py::test_odd[caf\xe9 ol\xe9] - assert not True
FAILED tests/test_probe.py::test_odd[trail ] - assert not True
FAILED tests/test_probe.py::test_odd[in[ner] br] - assert not True
FAILED tests/test_probe.py::test_long[a long spaced id that is fairly long indeed]
FAILED tests/test_probe.py::test_xp[x pass] - [XPASS(strict)] r
FAILED tests/test_probe.py::test_pre[k] - assert not True
ERROR tests/test_probe.py::test_setup[set up] - RuntimeError: setup boom
```

| probe | instrument says | truth | ok? |
|---|---|---|---|
| id containing `" - "` (`test_dash[x - y]`) | KILLED | failed | yes |
| unicode id (pytest escapes `\xe9` in both collect and summary) | KILLED | failed | yes |
| trailing-space id `test_odd[trail ]` | KILLED | failed | yes |
| brackets inside id `test_odd[in[ner] br]` | KILLED | failed | yes |
| long id, message dropped by `-q` width truncation | KILLED | failed | yes |
| setup ERROR on the named test | not killed | errored, not failed | yes (fail-closed, unchanged) |
| xfail(strict) XPASS | KILLED | pytest reports FAILED | unchanged from pre-fix |
| **`kills=[test_amb[a] - Failed: boom]]`, only `test_amb[a]` failed** | **KILLED** | **passed** | **NO — false KILLED** |
| **`kills=[test_amb[a]]`** | **not killed** | **failed** | **NO — false SURVIVED** |
| same two probes against `git show f7e83cd^:scripts/mutation_check.py` | not killed / KILLED | — | pre-fix was correct |

- CRLF: `_run_pytest` uses `text=True`, so pytest's output reaches the parser with `\n` only; a CRLF string
  handed to `failed_tests` directly would leave `\r` on message-less lines and fall back to the truncating
  regex (false SURVIVED only). Not reachable through `check()`.
- Truncation: `-q` shortens the message, never the nodeid, and appends `...`; it cannot forge a `" - "`
  match, but it CAN remove one, so whether the AT-473 misattribution fires depends on terminal width.
- Question, not a finding (pre-existing, not this unit): `FAILED` is matched with `^` over ALL output,
  including captured stdout printed in tracebacks, so a failing test that prints a line starting
  `FAILED <nodeid>` could contribute a failure. Unchanged by this unit.

## Existing specs re-run (parametrized kills)

| spec | recorded | re-run now |
|---|---|---|
| `qa/evidence/at465-466-unreadable-narration-keeps-its-cause` | 5/5 KILLED | 5/5 KILLED, identical rows |
| `qa/evidence/at438-display-contents` | 9/9 KILLED | 9/9 KILLED, identical rows |
| `qa/evidence/at355-refuse-bidi-overrides` | 5/5 KILLED | 5/5 KILLED, identical rows |

No result moved; no newly KILLED row.

## Known limits — judgement

- "Absent from the collected set keeps `\S+`" — honest.
- "A changed separator falls back, errs toward SURVIVED, never KILLED" — true for that fallback, but the
  section as a whole leaves the reader believing the change can only err toward SURVIVED. The
  ambiguous-sibling false KILLED (AT-473) is undisclosed, and the unit's own test asserts the unsafe
  resolution as correct. **Incomplete.**
- 330-line `scripts/` file outside doctor's cap — honest and accurate.

## Issues

- AT-469: stays **open** — the spaced-id case is handled, but the fix is not accepted.
- AT-473 (new, medium): the false KILLED above.
