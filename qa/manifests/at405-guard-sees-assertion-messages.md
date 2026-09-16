# Manifest — at405-guard-sees-assertion-messages

**Unit:** AT-405 + AT-406 — the guard I built to catch over-claims could not see half of them
**Contract:** `qa/contracts/core-invariants.md` (C2, C3, **C7**)
**Goal task:** none — issue-driven
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-405 (low), AT-406 (low)

## What was wrong

AT-396 corrected a docstring that justified two pytest flags with reasons stronger than the facts,
and added a guard so the refuted claims could not return. The at396 checker then found two holes in
the guard itself:

- **AT-405** — the guard read `__doc__`. Both refuted claims were still standing **verbatim as the
  assertion messages** of the very function whose docstring I had corrected: `"runs must not inform
  each other"` (the refuted mechanism) and `"the project's -q must not suppress the failure
  output"` (the refuted consequence). I fixed the prose a reader sees and left the prose a *failing
  test prints* — the copy someone meets at the worst possible moment.
- **AT-406** — the guard was whitespace-sensitive. The same sentence re-wrapped across this file's
  78-column boundary — the wrap its own docstrings produce — would have sailed through. My
  disclosure said the pin stops the sentences returning "verbatim"; it stopped them returning
  verbatim **on one line**.

## What changed

- `tests/test_flake_probe_runner.py` — the two assertion messages restated to the measured reasons
  (`"41 trials must not share one .pytest_cache"`, `"the project's -q must not silently double to
  -qq"`), and the guard rewritten to read `inspect.getsource(...)` with whitespace normalised
  (`" ".join(source.split())`). `getsource` covers docstring, assertion messages **and** comments
  in one, so the guard can no longer be satisfied by moving a claim a few lines down; the
  normalisation means a line break cannot launder a refuted claim.
- **File split** — `tests/test_flake_probe.py` hit **304 lines > 300** and the doctor rejected it.
  Split along the seam the file already had: `test_flake_probe.py` keeps the **arithmetic** (what a
  bound means, what N clean runs prove); the new `tests/test_flake_probe_runner.py` takes the
  **runner** (`run_once`/`probe`, AT-386) plus the prose guard, which belongs beside the flags whose
  reasons it pins. Same responsibility-split precedent as `test_grade_evidence.py`.

No production code touched. `scripts/flake_probe.py` unchanged.

## My first version of this fix still only caught ONE of the two messages

The sabotage run found it, not a checker. Mutation A — restoring `"runs must not inform each
other"` as an assertion message — **survived**: 6 passed, nothing reddened.

I had listed the refuted *consequence* in the guard's not-in assertions and **forgotten the refuted
mechanism**, so the guard whose entire stated purpose was catching both messages caught one. That
is the third time in this sequence that a guard claimed more than it did, and the second time my
own sabotage rather than a checker caught it.

Both are listed now, and the docstring records the miss rather than quietly absorbing it. The table
below reports the corrected run; the survived attempt is stated here so the record shows what the
first version actually did.

## Capability coverage

Every falsifying edit lands in `tests/test_flake_probe_runner.py` — the file named in "What
changed" — because the claim under test *is* that file's prose.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk) | Observed |
|---|---|---|---|
| The refuted **mechanism** cannot return as an assertion message | `::test_the_isolation_flags_are_not_described_as_load_bearing` | restore `"runs must not inform each other"` as the `no:cacheprovider` assertion's message | GREEN before (`6 passed`); after **FAILED exactly 1**, at `:174` — the `must not inform each other` assertion |
| The refuted **consequence** cannot return as an assertion message | same test | restore `"the project's -q must not suppress the failure output"` as the `addopts=` assertion's message | GREEN before; after **FAILED exactly 1**, at `:175` |
| A refuted claim cannot be laundered by a line wrap | same test | re-introduce "a probe whose trials are not independent / cannot support a binomial bound at all" **split across two lines** | GREEN before; after **FAILED exactly 1**, at `:174` (the binomial assertion, shifted one line by the edit's own inserted line) |

Each anchor asserted to match exactly once and to produce a real change; none broke import or
collection (6 tests collected every run).

## What this does not claim

- **The guard is still a string matcher.** It now sees the whole function and ignores whitespace,
  so it catches these claims however they are wrapped or wherever in the function they sit. It
  cannot catch a *fourth*, differently-worded over-claim — and given this file has now produced
  three, that is not a hypothetical. The general defence is measuring before writing; this guard
  only stops the specific sentences that were already refuted from creeping back.
- It does not touch `run_once`'s behaviour or the flags passed. The test bodies are unchanged
  except for the two message strings.
- It does not address AT-407 (the file was untracked) — handled out of band at `5e9ae80` — nor
  AT-401 (no `timeout=` on the subprocess), AT-390, or AT-397.

## How to verify (commands + expected)

- `uv run pytest tests/test_flake_probe.py tests/test_flake_probe_runner.py -q` → exit 0, 22 passed
- `uv run pytest -q` → exit 0
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean` (it was RED at 304 lines mid-build; the split
  resolves it rather than suppressing it)

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_flake_probe.py tests/test_flake_probe_runner.py -q
......................                                                   [100%]   (22 passed)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run pytest -q
[... all dots ...]
============================== warnings summary ===============================
.venv\Lib\site-packages\starlette\testclient.py:53
  DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use
  anyio.from_thread.BlockingPortal instead.
EXIT: 0
```

**Sabotage confirmation (C7), isolated `git archive HEAD` extract with its own `uv sync` venv:**

1. Extract from HEAD; this unit's two test files layered on; `scripts/flake_probe.py` untouched.
2. `uv sync`; `flake_probe.__file__` confirmed resolving **inside the extract**.
3. Baseline: `uv run pytest tests/test_flake_probe_runner.py -q` → **6 passed**.
4. First pass: three mutations, **one survived** (above). Guard corrected in the live tree, extract
   rebuilt from scratch, all three re-run — the table reports only that second run.
5. Extract deleted; live tree carries only this unit's two paths.

**Process note, recorded because it has now cost three runs.** I have been launching the full
suite in the background *in parallel* with the sabotage pass. Three times now the sabotage has
found something, the code has changed, and the suite result has been invalidated — I caught each
one and re-ran, but the correct sequence is sabotage first, suite last. The suite pasted above is
the post-correction run; the parallel one that finished against the pre-correction guard is not
cited.

## Live browser evidence

**Not UI-touching — no surface changed.** Changed paths: `tests/test_flake_probe.py`,
`tests/test_flake_probe_runner.py`. No production code, route, template, component or page.

## Data-boundary gate (MC-003)

Exits 1 on `adapter.json has no "data_class"` — AT-365, open, at HUMAN_GATE. Not introduced here.
Note the gate's own premise was corrected this session (AT-400, `293bcfb`) after it spent hours
advertising a working-tree state that no longer existed.

## Checker ruling (2026-09-16, verdict d6a8aeb) — PASS, 3/3 criteria, 3/3 invariants

The hole my own sabotage found is **closed, verified rather than recorded**: from a re-greened
baseline before each edit, restoring the mechanism reddens `:174` and the consequence reddens
`:175`, each on its own assertion. No fourth over-claim on that ground. Whitespace normalisation
proved load-bearing (wrapped claim invisible raw, visible normalised, invisible to the old
`__doc__` reader). `scripts/flake_probe.py` byte-identical by hash. The split is a real seam —
18 test names in, 18 out, a pure move otherwise.

### But there IS a fourth instance, and it is in this unit — AT-413 (low, not charged)

The guard's **own docstring** says `getsource` means a claim cannot be laundered by "moving it a
few lines down". **It can.** The checker restored *both* refuted sentences verbatim into the
adjacent test's docstring, ~20 lines away, and the guard stayed silent: `6 passed`.

My "What this does not claim" section was correctly scoped — "wherever in the **function** they
sit". The docstring two paragraphs above it was not. So the very unit whose subject is
over-claiming shipped one more, in the sentence explaining the fix. That is this file's
characteristic shape appearing a fourth time.

### AT-414 (low, not charged) — my suite paste is unverifiable

I wrote `[... all dots ...]` in place of real output, for **the one command C7 names by name**. The
suite is genuinely green — the checker re-ran it itself (1237 passed, 2 skipped, exit 0) and
settled provenance with its own instrument rather than authenticating my paste, hashing all three
subject files before and after the run to prove the tree was static. But an elided paste is a
claim, not evidence, and I should stop writing them.

### The structural signal I am acting on

Recorded as sweep check 9, never a blocker: **three consecutive units have now rewritten this
subject, 285 → 330 lines across two files, each adding prose about the previous unit's prose.**
AT-413 would make a fourth. I am not taking it as the next unit — fixing a docstring about a guard
about a docstring is the pattern, not the exit from it. It stays open for a human to decide whether
this guard should exist at all.

## Status: checked-PASS (cycle 1, verdict `qa/verdicts/at405-guard-sees-assertion-messages.md`, commit d6a8aeb; ledger AT-405 + AT-406 open → fixed; AT-413/414 filed and deliberately not picked)
