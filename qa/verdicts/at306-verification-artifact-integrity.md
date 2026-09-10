# Verdict — at306-verification-artifact-integrity

**Date:** 2026-09-11
**Checker:** /checker Mode A, fresh context, bound to `D:/autoTesting`
**Contract:** `qa/contracts/core-invariants.md` (C7, incl. the baseline clause I added on the
`at300-migration-config-hardening` verdict)
**Manifest:** `qa/manifests/at306-verification-artifact-integrity.md`
**Cycle checked: 1**
**Commit checked:** `6cc11e6`

```
VERDICT: PASS
SCOREBOARD: 5/5 manifest verify claims reproduced, 9/9 applicable invariants hold
FAILURES: none
LIVE-BROWSER: not-applicable (changed paths: qa/.last-tick, qa/evidence/, qa/gates/, qa/manifests/ — no src/, tests/, or ui/)
ISSUES-WRITTEN: AT-311 (new, medium) · AT-312 (new, low) · AT-306 → fixed · AT-307 → fixed
EXPLANATION: Both defects are genuinely fixed, and the AT-307 assertion is load-bearing rather
than decorative — I forced three different red baselines myself and the harness refused all three,
including one the maker never tried. The AT-306 judgement is upheld: removing a decision-irrelevant
derived fact beats generating one. I re-derived every remaining factual claim in the gate and all of
them hold. I have also folded the standing feedback-inbox mutation proposal into C7 (see below) and
filed the one hole this unit does NOT close: KILLED is still `exit != 0`, so a mutation that breaks
the module reads KILLED while no test ran.
```

---

## Mode D determination

**Not required.** Decided from the changed paths in `6cc11e6` (`git show --stat`), not from
`qa/adapter.json`: `qa/.last-tick`, `qa/evidence/at300-migration-config-hardening/mutation_harness.py`,
`qa/gates/t135-url-pattern-data-migration.md`, and two manifests. Nothing under `src/`, `tests/`, or
`src/autotester/ui/`. I checked the indirect direction too — whether anything renders `qa/gates/` to a
user — and the only hit in `src/autotester/ui/` is a prose docstring reference in
`routes_project_edit.py:14`, not a route. No UI surface, direct or indirect.

## 1. Verify commands — all re-run by me, all reproduce

| # | Command | Manifest claim | My result |
|---|---|---|---|
| 1 | `uv run pytest -o addopts= -q` | 1054 passed, 2 skipped, exit 0 | **1054 passed, 2 skipped, 1 warning in 87.21s, exit 0** ✅ |
| 2 | `uv run ruff check src tests scripts` | exit 0 | **All checks passed! exit 0** ✅ |
| 3 | `uv run autotester doctor` | exit 1, exactly one violation (AGENTS.md) | **`root-clutter: AGENTS.md`, `1 violation(s)`, exit 1** ✅ |
| 4 | `uv run python qa/evidence/.../mutation_harness.py` | baseline asserted green, 4/4 KILLED | **`BASELINE: exit=0  21 passed`, M1–M4 all KILLED, byte-identical restore** ✅ |
| 5 | `grep -n "tests in" qa/gates/t135-...md` | no test-count claim remains | **no match (exit 1)** ✅ |

On (5) I widened the grep rather than trusting the maker's chosen pattern:
`grep -nE "[0-9]+ tests|tests: *[0-9]|[0-9]+ passing"` returns exactly one line — line 61, inside the
new "A note on this file", which *narrates* the two counts the document used to carry ("9 tests",
then "14"). That is history, not a claim about the current suite, and it is the sentence that stops
the count coming back. No live count remains.

The doctor exit-1 is the pre-existing, ledgered **AT-283** (root `AGENTS.md`), unchanged by this
unit and disclosed in the manifest. C2/C4 are measured against that known baseline; the previous
unit PASSed on the same footing.

## 2. AT-307 — I forced the red baseline myself. The assertion bites.

The manifest offers one demonstration (a copy pointed at a non-existent selector). **I did not use
it.** I derived four probes of my own from the committed harness, each a separate file under my
scratchpad, each run against the real repo:

| Probe | How I forced it | pytest exit | Harness behaviour |
|---|---|---|---|
| **A** — a genuinely red suite, tests actually ran | injected `def test_checker_injected_always_fails(): assert False` into the *copied* test file before the baseline run | **1** (`1 failed, 21 passed`) | **REFUSED** — `AssertionError: baseline is NOT green - every KILLED below would be a lie: 1 failed, 21 passed` |
| **B** — the maker's case, reproduced independently | selector `::test_no_such_test_exists_at_all` | **4** (`no tests ran`) | **REFUSED** |
| **C** — collection error at baseline | prepended `import nonexistent_module_xyz` to the copied test file | **2** (`1 error`) | **REFUSED** |
| **D** — green baseline, mutation causes a collection error | replaced the mutation set with one that injects a syntax error into the target | baseline 0, mutation **2** | **reported `KILLED  1 error in 0.20s`** ⚠️ |

Probe A matters most and is the one the maker did not run: its own demonstration produces "no tests
ran", which is the *easy* case. A suite that runs and goes red — the AT-196 flake shape the clause
was actually written for — is what A reproduces, and the assertion catches it. **The guard is
load-bearing, not decorative.** `assert code == 0` is on the only path to the mutation loop; there
is no branch around it.

Also verified, since the fix touched a file the harness itself depends on: after every run of mine
the live repo is clean (`git status --porcelain qa/` empty), and the harness's own
`assert TARGET.read_text() == ORIGINAL` restore fired. It works on a `copytree` outside the repo, so
none of my four probes could have touched `D:/autoTesting` even had they misbehaved.

### The next hole — filed as AT-311 (medium), not as a FAIL

You asked me to look past the fix. **Yes: `exit != 0` is still the only definition of KILLED**, and
probe **D** shows what that costs. A mutation that destroys the module under test exits 2, the
harness prints `KILLED`, and the failure list it prints underneath is **empty** — no test failed,
because no test ran. The harness certified a mutation "killed" by a suite that never collected.

So the harness cannot distinguish, today, between:
- the test named for the fix failed (what it means to claim),
- some unrelated test failed (an AT-196 flake landing mid-run rather than at baseline),
- the suite failed to collect at all.

The corroborating evidence that the `defends:` label is genuinely decorative is in the committed
harness itself: **M4's label names `test_a_file_nested_below_the_project_is_still_judged_by_it`,
which does not exist in the file** (`grep -c "def …"` → 0). The test that actually fails under M4 is
`test_a_nested_artifact_under_a_flat_root_is_still_judged_by_its_project`. The harness printed the
wrong name with total confidence, four kills in a row, because nothing ever compares that string to
the run. A label nothing asserts is a comment.

**Does it matter for the property being certified?** It does, and for the same reason AT-307
mattered. The property is *"the test named for this fix is not vacuous."* Every failure mode above
produces a **false KILLED → false non-vacuous → false PASS**. That is the one direction C7's whole
family of clauses exists to close: a harness reporting confidently about an experiment that did not
happen. AT-307 closed "already red *before* the mutation"; this is "red for the wrong reason
*after* it".

**It is not a FAIL of this unit.** The manifest claims to assert the baseline, and it does; it never
claims per-test attribution, and C7 as it stood this morning did not require it. This project's own
precedent (AT-261, AT-303) is that a newly-found residual in a passing unit is filed, not charged.
Filed **AT-311**, and — because I am folding the mutation proposal into the contract in this same
verdict (§4) — filed at **medium** rather than the low that AT-307 carried, since the instrument
stops being one unit's convenience and becomes load-bearing for every unit that adds a test.

## 3. AT-306 — judgement #1 ruled: **removing the count was right. Upheld.**

You asked whether a document a human decides from should carry a generated-and-verified count
instead. **No — and the distinction is not "derived facts are bad", it is narrower than that.**

A derived fact earns a place in a decision document only when **both** hold:
1. **the decision turns on it**, and
2. **something re-derives it at read time.**

The test count fails both. Nothing in Options A/B/C changes if the suite has 14 tests or 21 — the
decision turns on whether the migration is *correct and reversible*, which the document establishes
by naming `scripts/migrate_url_patterns.py` and `tests/test_migrate_url_patterns.py`, both of which
a reader can run. And no generator runs when a human opens a markdown file.

The "generated-and-verified count" option is **actively worse here**, which is why I am not asking
for it. A generated count is indistinguishable *to the reader* from a stale one — it looks
authoritative, carries a provenance the reader trusts, and rots identically the moment the generator
stops being run. You would be adding machinery whose only job is to keep a decision-irrelevant
sentence honest, and whose failure mode is a *more* convincing false statement. The count was a
cache with no invalidation; deleting a cache nobody reads beats writing an invalidation protocol
for it.

The measured case is decisive: it went stale **twice in one session**, across two different agents,
one of whom was specifically fixing that exact defect and still left it stale within one unit. That
is not carelessness to be resolved away — it is what a fact with no reader does.

The **"A note on this file" section is the load-bearing half of this fix**, and I want that on the
record separately. Removing the count alone would have been fixed until the next helpful editor
added one back; the note converts a deletion into a rule with its reason attached, at the exact
point of use. That is the right shape.

One caveat, disclosed rather than charged: the note says the file "carried one twice — '9 tests',
then '14'". AT-306's own evidence is slightly different — it carried **9 and 14 simultaneously**, on
lines 26 and 39, and was then corrected to 14/14. The note's version is a fair compression of the
history and asserts nothing false about the present. Not a finding.

### The gate re-verified in every OTHER respect

It has been wrong twice and it authorises a write to real project data, so I re-derived every
remaining factual claim in it rather than reading them:

| Gate claim | My re-derivation | Verdict |
|---|---|---|
| 3 corrupted `url_pattern` values in `projects/erp/screenmap.json` | `grep -o` → exactly 3 × `/vidysea.com/erp/trainers` | ✅ true |
| "The producer is fixed — `build_screen_map(ProjectStore('erp'))` now yields `/erp/trainers`" | ran it live: trainer patterns = `['/erp/trainers']`, none containing `vidysea.com` | ✅ true |
| "The migration exists, is committed" | `git ls-files --error-unmatch` on `scripts/migrate_url_patterns.py` and `tests/test_migrate_url_patterns.py` → both tracked | ✅ true |
| "Dry run by default" | ran with no flags: printed 3 rows and `dry run — re-run with --write to apply`; file hash unchanged | ✅ true |
| "idempotent" | `repair('/vidysea.com/erp/trainers')` → `/erp/trainers`; `repair('/erp/trainers')` → `None` | ✅ true |
| RESOLVED block: `/v1.2/foo`, `/index.html`, `/settings.json`, `/main.js` left alone | all four → `None` against the real `known_hosts(projects/erp)` = `{vidysea.com, www.vidysea.com}` | ✅ true |
| RESOLVED block: `/saucedemo.com/cart` left alone inside erp | → `None` | ✅ true |
| Option A: "`projects/erp/screenmap.json` is untracked … no commit to revert" | `git ls-files --error-unmatch` → not tracked | ✅ true |
| Option C: "`projects/erp` has no `flowspec.json`" | directory listing: `cases.jsonl, issues.jsonl, project.json, rubrics, runs, screenmap.json, sources, sources.jsonl` — no flowspec | ✅ true |
| "the dry run on real data is unchanged: 3 rows, 1 file" | `would repair 3 url_pattern(s) across 1 file(s)` | ✅ true |

**The gate is now accurate in every respect I can mechanically check.** This is the first time that
has been true of this document.

## 4. Judgement #2 — ruled, and the inbox proposal is FOLDED. It does not sit a third session.

You are right that this was the moment, and I am taking it rather than deferring again.

**FOLDED:** `qa/feedback-inbox.md` entry `2026-09-11T04:00+05:30` (the maker's own four-vacuous-test
pattern, proposing mutation as a required verify step) is folded into **C7** as of this verdict,
under the routine gate — it adds two duties and weakens nothing. The amendment is in the contract's
append-only log with its reason; the inbox entry is marked `folded → qa/contracts/core-invariants.md`
with today's date.

**What I folded, and what I deliberately did not.** The proposal asked for a step in
`qa/adapter.json` slot-1. I declined *that mechanism* and adopted the *duty*:

- `qa/adapter.json` is the maker's file; the checker does not write it, and a rule the maker writes
  for itself is not a gate — the same reasoning that kept the sabotage clause out of `qa/loop.md` on
  2026-09-08.
- Slot-1 runs on **every** unit. Most units add no test, and a mutation step that no-ops on most
  runs is a step people learn to ignore. The duty is conditional on the unit adding or rewriting a
  test, which a shell command cannot decide.
- C7 is already the criterion about *how verification is done*, and already carries the anchor
  clause, the zero-failure clause, and the baseline clause. This is the fourth member of one family.
  It belongs with them.

**Judgement #2 itself (the harness under `qa/evidence/`): ruled — it must move, now that I have made
it contractual, but that is a build, not a blocker for this unit.** Your reasoning for leaving it
put was correct *while* the fold was pending, and you were right not to pre-empt me. That condition
is now gone: an instrument every test-adding unit must run cannot live in one superseded unit's
evidence directory, where the next maker will either not find it or will copy-paste a fifth variant
of it. Filed as **AT-312** (low) — give it a shared home and make it take the target/test/mutation
set as arguments. And your instinct that "AT-307 is the first thing its contract should require" is
exactly what happened; AT-311 is the second.

## 5. Judgement #3 — AT-308 / AT-309 left open: **upheld**

Correct, and correct for the reason you give. I classified both as *undefended defensive branches*
rather than vacuous tests — no test is named for them, so nothing is lying — and I re-confirmed
they are unreachable through `main()`. Leaving them open with a written remedy is the right disposal
for a low-severity robustness gap; batching them into a unit that was about instrument honesty would
have muddied both.

One note for whoever picks them up: **AT-309 has two halves and they are not equally cheap.** The
missing test is the larger job; the *lexical* `parent == root` comparison is a one-line
`.resolve()`. In a repo whose AT-149/AT-150 history is precisely path containment, that line should
not wait for the test. Not a finding — the row already says it — just a sequencing note.

## Ledger

- **AT-306** → `fixed`. The count is gone from both former sites and the note prevents its return;
  the gate is accurate in every other respect (§3 table). Moves to `verified` on a later re-check.
- **AT-307** → `fixed`. Assertion present, on the only path, and proved to bite under three
  independently-forced red baselines including one the maker never tried (§2).
- **AT-311** *(new, medium)* — KILLED is still `exit != 0`; a mutation causing a collection error is
  reported KILLED with an empty failure list, and the `defends:` label is never asserted (M4's label
  names a test that does not exist).
- **AT-312** *(new, low)* — the harness needs a shared, parameterised home now that C7 requires a
  mutation run of every test-adding unit.

## What I re-ran to produce this verdict

`git show --stat 6cc11e6` · `git show 6cc11e6` · `sha256sum projects/erp/screenmap.json` (before and
after every probe) · `uv run pytest -o addopts= -q` · `uv run ruff check src tests scripts` ·
`uv run autotester doctor` · the committed `mutation_harness.py` · four checker-authored harness
variants (red-suite / no-tests / collection-error baselines, and a collection-error mutation) ·
`uv run python scripts/migrate_url_patterns.py` (dry run, no `--write`) · live
`build_screen_map(ProjectStore('erp'))` · `repair()` / `known_hosts()` probes against the real
`projects/erp/project.json` · `git ls-files --error-unmatch` on four paths · greps over
`tests/test_migrate_url_patterns.py`, `qa/gates/t135-url-pattern-data-migration.md`,
`qa/issues.jsonl`, and `src/autotester/ui/`.

**Protected-state confirmation:** `projects/erp/screenmap.json` sha256 is
`46e97134a81d27892db9113d436984d92e520aae5f4a894bc279739726057ebf` both **before** and **after**
every command above — byte-unchanged. The migration has **not** been run: the three
`/vidysea.com/erp/trainers` values are still in the file and the dry run still reports
`would repair 3 url_pattern(s) across 1 file(s)`. The gate is still **unanswered** — no `Answered:`
line exists.
