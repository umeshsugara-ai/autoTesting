# Verdict — at154-at157-fail-closed

**Date:** 2026-09-08
**Cycle checked:** 1
**Manifest:** `qa/manifests/at154-at157-fail-closed.md` (commit `90e4219`, manifest `ca18643`)
**Contract:** `qa/contracts/core-invariants.md` — C9, C7
**Environment:** host, Docker down, `uv` native. Bare `uv run pytest`. Sabotage + waiver work done in
a `git archive HEAD` copy under the scratchpad with the repo venv pinned (AT-101 — the live tree was
never stashed, checked out, or restored).

## VERDICT: PASS

**SCOREBOARD: 2/2 criteria met, 2/2 invariants hold**
(C9 honour-or-reject for `done_check`; C7 independent verification + both sabotage clauses.)

## What I re-ran

| Command | My result | Manifest claim |
|---|---|---|
| `uv run pytest` | **658 passed, 2 skipped**, 76.72s | 658 passed, 2 skipped ✓ |
| `uv run ruff check src tests scripts` | `All checks passed!` | ✓ |
| `uv run autotester doctor` | `doctor: clean` | ✓ |

## 1. AT-155's seven false negatives + the AT-154 family — all now rejected

Driving `is_capable_of_failing` directly against the new predicate:

```
False  echo done
False  uv run python -c "pass"
False  test -f README.md
False  uv run pytest --collect-only tests/test_x.py
False  ls src || true
False  uv run pytest tests/test_explore.py -q || true
False  true # comment
False  uv run pytest tests/        False  uv run pytest tests
False  uv run pytest -q tests/     False  pytest tests/
```

Every finding I filed on the previous unit is closed by execution, not by assertion. AT-154, AT-155
and AT-157 are moved to `verified` in the ledger.

## 2. Second attempt at false negatives — four families still admitted (AT-158)

The maker asked me to try again. I found holes, and they share **one** root cause rather than four:
`_is_task_specific` matches its program names with `in parts` / `any(p.endswith(...))` — membership
over **all** tokens, not the program position.

```
True   uv run pytest --co tests/x.py        # --co IS --collect-only, excluded one line away
True   uv run pytest --co -q tests/x.py
True   uv run pytest tests/x.py | true      # splitter handles || but not |
True   uv run pytest tests/x.py |& true
True   echo pytest tests/x.py               # "pytest" as an argument to echo
True   echo x #check_deliverable.py         # shlex keeps comment tokens
True   true # pytest tests/x.py             # the suite pins `true # tests/test_x.py` as REJECT;
                                            # adding the word "pytest" defeats that pin
```

All seven exit 0 unconditionally. The `--co` one is the AT-154 shape recurring — the guard's own
stated logic beaten by a documented synonym. Filed **AT-158** (medium) with the one-line fix
direction: resolve the program token first, split on `|` too, add `--co`.

Shapes I probed that are **not** false negatives (they fail in the safe direction): a `.py` path that
does not exist (pytest exits 4), `-k`/`--deselect` matching nothing (exit 5), a bare
`check_deliverable.py` (its no-assertion guard exits 2), `> /dev/null` (exit status preserved).

## 3. The ruling you asked for — is the allowlist too narrow?

**The trade is right and I stand behind it.** A waiver is a sentence someone had to write and anyone
can `grep`; a false negative is nothing at all. Fail-closed stays. Two qualifications:

**(a) Two rejections are recognition bugs, not strictness** — they are the shape the branch was
written for, misspelled:

```
False  python3 scripts/x.py                    # branch tests "python" in parts / endswith("python")
False  uv run python src/autotester/tools/x.py # branch hard-codes the substring "scripts" in the path
```

Waiving these would be waiving a typo. Filed **AT-159** (low): match the interpreter with a regex
(`python`/`python3`/`py`) and drop the hard-coded `scripts` requirement, keeping the `-c` exclusion.

**(b) Everything else you listed is correctly waiver-gated.** Measured rejections I rule *correct*:
`./scripts/x.py`, `bash|sh scripts/x.sh`, `node tools/x.mjs`, `powershell -File x.ps1`,
`make verify-t150`, `uv run pytest -m t150`, `uv run autotester ledger check`,
`uv run python -m autotester.cli check`, `test -f <path>`, `grep -q <needle> <file>`.

The last two deserve a word, because they are as task-specific as `check_deliverable.py` and are the
most likely source of the waiver pressure you named. My ruling: **do not widen for them.**
`check_deliverable.py` exists precisely so that "assert this artifact is there" has one sanctioned,
readable, exit-code-correct spelling; admitting `test -f` and `grep -q` re-opens a shell-shaped
surface for a second time in three units. A writer who reaches for `test -f` should reach for
`check_deliverable.py --exists` instead, and that is a better outcome than either a waiver or a
wider allowlist.

And these were confirmed **already accepted**, so they need no waiver at all:

```
True   uv run pytest tests/test_a.py tests/test_b.py
True   uv run python -m pytest tests/test_x.py
True   uv run pytest tests/test_x.py::TestC::test_m
True   python scripts/check_deliverable.py --contains ../other/f.json needle
```

## 4. The waiver mechanism, end to end

Scratch copy of the archive, `.goal/goal.json` mutated per case, `tests/test_goal_done_checks.py`
re-run each time:

```
baseline (unmodified archive)                          rc=0  ........
1 unfailable, NO waiver              (expect FAIL)     rc=1  test_no_pending_task_has_a_done_check_that_cannot_fail
2 unfailable + 49-char waiver        (expect PASS)     rc=0  ........
3 unfailable + 3-char waiver         (expect FAIL)     rc=1  test_no_task_on_disk_carries_an_empty_waiver
4 waiver on OK task + separate offender (expect FAIL)  rc=1  test_no_pending_task_has_a_done_check_that_cannot_fail
5 waiver on OK task only             (expect PASS)     rc=0  ........
6 unfailable but status=done         (expect PASS)     rc=0  ........
```

Case 4 is the over-application question and it answers it: a waiver on one task exempts **only** that
task. Case 3 confirms the 20-character floor bites on real data, not only on the synthetic rows. A
`waiver: null` is treated as no waiver (not as a hollow one) — correct.

## 5. Sabotages Z1–Z5 reproduced in my own harness

Each mutation asserted anchor-matched-exactly-once **and** file-changed-on-disk before its result was
believed (C7), with a restored baseline before and after:

```
RESTORED baseline: rc=0 failures=[]
Z1 bare tests/ counts as specific again  anchor once=True changed=True -> 1  test_the_guard_recognises_the_shapes_it_exists_to_catch
Z2 || stops disqualifying                anchor once=True changed=True -> 1  test_the_guard_recognises_the_shapes_it_exists_to_catch
Z3 allowlist inverts back to a denylist  anchor once=True changed=True -> 2  test_a_waived_task_is_exempt..., test_the_guard_recognises...
Z4 a waiver need not say anything        anchor once=True changed=True -> 1  test_the_waiver_rule_actually_rejects_a_hollow_waiver
Z5 --contains drops the unreadable path  anchor once=True changed=True -> 1  test_check_deliverable_reports_an_unreadable_path_instead_of_crashing
RESTORED after all: rc=0 failures=[]
```

Z5 reverted the **actual fix hunk** (the try/except restored to the original one-line `read_text`),
not a nearby string. **The maker's claim that it closed both INCONCLUSIVE gaps is verified**: Z4 and
Z5 now fail, and they fail on the specific test each gap left unwritten. That is the C7 zero-failure
clause doing exactly the work it was added for, one unit after it was written — and it caught the
maker, not me, which is the right direction.

## 6. Are the two new tests tautological? — one is fine, one is not (AT-160)

**`test_the_waiver_rule_actually_rejects_a_hollow_waiver` — legitimate.** Synthetic rows, but the
**real** `_waiver_offenders` predicate, the same function that judges the real `goal.json` in
`test_no_task_on_disk_carries_an_empty_waiver`. Sabotage Z4 (threshold `< 20` → `< 0`) makes it fail,
so it is measuring the production rule, not restating its input. This is correct isolation: the rule
had no data on disk to bite on, so the test supplies data. Nothing about it can go stale — if the
threshold changes, the test fails.

**`test_a_waived_task_is_exempt_from_the_unfailable_check` — does not test what it is named.** It
asserts the two helpers *separately* (`not is_capable_of_failing(cmd)`, `waiver_of(task)` truthy) and
never asserts the **composition**. Sabotage Z6, mine:

```
Z6 (delete `and not waiver_of(t)` from the offenders comprehension)
   anchor matched once=True, file changed=True
   -> rc=0, ZERO failures — the exemption clause can be deleted and the suite stays green
```

The behaviour is correct today (§4 proves it end to end), so this is an **uncovered guard, not a
defect** — the same class the maker's own C7 clause exists to surface, this time inside a test
written to close that clause. Filed **AT-160** (medium): assert the offenders list over synthetic
rows (one waived, one not) and check only the unwaived id appears.

## 7. AT-157 — `--contains` behaviours

Run against `scripts/check_deliverable.py` in the archive copy:

```
--contains src needle            -> 1   FAIL src is not readable text (PermissionError)
--contains .work/bin.dat needle  -> 1   FAIL .work/bin.dat is not readable text (UnicodeDecodeError)
--contains pyproject.toml autotester -> 0   OK 1 deliverable(s) present
--contains README.md zzzzz-nope  -> 1   FAIL README.md does not mention 'zzzzz-nope'
--contains nope.txt x            -> 1   FAIL missing: nope.txt
--exists src/autotester/cli.py   -> 0
main([])                         -> 2   FAIL nothing asserted — a check with no assertion cannot fail
```

Directory, binary, hit, miss, missing, and the no-assertion guard all behave; no traceback anywhere;
`main([])` still returns 2. AT-157 closed.

## FAILURES

None.

## ISSUES-WRITTEN

- **AT-158** (medium) — allowlist still admits `--co`, pipe-neutered commands, and any command with a
  recognised program name appearing as an argument or in a comment; one root cause (token membership
  instead of program position).
- **AT-159** (low) — `python3 …` and a `.py` outside `scripts/` rejected by recognition bugs in a
  branch that intends to accept them; would consume a waiver for a typo.
- **AT-160** (medium) — `test_a_waived_task_is_exempt_from_the_unfailable_check` does not detect
  deletion of the exemption clause (Z6, zero failures).

Ledger: **AT-154, AT-155, AT-157 → `verified`.** AT-156 stays open (correctly deferred, as ruled).

## EXPLANATION

Every claim in the manifest reproduced under my own instruments: 658/2 with ruff and doctor clean,
all seven AT-155 false negatives and the whole AT-154 `pytest tests/` family now rejected, and all
five sabotages biting with anchor-once + file-changed asserted. The maker's specific claim — that it
closed the two gaps my C7 clause exposed — is verified: Z4 and Z5 both fail now, on the exact tests
the gaps were missing. On the open question I ruled the trade correct and fail-closed stays; the only
widening I would accept is two interpreter/path recognition bugs (AT-159), and I explicitly rule
against admitting `test -f`/`grep -q`, because `check_deliverable.py --exists` is the sanctioned
spelling and re-opening a shell surface is what AT-155 was. Three new issues, none of them a defect
in what this unit claims: two are residual holes in a guard that now fails closed by default, and one
is an uncovered guard inside a new test — filed, not FAILed, because the unit's claim is that the
predicate fails closed, and it verifiably does.
