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

---

# Verdict — t136-scorer (cycle 2)

**Date:** 2026-09-09 · **Cycle checked: 2** · **Commit under check:** `5cba7bb`
· **Bound to:** `d:/autoTesting`
**Contract:** `qa/contracts/video-learning.md` — VL7–VL14, I-VL7 (unchanged this cycle; nothing
was softened and nothing needed tightening).

```
VERDICT: PASS
SCOREBOARD: 8/8 criteria met, 1/1 invariants hold
FAILURES: none
LIVE-BROWSER: not-applicable (changed paths are core/env.py, stages/score.py, cli.py, cli_video.py,
  cli_issues.py, scripts/score_video_issues.py, docs/MAP.md, pyproject.toml, tests/*, and
  ui/app.py — whose entire diff is swapping `load_dotenv(repo_root()/".env")` for the shared
  `load_repo_env()` inside the existing lifespan hook. No route, template, component or rendered
  output changed. I read the ui/app.py diff myself rather than taking the manifest's word: the
  claim holds, and Mode D does not apply.)
ISSUES-WRITTEN: AT-229
EXPLANATION: Every cycle-1 finding is independently re-verified as fixed by driving the shipped
paths, not by reading the diff: the `done_check` command with no `--root` now exits 0 and scores a
real populated project; `ingest analyze` and `issues derive|list|export` all really run end to end
(register -> prep -> analyze -> derive -> list -> export -> score against the real 7-row workbook);
the match key is order-independent over 200 shuffles and over the exact permuted pair that moved
recall 0.5/1.0 in cycle 1; blank and `name (N).ext` recording cells no longer collide or self-match;
and coverage now reports `sources_with_no_analysis` and refuses `complete: true` while one exists.
All seven sabotages discriminate in my own `git archive` extract, EG included — the maker's
INCONCLUSIVE-then-pinned account of it is confirmed. T-136 itself stays `pending`: the real
`projects/erp/` still has no registered source, so the done_check still exits 2 — but now for the
reason it says, and the sequence that would close it is runnable.
```

## What I re-ran (my own evidence, none of it the maker's)

| Command | My result |
|---|---|
| `uv run pytest` (bare — `addopts=-q` already set) | **867 passed, 2 skipped**, 1 warning, 157s |
| `uv run ruff check src tests scripts` | `All checks passed!` (exit 0) |
| `uv run autotester doctor` | `doctor: clean` (exit 0) |
| `uv run autotester providers` | `available providers: gemini, langchain-fallback, mock` |
| `uv run autotester issues --help` | `derive`, `list`, `export` — all three present |
| `uv run autotester ingest --help` | `register list prep frames run` **+ `analyze`** |
| T-136's `done_check` verbatim, real repo | exit **2**, refusal naming a command that now exists |
| T-136's `done_check` verbatim, populated root | exit **0**, `recall 1.0`, 7/7 — **it can close** |

Working tree: `.goal/*` modified and `projects/pathlynks/approvals.jsonl` untracked as the dispatch
said. `projects/saucedemo/` and `qa/evidence/browser-…` appeared *during my own pytest run* — see
AT-229; not this unit's drift.

## 1. AT-219 driven the way it ships (VL8)

`ProjectStore("erp", None).paths.issues` → `D:\autoTesting\projects\erp\issues.jsonl`, and under
`AUTOTESTER_ROOT` → `<that root>\projects\erp\issues.jsonl`. Inside the repo, as VL8 demands.

The cycle-1 verdict said "it exits 2 for the right reason now" would not be the same as "it can
close", so I built the case that settles it. Under `AUTOTESTER_ROOT` pointed at a scratch root I
populated with **the real 7 truth rows from `ERP_Issues_Trainers.xlsx` turned into real `Issue`
rows through the real `ProjectStore`**, I ran the `done_check` string **verbatim, no `--root`**:

```
EXIT=0
{"truth_rows": 7, "reported": 7, "found": 7, "missed": 0, "false_positives": 0, "recall": 1.0,
 "coverage": {"observations_used": 0, "observations_expected": 0, "complete": false,
              "partial_sources": [], "sources_with_no_analysis": ["src0", "src1"]}, …}
```

T-136 is no longer structurally incapable of closing. It is merely not done. Against the real
`projects/erp/` (which still holds only `cases.jsonl`, `project.json`, `rubrics/`, `runs/`) the same
command exits 2 with the honest refusal — and the command that refusal names now exists.

## 2. AT-220 — the new commands driven, not merely listed (VL7)

I did not stop at `--help`. In a scratch root, through the shipped CLI only:

```
ingest register erp "…/erp1.mp4"     -> src_a6d5d1b66aa0  (exit 0)
ingest prep erp src_a6d5d1b66aa0     -> 30s, 1 chunk, 6 narration segments (exit 0)
ingest analyze erp … --models mock   -> exit 2: "every provider call failed — nothing to
                                        adjudicate. Check `autotester providers`"
issues derive erp                    -> "erp: 2 new issue(s); 2 total" (exit 0)
issues derive erp   (again)          -> "erp: 0 new issue(s); 2 total"  — idempotent
issues list erp                      -> both rows, severity + MM:SS + label + title
issues export erp                    -> "erp: 2 issue(s) -> …/projects/erp/issues.xlsx"
score_video_issues.py (no --root)    -> exit 0: reported 2, found 0, fp 2, coverage partial
```

`ingest analyze` **reaches `analyze()`** — the exit 2 is `NoObservations` raised out of the stage
and caught by the command, which is the stage refusing rather than the command being absent (the
registry's `mock` provider has no queued responses by construction, so every call fails; that is the
stub's nature, not a defect of this wiring). To get past it I wrote a real `analysis.json` through
the real `ProjectStore`/`VideoAnalysis` and drove `issues derive` on it: it produced two real `Issue`
rows, content-addressed and idempotent on a second run, which `list`, `export` and the scorer then
all consumed. **Track A is genuinely runnable end to end.** No command exists-and-errors-on-first-use.

`issues derive`'s own refusal names `autotester ingest analyze <project> <source-id>` — which also
exists. The advice chain terminates in real commands at every hop.

## 3. AT-228 and the leak, probed in the inverse (the premise, not the guard)

The guard itself, driven both ways in one process:

```
PYTEST_CURRENT_TEST set   -> `providers` = mock ;  GEMINI_API_KEY in os.environ: False
marker removed            -> `providers` = gemini, langchain-fallback, mock ; …: True
```

Then I went looking for a way around it rather than accepting it:

- **Subprocesses the suite spawns.** The only `env=` construction in the whole test tree is
  `tests/test_score_cli.py:162`, and it is `{**os.environ, …}` — the marker is inherited, so the
  child is guarded too. Every other `subprocess` use in `tests/` (media, frames, shellout, score CLI)
  inherits the environment unmodified. Nothing strips `PYTEST_CURRENT_TEST`.
- **`CliRunner` in-process.** Verified above: nothing lands in `os.environ`.
- **Import-time loads.** `load_repo_env()` is called only from `cli.py`'s `@app.callback()` and
  `ui/app.py`'s lifespan — neither at module import, so collection (when the marker is not yet set)
  loads nothing.
- **The bypass that does exist, and why it is not a leak here.** `scripts/bench_trial.py`,
  `scripts/regression_proof.py` and `scripts/run_pathlynks_first_cases.py` call `dotenv.load_dotenv`
  directly, unguarded. `tests/conftest.py` and two test modules import those scripts — but only for
  pure helpers; the `load_dotenv` calls sit inside `main()` and no test calls `main()`. So the
  premise holds today. It holds by nobody calling those entry points from a test, which is thinner
  than the guard, and I note it as a question rather than a finding (below).

`core/redact.assert_no_raw_secrets` and the screenshot masking are untouched by this unit; `.env`
remains gitignored and no key appears in any artifact I produced.

## 4. AT-221's totality (VL13)

Permuted through the real path, not the helper:

- The **exact cycle-1 case** (T1/T2 at 10s, issues X/Y equally similar at 0.8, `--threshold 0.7`):
  both orders now produce **byte-identical** report JSON, recall 1.0 either way.
- **200 random shuffles** of an 8-issue / 8-truth-row set: every report identical to the baseline.
- **Ids that tie.** `Issue.id` is content-addressed over project/source/screen/category/at-bucket/
  title, so two issues *can* share an id while differing in `what_is_wrong`. I built that pair: both
  orders yield the same recall, the same similarity and the same `false_positive_titles` — the
  report content does not permute, which is what VL13 asks for. (The store also refuses the second
  one — `add_issue` is idempotent on id — so `list_issues()` cannot even hand it over.)
- **Empty ids.** I could only construct these by `object.__setattr__` past `model_post_init`, which
  always stamps a non-empty id; with two forced-blank ids the choice does permute. Unreachable
  through any construction path in the codebase, so it is not a finding — recorded here so the next
  cycle knows it was tested rather than missed.

## 5. AT-223 / `recording_key` hunted for a survivor (VL10)

```
'erp1.mp4 (Divya Kamboj, …)' -> 'erp1.mp4'      'clip (1).mp4' -> 'clip (1).mp4'
'erp1.mp4(no space)'         -> 'erp1.mp4'      'clip (2).mp4' -> 'clip (2).mp4'   (distinct)
'erp (final) cut.mp4'        -> whole cell      'a.b.mp4 (x)'  -> 'a.b.mp4'
'ERP1.MP4' / '  erp1.mp4  '  -> 'erp1.mp4'      unicode 'रिकॉर्डिंग.mp4 (टीम)' -> 'रिकॉर्डिंग.mp4'
'' / '   ' / None / 0        -> '\x00unknown'   'v1.2 (draft)' -> whole cell
```

I could not build a collision: no two distinct recordings map to one key, and the sentinel cannot
equal any real cell (`\x00` is not producible from a workbook cell that reads as a filename).
Re-measured the cycle-1 killer: an all-blank recording column against blank-labelled issues now
scores **recall 0.0 with both rows counted as false positives**, where cycle 1 measured 1.0.

The shapes that *do* keep the whole cell — a label with no extension (`erp1`), a dot that is not an
extension (`v1.2 (draft)`), a parenthesis mid-name (`erp (final) cut.mp4`) — fail only by
**under-matching** (a truth row finds no report, recall goes down). That is the conservative
direction and VL10 asks only that absence and collision cannot manufacture agreement. Not charged.

Also re-verified on the way past: `at_seconds` still refuses `''`, `None`, `'abc'`, `'1:2:3'`
(TruthSheetError, never second zero); both real workbooks load off disk — Trainers 12 columns /
7 rows, ALL 13 columns / 32 rows (VL9); `--window` measured flipping recall at 20s and
`--threshold` at 0.9 on a fixture the bounds can bite (VL12); `stages/score.py` and the CLI contain
no provider, network, clock or randomness (I-VL7).

## 6. Sabotage — all seven re-run by me, EG included

`git archive HEAD` extract at `.work/chk2-t136/x`, `PYTHONPATH` pinned to the extract's `src` +
`tests`, full suite each time, restored by file copy — never `git stash`/`checkout`/`restore` in
the live tree (AT-101). Each anchor **asserted to match exactly once** and the file **re-read as
changed** before the run. Baseline in the extract: 867 passed, 2 skipped.

| | Sabotage (my own mutation, not the maker's script) | Maker | Mine | |
|---|---|---|---|---|
| EA | `--root` default walks to the drive again | 1 | **1** | discriminating |
| EB | tie-break drops the issue id | 1 | **1** | discriminating |
| EC | coverage stops recording an unanalysed source | 1 | **1** | discriminating |
| ED | `recording_key` splits on `(` always | 1 | **1** | discriminating |
| EE | an unknown recording may match another | 4 | **4** | discriminating |
| EF | the loader leaks into a test process | 1 | **1** | discriminating |
| EG | the CLI stops loading `.env` | 0→1 | **1** | discriminating |

**EG confirmed.** Replacing `load_repo_env()` in `cli.py`'s callback with `pass` now fails exactly
one test. The maker's account is accurate: the guard made the wiring's *effect* unobservable inside
a test process, so the wiring is pinned by watching the **call** (a spy on `cli.load_repo_env`)
instead — which is the right shape, and it is the shape AT-206 asked for. Reporting the first
attempt as INCONCLUSIVE rather than "the guard is vacuous" was correct per C7.

After the last restore, `git hash-object` on all four sabotaged files matches the live tree's blobs
exactly.

## Criteria, one by one

| | Verdict | Evidence |
|---|---|---|
| VL7 | **met** | `issues derive/list/export` and `ingest analyze` all exist **and run**; the refusal's named command produced real rows; its own refusal names another real command |
| VL8 | **met** | no-`--root` resolves inside the repo; `done_check` verbatim exits 0 on a populated root |
| VL9 | **met** | both workbooks read off disk: 12 cols/7 rows and 13 cols/32 rows |
| VL10 | **met** | `At` refused for unparseable; blank → a sentinel that matches nothing; `clip (1)/(2)` distinct; all-blank sheet now 0.0 |
| VL11 | **met** | recording ∧ window ∧ threshold all required (EE + the cycle-1 SD/SE/SF/SG remain live); each row claimed once (`remaining.remove`); leftovers counted as FPs — seen in the real run (2 reported, 0 found, 2 fp) |
| VL12 | **met** | window 5/10 → 0.0, 20/60 → 1.0; threshold 0.1/0.5 → 1.0, 0.9/0.99 → 0.0 |
| VL13 | **met** | identical report over 200 shuffles, over the cycle-1 pair, and over an id-tie pair |
| VL14 | **met** | `sources_with_no_analysis` reported; `complete` false while one exists — measured in the real end-to-end run and pinned by EC |
| I-VL7 | **holds** | no provider, network, clock or randomness in `stages/score.py` or the CLI |

## Ledger

- **AT-219** → **fixed** (§1) · **AT-220** → **fixed** (§2) · **AT-221** → **fixed** (§4) ·
  **AT-222** → **fixed** (§5/VL14) · **AT-223** → **fixed** (§5) · **AT-228** → **fixed** (§3).
- **AT-207** → **fixed**. Cycle 1 held it open because the missing-analysis case reintroduced the
  indistinguishability it was filed about. That case is now reported as its own third state and the
  coverage block reaches a reader in the shipped output. Only a later re-check moves any of these to
  `verified`.
- **AT-224** (no `Issue.project` filter) and **AT-225** (`AT-214` used twice — still duplicated,
  228 rows) stay **open**; neither was claimed by this unit and no criterion requires them.
- **AT-229** filed (new, medium): running `uv run pytest` writes into the repo working tree —
  `projects/saucedemo/` (project.json, crawl/, sources/, approvals.jsonl) and
  `qa/evidence/browser-…-checker/` appeared at 09:19 during my first suite run and are untracked.
  A suite that dirties the tree it is judged in corrupts the sweep's own bypass detection, which
  reads `git status`. Not this unit's doing; filed so it is on the record.

## Questions, not failures

- The three `scripts/*.py` that call `dotenv.load_dotenv` directly are unguarded by
  `core/env.py`'s test-process refusal. Today no test calls their `main()`, so nothing leaks — but
  C3 ("one concept, one place") points at the same fix that AT-228 just made for the CLI and the UI,
  and the premise would then hold by construction rather than by nobody calling them. Worth a unit;
  not charged here.
- `at_seconds` reads a bare number as seconds. Both real workbooks hold `MM:SS` strings so it never
  fires today, and an Excel time-formatted cell (a `datetime.time`) is refused rather than
  misread — so this is not the "scored as second zero" failure. Noted only because a hand-edited
  `29` in the `At` column would silently mean 29 seconds, which a reader might have meant as 29
  minutes.
- Reproductions live in `.work/chk2-t136/` (`probe_root.py`, `mk.py`, `mkanalysis.py`, `perm.py`,
  `rk.py`, `blank.py`, `leak.py`, `vl.py`, `sab.py`, extract at `x/`), uncommitted per the project's
  scratch rule.

## T-136 itself

**Stays `pending`, and for a materially better reason than last cycle.** The machinery is complete
and every gate on it now holds; what is missing is a real reading — no source registered against the
real `projects/erp/`, so no analysis, so no derived issues, so no recall number. That is now a
sequence a maker can run (`ingest register → prep → analyze → issues derive → score`) with the
credential this machine actually has, not a human gate. This PASS certifies the scorer unit, not
T-136's acceptance.
