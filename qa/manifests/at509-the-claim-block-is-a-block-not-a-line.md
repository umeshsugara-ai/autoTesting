# Manifest — at509-the-claim-block-is-a-block-not-a-line

**Unit:** AT-509 — `check_qa_issue_rows` gated both of its checks on a single **physical line**, so
an issue id named on a continuation of a wrapped `**Issues addressed:**` / `ISSUES-WRITTEN` block
was read by neither. Invisible, never mis-judged.
**Contract:** `qa/contracts/core-invariants.md` (C10: the guard over the handshake record must read
the record as written, not as it wishes it were formatted)
**Goal task:** none (issue-driven; filed by the at508 cycle-1 checker)
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-509 (medium, open -> fixed)

## The measurement first

AT-496 disclosed "only ids ON the marker line are read" as a **known limit**, and four units since
inherited that framing without ever testing it. It is not a limit; it is a defect with a scope:

```
manifests  13 artifacts gaining ids | 29 ids newly visible
verdicts    9 artifacts gaining ids | 21 ids newly visible
                                   -> 50 ids across 22 artifacts were invisible
```

Direction, established before the fix rather than assumed: a **miss** in both sub-checks. An id
that is never examined can neither over-accuse via `ledger-row-stale` nor under-protect via
`ledger-row-lost`. That makes it materially less urgent than AT-508, whose direction was a false
accusation — and worth saying plainly so the two do not blur together.

**Every one of the 50 has a ledger row**, checked before the fix was written. So this closes a real
blind spot without a single new violation appearing on the live tree, and `doctor` is clean before
and after.

## The fix's own first version was wrong, and the live tree caught it

The rule was "consume to the end of the markdown paragraph". That is right for a **manifest** — its
block is prose that wraps and ends at a blank line, and all 13 terminate that way. It is wrong for a
**verdict**, which is not a paragraph at all but a run of labelled fields with no blank line between
them. `ISSUES-WRITTEN:` is followed immediately by `EXPLANATION:` and several lines of free prose,
so the walk swallowed the explanation and reported two ids it merely discussed:

```
$ uv run autotester doctor          # first version of this fix
ledger-row-lost: qa/verdicts/at465-466-unreadable-narration-keeps-its-cause.md
  - AT-466b is named here but has no row in qa/issues.jsonl
ledger-row-lost: qa/verdicts/at500-a-letter-suffixed-id-is-an-id.md
  - AT-290a is named here but has no row in qa/issues.jsonl
2 violation(s)
```

Both are prose mentions inside an `EXPLANATION`. That is **the AT-504 false-accusation shape,
reintroduced by the fix for AT-509** — the exact regression this chain of units exists to prevent,
committed by the unit fixing the next link in the same chain. It was caught because the check is run
against the live corpus and not only against fixtures, which is the only reason it did not ship.

## What changed

- `src/autotester/ledger/checks.py`:
  - **`_NEW_FIELD = re.compile(r"^[\s>#*_-]*[A-Z][A-Z0-9 -]*:")`** — an ALL-CAPS label ending in a
    colon begins the next field of a verdict block. `AT-901 (low, cycle-1 FAIL)` is not one: no
    colon follows the capitalised run.
  - **`_marker_lines(body, marker)`** — the marker line plus its continuations, stopping at a blank
    line, a heading, the next field, or another marker line. Consuming *to a stop condition* rather
    than a fixed number of lines is what keeps it honest when someone wraps to three lines.
  - `named` and `claimed` both read `_marker_lines(...)` instead of filtering `body.splitlines()`.
- `tests/test_ledger_checks.py` — four new tests: an id on a continuation is named; a fix claim on a
  continuation reaches the stale check; the block ends at a blank line or a heading (parametrized);
  and a verdict block ends at the next FIELD rather than at a blank line — the last written
  specifically because the first version of this fix failed it against the real tree.

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_doctor.py` → `43 passed`
- `uv run autotester doctor` → `doctor: clean`. **This is the load-bearing one.** 50 ids became
  visible; if any lacked a row, or if a block over-ran into prose, this is where it shows.
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at509-the-claim-block-is-a-block-not-a-line/mutations.json`
  → `5/5 mutations killed`, exit 0
- Re-derive the 50 yourself — compare the ids on the marker line alone against
  `checks._marker_lines(...)` for every file in `qa/manifests` and `qa/verdicts`. Use `PYTHONUTF8=1`:
  the corpus contains `·` and `→` and this console is cp1252.
- Whole suite `uv run pytest -q` exits 0 — redirect to a **file** and scan it whole (AT-503: that
  command resolves to `-qq` and emits no summary line).

## Actual outputs (from maker's own run)

```
$ uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_doctor.py
43 passed in 0.56s
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean                      # with 50 more ids in scope than before
$ uv run python scripts/mutation_check.py qa/evidence/at509-.../mutations.json
5/5 mutations killed               # exit 0; every row's actual failure set == its claim exactly
```

## Capability coverage (each new claim -> its isolating falsification)

| capability | check | falsifying edit | observed |
|---|---|---|---|
| a continuation id is named | `test_an_id_on_a_continuation_line_is_still_named` | `named` back to one physical line | `KILLED` |
| a wrapped fix claim reaches the stale check | `test_a_fix_claim_on_a_continuation_line_is_read` | `claimed` back to one physical line | `KILLED` |
| a verdict block ends at the next FIELD | `test_a_verdict_block_ends_at_the_next_FIELD...` | drop the `_NEW_FIELD` stop | `KILLED` |
| the block ends at a blank line | `..._blank_line_or_a_heading[\n\nAT-901 …]` | drop the blank-line stop | `KILLED` |
| the block ends at a heading | `..._blank_line_or_a_heading[\n## Why AT-901 …]` | drop the heading stop | `KILLED` |

`5/5 mutations killed`, **each isolated to exactly one test** — no mutation is caught by a second
test covering for it. The three stop conditions are deliberately falsified separately, because the
whole risk of this unit is a block that runs too far, and a single "it stops somewhere" test would
have hidden two of the three.

One process note: the first mutation run was **refused**, not failed —
`MUTATION RUN INVALID: … names test(s) that are not collected`, exit 2 — because a parametrized
nodeid carries the two characters `\n`, and this file's JSON had produced a real newline. The
instrument's fail-closed design caught a bad evidence file rather than scoring it.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/ledger/checks.py`,
`tests/test_ledger_checks.py`, `qa/evidence/at509-the-claim-block-is-a-block-not-a-line/*`.

## Known limits (disclosed, not claimed)

- **A continuation line's prose is now in scope, and nothing protects it the way `_is_marker_line`
  protects the first line.** AT-504's backtick rule gates only the marker line; an id merely
  discussed on a continuation counts as named. `at298-migration-host-guard.md` already does this —
  *"filed twice under the `b`-suffix convention AT-293 established"* — and `AT-293` is now read as
  named. It has a row, so nothing is reported, and all 50 newly-visible ids have rows. But the
  residual risk is real and is the same shape that produced the two false positives above: a
  document *about* the guard, wrapping, naming an example id with no row. **I judged the trade
  worth it** (50 real ids recovered against 0 current false positives, and the direction of the old
  behaviour was a silent miss) — but the checker should weigh that independently, and if it
  disagrees the honest answer is a narrower rule that requires a list separator, not a claim that
  the risk is absent.
- **`_NEW_FIELD` is a heuristic about ALL-CAPS labels.** A manifest whose continuation begins with
  something like `NOTE:` would end the block early — a miss, not a false accusation, which is the
  safer direction. None exists today.
- **The stale check still matches a parenthetical within one line.** `AT-900\n(low, open -> fixed)`
  split across the wrap is still not read as a claim; only `AT-900 (low, open -> fixed)` wholly on
  one line is. `at358-visual-order-detector.md` writes it the latter way, which is why this works in
  practice, but the limit is real.
- **AT-507 and AT-510 are untouched**, and `docs/ARCHITECTURE.md` still sits at exactly 150/150.

## Status: ready-for-check
