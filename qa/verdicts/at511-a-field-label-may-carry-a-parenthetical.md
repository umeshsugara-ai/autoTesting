# Verdict — at511-a-field-label-may-carry-a-parenthetical

**Cycle checked:** 1
**Date:** 2026-09-18
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`
**Unit commit:** `e5efa7a`. Tick stamp `88c1373` confirmed to touch only `qa/.last-tick`.
**Contract:** `qa/contracts/core-invariants.md`, C10 and C7.

## Re-run, independently, everything the manifest claims

- `uv run pytest -q -o addopts= tests/test_ledger_checks.py tests/test_doctor.py` → **46 passed**
  (matches).
- `uv run ruff check src tests scripts` → **All checks passed!** (matches).
- `uv run autotester doctor` → **doctor: clean** (matches).
- `uv run python scripts/mutation_check.py qa/evidence/at511-a-field-label-may-carry-a-parenthetical/mutations.json`
  → **4/4 mutations killed**, exit 0. Read each result's `claims to kill` vs `actually failed`
  line myself: all four are an exact one-to-one match (not merely a superset), so each row is
  isolated to precisely the test it names. This tool is the project's declared
  `isolation.sandbox` (`qa/adapter.json`) — it copies `scripts/tests/src` to a temp dir outside
  the repo, asserts the baseline is green, checks the anchor matches exactly once, and restores
  the file after each mutation — so re-running it myself satisfies step 4b's isolation
  requirement without a second hand-rolled copy.
- `PYTHONUTF8=1 uv run python qa/evidence/at511-.../at511_measure.py` → **SHRINKS: 0 / GROWS: 0**
  (matches — the proposal now *is* shipped, as the manifest predicted).
- **Independently re-derived the historical 6-dropped/0-added headline myself, from scratch, not
  by re-running the maker's own comparison script.** Loaded the PRE-FIX module
  (`git show 97fba9f:src/autotester/ledger/checks.py`) via `importlib.util.spec_from_file_location`
  from a copy written only to my own scratchpad (never into the bound tree), registered it in
  `sys.modules` first, and diffed the id set `_marker_lines` yields — old module vs the currently
  shipped one — over every file in `qa/manifests/*.md` and `qa/verdicts/*.md`. Result: exact match
  to the manifest's claim — `verdicts/at097-session-start-hook-regression.md` drops `AT-029,
  AT-097`; `verdicts/at176-at178-render-not-scan.md` drops `AT-174, AT-176, AT-178, AT-189`;
  2 artifacts changed, 6 dropped, 0 added, nothing else in the whole corpus moved.
- `uv run pytest -q` → **exit 0**, redirected to a file and scanned whole (not `tail`ed, per
  AT-503): 640 dots across the summary lines, one `s` (a pre-existing documented skip), zero
  `FAILED`/`ERROR` anywhere in the file. Matches.
- **C10 diff scope:** `git show --stat e5efa7a` touches exactly
  `src/autotester/ledger/checks.py`, `tests/test_ledger_checks.py`, and the unit's own
  `qa/manifests/at511-...md` + `qa/evidence/at511-.../*` — nothing else, no deletion of an
  unrelated function/test/config key. Clean.

## Attacking the five points named in the dispatch

1. **Digit-labeled real field.** Grepped `qa/manifests`, `qa/verdicts`, `qa/contracts` for any
   ALL-CAPS field label containing a digit (`PHASE 2 NOTES:`-shaped) — **zero hits**. The
   manifest's own disclosure ("None exists today... that is a trade, not a proof") holds; no
   live instance exposes this blind spot.
2. **The 167 number, and whether it's the right argument.** Independently counted lines matching
   the naive "any parenthetical" widening across `qa/**/*.md`: **172** (close to the manifest's
   167 — the gap is almost certainly scan-scope, e.g. `qa/contracts`/`qa/gates` included here vs
   not there; not investigated further since neither number is what PASS rests on). More to the
   point of the question asked: I traced whether any of those lines actually occur as a *follow*
   line inside a live `_marker_lines` walk today — i.e. would genuinely have ended a real block
   early — and found **zero**. Checked this by hand on the manifest's own three cited examples:
   `AT-036 (filed in the previous unit):` in `qa/manifests/at036-screenshot-retry.md:12`,
   `AT-038 (filed by the checker...):` in `qa/manifests/at038-secrets-scan-key-scoped.md:11`, and
   `**AT-335 (filed, high, NOT fixed):**` in `qa/manifests/at227-first-paint-modal.md:184` — each
   sits under its own heading, separated from the nearest `**Issues addressed:**` marker line by
   a blank line and an intervening `##` heading, so the walk never reaches any of them regardless
   of the digit rule. **So the sentence "Every one would end a block early" overstates today's
   demonstrated impact** — none of the 167/172 lines are actually swallowed by the naive rule in
   the current corpus; the digit rule is a defense against a hypothetical future shape, not a
   fix for an observed one. This does not weaken the unit: the manifest itself already names line
   counts "the wrong measure" and rests its real evidence on the id-set diff, which I reproduced
   independently and exactly (6/0 above). Recorded here as a narrative-precision note, not a
   FAILURES line — nothing about the fix's correctness turns on it, and mutation row 2 (digits
   back in the label) still correctly proves the guard is load-bearing against that hypothetical.
3. **The fence stop — luck or design?** Confirmed **luck of ordering**, exactly as the manifest's
   Known-limits admits. Traced `qa/verdicts/at500-a-letter-suffixed-id-is-an-id.md`: the real
   `ISSUES-WRITTEN:` field (line 140) sits inside a fenced dump of the checker's own returned
   verdict block (fence opens line 133, closes line 162). The walk starting at line 140 stops one
   line later at `EXPLANATION:` (line 141) via the pre-existing `_NEW_FIELD` condition — it never
   reaches, and therefore never needs, the newly-added fence-stop, because every field in that
   dump is immediately followed by another field with no blank line between. If `ISSUES-WRITTEN`
   had instead been the LAST field before the closing fence with nothing after it, the new
   fence-stop would matter and does correctly stop the walk there (that is the shape the original
   AT-511 issue's evidence names — `at147-at148-grant-boundary.md` etc.). The **unhandled** case is
   different and narrower: a marker line that starts a walk from ALREADY INSIDE a pre-existing
   fence opened before it (e.g. an illustrative quote of a verdict block inside prose discussing
   this very bug) — `_marker_lines` has no memory of fence state when it looks for where a marker
   block *starts*, only when deciding where a block *ends*. No live document is misread by this
   today (checked: no manifest's `**Issues addressed:**` scan and no verdict's `ISSUES-WRITTEN`
   scan currently starts inside an open fence). This is disclosed in the manifest's Known-limits
   but, unlike the C2 item below, was not yet given a ledger row — filing one now (AT-514, low).
4. **C2 near-cap, filed as a row rather than left in prose.** `wc -l tests/test_ledger_checks.py`
   = **295**, five lines under the 300 cap — confirmed. Fourth consecutive unit (AT-508, AT-509,
   AT-511) adding to this file since its AT-506 split, and `doctor` stays silent until 301 — the
   AT-506 shape one file later, exactly as flagged. Filing **AT-513** (medium,
   `structural-erosion`), matching AT-506's own severity/type, at the next free id (max existing
   id in the ledger is AT-512).
5. **Look for the next one.** No further distinct defect found beyond the two already covered
   above. The original AT-511 ledger issue's second concern (a closing ` ``` ` swept into a block
   when `ISSUES-WRITTEN` is the last field) is fixed and independently confirmed via
   `test_a_code_fence_ends_the_block` and its mutation row. The one residual gap is the
   marker-starts-inside-an-open-fence shape named in point 3, now tracked as AT-514.

## Capability coverage

4/4 rows reproduced via `scripts/mutation_check.py` (the project's declared sandbox instrument),
re-run myself and checked kill-attribution line by line, not read from the manifest's paste.

## Live browser

Not UI-touching. Changed paths: `src/autotester/ledger/checks.py`, `tests/test_ledger_checks.py`,
and the unit's own manifest/evidence — no rendered surface changed. Mode D correctly not run.

## Issues addressed

`AT-511` (medium) — verifiably fixed by this unit (evidence above: the exact 6-id over-run this
issue named is gone, 0 new ones added). Flipped to `fixed`. `AT-512` (low) is a different
mechanism and correctly left untouched by this unit, per the manifest.

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met (C7, C10), all invariants hold
FAILURES (if any):
- none at >80% confidence against this unit's own criteria/capabilities
CAPABILITY-COVERAGE: 4/4 rows reproduced (scripts/mutation_check.py, isolated single-hunk edits, kill-attribution confirmed one-to-one)
LIVE-BROWSER: not-applicable (changed paths: src/autotester/ledger/checks.py, tests/test_ledger_checks.py, qa/manifests/…, qa/evidence/…)
ISSUES-WRITTEN: AT-513 (new, medium), AT-514 (new, low); AT-511 flipped open -> fixed
EXPLANATION: The fix is correct and independently re-derived from first principles, not from the
manifest's own measurement script — I loaded the pre-fix module by path and diffed id sets myself,
landing on the same 6-dropped/0-added headline. The digit-exclusion guard is proven load-bearing
against the rejected naive widening (mutation row 2), though the manifest's "every one would end a
block early" framing overstates today's demonstrated impact — none of the 167/172 matching lines
actually sit inside a live marker-continuation walk right now, a defense-in-depth claim rather than
an observed defect, noted but not a failure. Two new low/medium findings filed (C2 near-cap,
fence-start-inside-a-fence gap), both disclosed in the manifest's own Known-limits and neither
blocking this PASS.
```

## Handshake

Checker: fresh Mode A subagent, bound to `d:/autoTesting`, dispatched to check
`at511-a-field-label-may-carry-a-parenthetical` fix cycle 1.
