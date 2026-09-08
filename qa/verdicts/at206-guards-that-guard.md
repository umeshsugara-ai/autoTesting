# Verdict — at206-guards-that-guard

**Date:** 2026-09-09
**Unit:** AT-206 + AT-192 + AT-193 + AT-170 — make the class guards guard their class
**Commit checked:** `9351387`
**Cycle checked:** 1
**Contract:** `qa/contracts/core-invariants.md` C7 · `qa/contracts/video-learning.md` VL1
**Mode:** A, bound to `D:/autoTesting`. Adapter `coding`.

## VERDICT: FAIL

**SCOREBOARD:** 8/11 criteria met, 2/2 invariants hold

---

## What I re-ran myself

Everything below was produced in this session. Nothing in the manifest was read as evidence.

**Adapter slot 1, on the live tree:**

- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`

**Baseline, in an isolated `git archive HEAD` extract** (`.work/chk206/base`, `PYTHONPATH`
pinned to the extract's own `src`; the live tree was never `stash`ed, `checkout`ed or
`restore`d — AT-101):

```
uv run pytest   →   817 passed, 2 skipped, 1 warning in 72.02s
```

`git status --porcelain` on `src` and `tests` is empty before and after every experiment below.

**Eleven sabotages**, each in its own fresh copy of the extract, each asserting its anchor
matched **exactly once** and the file re-read as **changed** before any result was believed
(C7), each followed by the **full** suite (`addopts = -q` is already set, so no command-line
`-q`; `FAILED` lines counted):

| # | Sabotage | Failures | Which tests |
|---|---|---|---|
| S1 | `_render`'s `JoinedStr` folding **deleted whole** | **2** | `..._sees_the_COMPOSED_site...`, `..._imported_from_another_module...` |
| S2 | `COMMAND` requires a leading backtick (AT-178 undone) | **2** | same two |
| S3 | `_imported_constants` returns `{}` (AT-192 undone) | **1** | `..._reports_what_it_could_not_resolve` |
| S4 | `_is_documentation` excludes the parent node only (AT-193 undone) | **1** | `..._written_as_an_f_string_is_not_read_as_advice` |
| S5 | dedup key back to `(file, command)` (AT-206 proper) | **1** | `..._sees_the_COMPOSED_site_not_just_the_constant` |
| S6 | `unresolved_in` returns `[]` unconditionally | **1** | `..._hole_report_actually_reports_a_hole` |
| S7 | `-ss` before `-i` in `encode_chunks` | **1** | `..._chunk_is_cut_with_the_seek_AFTER_the_input` |
| S8 | `-ss` before `-i` in `extract_frame` | **1** | `..._frame_is_grabbed_with_the_seek_AFTER_the_input` |
| S9 | `ffmpeg_available` true when **either** binary runs | **2** | `..._one_binary_present_is_not_enough[ffmpeg]`, `[ffprobe]` |
| S10 | `probe` raises instead of returning zeros | **2** | `..._cannot_be_probed_returns_zeros`, `..._unreadable_json_...` |

Every one of the seven sabotages the dispatch required bites. **The four AT-170 sabotages a
previous checker ran to zero failures each now fail.** The manifest's own discrimination counts
(2, 2, 1, 1, 1, 1 on the collector; 1, 1, 2, 2 on the media boundary) reproduce exactly.

### C7's zero-failure clause fired once — on my own harness, not on the maker's

My first S5 changed only the two membership expressions and left the `seen` type annotation
and one of the two key constructions inconsistent, so the check key and the add key never
matched: dedup was **disabled** rather than **reverted**. Anchor matched once, file changed,
and the suite came back **823 passed / 0 failures** — six *more* passing cases than baseline,
which is the tell. Under C7 that is INCONCLUSIVE about the guard, not evidence of a vacuous
one. Re-run with all three lines changed together (a true revert of the AT-206 hunk) it fails
`test_the_collector_sees_the_COMPOSED_site_not_just_the_constant`, as recorded above. Stated
because the null result was mine and the clause is what caught it.

---

## Criteria

| # | Claim judged | Verdict |
|---|---|---|
| 1 | Deleting the renderer fails the suite (AT-206's acceptance) | **met** — S1, 2 failures |
| 2 | Reverting the dedup key to `(file, command)` fails | **met** — S5, 1 failure |
| 3 | AT-178's backtick regression fails | **met** — S2, 2 failures |
| 4 | AT-192 (cross-file constants) is guarded | **met** — S3, 1 failure |
| 5 | AT-193 (documentation descendants) is guarded | **met** — S4, 1 failure |
| 6 | The hole reporter cannot be silently emptied | **met** — S6, 1 failure |
| 7 | Four AT-170 media behaviours are guarded on real argv | **met** — S7–S10, 6 failures |
| 8 | `uv run pytest` / ruff / doctor clean, reproduced | **met** — 817+2, clean, clean |
| 9 | "`len(commands) >= 6` … is gone. **Sites are now pinned individually, by line**" | **NOT met** — see F1 |
| 10 | The composed-site guard cannot be satisfied for a wrong reason | **NOT met** — see F2 |
| 11 | The hole detector's two exemptions are narrow enough to be honest | **NOT met** — see F3 |

**Invariants:** C7 (verification independent; sabotage asserts it applied; zero-failure is
INCONCLUSIVE) **holds** — the maker's harness discipline is real and I reproduced it from
scratch. VL1 (a missing tool produces a smaller result, never an exception) **holds** and is
now guarded for the first time (S9, S10).

---

## FAILURES

### [C9-claim] F1 · sev: high · the guard that used to bite on site removal was deleted and nothing replaced it · issue: AT-210

The manifest says the `len(commands) >= 6` slack "is gone" and that "sites are now pinned
individually, by line." The first half is true. The second is not, and the net effect is a
**loss** of coverage, not a gain.

`test_every_command_the_code_names_is_one_the_cli_exposes` is `@pytest.mark.parametrize`d over
`advice()`. Parametrisation validates the sites that *are* collected; it pins none of them into
existence. When a site stops being collected its test case simply **stops existing** — pytest
reports one fewer passing test and no failure.

Measured, in the extract, on the two files this class was built for:

```
P1  src/autotester/core/consent.py:35   "autotester approve" -> "aaaa approve"   (AT-178's own site)
      -> 25 passed, 0 failures   (baseline for these two files: 26 passed)
P2  src/autotester/doctor.py:114        "autotester map"     -> "aaaa map"
      -> 25 passed, 0 failures
```

Of the 11 collected sites, exactly **two** are pinned by an existence assertion —
`stages/media_prep.py:30` and `:157`, by the AT-206 test. The other **nine can each be deleted
with zero failures**. Under the old `>= 6` bound, deleting six of them did fire; under the new
guard, deleting all nine does not. For the unit whose whole subject is that a check which
cannot fail is not a check, this is the class arriving inside its own fix — the same shape the
manifest correctly identifies in AT-206 and in sabotage BF.

Fix direction: assert the collected set against a committed inventory (file + command, with a
line-independent identity), so a site leaving the codebase is a failure and adding one is a
one-line diff — not a silently smaller parametrisation.

### [C7] F2 · sev: medium · `test_the_collector_sees_the_COMPOSED_site_not_just_the_constant` passes on a stranger's line number · issue: AT-211

The test builds `lines = {a.line for a in prep}` over **every** file's `ingest prep` sites, then
indexes those line numbers into `stages/media_prep.py`:

```python
prep = [a for a in advice() if a.command == "ingest prep"]
lines = {a.line for a in prep}
source = (SRC / "stages" / "media_prep.py").read_text(...).splitlines()
...
composed = [n for n in lines if "PREP_COMMAND" in source[n - 1] ...]
```

Nothing filters `prep` to `media_prep.py`. A line number harvested from any other module is
looked up in `media_prep.py`'s text, so an unrelated site at the right *number* satisfies the
assertion the renderer is supposed to be the only thing that can satisfy.

Measured (P3): renderer folding deleted (S1) **and** a decoy `HINT = "autotester ingest prep"`
placed at line 157 of a new `src/autotester/core/pad_probe.py` — `media_prep.py:157` is the
f-string that interpolates `PREP_COMMAND`. Result: `test_the_collector_sees_the_COMPOSED_site_not_just_the_constant`
**passes**. Only `test_a_constant_imported_from_another_module_still_resolves` — which runs on
a synthetic source, not on the repo — caught the deletion. So AT-206's own guard survives its
own sabotage by coincidence of a sibling test, which is precisely the property this unit exists
to remove.

Fix direction: filter `prep` to `a.where == Path("stages") / "media_prep.py"` before taking
line numbers; the file the lines are read from must be the file the lines came from.

### [C7] F3 · sev: medium · a module-level name bound to a non-constant string is invisible to both the collector and the hole reporter · issue: AT-212

`_module_level_names` exempts every name the module binds at top level, on the stated premise
that "a SCREAMING_CASE name bound here to a non-string is a number or a tuple, never a command."
The premise is true only of *literal* bindings. `_module_constants` resolves `NAME = "literal"`
only, so any command name bound to an **expression** is unresolvable by the renderer **and**
exempted from the hole report by the very same name.

Measured (P6) — a module of exactly the shape this codebase already writes:

```python
PREP_COMMAND = os.environ.get("CMD", "autotester ingest prep")
def f(slug):
    raise ValueError(f"run `{PREP_COMMAND} {slug}` on the HOST first")
```

Result: **27 passed, 0 failures.** The site is collected as no command at all, and
`unresolved_in_source(SRC) == []` still holds. A real command name, a real operator-facing
message, and the detector built to make blind spots countable is silent — which is the AT-192
hole with a different binding form. (P4, the lowercase-alias variant, likewise: 26 passed, 0
failures. That one I consider defensible design; this one is not, because the name *is*
SCREAMING_CASE and the exemption fires only because the module happens to assign it.)

Fix direction: exempt a module-level name only when its binding is a resolved **non-string
constant**, not merely because the name is bound.

---

## Not failures — questions and observations

- **The `Recorder` fake is honest about ordering, and silent about the program.** S7–S10 prove
  the media tests read the real argv and would fail against any stub that did not produce
  ffmpeg's actual argument order — that question is answered affirmatively. But nothing asserts
  `argv[0]`: renaming `encode_chunks`' binary to `ffmpeg-x` (P5) yields **0 failures**, so the
  stage could shell out to a program that does not exist and the guard would say nothing. Filed
  low as AT-213 rather than as a failure — VL1 is about degradation, not about the binary's
  name, and the manifest never claimed it.
- The manifest's closing paragraph ("it does not claim the class is fixed") is the right posture
  and I am not charging it for the claim it declined to make. F1 is charged because the manifest
  *did* make the narrower claim, and it does not hold.
- Three of the four named issues are genuinely and independently fixed; the ledger is updated
  accordingly below. The FAIL is about residue this unit introduced, not about work it did not do.

## Ledger

- `AT-206`, `AT-192`, `AT-193`, `AT-170` → **verified** (each sabotage above discriminates).
- New: `AT-210` (high), `AT-211` (medium), `AT-212` (medium), `AT-213` (low).

## ISSUES-WRITTEN: AT-210, AT-211, AT-212, AT-213

## EXPLANATION

Every sabotage the manifest claims discriminates does discriminate, reproduced from scratch in
an isolated extract, and the four AT-170 mutations that a previous checker ran to zero failures
now each fail — the four named defects are really fixed. The FAIL is for what the unit's own
subject holds it to: it removed the `len(commands) >= 6` bound, which did bite when sites
disappeared, and replaced it with a parametrisation that cannot, leaving nine of eleven advice
sites deletable with zero failures; the one guard it did pin can be satisfied by a line number
from a different file; and the hole detector it added is blind to a command name bound to an
expression. A guard that cannot fail is this unit's own definition of the defect.
