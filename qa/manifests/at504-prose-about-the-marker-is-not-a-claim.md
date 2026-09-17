# Manifest — at504-prose-about-the-marker-is-not-a-claim

**Unit:** AT-504 — `check_qa_issue_rows` decides which lines carry an issue claim with
`marker in line`, so a document that *discusses* the marker is read as one that *uses* it. The
guard's own documentation therefore inflates its output, without bound, as more documents describe
it.
**Contract:** `qa/contracts/core-invariants.md` (C10: a maker/checker commit names the qa/ files its
handshake writes — a guard over that record must report the record, not the prose about it)
**Goal task:** none (issue-driven; filed and escalated low -> medium by the at500 cycle-1 checker)
**Date:** 2026-09-18
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-504 (medium, open -> fixed)

## The measurement first

This is my own debt, two units old, and it was caught by the checker rather than by me.

`AT-500` shipped a real-repo falsification: delete `AT-298b`'s ledger row and the guard names the
loss from the surviving handshake artifacts. I measured **2** violations and wrote 2 into the
manifest. That number then decayed while nobody touched the code:

```
2  when I ran the probe   (the at500 manifest did not exist yet)
3  once the at500 manifest existed   -- its line 25 quotes `**Issues addressed:**` while naming
                                        AT-298b, as documentation OF THE BUG
4  once the at500 verdict existed    -- the verdict quotes the same line while recording the finding
```

Each new document that so much as mentions the marker adds another phantom row. The cycle-1 checker
reproduced both increments independently and raised the issue from low to medium on that basis. It
is inert while the ledger is intact (`0` violations with the row present, `doctor: clean`), so it
never blocked anything — it just made the guard progressively less precise about a real loss.

**The obvious fix is wrong, and I measured that before writing it.** Tightening `marker in line` to
`line.lstrip().startswith(marker)` would have dropped **12 real claims**, because the marker is
written decorated in live verdicts:

```
**ISSUES-WRITTEN:** AT-106, AT-107                         qa/verdicts/at097-session-start-hook-regression.md
**ISSUES-WRITTEN:** AT-192 (medium), AT-193 (medium), ...  qa/verdicts/at176-at178-render-not-scan.md
## ISSUES-WRITTEN: AT-210, AT-211, AT-212, AT-213          qa/verdicts/at206-guards-that-guard.md
## ISSUES-WRITTEN: AT-214                                  qa/verdicts/at206-guards-that-guard.md
```

Measured over the live tree with the shipped predicate: **627 ids still read** (12 more than the
naive form would keep), **exactly 3 dropped** — the three prose mentions AT-504 named — and **0**
ids read that the old test did not read, i.e. the new predicate is a strict subset of the old one
and cannot invent a claim.

## What changed

- `src/autotester/doctor.py`:
  - `import re` hoisted to module scope (it was a function-local import; the new helper needs it).
  - **`_MARKER_LEAD = re.compile(r"^[\s>#*_-]*")`** — the markdown decoration that may precede a
    marker and still leave it a marker.
  - **`_is_marker_line(line, marker)`** — strips that decoration, then requires the line to *start*
    with the marker (with the marker's own `*` bold wrapper stripped, since the line's was).
    **A backtick is deliberately NOT in the stripped set:** it is the one character that reliably
    separates `` `ISSUES-WRITTEN` marker. The only ids it reads are… `` (prose) from
    `**ISSUES-WRITTEN:** AT-106` (a claim). That asymmetry is the whole fix.
  - Both `named` and `claimed` now use `_is_marker_line` instead of `marker in line`.
- `tests/test_doctor.py` — three new tests:
  - `test_a_decorated_marker_line_is_still_a_marker_line`, parametrized over the four live forms
    (bare, `**bold:**`, `## heading`, `  - list item`) — this is the guard against over-tightening,
    and it is the test the 12-claim measurement exists to justify.
  - `test_prose_that_quotes_the_marker_is_not_a_claim`, parametrized over the two real shapes from
    at500's manifest.
  - `test_a_line_opening_with_the_marker_in_backticks_is_not_a_claim` — the harder case from at500's
    own verdict, where the marker really is at the start of the line's content and *only* the
    backtick distinguishes it.

## How to verify (commands + expected)

- `uv run pytest -q -o addopts= tests/test_doctor.py` → `30 passed`
- `uv run autotester doctor` → `doctor: clean`
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run python scripts/mutation_check.py qa/evidence/at504-prose-about-the-marker-is-not-a-claim/mutations.json`
  → `4/4 mutations killed`, exit 0
- **The compounding is gone, measured the same way it was found:**
  `uv run python qa/evidence/at500-a-letter-suffixed-id-is-an-id/probe_after.py` → `2` violations
  with `AT-298b`'s row deleted (not 4), `0` with it intact. That also restores the truth of the
  number AT-500's manifest originally recorded.
- The whole suite `uv run pytest -q` exits 0. It resolves to `-qq` and prints **no** summary line
  (AT-503, open) — judge it by exit code and the `[100%]` line.

## Actual outputs (from maker's own run)

```
$ uv run pytest -q -o addopts= tests/test_doctor.py
30 passed
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run python scripts/mutation_check.py qa/evidence/at504-.../mutations.json
4/4 mutations killed                      # exit 0, first run

$ uv run python qa/evidence/at500-.../probe_after.py
INTACT:            0 violation(s) naming AT-298b
AT-298b DROPPED:   2 violation(s) naming AT-298b
  ledger-row-lost: qa/manifests/at298-migration-host-guard.md
  ledger-row-lost: qa/verdicts/t135-coverage-merge-expand.b.md
```

## Capability coverage (each new claim -> its isolating falsification)

`qa/evidence/at504-prose-about-the-marker-is-not-a-claim/mutations.{json,out}`; every edit is one
hunk in `src/autotester/doctor.py`. Ids below are in `tests/test_doctor.py`.

| capability | check | falsifying edit | observed |
|---|---|---|---|
| prose about the marker is not a claim | `test_a_line_opening_with_the_marker_in_backticks...` | `_is_marker_line` body -> `marker in line` | `KILLED` |
| a decorated claim is still a claim | `test_a_decorated_marker_line_is_still_a_marker_line[**bold**, ## heading]` | drop the `_MARKER_LEAD.sub` strip | `KILLED` |
| the marker's own bold wrapper is stripped too | `..._manifest_names...`, `..._still_open...` | `marker.strip("*")` -> `marker` | `KILLED` |
| a backtick is not decoration | `test_a_line_opening_with_the_marker_in_backticks...` | add `` ` `` to `_MARKER_LEAD`'s class | `KILLED` |

`4/4 mutations killed`. The fourth row is the one that matters most and the one a lazier test set
would have missed: every other mutation is caught by several tests at once, while adding a backtick
to the stripped set is caught by exactly one — the test written for precisely that asymmetry.

## Live browser evidence

Not UI-touching — no surface changed. Changed paths: `src/autotester/doctor.py`,
`tests/test_doctor.py`, `qa/evidence/at504-prose-about-the-marker-is-not-a-claim/*`.

## Known limits (disclosed, not claimed)

- **A list item that only talks about the marker is still a false positive.** `- ISSUES-WRITTEN
  lines are read by the guard, so AT-900 …` strips to `ISSUES-WRITTEN lines are read…` and counts.
  No such line exists in the tree today (the measurement found exactly 3 loose-only ids and all 3
  are now excluded), but the predicate is a heuristic over prose and will never be airtight. The
  honest bound is: it is a strict subset of the old behaviour, so it can only ever report fewer
  phantoms than before, never more.
- **Still line-scoped.** An `**Issues addressed:**` claim that wraps onto the next line still has
  its continuation ignored — the pre-existing limit AT-496 disclosed, unchanged here. Several live
  manifests do wrap (`at496`'s own does), so this is real, not theoretical.
- **`src/autotester/doctor.py` is now 287 lines against C2's 300 cap**, up from 264 two units ago.
  Three consecutive units have added to this one file. That is the same structural-erosion shape as
  AT-488 and AT-502; I am naming it here rather than splitting mid-fix-cycle, and the next unit to
  touch this file should treat the split as its first question, not its last.
- **AT-503 is untouched** — the adapter's verify command is still unreadable. Its fix changes either
  `qa/adapter.json` (which a maker may not rewrite mid-run) or `pyproject.toml`'s repo-wide
  `addopts`, so it wants its own unit and probably a decision.

## Status: checked-PASS

Cycle 1, `qa/verdicts/at504-prose-about-the-marker-is-not-a-claim.md` (commits `3fff45b`, then
`d2b5b98` adding the erosion judgement), pushed per D-007. PASS with no failures.

The checker re-derived the over-tightening numbers with its own script rather than trusting the
pasted ones, and reproduced all three structural deltas exactly: **+12** against a naive
`startswith`, **−3** against the old substring test, **0** gained — the strict-subset property that
matters. Its absolute total read 629 where this manifest says 627; that gap is real and benign, and
worth recording rather than smoothing over: two loops share this working tree and a couple of `qa/`
files landed between my measurement and its own. The deltas are exact because they are structural;
the absolute is a moving target because the corpus is.

It also checked the two things this manifest asserted without proving, and both held: the three
decorated-marker citations (`at097`, `at176`, `at206`) are live lines, and the disclosed list-item
blind spot (`- ISSUES-WRITTEN lines are read…`) exists nowhere in the tree today.

**AT-506 (medium) filed against the erosion this manifest only noted in prose.** `doctor.py` grew
264 → 287 across three consecutive units (`385fec1`, `17d0d58`, `6f97f45`), and `doctor` stays
silent until 301. The checker judged that the AT-502 precedent makes this a filed row rather than a
manifest note, and it is right: a limit recorded only in the prose of a closed manifest is a limit
nobody will read at the moment it matters. The next unit touching `src/autotester/doctor.py` opens
with the split question.
