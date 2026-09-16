# Verdict — at335-flake-probe-harness

**Cycle checked: 1** (manifest `Fix cycle: 1`)
**Date:** 2026-09-16
**Checker:** /checker Mode A, fresh context, bound to `d:/autoTesting`
**Contract:** `qa/contracts/explore.md` + `qa/contracts/core-invariants.md` (C2 / C3 / C7)
**Adapter:** `qa/adapter.json` (coding; `isolation.sandbox = worktree-copy`)

## VERDICT: PASS

The unit ships a measurement instrument, not a fix, and it earns that. Every number in the
manifest that I could re-derive, I re-derived independently, and all of them hold. All four
capability rows reproduce in my own throwaway copy. The headline result survives scrutiny
because the manifest qualifies it before I had to.

---

## Environment note, read this first

**Another maker session is actively editing this working tree**, and it is currently red for
reasons that have nothing to do with this unit:

```
$ uv run autotester doctor        (bound tree)
file-too-long: tests\test_browser_visual_order.py - 321 lines > 300
1 violation(s)                                              DOCTOR_EXIT:1

$ uv run pytest -q                (bound tree)
ERROR collecting tests/test_browser_unreadable.py
tests\test_browser_unreadable.py:41: NameError: name 'pytest' is not defined
!!! Interrupted: 1 error during collection !!!             EXIT:2
```

Attribution, established rather than assumed:

- `tests/test_browser_visual_order.py` is `M` in git and is **297 lines at HEAD, 321 in the
  worktree** — another session's uncommitted growth past C2's 300-line rule.
- `tests/test_browser_unreadable.py` is **untracked**, timestamped `13:23` today, and is
  mid-write (missing `import pytest`). It did not exist when this session started.
- `tests/conftest.py` became `M` *during* this check.

Neither path is this unit's. This unit's only changed paths are `scripts/flake_probe.py` and
`tests/test_flake_probe.py`, both untracked-new. **I therefore re-ran every verify command in a
reconstruction of this unit's own post-change tree**, built outside the bound root, and it is
green (below). Charging the maker for a neighbour's half-saved file would be charging an
environmental denial. Filed separately as AT-391 — this is the second-order cost of two makers
sharing one working tree, and it makes slot-1 unreproducible for *either* of them.

## The copy (step 4b sandbox) — and proof it is real

`git archive HEAD | tar -x` into the scratchpad **outside** `d:/autoTesting`, then this unit's
two files layered on from the working tree. That reconstruction is exactly the tree the manifest
describes (it changes no tracked file), and it deliberately excludes the neighbour session's
in-flight edits. Its own `uv sync`, and the `autotester.pth` trap named in the dispatch checked
explicitly:

```
flake_probe: ...\scratchpad\at335copy\scripts\flake_probe.py
autotester : ...\scratchpad\at335copy\src\autotester\__init__.py
```

Both resolve **inside the copy**. No result below was read from the live tree.

## Step 3 — verify commands, re-run by me

| Command | Where | Result |
|---|---|---|
| `uv run pytest tests/test_flake_probe.py` | bound tree | **16 passed** (exit 0) |
| `uv run ruff check src tests scripts` | bound tree | `All checks passed!` (exit 0) |
| `uv run ruff check src tests scripts` | copy | `All checks passed!` (exit 0) |
| `uv run autotester doctor` | copy | **`doctor: clean`** (exit 0) |
| `uv run pytest -q` | copy | green except one copy artifact, resolved — see below |
| `uv run autotester doctor` | bound tree | exit 1, **neighbour's file** (above) |
| `uv run pytest -q` | bound tree | exit 2, **neighbour's file** (above) |

The one failure in the copy's full suite was
`tests/test_ui_sources.py::test_uploaded_recordings_are_gitignored` —
`git check-ignore` returning `fatal: not a git repository`, i.e. an artifact of extracting a
tree without `.git`. `git init -q` in the copy, re-run: **9 passed**. Not a finding about the
unit; recorded so the next checker building a copy expects it.

`doctor: clean` in the copy is what proves the bound tree's violation is entirely the
neighbour's. This unit's two files are **186** and **151** lines — C2 satisfied with margin.

## The arithmetic, re-derived from scratch (dispatch question 1)

I did not read the manifest's numbers. I recomputed them:

```
ceiling(13) = 1-0.05**(1/13) = 0.20581666...   -> 20.6%   ✓ manifest's ~20.6%
ceiling(41) = 1-0.05**(1/41) = 0.07046111...   ->  7.0%   ✓ manifest's 7.0%
runs_for_confidence(1/14)    = 41                          ✓ manifest's 41
suspected 1/14               = 0.07142857
ceiling(41) < 1/14           = True   (0.070461 < 0.071429)
rule-of-three at 41: -ln(0.05)/41 = 0.0730666  -> 7.3%, ABOVE 7.1%
```

**The self-contradiction the manifest confesses to is real.** Under the rule-of-three form the
module would tell you to run 41 times and then report a bound of 7.3% against a suspected 7.1%
— "run 41 times" followed by "41 was not enough", about the same question. Confirmed, not taken
on trust.

**Does the named test actually pin the agreement?** Yes, and it pins the direction that matters:
`test_the_named_sample_size_actually_achieves_what_it_claims` asserts
`ceiling_given_no_failures(runs_for_confidence(SUSPECTED_RATE)) < SUSPECTED_RATE`. My row-1
mutation (below) proves it is load-bearing: swapping the exact form back to the rule-of-three
reddens it.

**One correction to the manifest's wording, and the reason it is only a `low`.** "Exact inverses
of each other" is true of the mathematics and **not** of the implementation's round trip:
`runs_for_confidence(ceiling_given_no_failures(n))` returns `n+1` for **236 of the first 499
values of n** (n = 6, 9, 14, 21, 22, 24, 28, …), because `math.ceil` sits on a float epsilon. The
direction the tool actually depends on — `ceiling(runs_for_confidence(r)) <= r` — I checked at
1799 rates from 0.0005 to 0.9 and it holds **everywhere, no exceptions**. So the tool is correct
in every use it is put to, and the test pins the one point where the contradiction lived. The
phrase over-claims; the code does not. **AT-388, low.**

## The headline result (dispatch question 2) — knife-edge, and adequately qualified

0 failures in 41 runs bounds the rate at **7.046%**; the suspected rate is **7.143%**. The margin
is **0.097 of a percentage point**. "Excludes" is literally true at 95% and is what the shipped
tool prints — I generated it myself from the saved data:

```
tests/test_explore_modal.py::test_the_crawl_gets_past_the_modal: 0 failure(s) in 41 run(s)
  zero failures bounds the true rate at 7.0% (95% confidence) — NOT at zero
  the suspected 7.1% rate is outside that bound, so this probe excludes it; 41 runs are
  needed for a 95% chance of seeing it
```

**Ruling: the three qualifications are adequate and the unit does not over-claim.** The manifest
states the margin, states that only 7.1% is excluded and not the bug, states that the line was
recomputed, and adds a fourth qualification most makers would have omitted — that the runs were
sequential on a machine shared with a concurrent maker, uncontrolled for CPU contention, and
that a quiet machine is *arguably the least likely condition* to reproduce a timing-suspected
flake. That last sentence argues against the author's own result. Nowhere does the manifest say
AT-335 is fixed, absent, or explained.

**One thing the qualifications do not say, and a future reader will need it.** The 7.1% anchor is
not an established rate — it is **one observed failure in roughly fourteen runs**, a
single-observation point estimate whose own 95% interval runs from well under 1% to over 30%.
"This probe excludes 7.1%" therefore excludes a number that was never more than a guess, which is
a much smaller claim than it sounds. The manifest's qualification (ii) gestures at the right
conclusion — any true rate below ~7% survives — without naming why the 7.1% figure itself is
soft. Not an over-claim by this unit; a guardrail against the next unit citing it as settled.
**AT-389, low.**

## The recomputation (dispatch question 3) — LEGITIMATE

I opened the saved data myself, `.work/at335-flake-probe.json`:

```
nodeid      tests/test_explore_modal.py::test_the_crawl_gets_past_the_modal
runs 41     failures 0     returncodes {0}     indices contiguous 1..41
observed_rate 0.0          ceiling_at_confidence 0.07306664081839
total 1388.5s = 23.1 min   per-run 33.41s .. 35.33s
```

Two things follow, and they cut the maker's way.

1. **The stored ceiling is `0.073067`, which is exactly `-ln(0.05)/41` — the buggy rule-of-three
   form.** The artifact on disk independently corroborates the maker's account that the 41 runs
   were driven before the fix landed. That story could have been quietly dropped; instead the
   evidence file confirms it.
2. **The bound is a pure function of `(n, failures, confidence)`.** The measurement is the 41
   outcomes, and they are intact, self-consistent, contiguous, and carry per-run wall times
   (33–35s each, 23.1 min total) consistent with real browser crawls. Re-deriving 0.070461 from
   them with the shipped code is arithmetic on preserved data, not a substituted experiment.

Re-driving 23 minutes of browser would not improve this bound by a single digit — it would
produce a **different sample**, and re-sampling until the number reads better is precisely the
evidence-massaging the manifest elsewhere refuses to do. **The evidence does not need to be
re-gathered.**

**The presentation, though, is a defect.** The recomputed lines are printed inside a
`$ uv run python scripts/flake_probe.py …` shell-transcript block, which reads as pasted stdout,
and C7's Verify clause asks a manifest to paste real output. The disclosure fifteen lines later
repairs the meaning but not the formatting, and the block also silently drops the line's trailing
`; 41 runs are needed for a 95% chance of seeing it`. The numbers are correct — I re-derived
every one — so this is a labelling fault, not a fabrication. **AT-387, low.** A recomputed figure
belongs outside a `$` block, labelled as recomputed at the point of use.

## Step 4b — capability coverage: 4/4 rows reproduced

Harness: my own, in the copy, per C7 — asserts the named check **GREEN in the copy** before each
edit, asserts the anchor matched **exactly once**, asserts the **file on disk changed**, then
reads the **`FAILED` list** rather than the exit code, and restores from a pristine copy between
rows. Every edit is single-hunk, single-file, in `scripts/flake_probe.py`, which the manifest's
"What changed" names.

| # | Named check | Before (copy) | Anchor | After |
|---|---|---|---|---|
| 1 | `test_the_named_sample_size_actually_achieves_what_it_claims` | `1 passed` | 1 | **3 failed, 13 passed** — named test present |
| 2 | `test_an_empty_probe_has_no_rate_rather_than_a_rate_of_zero` | `1 passed` | 1 | **1 failed, 15 passed** — named test present |
| 3 | `test_a_probe_that_saw_nothing_reports_a_bound_and_not_a_zero` | `1 passed` | 1 | **1 failed, 15 passed** — named test present |
| 4 | `test_a_reproduced_failure_reports_the_observed_rate_and_keeps_its_evidence` | `1 passed` | 1 | **2 failed, 14 passed** — named test present |

Failure counts match the manifest exactly (3+2 others / 1 / 1 / 2). Nothing broke import or
collection — 16 tests collected on every run, so no row reddened for the wrong reason. Row 3
fired on its own named assertion, verbatim:

```
>       assert "NOT at zero" in lines, "the sentence that stops a clean probe reading as proof"
E       assert 'NOT at zero' in '...bounds the true rate at 20.6% (95% confidence)\n ...'
```

**Dispatch question 6 — row 4's edit applies and reddens.** `if not self.runs or self.failures:`
→ `if not self.runs:` matched **exactly once**, changed the file, and produced two failures
including its own named test. The manifest's account of the earlier miss is credible on its face
and, as it happens, I reproduced the same class of miss from the other side: **my own row-3
anchor matched zero times** on the first attempt (I had the indentation wrong), and my harness
refused to write and reported nothing rather than re-reporting row 2's result. That is C7's
anchor clause working live, on the checker's side of the table, in the same session it is being
judged on the maker's.

**Trap hunt.** Neither trap is present. No row's check asserts a state the bug also produces —
each reads a *computed value or an emitted string* from fabricated `Run` rows, so there is no
restore/retry/fallback path that could make the end state identical either way. No row reads live
state to judge live state: the entire test file is driven by hand-built `Summary` objects and
never touches a browser, a clock, or a subprocess. Row 1's mutation reddens two tests beyond its
own; the manifest discloses this ("that test + 2 others") and it is the expected blast radius of
changing a shared statistical primitive, not a collection break.

## The enumerated debt (dispatch question 5) — judged as DEBT, and partly discharged by me

`run_once` and `probe` — the subprocess halves — have no isolating test. The manifest states this
plainly under "What this does not claim". **Judged as debt, never as a pass.**

It matters more than the manifest's placement suggests: **the entire 41-run headline rests on
`run_once` correctly mapping a non-zero returncode to `failed`.** If that mapping were broken,
41 green runs would be 41 undetected failures and nothing in the 16 tests would notice. So I
exercised both branches end-to-end in the copy myself, which nothing in the unit does:

```
# forward branch — the real subject, the manifest's own cheap re-run
$ uv run python scripts/flake_probe.py "tests/test_explore_modal.py::test_the_crawl_gets_past_the_modal" --runs 3
tests/...::test_the_crawl_gets_past_the_modal: 0 failure(s) in 3 run(s)
  zero failures bounds the true rate at 63.2% (95% confidence) — NOT at zero
  the suspected 7.1% rate is inside that bound, so this probe does NOT exclude it; ...
EXIT:0                                        # matches the manifest's expected clause exactly

# failing branch — my own injected always-red test, which the unit never tries
$ uv run python scripts/flake_probe.py "tests/test_zz_probe_selfcheck.py::test_always_fails" --runs 3
tests/test_zz_probe_selfcheck.py::test_always_fails: 3 failure(s) in 3 run(s)
  run 1 FAILED (rc=1, 1.5s) / run 2 FAILED (rc=1, 1.6s) / run 3 FAILED (rc=1, 1.4s)
  observed rate 100.0% — reproduced, evidence captured
EXIT:0
report: failures=3, ceiling_at_confidence=None, tail="... assert 1 == 2 / 1 failed in 0.20s"
```

So failure detection works, the probe does not stop at the first red, the tail is captured, the
zero-failure bound is correctly withheld, and exit stays 0 either way. The behaviour is sound
**today**; what is missing is anything that would notice if it stopped being sound.

**And the stated reason for not testing it is wrong.** "Testing them would mean shelling out to
pytest from inside pytest" is not so: monkeypatching `subprocess.run` tests `run_once` directly,
and monkeypatching `run_once` tests `probe`. The debt is cheaper to close than the manifest
believes. **AT-386, medium** — the one finding here I would actually like to see closed.

**A note on the enumeration form, which is a shortfall but not a failure.** Step 4b treats an
`UNVERIFIED` capability row carrying an **issue id** as enumerated debt. This debt was enumerated
in prose with no ledger id, so it lived only in a manifest that will one day be archived. The
substance was disclosed prominently and in the author's own words, and I verified the behaviour
independently, so failing the unit over the *format* of an honest disclosure would burn a fix
cycle to reformat a paragraph. I have written the ledger row myself — that is the checker's
surface, not the maker's. Next test-shipping unit: an `UNVERIFIED` row with an id.

## Dispatch question 4 — a measurement instrument against a `high` bug

**Acceptable, and correctly sequenced. Not an under-delivery.**

The alternative was to ship a retry, a tolerance, or a settle change and call AT-335 closed on
the strength of 13 green runs. C7 names that move by its own name: a fix verified against a
sample that bounds the rate at 20.6% is an unfalsifiable claim. AT-335's original filer refused
it; this unit refuses it again and, unlike the first refusal, can now say **how little** 13 runs
proved. The mechanism is unconfirmed, the return ladder is untouched, and no production code
changed — I verified that: the unit's entire footprint is two untracked-new files, so `execute.py`
and `execute.md` are absent from the diff (X1), and `stages/explore*.py` is byte-unchanged.

**`Issues addressed` checked against `qa/issues.jsonl`:** AT-335 is claimed **partially** and the
manifest says in bold that it must not be closed. The ledger row reads
`{"id": "AT-335", "severity": "high", "status": "open"}` — **still open**, as claimed. The
manifest's claim and the ledger agree. Nothing was quietly closed.

AT-365 (the MC-003 `data_class` gate) is correctly identified as pre-existing and at HUMAN_GATE;
not chargeable here and not introduced here — the changed paths hold no data.

## Criteria and invariants

- **explore.md X1** — actively verified: `execute.py`/`execute.md` absent from the diff;
  `run_case` untouched. **X2–X16** — no file under `src/autotester/` changed, so every criterion
  is byte-unchanged and holds vacuously.
- **C1** — no domain shape added. `flake_probe.Run` is a tool-internal dataclass describing one
  pytest invocation; it does not duplicate `schema/run.py::Run` (an `Artifact` describing a
  regression run over cases) and is never serialized as a domain artifact. Not a C1 violation.
- **C2** — 186 / 151 lines; no function near 50 lines; both modules carry a docstring stating one
  job. `doctor: clean` in the copy.
- **C3** — no `*_v2`/`*_new` names; the new module's reason is stated in the manifest. One
  recorded-not-charged item: `flake_probe.py` introduces public top-level `Run` and `probe`,
  colliding with `schema/run.py::Run` and `media/probe.py::probe`. C3's text is unscoped but its
  gate (`doctor.check_duplicate_definitions`) globs `src/` only — the exact divergence already
  open as **AT-327**, which names `scripts/` by name. The precedent recorded in this contract's
  own amendment log (2026-09-11, at311) is to record and not charge: a criterion is not
  *strengthened* mid-verdict to fail an artifact any more than it is softened to pass one.
  **AT-390, low**, filed under AT-327's umbrella.
- **C4** — scratch went to `.work/at335-flake-probe.json` (gitignored); no repo-root clutter; the
  two files sit in the declared `scripts/` and `tests/`.
- **C5 / C6 / C8 / C9** — untouched; no secret, artifact model, provider call or control field is
  in scope.
- **C7** — the crux, and it holds. The mutation duty on a unit that adds tests is discharged:
  four mutations, green baseline asserted, anchors asserted exactly-once, file-changed asserted,
  kills attributed to named tests in the `FAILED` list, and I re-ran all four myself rather than
  reading them. **No unreachability claim is made anywhere in the manifest** — the `run_once`
  paragraph says the halves are *not covered*, which is an admission, not the unfalsifiable
  negative C7's clause forbids, and it is not used to justify calling anything proven. The
  "pastes real output" clause is met for every command except the recomputed statistics block,
  which is disclosed and whose numbers I re-derived (AT-387).

## SCOREBOARD

16/16 explore criteria hold (X1 actively verified; X2–X16 byte-unchanged), 9/9 core invariants
hold, 4/4 capability rows reproduced.

## Issues written

| id | sev | what |
|---|---|---|
| AT-386 | medium | `run_once`/`probe` have no standing test although the 41-run headline rests on the returncode→`failed` mapping; the manifest's stated reason for not testing them is inaccurate |
| AT-387 | low | recomputed statistics presented inside a `$ command` transcript block (C7 "pastes real output"); disclosed, numbers correct, trailing clause elided |
| AT-388 | low | "exact inverses" over-states the implementation — the `rfc∘ceiling` round trip drifts by +1 for 236 of the first 499 n |
| AT-389 | low | the 7.1% anchor is a one-observation estimate with a very wide interval; "excludes 7.1%" must not later be cited as if 7.1% were established |
| AT-390 | low | `flake_probe.py` adds public `Run` / `probe` colliding with `schema/run.py` / `media/probe.py` — C3 text-vs-gate, under open AT-327 |
| AT-391 | low | two maker sessions share one working tree, so slot-1 verify is currently unreproducible in it for either unit |

## Return block

```
VERDICT: PASS
SCOREBOARD: 16/16 criteria met, 9/9 invariants hold
FAILURES (if any): none
CAPABILITY-COVERAGE: 4/4 rows reproduced in a throwaway copy outside the bound root (green
  asserted in the copy before each edit; anchor-exactly-once and file-changed asserted; kills
  attributed to the named test in the FAILED list). One enumerated debt (run_once/probe, no
  isolating test) judged as debt, not a pass, and exercised end-to-end in both branches by the
  checker — ledger id assigned: AT-386.
LIVE-BROWSER: not-applicable (changed paths: scripts/flake_probe.py, tests/test_flake_probe.py —
  no route, template, component or page; no production code changed). A browser WAS driven 6
  times by me through the probe, as this unit's subject rather than as UI validation.
ISSUES-WRITTEN: AT-386, AT-387, AT-388, AT-389, AT-390, AT-391
EXPLANATION: The statistics are exact and I re-derived every one of them from scratch — 13 clean
  runs really do bound the rate at 20.6%, 41 runs at 7.0%, the two functions genuinely agree at
  the point that matters, and the rule-of-three self-contradiction the manifest confesses to is
  real. All four falsifying edits reproduce with the right assertion firing. The recomputed
  headline is legitimate: the saved per-run data is intact and its stored 0.073067 independently
  corroborates the pre-fix bug, and re-driving 23 minutes of browser would produce a different
  sample rather than a better bound. Shipping an instrument instead of an unverifiable fix
  against a high bug is the correct call under C7, and AT-335 stays open exactly as claimed.
  Six issues filed, none blocking; the one worth closing is AT-386.
```
