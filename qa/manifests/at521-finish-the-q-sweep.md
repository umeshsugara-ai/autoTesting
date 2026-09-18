# Manifest — at521-finish-the-q-sweep (AT-521 + AT-522)

**Unit:** AT-521 + AT-522 — finish the `-q` sweep AT-503 started. AT-503
(`qa/manifests/at503-pytest-a-summary-line-not-just-dots.md`, checked-PASS cycle 1) fixed
`qa/adapter.json`'s slot-1 verify command and `CLAUDE.md`'s Commands block: pytest's `-q` is an
additive `argparse` count, `pyproject.toml:62`'s `addopts = "-q"` already contributes one, so a
second CLI `-q` reaches `-qq`, which prints no `N passed`/`N failed` summary line at all — only
dots and `[100%]`. AT-503's own file set was narrow; its checker filed two residuals for the
surfaces it could not touch:
- **AT-521** — `CLAUDE.md`'s two prose mentions outside the Commands block, the untracked
  `AGENTS.md`, and `qa/loop.md` still name the doubled command.
- **AT-522** — most per-file `cmd` rows in `.goal/goal.json` carry the same doubling.

**Contract:** `qa/contracts/core-invariants.md` C7 (verification is judged on real, re-runnable
output).
**Goal task:** none named directly (tooling/doc fix, same shape as AT-503/AT-507/AT-513).
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-521 (low, open → fixed here), AT-522 (low, open → fixed here). Neither
flipped by me — `qa/issues.jsonl` is the checker's write surface (AT-499).

## Step 1 — measure first, re-derived independently (not taken on trust)

The AT-503 checker's AT-522 filing said "43 of 50 total `cmd` rows." I re-derived every number
from scratch rather than accept it. Full commands + output in
`qa/evidence/at521-finish-the-q-sweep/measurement.log`:

| measurement | command | result |
|---|---|---|
| total `cmd`-string rows in `.goal/goal.json` | `grep -o '"cmd": "[^"]*"' .goal/goal.json \| wc -l` | **50** |
| of those, rows that invoke pytest | `grep -o '"cmd": "[^"]*pytest[^"]*"' .goal/goal.json \| wc -l` | **44** |
| total `' -q'` occurrences anywhere in the whole file | `grep -n ' -q' .goal/goal.json \| wc -l` | **43** |
| any of those outside a `"cmd"` row? | `grep -n ' -q' .goal/goal.json \| grep -v '"cmd"'` | **none** — every `-q` in the file lives inside a `cmd` string, one per line, confirming a plain `s/ -q//` on `"cmd"` lines is safe and sufficient |
| the one pytest row with no `-q` at all | (listed in measurement.log) | `uv run pytest tests/test_adjudicate*.py … tests/test_issues.py` — already correct, untouched |

**This confirms AT-522's own number exactly: 43 of 50.** (My first pass on the orchestrator side
miscounted 100 because `grep -c '"cmd"'` also matches the `"type": "cmd"` discriminator on the
same object — a different string. The precise pattern `"cmd": "[^"]*"` is the one that matters
and gives 50, matching the filed issue.)

**Distinct shapes** (all mechanically identical — a single ` -q` token to delete): leading
(`pytest -q <path>`, 1 row), trailing at end-of-string (`<path>.py -q"` or `::test_id -q"`, 39
rows), trailing before a chained `&&` (`<path> -q && uv run autotester doctor`, 3 rows).

**Doc surfaces (`qa/evidence/at521-finish-the-q-sweep/doc_surfaces_before.log`):**
- `CLAUDE.md:68` (Maker-checker discipline, adapter-summary bullet) and `CLAUDE.md:103` (Lab
  Protocol Validators bullet) — both still named `uv run pytest -q`. (Commands block itself was
  already fixed by AT-503.)
- `qa/loop.md:14` — slot-1 Verify line named `uv run pytest -q`.
- `AGENTS.md:68`, `:89` (its own Commands block — AT-503 never touched this file), `:101` — all
  three mirror the pre-fix `CLAUDE.md`.

## Step 2 — verify the premise on a real example before mass-editing

Took one actual `cmd` string from `.goal/goal.json` (`tests/test_coverage.py`, T-089's
done_check), ran it as-is (CLI `-q` stacked on the config's `-q`, i.e. today's doubled state) and
without the CLI `-q` (the corrected state), each redirected to a file and read whole — not a
`tail`. Logs: `qa/evidence/at521-finish-the-q-sweep/premise_with_cli_q.log` and
`premise_bare.log`.

```
=== with CLI -q added (doubling, as currently in goal.json) ===
.............                                                            [100%]
exit=0

=== without CLI -q (bare, matches adapter.json's now-fixed command) ===
.............                                                            [100%]
13 passed in 0.08s
exit=0
```

Exactly the AT-503 mechanism, reproduced on a fresh example: the doubled form prints no summary
line; the corrected form does. A 43-row edit justified by argument alone would not have been
acceptable here — this is the captured run that justifies it.

## Step 3 — the edit

**`.goal/goal.json`** (live shared state; the dashboard and another maker/loop read it — kept
minimal and structurally identical, no reparse-and-redump):

- Read the file as raw bytes (it is CRLF-terminated — confirmed with `xxd`; a naive line-based
  tool that doesn't preserve `\r\n` would silently reformat the whole file's line endings, which
  is exactly the AT-496 failure class this brief warned about).
- For every line containing both `"cmd"` and `' -q'` (43 lines, all independently identified in
  Step 1), removed the first `' -q'` substring only. Nothing else on the line, and no other line,
  was touched.
- Verified byte delta: 44445 → 44316 bytes, a difference of exactly 129 = 43 × 3 (`" -q"` is 3
  bytes) — confirms nothing beyond the 43 intended deletions changed.
- `python3 -c "import json; json.load(...)"` — still valid JSON, 55 tasks (unchanged count)
  before and after.
- Diff of my edit alone (before my touch vs. after, byte-identical apart from the 43 lines):
  `qa/evidence/at521-finish-the-q-sweep/goal_json_my_edit.diff` — **exactly 43 hunks, one line
  each, `-q` removed and nothing else.**

**Pre-existing dirty state, not mine (disclosed, not hidden):** `.goal/goal.json` was already
modified in the working tree before I touched it (`git status` at session start showed
`M .goal/goal.json`). I diffed the committed `HEAD` blob against my own "before" snapshot
(via Python `difflib` on `splitlines()`, which is line-ending-agnostic, since a raw `diff` against
`git show HEAD:...` falsely reports every line changed due to LF-vs-CRLF blob normalization) and
found two pre-existing changes that are **not part of this unit**: `"updated"` timestamp
(`2026-09-11T07:08:52` → `2026-09-18T08:37:02`) and the `analytics` block
(`velocity_per_day`/`eta_days`/`last_deterministic_tick`) — both look like live dashboard/tracker
writes from a separate process, present before I started and untouched by me. `git diff --stat`
against `HEAD` therefore shows more than 43 changed lines; the 43-hunk diff above is the
authoritative measure of *my* edit.

**`CLAUDE.md`** — two prose lines outside the already-fixed Commands block:
- `:68` `uv run pytest -q` → `uv run pytest` (kept the rest of the bullet, added "no CLI `-q` on
  pytest; see Commands below, AT-503").
- `:103` (Lab Protocol Validators bullet) `uv run pytest -q` → `uv run pytest (no CLI -q, AT-503)`.

**`AGENTS.md`** — confirmed first this is an **independent, untracked file**, not a symlink
(`os.path.islink('AGENTS.md') == False`) and not identical content (`diff AGENTS.md CLAUDE.md`
showed exactly 3 real differences before my edit: a `.Codex` vs `.claude` path in "Plan of
record", the un-fixed `pytest -q` Commands line, and `.Codex` vs `.claude` in "Enforcement
paths"). Last modified 2026-09-10, i.e. before AT-503 (2026-09-18) — it simply predates the fix
and was never in AT-503's file set. Applied the same three edits CLAUDE.md already carries
(Commands-block comment, the adapter-summary bullet, the Validators bullet), leaving its
`.Codex`-vs-`.claude` path differences untouched — that is a separate, pre-existing drift outside
this unit's brief (not about pytest `-q`).

**`qa/loop.md`** — `:14` `uv run pytest -q` → `uv run pytest (no CLI -q; ... AT-503)`.

## How to verify (commands + expected)

```
grep -c ' -q' .goal/goal.json                                    # expect: 0
python3 -c "import json; json.load(open('.goal/goal.json', encoding='utf-8')); print('valid JSON')"
                                                                   # expect: valid JSON
grep -n 'pytest -q\|pytest.*-q"' CLAUDE.md AGENTS.md qa/loop.md   # expect: no match as a live
                                                                   # command (CLAUDE.md/AGENTS.md
                                                                   # line ~91 keeps the AT-503
                                                                   # explanatory comment text
                                                                   # "...makes pytest -qq..." --
                                                                   # that is prose about the bug,
                                                                   # not a command to run)
uv run ruff check src tests scripts                               # expect: All checks passed!
uv run autotester doctor                                          # expect: doctor: clean
uv run pytest tests/test_coverage.py                              # expect: dots + "N passed in …s"
```

**Full suite is deliberately NOT re-run wholesale here** — no `src/` file changed, and it has run
clean multiple times today already. **However, see Step 4 below: one specific, targeted test file
WAS run and DOES regress as a direct, mechanical consequence of this edit** — that is not covered
by "no src/tests file changed," and I would not have found it without running it.

## Step 4 — a regression this edit causes — **FIXED by the maker after hand-back**

> **Status update, written by the orchestrating maker, not the build agent.** The build agent
> correctly refused to fix this because `tests/` was outside the file set I gave it, and it named
> the exact line and the exact one-line fix instead. **I applied that fix**, because the
> alternative was leaving the tree red while a second build subagent was running verification
> commands in it — a red baseline makes every concurrent measurement meaningless
> (`scripts/mutation_check.py` refuses outright on one, for exactly this reason).
>
> `tests/test_goal_done_checks.py:229` now reads `f"uv run pytest {spec}"` with a comment naming
> AT-503/AT-522. Re-run after the fix:
>
> ```
> $ uv run pytest tests/test_goal_done_checks.py
> 7 passed in 0.09s
> $ uv run autotester doctor       → doctor: clean
> $ uv run ruff check src tests scripts → All checks passed!
> ```
>
> I also checked whether any other test hardcodes the doubled command. Two hits in
> `tests/test_goal_done_check_shapes.py` (lines 23, 53) are **fixtures for a predicate about
> command *shapes***, not assertions about `.goal/goal.json`'s contents, so they are correct as
> they stand and were deliberately left alone.
>
> The section below is the build agent's original disclosure, kept verbatim as the record of what
> it found and reported. Its "not fixed here" framing was accurate when written.

### Original disclosure (build agent, unedited)


Ran the two goal.json-shape test files (not the full suite) because `.goal/goal.json`'s content
changed and these files exist specifically to police that content's shape:

```
uv run pytest tests/test_goal_done_checks.py tests/test_goal_done_check_shapes.py
......F..                                                                [100%]
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
1 failed, 8 passed in 0.27s
```

Full captured output: `qa/evidence/at521-finish-the-q-sweep/goal_done_checks_regression.log`.

**Root cause:** `tests/test_goal_done_checks.py:229` hardcodes
`f"uv run pytest {spec} -q"` as the *expected* `done_check.cmd` for ten tasks (T-160..T-169). My
edit correctly removed the CLI `-q` from all ten of those real rows in `.goal/goal.json`
(confirmed: `by_id[tid]["done_check"]["cmd"]` for T-160..T-169 now has no trailing `-q`, for
every one of the ten), so the hardcoded expectation is now stale by exactly the same defect this
unit exists to fix.

**The one-line correction** (not applied — `tests/` is outside this unit's declared file set,
which is `.goal/goal.json`, `CLAUDE.md`, `AGENTS.md`, `qa/loop.md`, `qa/manifests/at521-*.md`,
`qa/evidence/at521-*/`; the brief also names a *different*, concurrently-worked file
`tests/test_doctor.py` and says nothing authorizes touching any other test file):

```python
# tests/test_goal_done_checks.py:229 — current (stale after this unit's edit):
expected = {key: (deps, f"uv run pytest {spec} -q") for key, (deps, spec) in expected.items()}
# should become:
expected = {key: (deps, f"uv run pytest {spec}") for key, (deps, spec) in expected.items()}
```

I am flagging this as prominently as I can rather than silently leaving it, or silently fixing
it outside my authorized surface. `uv run autotester doctor` and `uv run ruff check src tests
scripts` — the two checks this unit's hard constraints actually name as must-pass — are both
green (below). The full `uv run pytest` bare suite will show exactly this one `FAILED` until the
one-line fix above lands; that is a known, named, root-caused, one-line-fix-away state, not an
unexplained one.

## Actual outputs (from my own run)

```
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ grep -c ' -q' .goal/goal.json
0
$ python3 -c "import json; json.load(open('.goal/goal.json', encoding='utf-8')); print('ok', len(json.load(open('.goal/goal.json', encoding='utf-8'))['tasks']))"
ok 55
```

## Capability coverage (each claim → its isolating check)

| capability | check | falsifying condition | observed |
|---|---|---|---|
| Every per-file pytest `cmd` row in `.goal/goal.json` that had a redundant CLI `-q` now prints a summary line when run | `uv run pytest tests/test_coverage.py` (one real row, bare) vs. the same row with `-q` restored | put `-q` back on the CLI | fixed: `13 passed in 0.08s`; pre-fix (same command +`-q`): no summary, dots only |
| `.goal/goal.json` is otherwise byte-identical (JSON validity, task count, all non-`-q` content) | byte-delta check (129 = 43×3), JSON parse, task-count comparison, full before/after diff | any reformatting, reordering, or unrelated field change | delta is exactly 43×3 bytes; diff shows exactly 43 one-line hunks; JSON parses; 55 tasks before and after |
| `CLAUDE.md` / `AGENTS.md` / `qa/loop.md` no longer instruct a doubled command anywhere | `grep -n 'pytest -q\|pytest.*-q"'` on all three | any live instruction still reads `uv run pytest -q` as something to run | no live command match; the only remaining string is the AT-503 explanatory comment naming the bug, not a command |
| `doctor` and `ruff` are unaffected (config/doc/data-only change) | `uv run autotester doctor`, `uv run ruff check src tests scripts` | either goes non-clean | both green (pasted above) |

**NO ISOLATING FALSIFICATION for the prose edits themselves** (`revert_op: none`) — same as
AT-503's own manifest: reverting the CLAUDE.md/AGENTS.md/qa/loop.md wording changes nothing
pytest does, only whether a reader reproduces the footgun.

## Live browser evidence

Not UI-touching — no `src/` file, no `ui/` route, no browser surface changed. Changed paths:
`.goal/goal.json`, `CLAUDE.md`, `AGENTS.md`, `qa/loop.md`,
`qa/manifests/at521-finish-the-q-sweep.md`, `qa/evidence/at521-finish-the-q-sweep/*`.

## On the checker's proposed regression guard (AT-523) — extended to `.goal/goal.json`

AT-503's checker proposed, for `qa/adapter.json` only: assert the verify `cmd` never stacks a CLI
`-q` on top of `pyproject.toml`'s `addopts`. That guard is carried on AT-523, not mine to build.
The brief asks me to decide, and argue, whether an equivalent guard over `.goal/goal.json`'s ~50
`cmd` rows is worth it.

**I'd add it, and here's the argument both ways:**

*For:* This unit just proved the defect is not self-healing — AT-503 fixed the adapter's own
command; the identical bug independently survived in 43 unrelated rows of a second file for
exactly the two weeks between then and now, because nothing enforces it. `.goal/goal.json` is
edited by many separate task-authoring events (new tasks added over months, per the file's own
history), so a guard here has far more surface to protect than the single adapter.json string
AT-523 already covers, and the fix is cheap: `tests/test_goal_done_check_shapes.py` already hosts
exactly this kind of predicate-correctness test (`is_capable_of_failing`), so a sibling assertion
— "no `done_check.cmd` combines a CLI `-q` with a config that already sets one" — is a natural,
in-place addition, not a new module. It would also have caught Step 4's regression at goal.json
level, one layer earlier than the `test_revised_goal_contract_is_registered` hardcoded-string
break did.

*Against:* The guard is about `.goal/goal.json`'s own internal consistency (a repo-authored
data file), not about pytest's CLI semantics — same distinction AT-503's manifest used to argue no
pytest-behavior test was warranted. It only prevents a symptom (no summary line); it does not
prevent someone from reintroducing `-q` in a way that also breaks the exit code, which is the
only thing every current consumer of these commands actually gates on. It is one more assertion
to maintain in a test file `doctor` already caps at 300 lines, and — per Step 4 — the sibling
file `test_goal_done_checks.py` already has an *existing*, uncorrected assertion that is now
stale from this very unit; a new guard added on top of a known-broken neighbor without fixing the
neighbor first would be adding scope while leaving a known defect unaddressed.

**Recommendation:** worth building, but only as a fast-follow that starts by fixing Step 4's
one-line regression first (so the guard isn't added next to a file that already has a
self-inconsistent expectation), then adds the guard as a sibling assertion in
`tests/test_goal_done_check_shapes.py`, scoped to `.goal/goal.json` `done_check.cmd` strings the
same way AT-523 scopes it to `qa/adapter.json`. Not built here — it requires editing `tests/`,
outside this unit's declared file set.

## Known limits (disclosed, not claimed)

- **A real, named, root-caused, one-line-fix-away test regression exists and is NOT fixed by this
  unit**: `tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered` now fails
  because it hardcodes `-q` on ten expected `cmd` strings this unit correctly removed from the
  real data. See Step 4 for the exact line and fix. `tests/` is outside this unit's declared file
  set (`.goal/goal.json`, `CLAUDE.md`, `AGENTS.md`, `qa/loop.md`, manifest, evidence) and the
  brief separately reserves `tests/test_doctor.py` for a concurrently-running second build
  subagent — I did not expand my own file set to cover a different, unreserved test file either,
  even though the fix is trivial and squarely caused by my own edit. This is the single most
  important thing in this manifest for whoever picks up next.
- **No new test is added by this unit for the `.goal/goal.json` change itself** — see the guard
  discussion above; I judged building it to require `tests/` access outside my file set, so I
  argued the case instead of building it.
- **`AGENTS.md`'s `.Codex`-vs-`.claude` path drift (2 lines) is left as-is** — real, visible in
  the diff I captured, but unrelated to the `-q` doubling this unit is scoped to; flagging it here
  rather than silently fixing or silently ignoring it.
- **The pre-existing dirty state in `.goal/goal.json`** (`updated` timestamp, `analytics` block)
  that was already in the working tree before I started is disclosed above (Step 3) and is not
  mine; `git diff --stat` against `HEAD` will show more than 43 changed lines because of it — the
  43-hunk `goal_json_my_edit.diff` in the evidence folder is the accurate measure of this unit's
  own change.
- **`qa/contracts/core-invariants.md` still carries the same `-q` doubling on at least three
  *other* Verify clauses** (lines ~23, ~56, ~139 — not C7, which AT-503's checker already fixed).
  Noticed while confirming contracts were fully folded; not filed as a new issue (I cannot write
  `qa/issues.jsonl`) and not edited (contracts are checker-owned, never maker-edited) — named here
  so it isn't lost.
- **`qa/issues.jsonl`'s AT-521/AT-522 rows are not flipped by this manifest** — that ledger is the
  checker's write surface (AT-499); this manifest is the fix for the checker to verify and close.

## Status: ready-for-check
