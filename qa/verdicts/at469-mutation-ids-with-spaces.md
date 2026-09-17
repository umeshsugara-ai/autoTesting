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

---

# Cycle 2

**Date:** 2026-09-17
**Checker:** /checker Mode A (fresh subagent, bound to `d:/autoTesting`; a prior cycle-2 dispatch died on a network error before writing anything)
**Manifest:** `qa/manifests/at469-mutation-ids-with-spaces.md` (Fix cycle: 2, Status: ready-for-check)
**Cycle checked: 2**
**Unit commit:** ee98728 (HEAD 562a80c only stamps `qa/.last-tick`; `git diff --quiet HEAD -- scripts/mutation_check.py tests/test_mutation_check.py tests/conftest.py` is clean)

```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (C7 attribution clause + mutation duty), invariants hold (doctor clean)
FAILURES (if any):
CAPABILITY-COVERAGE: 4/4 rows reproduced
LIVE-BROWSER: not-applicable (scripts/mutation_check.py, tests/test_mutation_check.py, qa/evidence/at469-mutation-ids-with-spaces/, qa/manifests/at469-* — a verification CLI and its tests; confirmed from `git show ee98728 --stat`)
ISSUES-WRITTEN: AT-478, AT-479 (both low, pre-existing, not charged); AT-469 and AT-473 open -> fixed
EXPLANATION: AT-473 is closed: 19 real-pytest probes (both directions of the cycle-1 ids, a three-sibling " - " chain, an uncollected prefix-sharing id, duplicated and printed FAILED lines) found no false KILLED introduced by this unit; every ambiguous line is credited to nobody. The instrument is strictly safer than both predecessors: the pre-fix `\S+` reading itself gave false KILLEDs on four chain shapes (P2, P3b, P3c, P3f) that ee98728 reports correctly. Two false-KILLED shapes remain and are identical under f7e83cd^ — a mutation that renames a parametrize id (AT-479), and a failing test printing a sibling's summary line into captured stdout (AT-478; after AT-469 it also reaches spaced ids, the only "worse" delta) — filed low, not charged.
```

## What I re-ran (my own runs)

| command | result |
|---|---|
| `uv run pytest tests/test_mutation_check.py tests/test_mutation_sandbox.py` | `23 passed in 217.37s` — matches |
| `uv run ruff check src tests scripts` | `All checks passed!` — matches |
| `uv run autotester doctor` | `doctor: clean` — matches |
| `uv run python scripts/mutation_check.py qa/evidence/at469-mutation-ids-with-spaces/mutations.json` | `4/4 mutations killed`, rows and attributions identical to the manifest — matches |
| `uv run pytest -p no:cacheprovider -rfE` (full, pytest's own exit code captured) | `1407 passed, 2 skipped, 32 xfailed, 1 warning in 508.61s`, exit 0 |

**The manifest's one full-suite failure** (`tests/test_explore_live.py::test_the_dialog_page_does_not_trap_the_crawl`, `aborted_error`): not reproduced — it passed in my full run. It is also unrelated by construction: ee98728 touches only `scripts/mutation_check.py`, its test file, and at469 qa files; no explore code. Consistent with the AT-196 flake in the contract's amendment log. Not charged.

## Capability coverage (4b) — throwaway copies

A fresh copy per row of `scripts/ tests/ src/ pyproject.toml` in the session scratchpad (outside the bound root); named check(s) run from the copy's cwd. The test file inserts its own `parents[1]/scripts`, so `mutation_check` is the copy's (row 1's copy-only edit flipped the result — proof). Every cell is a single-hunk edit to `scripts/mutation_check.py`, a file named in "What changed" -> admissible. Anchor asserted to match exactly once; file asserted changed.

| row | before (copy) | after edit | assertion that fired |
|---|---|---|---|
| 1 `failed_tests(out, set().union(...))` -> `failed_tests(out)` | 1 passed | exit 1 | `assert result["killed"] is True` — `'killed': False, 'expected': ['tests/test_spaced.py::test_small[one small value]']` |
| 2 `whole = [...]` -> `whole = []` | 1 passed | exit 1 | first set equality — left has `tests/t.py::test_x[a`, right `test_x[a b]` |
| 3 `if len(whole) == 1: add(whole[0])` -> `if whole: add(max(whole, key=len))` | 1 passed + 1 passed | exit 1 + exit 1 | e2e: `assert result["killed"] is False` — `'killed': True, 'expected': ['tests/test_amb.py::test_amb[a] - AssertionError: r]']`; unit: `assert {'tests/t.py::test_z[q] - r]'} == set()` (the AT-473 ambiguous case) |
| 4 `startswith(n + " - ")` -> `startswith(n)` | 1 passed | exit 1 | stranger case — `{'tests/t.py::test_y'} == {'tests/t.py::test_yz'}` |

All four die for the assertion they are named for; none is an import or collection failure. No state trap: the AT-473 e2e check asserts `killed is False` on a run where the named sibling passed, a state the cycle-1 rule demonstrably does not produce.

## Adversarial probes — real pytest, `check()` on a scratch repo, three instruments

Scratch repo: one module line `FAIL = {}; GEN = ["c"]` mutated per probe; tests parametrized with the probe ids. Instruments: `ee98728` (head), `f7e83cd^` (pre-fix), `f7e83cd` (cycle 1). The truth column is about the NAMED test.

| probe | head | pre-fix | cycle 1 |
|---|---|---|---|
| P1 ids `['a','a] - Failed: boom']`, only `[a]` fails `boom] - z`; kills sibling (passed) | not killed | not killed | **KILLED** |
| P1 same; kills `[a]` (failed) | not killed (disclosed fail-closed) | KILLED | not killed |
| P2 only sibling fails `z`; kills `[a]` (passed) | not killed | **KILLED** | not killed |
| P2 same; kills sibling (failed) | not killed (disclosed) | not killed | KILLED |
| P3a chain `b`, `b] - Failed: X`, `b] - Failed: X] - Failed: Y`; `[b]` fails `X] - Failed: Y] - z`; kills middle / last (passed) | not / not | not / not | not / **KILLED** |
| P3b middle fails `Y] - z`; kills `[b]` / last (passed) | not / not | **KILLED** / not | not / **KILLED** |
| P3c last fails `z`; kills `[b]` / middle (passed) | not / not | **KILLED** / not | not / not |
| P3d `[b]` fails `X]` (line equals middle's nodeid); kills middle (passed) | not | not | **KILLED** |
| P3e `[b]` fails `q`; kills `[b]` (failed) | KILLED | KILLED | KILLED |
| P3f middle fails `q`; kills `[b]` (passed) | not | **KILLED** | not |
| P4 mutation renames the id to uncollected `test_gen[c] - Failed: q]`, which fails `w`; kills `test_gen[c]` (never ran) | **KILLED** | **KILLED** | **KILLED** |
| P4b uncollected `test_gen[c d]` fails; kills `test_gen[c]` | not | not | not |
| P5 failing `test_printer` prints `FAILED tests/test_p.py::test_sp[x y] - boom`; kills `test_sp[x y]` (passed) | **KILLED** | not | **KILLED** |
| P5b same with space-free `test_ns[x]` (passed) | **KILLED** | **KILLED** | **KILLED** |
| P6 `test_dup[m n]` fails and prints its own summary line twice; kills it (failed) | KILLED | not (truncated `[m`) | KILLED |
| P6b printer prints the ambiguous amb line twice while `[a]` fails; kills sibling (passed) | not | not | **KILLED** |

- **AT-473 closed.** Head has zero false KILLED across every ambiguity, chain and duplicate shape; its only wrong answers there are the disclosed fail-closed SURVIVEDs.
- **Head is strictly safer than the pre-fix instrument**, which false-KILLED on P2, P3b, P3c, P3f (its `\S+` read `test_chain[b]` / `test_amb[a]` out of a sibling's line).
- **P4 -> AT-479 (low, pre-existing, identical in all three):** attribution knows only the BASELINE collection, so a mutation that changes parametrize ids can credit a test that never ran.
- **P5 -> AT-478 (low):** `^FAILED` scans captured stdout. Pre-existing for space-free ids (P5b, all three); AT-469 extends it to spaced ids (P5). It is the one shape this unit made reachable, but it needs a failing test to print a verbatim summary line naming a sibling, is already reachable for every space-free id, and the same change removes four other false-KILLED shapes — not charged, filed.

## Existing specs re-run

| spec | recorded | re-run now |
|---|---|---|
| `qa/evidence/at465-466-unreadable-narration-keeps-its-cause` | 5/5 KILLED | 5/5 KILLED, identical rows |
| `qa/evidence/at438-display-contents` | 9/9 KILLED | 9/9 KILLED, identical rows |
| `qa/evidence/at355-refuse-bidi-overrides` | 5/5 KILLED | 5/5 KILLED, identical rows |

Nothing newly KILLED, nothing moved.

## Known limits — judgement

- Cycle 1's incomplete "can only err toward SURVIVED" claim is explicitly corrected — honest.
- "An ambiguous line reads SURVIVED even when the named test really failed" — reproduced (P1, P2), honest.
- "Pre-existing: `^FAILED` scans captured stdout; this unit does not touch that" — the regex is untouched, but P5 shows the attribution change lets that scan reach spaced ids. Minor omission, recorded in AT-478.
- 330-line `scripts/` file outside doctor's cap — accurate.

## Issues

- AT-469: open -> **fixed** (spaced ids attributed; row 1, P6).
- AT-473: open -> **fixed** (no false KILLED on any ambiguity shape; row 3, P1-P3).
- AT-478 (new, low): `^FAILED` over captured stdout lets a printed line fake a kill; spaced ids now included.
- AT-479 (new, low): a mutation that renames a parametrize id can credit a test that never ran.
