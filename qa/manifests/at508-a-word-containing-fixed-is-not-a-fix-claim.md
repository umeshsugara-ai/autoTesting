# Manifest — at508-a-word-containing-fixed-is-not-a-fix-claim

**Unit:** AT-508 — the "did this manifest claim a fix?" filter was a bare substring test, so an
ordinary word *containing* "fixed" read as a fix claim. It then accused a manifest that had
**correctly** declared an issue unfixed of leaving a stale ledger row — the exact case the filter
exists to protect. A false accusation, not a miss.
**Contract:** `qa/contracts/core-invariants.md` (C10: the guard over the handshake record must
report the record truthfully — an accusation it cannot support is worse than a gap)
**Goal task:** none (issue-driven)
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-508 (medium, open -> fixed)

## Provenance — this one was not found by the maker-checker pair

Live since `385fec1` (AT-496). **Four units built directly on top of this function** — AT-496 wrote
it, AT-500 widened its id pattern, AT-504 fixed its marker test, AT-506 moved it to its own module —
and each passed an independent `/checker`. None of them saw this.

It was found by a fresh **`senior-software-engineer`** review dispatched over the whole session's
diff, and confirmed independently twice more: by the maker, and by the at506 checker, which
re-derived it from scratch rather than acting on a relayed claim and filed AT-508 on its own
evidence. That is worth recording plainly: a checker judges a unit against its contract and its own
claims, which is a narrower question than "is this code correct". The pair did its job and the job
was not enough.

## The measurement first

The shipped filter was `"fixed" in note.lower() and "not fixed" not in note.lower()`. Reproduced
against the live code, ledger row `AT-900` correctly `open`, verdict `VERDICT: PASS`:

```
'AT-900 (low, unfixed - tracked separately)'  -> ledger-row-stale   FALSE ACCUSATION
'AT-900 (low, not-fixed, deferred)'           -> ledger-row-stale   FALSE ACCUSATION
'AT-900 (low, not yet fixed)'                 -> ledger-row-stale   FALSE ACCUSATION
'AT-900 (low, prefixed by AT-899)'            -> ledger-row-stale   FALSE ACCUSATION
'AT-900 (low, NOT fixed - reasons below)'     -> []                 correct
'AT-900 (low, open -> fixed)'                 -> ledger-row-stale   correct
```

Only the one exact phrase "not fixed" was excluded. A hyphen, an intervening word, or a prefix all
defeated it.

**Over-tightening is the dangerous direction, so it was measured before the fix was written**
(`qa/evidence/.../at508_measure.py`, output in `note-survey.out`). Every parenthetical on every
`**Issues addressed:**` line in the live manifests, old predicate versus new:

```
distinct notes: 54 | unchanged verdict: 54 | CHANGED: 0
```

Not one real note in the repository changes meaning. The live corpus uses 24 distinct shapes and
both arrow forms — `(low, open -> fixed)` **and** `(medium, open → fixed)` — plus bare `(fixed)`,
`(medium, fixed)`, and non-claims like `(medium)`, `(partial)`, `(the cycle-1 FAIL)`,
`(root cause, fix REPLACED in cycle 2)`, `(new, filed not fixed)`.

## What changed

- `src/autotester/ledger/checks.py` — two module constants and one predicate, replacing the inline
  condition:
  - `_FIXED = re.compile(r"\bfixed\b", re.IGNORECASE)` — the **word boundaries alone** settle
    `unfixed` and `prefixed`; neither has a boundary before `fixed`.
  - `_NOT_FIXED = re.compile(r"\bnot\b[\w\s-]{0,15}?\bfixed\b", re.IGNORECASE)` — the negation
    stays a regex so it also catches a hyphen (`not-fixed`) or an intervening word
    (`not yet fixed`). Its character class **cannot cross punctuation**, which is what stops a
    `not` belonging to a different clause from swallowing a real claim:
    `(not a duplicate, open -> fixed)` is still a claim.
  - `_claims_a_fix(note)` — the two combined, with the reasoning in its docstring.
- `tests/test_ledger_checks.py` — two parametrized tests, one per direction: four notes that merely
  contain the word, and four real claims (both arrows, bare `fixed`, and the clause-crossing case).

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_doctor.py` → `38 passed`
- `uv run autotester doctor` → `doctor: clean`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at508-a-word-containing-fixed-is-not-a-fix-claim/mutations.json`
  → `4/4 mutations killed`, exit 0
- **Re-derive the no-regression claim yourself:**
  `PYTHONUTF8=1 uv run python qa/evidence/at508-a-word-containing-fixed-is-not-a-fix-claim/at508_measure.py`
  → `distinct notes: 54 | unchanged verdict: 54 | CHANGED: 0`. `PYTHONUTF8=1` is needed because the
  live corpus contains `→` and this console is cp1252.
- Whole suite `uv run pytest -q` exits 0 — redirect to a **file** and scan it whole; that command
  resolves to `-qq` and prints no summary (AT-503).

## Actual outputs (from maker's own run)

```
$ uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_doctor.py
38 passed in 1.10s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run python scripts/mutation_check.py qa/evidence/at508-.../mutations.json
4/4 mutations killed          # exit 0, first run, every row's actual failures == its claim exactly
$ PYTHONUTF8=1 uv run python .../at508_measure.py
distinct notes: 54 | unchanged verdict: 54 | CHANGED: 0
```

## Capability coverage (each new claim -> its isolating falsification)

| capability | check | falsifying edit | observed |
|---|---|---|---|
| a word merely containing "fixed" is not a claim | `..._merely_contains_fixed...` (all 4 notes) | the bare substring test restored | `KILLED` |
| word boundaries are what settle `unfixed`/`prefixed` | `...[unfixed]`, `...[prefixed by an earlier note]` | `\bfixed\b` -> `fixed` | `KILLED` |
| the negation catches a hyphen or an intervening word | `...[not-fixed]`, `...[not yet fixed]`, `..._did_NOT_fix_stays_open` | drop `and not _NOT_FIXED.search(note)` | `KILLED` |
| the negation must not cross punctuation | `test_a_real_fix_claim_still_counts[not a duplicate, open -> fixed]` | `[\w\s-]{0,15}?` -> `[\s\S]{0,40}?` | `KILLED` |

`4/4 mutations killed`, every row's actual failure set equal to its claimed set — no over-claim and
no under-claim. The four mutations are deliberately one per *mechanism* rather than one per symptom:
the boundaries and the negation fix different halves of the bug, and the fourth is the only way the
fix itself can go wrong.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/ledger/checks.py`,
`tests/test_ledger_checks.py`, `qa/evidence/at508-a-word-containing-fixed-is-not-a-fix-claim/*`.

## Known limits (disclosed, not claimed)

- **`{0,15}` is a tuned constant, not a principle.** `(not fixed in this cycle, deferred)` is caught;
  a longer interposed clause such as `(not, after some deliberation, fixed)` is 26 characters and
  would read as a claim. No such note exists in the 54 live ones. The bound trades a rare
  false accusation for a rare miss, and given the whole point of this unit is that a false
  accusation costs more, it is deliberately the conservative direction — but it is a guess about
  English, and it should be revisited if the corpus grows a counter-example.
- **`(this cycle's fix — …)` is still not read as a claim**, because it says "fix", not "fixed".
  Two live manifests use that phrasing. I left it alone: widening to `fix\w*` would re-admit
  `prefix`, and the shape is rare enough that inventing coverage for it risks the exact class of
  bug this unit closes. Named here so it is a known gap rather than an unknown one.
- **The filter still trusts the manifest's own parenthetical.** A manifest that claims a fix it did
  not make produces a violation against the ledger rather than against the manifest. That is
  AT-496's original disclosed limit and is unchanged.
- **AT-507 is untouched** — `docs/ARCHITECTURE.md` still sits at exactly 150/150.

## Status: checked-PASS

Cycle 1, `qa/verdicts/at508-a-word-containing-fixed-is-not-a-fix-claim.md` (commit `62bc1fd`).
PASS, no failures: the checker re-derived the 54/54 no-regression result against the shipped
functions rather than running this unit's script and believing it, and reproduced all four mutation
rows in a fresh throwaway copy from a proven-green baseline.

**The finding that matters is not the confirmation — it is AT-509 (medium), which it went looking
for.** `check_qa_issue_rows` and `_is_marker_line` read only the marker line itself, so an issue id
named on a **continuation line** of a multi-line `**Issues addressed:**` list is silently skipped by
both the row-lost and the row-stale checks. AT-496 disclosed "only ids ON the marker line are read"
as a known limit and four units since then have treated it as a limit rather than a defect.

**The blindness is live — but my first statement of where was wrong, and the checker corrected it.**
I asserted that `at496-the-ledger-never-loses-a-row.md` demonstrates the gap. It does not: its
marker line (line 12) carries *both* `AT-496` and `AT-475`, and the continuation (line 13) carries
no id at all. I verified that myself after the correction rather than taking it on report. The real
instances the checker found are three other manifests — `at011-loop-md.md` (`AT-027`),
`at357-scope-sandbox-assertions.md` (`AT-384`, `AT-385`) and
`at379-scrollable-pane-reachability.md` (eight ids) — **11 ids invisible today**, all of which
happen to have rows, so no consequence has landed yet.

The direction is also now established fact rather than inference: it is a **miss** in both
sub-checks, not a false accusation. An id that is never examined can neither over-accuse via
`ledger-row-stale` nor under-protect via `ledger-row-lost`. That is a materially lower severity than
AT-508's direction, and worth saying plainly instead of letting the two findings blur together.

Also filed: **AT-510 (low)**, the `"fix"`-versus-`"fixed"` gap this manifest disclosed under Known
limits, promoted from prose to a tracked row per the AT-502/AT-507 precedent.

`uv run autotester doctor` → `doctor: clean` after the ledger close, checked this time rather than
assumed — the checker two units earlier PASSed its unit and left its own row `open`, and this guard
caught it.
