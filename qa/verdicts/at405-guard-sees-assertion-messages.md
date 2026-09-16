# Verdict — at405-guard-sees-assertion-messages

**Cycle checked:** 1
**Date:** 2026-09-16
**Mode:** A (unit check), bound to `d:/autoTesting`
**Contract:** `qa/contracts/core-invariants.md` — C2, C3, C7
**Manifest:** `qa/manifests/at405-guard-sees-assertion-messages.md` (Status: ready-for-check, Fix cycle: 1)
**Adapter:** `qa/adapter.json` (coding) — slot 1 re-run in full by this checker

## VERDICT: PASS

---

## What I re-ran myself (nothing below is read from the manifest)

| Command | My result |
|---|---|
| `uv run pytest tests/test_flake_probe.py tests/test_flake_probe_runner.py -q` | `......................` → **22 passed**, exit 0 |
| `uv run ruff check src tests scripts` | `All checks passed!`, exit 0 |
| `uv run autotester doctor` | `doctor: clean`, exit 0 |
| `uv run pytest -q` | 1237 tests, 2 skipped, 0 failed, **SUITE_EXIT: 0** |

All four match the manifest's expected clauses.

## 1. Does `scripts/flake_probe.py` really go untouched? — verified by hash, not by belief

```
git hash-object scripts/flake_probe.py   -> cddc38772f2221e7a6e1dd024cdb59f99b51f3ff
git rev-parse HEAD:scripts/flake_probe.py -> cddc38772f2221e7a6e1dd024cdb59f99b51f3ff
```

Identical. No production code changed. `git status -- tests/ scripts/` shows this unit's two paths
(`M tests/test_flake_probe.py`, `?? tests/test_flake_probe_runner.py`) and nothing else of its own;
the other two dirty test paths (`tests/test_browser_unreadable.py`,
`tests/fixtures/bidi_site/scrolled_panes.html`) belong to the concurrent at379 session and were not
touched, staged or judged here (AT-391).

## 2. Does the suite output correspond to the CURRENT code? — the process fault, independently settled

The manifest self-reports that three earlier suite runs were invalidated by sabotage changing the
code underneath them. I did not try to authenticate the maker's paste — I made the question moot:

- I hashed all three subject files **before** launching `uv run pytest -q`, and again **after** it
  exited. `cddc3877… / 11e08b3f… / e1237fdc…` both times, byte-identical.
- Every falsifying edit I ran lived in a throwaway copy **outside** the bound root
  (`…/scratchpad/at405copy`), so the bound tree was provably static for the whole suite window.

So the green suite I am citing is a green suite **of the code in this verdict**. The maker's own
paste, separately, is elided (`[... all dots ...]`) and therefore unverifiable as to provenance —
filed as **AT-414** (low), below.

## 3. Capability coverage — all 3 rows reproduced, in a copy outside the bound root

**Copy:** `C:/Users/.../scratchpad/at405copy` — `tests/test_flake_probe_runner.py` +
`scripts/flake_probe.py` only. The note about the repo `.venv`'s `autotester.pth` was heeded: these
tests import `flake_probe` from `scripts/`, so I asserted the subject resolves inside the copy
before trusting any result —

```
flake_probe.__file__ = ...\scratchpad\at405copy\scripts\flake_probe.py
```

**Copy baseline (its own green, not step 3's):** `6 passed in 0.02s`, and the named check alone
`1 passed`. Re-greened to `6 passed` immediately before each of the three edits, and after the last.

| Row | Falsifying edit (single hunk, single file, the file named in "What changed") | GREEN before | Observed after |
|---|---|---|---|
| A — refuted **mechanism** cannot return as an assertion message | `"41 trials must not share one .pytest_cache"` → `"runs must not inform each other"`; anchor asserted to match **exactly once**, file rewritten | `6 passed` | **1 failed, 5 passed** — `test_the_isolation_flags_are_not_described_as_load_bearing` at **:174**, on `assert "must not inform each other" not in source` |
| B — refuted **consequence** cannot return as an assertion message | `"…must not silently double to -qq"` → `"…must not suppress the failure output"`; anchor matched once | `6 passed` | **1 failed, 5 passed** — same test at **:175**, on `assert "must not suppress the failure output" not in source` |
| C — a refuted claim cannot be laundered by a line wrap | re-introduced *"A probe whose trials are not independent cannot support a binomial / bound at all."* into the flags docstring, **wrapped inside the phrase**; anchor matched once | `6 passed` | **1 failed, 5 passed** — same test at **:176**, on `assert "cannot support a binomial bound" not in source` |

Line numbers differ from the manifest's (`:174/:175/:174`) only because my row-C insertion is three
lines where the maker's was one; each failure is the assertion the row is **named for**, which is
what step 4b requires. No edit broke import or collection — 6 tests collected on every run.

**Row C's mechanism is load-bearing, not incidental.** With the row-C mutation applied I probed the
guard's two readings directly:

```
RAW getsource contains phrase on one line : False
NORMALISED getsource contains phrase      : True
__doc__ (old AT-405 guard) contains phrase: False
```

So the wrapped claim is invisible to the pre-AT-406 whitespace-sensitive matcher and invisible to
the pre-AT-405 `__doc__` reader, and is caught only by `" ".join(getsource(...).split())`. Both
fixes are doing work; neither is decoration.

## 4. The question this check was sent to settle: does the guard catch BOTH messages?

**Yes — verified, not recorded.** The maker's own sabotage found that its first version listed the
refuted *consequence* and forgot the refuted *mechanism*, and the manifest claims it corrected that
and re-ran. Rows A and B above are that claim re-derived from scratch in my own copy: restoring the
**mechanism** as an assertion message reddens the guard on its own dedicated assertion (`:174`), and
restoring the **consequence** reddens it on `:175`. Neither is riding the other's failure — each
mutation was run from a re-greened copy and produced exactly one failure with the matching message.

There is therefore **no fourth over-claim to charge** on the uncovered-message ground. The two
assertion messages now standing in the live tree are the measured ones
(`"41 trials must not share one .pytest_cache"`, `"the project's -q must not silently double to
-qq"`), which is exactly AT-405's `expected` remedy, and the normalisation is exactly AT-406's.

## 5. Is a string matcher over prose still earning its place? — not the AT-218 class, with one measured narrowing

**It is earning its place, and it is not vacuous.** Vacuity has a definition here and this guard
fails it in the right direction: three independent mutations each reddened it, each on its own
assertion, from an asserted-green baseline. AT-218's class is a guard that *cannot* be reddened;
this one can be reddened three different ways.

The disclosure in "What this does not claim" is **adequate and accurate on its own terms** — it says
plainly that a fourth, differently-worded over-claim is not hypothetical given this file has produced
three, and that the general defence is measuring before writing. That is the honest bound.

**One narrowing the in-code docstring overstates, measured (AT-413, low, filed not charged).** The
guard docstring says `getsource` means the guard "can no longer be satisfied by moving a claim a few
lines down". It can. From the same green copy I restored **both** refuted sentences verbatim into the
docstring of the *adjacent* test (`test_the_probe_runs_every_trial_even_after_one_fails`, ~20 lines
down) — anchor matched exactly once, file rewritten — and the suite stayed **`6 passed`**, guard
silent. The manifest's own disclosure is correctly scoped ("wherever in the **function** they sit");
the docstring's "a few lines down" is not. Same shape as AT-405/AT-406 — the claim one notch more
generous than the mechanism — which is why it is filed rather than charged: this repo settles a prose
over-claim with a low ledger row (AT-388, AT-389, AT-396, AT-405, AT-406), and charging it would burn
a fix cycle to edit one sentence in a docstring while the mechanism under it is sound.

**Structural signal, not a verdict (sweep check 9; never a blocker on a passing unit).** This subject
has now been rewritten by three consecutive units — `ef9e819` (AT-386), at396, and this one — growing
285 lines in one file to 330 across two, with each unit's addition being *more prose about the
previous unit's prose*. The guard-of-a-guard depth here is now two, and the fourth-generation pattern
AT-218 names is the reason that is worth saying out loud even on a PASS. It does not change this
verdict: the mechanism is falsifiable, the disclosure is honest, and the remedy AT-218 is queued for
is a HUMAN_GATE decision about how the maker authors guards, not another automated layer.

## 6. The file split — a real seam, and nothing lost

**Seam.** `test_flake_probe.py` keeps the arithmetic: it imports *names* (`ceiling_given_no_failures`,
`runs_for_confidence`, `describe`, `write_report`) and tests pure functions over fabricated `Run`
rows. `test_flake_probe_runner.py` imports the *module* and tests subprocess behaviour by
monkeypatching `flake_probe.subprocess.run`. Different subject, different instrument, different
import style, separate module docstrings each stating one job. The precedent cited is real —
`tests/test_grade.py` / `tests/test_grade_evidence.py` was split for the same rule and states the
same justification in its own docstring. The 300-line rule **triggered** the split; it did not
invent the boundary. Not a line-count dodge.

**Nothing lost.** HEAD's file held 18 `def test_` names; the post-change pair holds 12 + 6 = the same
18, no renames. 22 collected before and 22 after (parametrised cases). Diffing HEAD's runner half
against the new file's body shows a **pure move** apart from exactly the changes the manifest claims:
the two assertion messages, the guard's `__doc__`→`getsource` body, and the guard docstring. No other
line moved.

## 7. Contract judgement

| Criterion | Verdict | Evidence |
|---|---|---|
| **C2** — no file in `src/`/`tests/` > 300 lines; module docstring states its one job | **holds** | `doctor: clean` (it was RED at 304 mid-build; the split resolves rather than suppresses). 152 + 178 lines. Both modules carry a one-job docstring. |
| **C3** — one concept one place; edit in place; a new module needs a stated reason in the manifest | **holds** | `doctor: clean` (duplicate-concept + drift-filename rules). No `*_v2/_new` name. The new module's reason is stated in "What changed" and is the doctor rule itself plus a named responsibility seam. No test name is duplicated across the pair. |
| **C7** — verification is independent; a unit that adds or rewrites a test mutation-tests it, from an asserted-green baseline, with a named failing test per mutation | **holds** | The unit rewrites a test and pastes a mutation run with a green baseline and per-mutation attribution; I re-ran all three in my own copy and reproduced each. The maker's *first* run is reported honestly as a SURVIVED mutation rather than absorbed — which is C7's zero-failure discipline applied to itself. `uv run pytest -q` exits 0 and the manifest pastes real output for three of four commands (the fourth is elided → AT-414). No unreachability claim is made. |

## 8. `Issues addressed` vs the ledger

| Claimed | Ledger before | Genuinely fixed by this unit? |
|---|---|---|
| **AT-405** (low) — guard read `__doc__`, could not see the assertion messages | `open` | **Yes.** Guard now reads `getsource`; both messages restated to the measured reasons, exactly AT-405's `expected`. Rows A + B reproduce the coverage. → `fixed` |
| **AT-406** (low) — pin was whitespace-sensitive | `open` | **Yes.** `" ".join(source.split())`, exactly AT-406's proposed strengthening. Row C reproduces it, and the raw-vs-normalised probe proves the normalisation is what catches it. → `fixed` |

Correctly **not** claimed: AT-407 (fixed out of band at `5e9ae80` — confirmed, the file is tracked),
AT-401, AT-390, AT-397. The MC-003 `data_boundary.py` exit-1 on missing `data_class` is AT-365 at
HUMAN_GATE, not introduced here, not chargeable.

## FAILURES

None.

---

```
VERDICT: PASS
SCOREBOARD: 3/3 criteria met (C2, C3, C7), 3/3 invariants hold
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 3/3 rows reproduced in a throwaway copy outside the bound root, each from its own asserted-green baseline (6 passed), each reddening exactly the assertion its row is named for
LIVE-BROWSER: not-applicable (changed paths: tests/test_flake_probe.py, tests/test_flake_probe_runner.py — no production code, route, template, component or page)
ISSUES-WRITTEN: AT-413 (low), AT-414 (low); AT-405 open → fixed, AT-406 open → fixed
EXPLANATION: The guard genuinely catches BOTH refuted messages — restoring the mechanism reddens :174 and the consequence reddens :175, each from a re-greened copy, so the hole the maker's own sabotage found is closed rather than merely reported. The whitespace normalisation is load-bearing (the wrapped claim is invisible raw, visible normalised) and scripts/flake_probe.py is byte-identical to HEAD. The split is a real seam — arithmetic vs subprocess runner, 18 test names in and 18 out, a pure move otherwise — not a line-count dodge. Two low rows filed, not charged: the guard's docstring claims more reach than it has (both sentences restored one function away leave it silent — AT-413), and the manifest's full-suite paste is elided rather than real output (AT-414); the suite is green regardless, re-run by this checker against a tree hashed identical before and after.
```
