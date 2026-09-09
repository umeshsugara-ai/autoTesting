# Verdict — t136-scorer

**Date:** 2026-09-09 · **Cycle checked: 1** · **Commit under check:** `e65447a`
(manifest at `60ad180`) · **Bound to:** `d:/autoTesting`
**Contract:** `qa/contracts/video-learning.md` — VL7–VL14 and I-VL7 authored by this checker in
the same commit, at the manifest's request.

```
VERDICT: FAIL
SCOREBOARD: 3/8 criteria met, 1/1 invariants hold
FAILURES:
- [VL7]  sev: high     · the refusal names `autotester issues derive`, which the CLI does not expose — and NO command anywhere derives video issues, so there is no right name to substitute · point the advice at a real command (or build the derive command as its own unit) and extend the advice collector's roots to `scripts/` · issue: AT-220
- [VL8]  sev: high     · the shipped command resolves its project root to `D:\`, reading `D:\projects\erp\issues.jsonl` — so today's exit 2 is a path bug, not the refusal the manifest argues from, and T-136's `done_check` can never pass · `root = args.root or repo_root()`, plus one test that runs the done_check invocation verbatim · issue: AT-219
- [VL13] sev: high     · recall itself moves with `store.list_issues()` order — measured 0.5 vs 1.0 on a permuted pair — because `max()` returns the first maximum and the candidate key is not total · make the key total (append the issue id) or sort candidates on content, and pin it with a permutation test · issue: AT-221
- [VL14] sev: high     · `coverage()` skips a contributing source whose analysis is missing, so `complete: true` is reachable while a scored source's reading is unknown — AT-207's untruth inside AT-207's fix · count sources with no analysis and let any of them force `complete: false` · issue: AT-222
- [VL10] sev: medium   · a blank recording cell keys to `""` and matches other blanks (measured recall 1.0 on an all-blank sheet), and `clip (1).mp4` / `clip (2).mp4` collapse to one key · refuse a blank recording cell the way `at_seconds` refuses a blank `At` · issue: AT-223
ISSUES-WRITTEN: AT-219, AT-220, AT-221, AT-222, AT-223, AT-224, AT-225
EXPLANATION: The unit's honesty about what it does not deliver is genuine and is upheld — no
vision credential exists, `projects/erp/` is empty of sources and analyses, and leaving T-136
`pending` is right. But the evidence the manifest offers for that honesty does not survive
re-derivation: the exit 2 it points at is produced by a default root of `D:\`, not by the absence
of issues, and the refusal it exits with names a command that does not exist. Two of the three
things this unit added on top of the machinery — the recall number's determinism and AT-207's
coverage — are each defeated by a case the maker's own stated principles already condemn.
```

---

## What I re-ran (nothing here is the maker's pasted output)

| Command | My result |
|---|---|
| `uv run pytest` | **846 passed, 2 skipped**, 1 warning — matches the manifest |
| `uv run ruff check src tests scripts` | `All checks passed!` (exit 0) |
| `uv run autotester doctor` | `doctor: clean` (exit 0) |
| `uv run autotester providers` | `available providers: mock` — **the maker's claim is true** |
| `uv run python scripts/score_video_issues.py --project erp --truth ".../ERP_Issues_Trainers.xlsx" --sheet "Trainer module"` | exit **2**, the refusal text verbatim — **but see VL8** |
| `uv run autotester issues derive --help` | `No such command 'issues'` |
| `uv run autotester --help` / `ingest --help` | no `issues` group; `ingest` = register / list / prep / frames / run |

Working tree at check time: only `.goal/dashboard.html` and `.goal/goal.json` modified, as the
dispatch said. No drift.

## The thing I was asked to judge first: is the refusal honest?

**The claim is true. The evidence for it is not.**

Verified true, independently:

- `available providers: mock`. No vision credential on this host.
- `projects/erp/` contains `cases.jsonl`, `project.json`, `rubrics/`, `runs/` — and **no**
  `sources.jsonl`, `sources/`, `media.json`, `analysis.json` or `issues.jsonl`. No model has
  watched a recording.
- The manifest states the shortfall in its second heading rather than burying it, and files
  `qa/gates/t136-model-credentials.md` as a HUMAN_GATE. That is the behaviour this project wants
  and I am not charging it.
- **Leaving T-136 `pending` is correct**, and I am upholding it. A scorer that exited 0 printing
  `recall: 0.0` would be AT-100's class aimed at the north star, exactly as argued.

What does not survive re-derivation is the *demonstration*. The manifest's centrepiece is "run it
today and it exits 2, and that is why T-136 is not closed." I ran it; it exits 2. Then I read why:

```
scripts/score_video_issues.py:92
    root = args.root or ProjectPaths(args.project).root.parent.parent
```

`repo_root()` is `D:\autoTesting`, so that expression is **`D:\`**, and the command opens
`D:\projects\erp\issues.jsonl` — outside this repository. The same message and the same exit code
would be printed against a project with a thousand derived issues. The exit code is not reporting
what the manifest says it is reporting, and every CLI test passes `--root` explicitly
(`tests/test_score_cli.py:76`), so the branch that actually ships is executed by nothing in the
suite.

This is not cosmetic. `.goal/goal.json`'s `done_check` for T-136 is the command **without**
`--root`, expecting exit 0. As shipped, T-136 cannot close even after a credential arrives. The
maker's decision to leave the task pending is right; the reason it is right is one the manifest
does not know about.

And a second reason it could not have closed anyway: `stages/issues.py::derive_issues` has **no
caller under `src/`**. Nothing in the CLI derives or persists video issues. A credential alone
would not have produced the artifact the scorer needs.

**Verdict on the gate question:** the maker is *not* using the HUMAN_GATE to dodge a failing
acceptance. It could not have met the acceptance another way, and it said so first. What it did do
is offer a broken command's exit code as proof of a property that command does not have.

## Pressed hard, as instructed

### 1. Is the exit-code guard real or cosmetic?

**Real in the direction tested, incomplete in the inverse.** Sabotage SH (`return 2` → `return 0`
on the nothing-to-score path) fails exactly 1 test — the guard bites. But I looked for exit 0 where
it should not be, on a temp root so the VL8 bug is out of the way
(`.work/chk-t136/probe6.py`, real `ProjectStore`, real JSON on disk):

| Case | Result |
|---|---|
| Truth sheet with rows but every `At` unparseable | exit **2** — correctly refused at load |
| Recording column present but **empty in every row**, issues on a real clip | exit **0**, `recall 0.0` |
| Recording column empty **and** issue labels empty | exit **0**, **`recall 1.0`, found 2, fp 0** |
| Issues carrying a different project's slug | exit **0**, scored normally |
| No analysis on disk at all | exit **0**, `complete: false` — **correct** |
| Truth rows on `erp1`, issues only on `erp2` | exit **0**, `recall 0.0` |

The third row is the one that matters: an all-blank recording column produces a *perfect score*.
The maker's own stated method is that a fact which "silently yields a recall of zero" gets enforced
in code rather than remembered — that is precisely why `at_seconds` refuses. The recording column
is the one input where the same reasoning was not applied, and it fails in the flattering direction
as well as the zero one (AT-223).

The all-zero coverage case, credit where due, is right: `expected == 0` makes `complete` false, so
"no analysis anywhere" cannot masquerade as complete.

### 2. Greedy matching

Greedy-over-optimal is a stated, defensible trade and I am not charging it — the docstring is
honest that optimal would raise recall. What is charged is the claim attached to it: *"the ordering
is deterministic because candidates sort on similarity then time."*

`score.py:219` is `max(candidates, key=lambda c: (c[0], -c[1]))`. `max` returns the **first**
maximum, and `candidates` is built by iterating `remaining` — i.e. the order `list_issues()` read
`issues.jsonl`. A tie on both keys hands the decision straight to file order. That is the same
sentence VL4 already contains about `adjudicate`, and AT-197 is the issue that cost T-133 a fix
cycle for it.

Measured (`.work/chk-t136/probe4.py`), truth `T1="cat dog"`, `T2="cat dot bird"`, both at 10s;
issues `X="cat dot"`, `Y="cad dog"`, both at 10s; `similarity(T1,X) == similarity(T1,Y) == 0.8`:

```
--threshold 0.7   issue order [X, Y] -> recall 0.5
                  issue order [Y, X] -> recall 1.0
```

At the default threshold the recall coincides, but the *claim* still permutes: with two identical
issues, `per_row[T1].matched_title` and `similarity` name X or Y purely by list order
(`probe2.py` case B). So the JSON report is order-dependent under shipped defaults, and recall is
order-dependent one flag away. Ties are reachable from the shipped ensemble — two models × two
prompts, with `join_issues` merging only inside a window. Filed AT-221, criterion VL13.

### 3. `recording_key`

Measured (`.work/chk-t136/probe1.py`):

```
'erp1.mp4 (Divya Kamboj, trainer pipeline)' -> 'erp1.mp4'   correct, and the point of the function
'clip (1).mp4'                              -> 'clip'
'clip (2).mp4'                              -> 'clip'        <- two recordings, one key
'erp (final) cut.mp4'                       -> 'erp'
''  /  None  /  '   '  /  0                 -> ''            <- and '' matches ''
```

`name (N).ext` is what Windows and Chrome name a duplicate download, so the collision is ordinary,
not exotic. The blank case is the sharper one, for the reason in §1. AT-223.

### 4. AT-207's coverage

`coverage()` **does** read real persisted analyses — `store.load_analysis(source_id)` off disk, and
the fixture writes real `analysis.json` files, so this is not a fixture-only claim. Good.

The hole is the one the dispatch suspected. `coverage()` line 53:

```python
analysis = store.load_analysis(source_id)
if analysis is None:
    continue
```

Measured end to end (`.work/chk-t136/probe7.py`): two sources each contributing a scored issue,
`analysis.json` present for one of them (4/4), absent for the other →

```json
{"observations_used": 4, "observations_expected": 4, "complete": true, "partial_sources": []}
```

The second source's reading is not partial and not zero — it is **unknown** — and the report says
the run was complete. AT-207 was filed because a fragment and a full reading were
indistinguishable; this is that, one level up, inside AT-207's own fix. AT-222, criterion VL14.

### 5. AT-208

**Fixed, and no caller regressed.** `adjudicate(..., expected=None)` writes
`observations_expected=0` (`stages/adjudicate.py:229`); `is_complete` requires
`observations_expected > 0`, so it is False. Sabotage SJ (restoring `len(shifted)`) fails exactly
1 test — `test_omitting_expected_records_UNKNOWN_not_complete` — so the guard is live, not
decorative. The single production caller, `stages/analyze_video.py:181`, still passes the real
product; every other call site is a test. Nothing to charge.

## Sabotage — all ten re-run by me

Isolated `git archive HEAD` extract at `.work/chk-t136/x`, `PYTHONPATH` pinned to the extract's
`src` + `tests`, full suite each time, restored by file copy — never `git stash`/`checkout`/
`restore` in the live tree (AT-101). For each: **the anchor was asserted to match exactly once and
the file re-read as changed** before the run. Extract verified byte-identical to the live tree
after the last restore.

| | Sabotage | Maker | Mine | |
|---|---|---|---|---|
| SA | `at_seconds` returns 0 instead of refusing | 1 | **13** | discriminating |
| SB | `recording_key` keeps the whole cell | 5 | **5** | discriminating |
| SC | `RECORDING_COLUMNS` forgets `Clip` | 8 | **8** | discriminating |
| SD | matching ignores which recording | 1 | **1** | discriminating |
| SE | matching ignores the time window | 2 | **2** | discriminating |
| SF | matching ignores the similarity threshold | 2 | **2** | discriminating |
| SG | one issue may claim many truth rows | 3 | **3** | discriminating |
| SH | CLI exits 0 with nothing to score | 1 | **1** | discriminating |
| SI | coverage always claims complete | 1 | **1** | discriminating |
| SJ | `adjudicate(expected=None)` flatters itself again | 1 | **1** | discriminating |

**Zero INCONCLUSIVE**, as claimed. SA differs (13 vs 1) only because my mutation returns 0.0 for
every cell rather than only for unparseable ones; the class is the same and the guard bites either
way. The manifest's sabotage table is honest and I could not falsify a row of it.

This is worth saying plainly given AT-218's standing complaint about vacuous guards: **the guards
this unit built are not vacuous.** All five failures above are about behaviour the unit never
guarded at all, not about guards that fail to guard.

## Issues addressed, checked against the ledger

- **AT-207** — `open` → stays **open**. Surfacing was built and does read real analyses, but the
  missing-analysis case reintroduces the exact indistinguishability the issue was filed about
  (AT-222). Not moved to `fixed`.
- **AT-208** — → **fixed** (see §5). Only a later re-check moves it to `verified`.

## Notes that are not failures

- I did not re-litigate greedy-vs-optimal; the trade is stated and reasonable.
- The manifest's two self-caught mistakes (the `.py`-file test that asserted openpyxl's error, and
  the byte-identical CLI fixture) are both real corrections and both improve the evidence. The
  second is why sabotages SE and SF discriminate at all.
- `qa/issues.jsonl` carries the id `AT-214` twice, from two different earlier checks. Not this
  unit's doing; filed as AT-225 so it is on the record before either row is closed.
- Reproductions live in `.work/chk-t136/` (`probe1`–`probe7`, `sabotage.py`, extract at `x/`),
  uncommitted per the project's scratch rule.

## Fix direction, in the order I would take it

1. **AT-219 / VL8** — `root = args.root or repo_root()`. One line, and it is what makes every other
   claim about the exit code checkable. Add a test that runs the `done_check` invocation verbatim
   and asserts the path opened is inside the repo.
2. **AT-220 / VL7** — decide what the operator is actually told to run. There is no `issues derive`
   command and no caller of `derive_issues`; either build that command as its own unit or point the
   advice at what exists. Then extend `advice_in_source`'s roots to `scripts/` — the class-level
   guard has now been scoped past a live instance twice.
3. **AT-221 / VL13** — total the candidate key, permutation-test it over the shipped shape.
4. **AT-222 / VL14** — a source with no analysis is a third state, not a skip.
5. **AT-223 / VL10** — refuse a blank recording cell; key on a filename, not on everything before
   the first parenthesis.

T-136 stays `pending`, correctly.
