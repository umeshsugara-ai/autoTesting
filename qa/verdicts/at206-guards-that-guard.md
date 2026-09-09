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

---

# Verdict — at206-guards-that-guard (cycle 2)

**Date:** 2026-09-09
**Unit:** AT-206 + AT-192 + AT-193 + AT-170, plus AT-210/211/212/213 from cycle 1
**Commit checked:** `eabc638` (manifest at `7c168e0`)
**Cycle checked:** 2
**Contract:** `qa/contracts/core-invariants.md` C7 · `qa/contracts/video-learning.md` VL1
**Mode:** A, bound to `D:/autoTesting`. Adapter `coding`.

## VERDICT: PASS

**SCOREBOARD:** 11/11 criteria met, 2/2 invariants hold

---

## What I re-ran myself

Everything below was produced in this session by a checker with no cycle-1 context beyond the
cycle-1 verdict file. Nothing in the manifest was read as evidence.

**Adapter slot 1, live tree:**

- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`

**Baseline, in an isolated `git archive HEAD` extract** (`.work/chk206c2/base`, `PYTHONPATH`
pinned to the extract's own `src`; the live tree was never `stash`ed, `checkout`ed or `restore`d
— AT-101):

```
uv run pytest   →   818 passed, 2 skipped, 1 warning in 77.59s
```

Every sabotage below ran through `.work/chk206c2/drive.py`, which asserts — before any result is
believed — that its **anchor matched exactly once** and that the **file re-read as changed**
(C7); restore is by file copy from a snapshot, never by git. `git status --porcelain` on `src`
and `tests` was empty before and after every experiment. Each run is the **full** suite
(`addopts = -q` is already set, so no command-line `-q`); `FAILED` lines counted.

### The fourteen required sabotages — all fourteen discriminate

| # | Sabotage | Fails | Tests |
|---|---|---|---|
| S1 | `core/consent.py`'s advice site deleted (AT-210 attack 1) | **5** | `..._no_advice_site_can_vanish_unnoticed` + `test_consent`, `test_crawl_real_cli`, `test_explore`, `test_ui_crawls` |
| S2 | `doctor.py`'s `map` site deleted (AT-210 attack 2) | **1** | `..._no_advice_site_can_vanish_unnoticed` |
| S3 | renderer `JoinedStr` folding deleted **+** decoy `HINT = "autotester ingest prep"` at line 157 of a new module (AT-211 replay) | **3** | `..._sees_the_COMPOSED_site...`, `..._imported_from_another_module...`, `..._can_vanish_unnoticed` |
| S4 | `PREP_COMMAND = os.environ.get("CMD", "autotester ingest prep")` planted in `src/` (AT-212) | **2** | `..._reports_what_it_could_not_resolve`, `..._can_vanish_unnoticed` |
| S5 | `_imported_constants` returns `{}` (AT-192 undone) | **1** | `..._reports_what_it_could_not_resolve` |
| S6 | `_is_documentation` excludes the parent node only (AT-193 undone) | **1** | `..._f_string_is_not_read_as_advice` |
| S7 | dedup key back to `(file, command)` (AT-206 proper) | **2** | `..._sees_the_COMPOSED_site...`, `..._can_vanish_unnoticed` |
| S8 | `unresolved_in` returns `[]` unconditionally | **1** | `..._hole_report_actually_reports_a_hole` |
| S9 | `COMMAND` requires a leading backtick (AT-178 undone) | **3** | `..._COMPOSED_site...`, `..._imported_from_another_module...`, `..._can_vanish_unnoticed` |
| S10 | `-ss` before `-i` in `encode_chunks` | **1** | `..._chunk_is_cut_with_the_seek_AFTER_the_input` |
| S11 | `-ss` before `-i` in `extract_frame` | **1** | `..._frame_is_grabbed_with_the_seek_AFTER_the_input` |
| S12 | `ffmpeg_available` checks `ffmpeg` only | **1** | `..._one_binary_present_is_not_enough[ffprobe]` |
| S13 | `probe` re-raises instead of returning zeros | **2** | `..._cannot_be_probed_returns_zeros`, `..._unreadable_json_...` |
| S14 | `ffmpeg`→`ffmpeg-x` (both call sites) + `ffprobe`→`ffprobe-x` (AT-213) | **3** | both seek tests + `..._cannot_be_probed_returns_zeros` |

**Zero INCONCLUSIVE results this cycle** — every one of the fourteen produced at least one
failure, so C7's zero-failure clause had nothing to fire on. S1, S2, S3 and S4 are the cycle-1
checker's own four constructions, rebuilt from its verdict text and re-run here: **each one that
previously produced zero failures now fails.**

Two deltas from cycle 1 worth stating, neither a defect: S12 fails 1 rather than 2 because I
narrowed the tuple to `("ffmpeg",)` (only the `ffprobe` parametrisation can then fire) where the
cycle-1 checker made the function true on *either* binary; and S5 fails only the hole-report test
because no command constant in this repo is currently imported across a file boundary, so
cross-file resolution has no live site to lose.

### The three pressure probes the dispatch asked for

**P1 — a compensating pair inside one file: 818 passed, 0 failures.** `doctor.py`'s real
`autotester map` advice was deleted **and** an identical live `"run \`autotester map\` (decoy)"`
string added at a different line of the same file. `EXPECTED_SITES` is unchanged (it is keyed on
`(file, command)`) and `EXPECTED_SITE_COUNT == 11` is unchanged, so the guard is silent.

This is a **null result whose mutation is proven live** — S2 is the same deletion without the
compensation and it fails — so it is not INCONCLUSIVE under C7; it is a real, measured bound on
the guard. **It is not charged as a failure**, for two reasons stated plainly. First, a
line-independent identity is exactly what the cycle-1 verdict's own fix direction prescribed
("assert the collected set against a committed inventory (file + command, with a
line-independent identity)"), and softening or re-litigating a fix I prescribed, after the maker
built it, would be the checker moving the target. Second, the compensating change is not a way to
*lose* the advice: it requires adding a live string that names the same command in the same file,
which is itself a real advice site that `test_every_command_the_code_names_is_one_the_cli_exposes`
still validates against the CLI. The operator still gets told to run `autotester map` from
`doctor.py`. Recorded as **AT-214 (low)** so the bound is countable rather than folklore.

**P2 — a site moved between files: 5 failures.** `core/consent.py`'s `approve` advice deleted and
an identical `"uv run autotester approve x --kind y"` added to `doctor.py`.
`test_no_advice_site_can_vanish_unnoticed` fails on **both** halves — `gone:
('core/consent.py', 'approve')` and `new: ('doctor.py', 'approve')` — so the inventory is
genuinely file-keyed and breaks in both directions. Four consent/crawl/explore/ui tests fail
alongside it.

**P3 — is the composed `media_prep.py` site individually required: 1 failure.**
`{PREP_COMMAND}` in the refusal replaced by the literal text `autotester ingest prep`, with the
constant definition left intact. Site count stays 11 and `EXPECTED_SITES` is unchanged, but
`test_the_collector_sees_the_COMPOSED_site_not_just_the_constant` **fails** on its `composed`
assertion. So the constant-definition site alone cannot satisfy the guard, and
`EXPECTED_SITE_COUNT == 11` is not the thing carrying that weight — the interpolation assertion
is. The two `media_prep.py` sites are each individually required, by different tests.

### `NEVER_A_COMMAND` attacked with eight binding forms — it holds

Collector-level probe of `advice_in` / `unresolved_in` against a module that hides a real command
behind each binding form:

| Binding form | collected as advice | reported as a hole |
|---|---|---|
| `ast.IfExp` — `"autotester ingest prep" if os.name else "x"` | yes | yes |
| `ast.BinOp` concat — `"autotester " + "ingest prep"` | yes | yes |
| f-string constant — `f"autotester ingest prep"` | yes | yes |
| tuple unpacking — `PREP_COMMAND, _OTHER = ("autotester ingest prep", 1)` | yes | yes |
| starred unpack — `*PREP_COMMAND, _Z = [...]` | yes | yes |
| bound in `if TYPE_CHECKING:` then rebound to `os.environ[...]` | no | **yes** |
| `AnnAssign` to a call — `PREP_COMMAND: str = os.environ["C"]` | no | **yes** |
| `PREP_COMMAND: str = ()` | no | no — but the value genuinely *is* an empty tuple; no command is hidden |

I could not construct a binding that both conceals a real command string and escapes the hole
report. The tuple and starred forms are the interesting near-misses: `_module_level_names` sees
`isinstance(value, NEVER_A_COMMAND)` and would exempt, but the target is an `ast.Tuple` rather
than an `ast.Name`, so the comprehension binds nothing and no exemption is granted. That is luck
rather than intent, but it is correct luck, and the hole report catches the form regardless. The
AT-212 tightening stands up under attack.

---

## Criteria

| # | Claim judged | Verdict |
|---|---|---|
| 1 | Deleting the renderer fails the suite (AT-206's acceptance) | **met** — S3, 3 failures |
| 2 | Reverting the dedup key to `(file, command)` fails | **met** — S7, 2 failures |
| 3 | AT-178's backtick regression fails | **met** — S9, 3 failures |
| 4 | AT-192 (cross-file constants) is guarded | **met** — S5, 1 failure |
| 5 | AT-193 (documentation descendants) is guarded | **met** — S6, 1 failure |
| 6 | The hole reporter cannot be silently emptied | **met** — S8, 1 failure |
| 7 | Four AT-170 media behaviours are guarded on real argv | **met** — S10–S13, 5 failures |
| 8 | `uv run pytest` / ruff / doctor clean, reproduced | **met** — 818+2, clean, clean |
| 9 | **AT-210** — an advice site cannot vanish unnoticed | **met** — S1 (5) and S2 (1), the cycle-1 attacks that scored zero; P2 confirms the inventory is file-keyed both ways |
| 10 | **AT-211** — the composed-site guard cannot be satisfied for a wrong reason | **met** — S3 replays the cycle-1 decoy-at-line-157 attack and now fails it, including the COMPOSED test itself; P3 confirms the composed site is individually required |
| 11 | **AT-212** — the hole detector's exemptions are narrow enough to be honest | **met** — S4, and eight binding forms attacked without finding an escape |

**Invariants.** C7 (verification independent; sabotage asserts it applied; a zero-failure result
is INCONCLUSIVE until the mutation is shown live) **holds** — I reproduced the maker's discipline
from scratch and applied the zero-failure clause to my own P1 rather than reporting it as a
vacuous guard. VL1 (a missing tool produces a smaller result, never an exception) **holds**, and
is now guarded on the program as well as the argument order (S14).

## FAILURES

None.

## Not failures — observations

- **AT-214 (low), the P1 bound.** The inventory's identity is `(file, command)`, so a site can be
  relocated within its own file without a failure. Prescribed by cycle 1 and harmless in the
  direction that matters (the file still names a real command, still CLI-validated). Filed so
  that the next person who widens `EXPECTED_SITES` reads a measurement rather than guessing.
- **`unresolved_in` reads only `ast.Name` interpolations.** A command hidden behind a `Subscript`
  or `Attribute` (`f"{CMDS[0]}"`, `f"{MESSAGES.PREP}"`) is neither collected nor reported. This is
  outside every claim the manifest makes — the docstring says SCREAMING_CASE *names*, and that is
  what it does — and this codebase writes no such form today. Raised as a question, not a finding;
  I would not defend it as a defect at >80 %.
- The manifest's discrimination counts (1, 1, 3, 3, 1, 1, and 3 on the AT-211 replay) are
  consistent with mine where the sabotages are the same shape. Where mine differ (S5, S12) the
  cause is my mutation, not the maker's tests, and is stated above.
- The manifest's closing note from cycle 1 — "it does not claim the class is fixed" — is still the
  right posture and I am still not charging it for a claim it declined to make. The narrower claim
  cycle 1 *did* make and failed ("sites are now pinned individually") has been withdrawn and
  replaced by a guard that measures.
- No `.goal/goal.json` task matches this unit slug, so the PASS closes nothing there; the
  `/goal` close step is a documented no-op here rather than a skipped duty.

## Ledger

- `AT-210`, `AT-211`, `AT-212`, `AT-213` → **verified** (each of the cycle-1 checker's own
  zero-failure attacks re-run here and each now fails).
- New: `AT-214` (low).

## ISSUES-WRITTEN: AT-214

## EXPLANATION

All four issues the cycle-1 checker filed are independently re-verified as fixed: its two
site-deletions, its decoy-at-line-157 replay against a deleted renderer, its `os.environ.get`
binding, and its `ffmpeg-x` rename each produced zero failures at `9351387` and each now fails at
`eabc638`, alongside the seven original sabotages which all still discriminate. I pressed the
three places most likely to still be wrong — a compensating pair against `EXPECTED_SITE_COUNT`, a
cross-file site move, and eight binding forms against the new `NEVER_A_COMMAND` exemption — and
found one measured bound (a site may be relocated within its own file, filed low as AT-214) which
is the line-independent identity cycle 1 itself prescribed, and no way to hide a command from both
the collector and the hole report. This unit is held to its own thesis and meets it.
