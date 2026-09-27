# Manifest — t186-details-content

**Unit:** T-186 / AT-453 — closed `<details>` judged by `::details-content`'s computed
`content-visibility` alone, ignoring the pseudo's own `display`, so an author
`::details-content{display:contents}` or `{display:inline}` (content-visibility does not apply,
the body still paints) drops visible text.
**Contract:** `qa/contracts/ui.md` U14(b)/U14(c) (D-049 amendment) · `qa/contracts/core-invariants.md` C2, C7
**Goal task:** T-186
**Date:** 2026-09-27
**Fix cycle:** 1 of max 2 (D-048 gate option b — this unit is capped at 2 cycles, not 3)
**Dual check:** no (`base_criticality: medium`, not `critical`)
**Persona walk:** skip (backend-only: a browser-side text-visibility detector fix in
`src/autotester/browser/visual_order.js`; no screen, navigation path, or user-facing flow in
`ui/app.py` touched — audience for this repo is `internal-tool`/local single-operator per
`qa/contracts/ui.md` No-fire list, and this unit changes none of its routes)
**Issues addressed:** AT-453 (open → fixed, pending checker verification)
**Executor:** claude-sonnet-subagent (a /maker build subagent, run in its own worktree
`D:/autoTesting/.claude/worktrees/agent-a5a815f4c0d62fe8b`, branch `wave/t186-details-content`)
**Executor rationale:** Dual check not required (medium criticality); no delegation ledger/class
tag exists for this task shape and the fix direction was already measured and validated by a
prior checker (D-049) down to the exact code line, so there is no discovery work to hand to an
external model — a Claude subagent applying and re-verifying an already-proven patch is the
right-sized executor.

## The criterion that decides what "hidden" means here

`qa/contracts/ui.md` **U14(b)** — "No new false negative on visible text": *"A change to the
detector must not stop reporting text a reader can see on a page where the pre-change detector
reported it."* The **pre-change detector**, per D-048/D-049, is the code at this unit's branch
point (master `72513124`), and the **north-star tie-break** written into U14 is explicit: *"where
suppressing a false positive and keeping a true positive conflict, keeping the visible text
wins."* U14(c) is the disclosed **does-not-see list** — classes filed but not charged — and
AT-453 is named there explicitly as **excluded**: *"AT-453 (the `::details-content`
display:contents/inline miss) is NOT added to (c). It stays charged and open as its own unit,
capped at 2 cycles."* So the criterion is unambiguous: this class of miss is charged, not filed,
and "hidden" for a closed `<details>`'s body means what the browser's own paint says, not what
`content-visibility` alone says.

That criterion does not, by itself, spell out the exact expression. The **operational definition**
comes from AT-453's own filed evidence (`qa/issues.jsonl` id `AT-453`) and D-049's `Links`, which
cite a **measured, checker-validated fix direction**:
`qa/evidence/browser-at438-display-contents-2026-09-16-checker-c3/fixdir3.py` — the checker
already built and ran this exact candidate against 26 details-shaped pages (`fixdir3.out`,
`CAND wrong: []`) before this unit existed:

```
OLDL = 'window.getComputedStyle(box, "::details-content").contentVisibility === "hidden") return false;'
NEWL = '(p => p.contentVisibility === "hidden" && HIDES_ON.test(p.display))(window.getComputedStyle(box, "::details-content"))) return false;'
```

I did not have to guess: the criterion (U14b/c) says this class is charged, and the checker's own
prior measurement already named the exact correct expression. I applied that expression verbatim
(same semantics, reformatted to fit house style with a leading arrow function), not a fresh guess
of my own — which is exactly what the brief's cycle-cap warning asked to avoid.

## What changed

- `src/autotester/browser/visual_order.js:70-77` (`contentsRenders`) — the `<details>` branch now
  reads the `::details-content` pseudo's computed style **once** and checks
  `contentVisibility === "hidden" && HIDES_ON.test(display)` instead of `contentVisibility ===
  "hidden"` alone. A single hunk; no other line in the file touched. Comment added citing AT-453
  and the measurement it is based on.
- `tests/fixtures/bidi_site/cvcontents.html` — two new rows, scoped by id so neither can change the
  plain closed-details case (`#a3`, `#a4`) or the accordion case (`#accordion`) already in the
  fixture:
  - `#a3::details-content { display: contents }` — closed `<details>`, body
    `CONTENTS_DETAILSCONTENT_CONTENTS_A3` (must now be reported).
  - `#a4::details-content { display: inline }` — closed `<details>`, body
    `CONTENTS_DETAILSCONTENT_INLINE_A4` (must now be reported).
- `tests/test_browser_visual_order.py` — the two new sentinels added to
  `test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor`'s `shown` tuple, with a
  docstring paragraph naming AT-453 and its evidence. File is now exactly 300 lines (the cap).

## How to verify (commands + expected)

- `uv run pytest tests/ -k details` → exit 0 (the unit's `done_check`)
- `uv run pytest tests/test_browser_visual_order.py tests/test_browser_scroll_invariance.py tests/test_browser_unreadable.py` → all pass/xfail as before, no new failure
- `uv run pytest` → exit 0, one summary line (no `-q`, AT-503)
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/ -k details
1 passed, 2055 deselected, 1 warning in 24.34s
```

```
$ uv run pytest tests/test_browser_visual_order.py -v
collected 32 items
tests\test_browser_visual_order.py ................................      [100%]
32 passed in 9.07s
```

```
$ uv run pytest tests/test_browser_scroll_invariance.py tests/test_browser_visual_order.py tests/test_browser_unreadable.py -v
collected 98 items
tests\test_browser_scroll_invariance.py ..xx....xx..xx........xx..xx..xx [ 32%]
..xx..............                                                       [ 51%]
tests\test_browser_visual_order.py ................................      [ 83%]
tests\test_browser_unreadable.py ................                        [100%]
84 passed, 14 xfailed in 30.39s
```

```
$ uv run ruff check src tests scripts
All checks passed!
```

```
$ uv run autotester doctor
doctor: clean
```

```
$ uv run pytest
3 failed, 2033 passed, 6 skipped, 14 xfailed, 15 warnings in 1564.96s (0:26:04)
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
```

**The first run above was piped through `tail -60`, which is exactly the trap this unit's brief
warned about** ("a grouped command reports only the last exit code") — the shell-visible exit code
was `tail`'s (0), not pytest's. Nothing was actually masked here (the summary line and every
`FAILED` row above are pytest's own real stdout, captured intact), but I re-ran it a second time
with no pipe, redirected straight to a file, exit code captured immediately after:

```
$ uv run pytest > .work/full-pytest-run2.txt 2>&1; echo EXITCODE:$? >> .work/full-pytest-run2.txt
$ tail -6 .work/full-pytest-run2.txt
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
3 failed, 2033 passed, 6 skipped, 14 xfailed, 15 warnings in 968.40s (0:16:08)
EXITCODE:1
```

**Identical failure set both runs** (same three, in the same order), and this second run's own
`$?` — not a downstream process's — is `1`. `.work/` is gitignored so this file is not committed;
the pasted tail above is the record.

**Three failures total, not one.** The brief named one known pre-existing failure (AT-627). A
second class exists, also pre-existing and also unrelated to this unit's diff:

1. **AT-627** (named in the brief): `test_flake_probe_real_process.py::…grandchild` — low,
   open, load-sensitive. Reproduced in isolation on this branch:
   ```
   $ uv run pytest tests/test_flake_probe_real_process.py -v
   FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
   1 failed, 1 passed in 11.65s
   ```
2. **NOT named in the brief, found during this unit's verify:**
   `test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail` and
   `::test_revised_goal_contract_is_registered`. Both are about `.goal/goal.json` task
   registration, not this unit's code:
   - `git diff --stat .goal/goal.json .goal/dashboard.html` is **empty** in this worktree — I
     never wrote to either file, so whatever state they are in is exactly master `72513124`'s,
     unrelated to anything this unit built.
   - `test_no_pending_task_has_a_done_check_...` fails because five ALREADY-REGISTERED pending
     tasks — **including this unit's own `T-186`** — carry a `done_check.cmd` shape
     (`uv run pytest tests/ -k <filter>`) that the test's own allowlist (AT-154/AT-155) does not
     credit as task-specific: `tests/` is "the whole suite wearing a path", and `-k` is not
     parsed. Measured: `uv run pytest tests/ -k details --collect-only -q` collects exactly
     **one** test, `test_browser_unreadable.py::…[closed-details]`, which already passed before
     this unit existed — T-186's registered done_check does not exercise the fix this manifest
     is about (see "How to verify" above, and note the unit's actual `done_check` from the queue
     still exits 0, which I ran and pasted first). This is a **task-registration defect**, not a
     code defect, and predates this unit (`T-186` was `created: 2026-09-26T22:47:07`, `attempts:
     0`, before this session started).
   - `test_revised_goal_contract_is_registered` fails on a hardcoded `assert … == 70`; the real
     count is `81`. Also unrelated to this unit's code, and also pre-existing.
   - Filed to `qa/feedback-inbox.md` (2026-09-27 entry) rather than fixed here: rewriting five
     tasks' `done_check`s and a hardcoded task-count assertion is its own unit, not a
     single-hunk fix inside a 2-cycle-capped detector unit, and `.goal/goal.json` /
     `test_goal_done_checks.py` are outside what this manifest's "What changed" touches.

**Confirmed: these three are the only full-suite failures**, and none is caused by this unit's
diff (`src/autotester/browser/visual_order.js`, `tests/fixtures/bidi_site/cvcontents.html`,
`tests/test_browser_visual_order.py` — none of which either failing area imports or reads).

## Capability coverage (each new claim -> its isolating falsification)

| capability (one line) | the check that covers it | the falsifying edit | observed (pasted runner output) |
|---|---|---|---|
| a closed `<details>` whose `::details-content` is author-overridden to `display:contents` reports its body text (AT-453, A3) | `tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor` (asserts `CONTENTS_DETAILSCONTENT_CONTENTS_A3 in seen`) | revert `visual_order.js:76-77` to the pre-fix line: `window.getComputedStyle(box, "::details-content").contentVisibility === "hidden") return false;` (drops the `HIDES_ON.test(display)` conjunct) | GREEN before (throwaway copy, `git archive` of the working tree via `git stash create`): `1 passed in 9.07s`. RED after, same node id, same assertion line: `AssertionError: ('CONTENTS_DETAILSCONTENT_CONTENTS_A3', 'Quarterly report for the trainers list...firstdca3a4')` — the A3 sentinel is the one named in the failure, not an import/collection error. |
| the same, for `display:inline` (AT-453, A4) | same test, `CONTENTS_DETAILSCONTENT_INLINE_A4 in seen` | same single-hunk revert (one edit covers both A3 and A4, since both go through the same conjunct) | Covered by the same GREEN-before/RED-after pair above — the revert also drops A4's report (confirmed: with the revert applied, neither A3 nor A4 appears in `seen`; the assertion fires on A3 first because it is listed first in the tuple, so RED shown above is the joint failure). |
| the ordinary closed-`<details>` case (no author override) still stays hidden -- the fix must not become a blanket "closed details always paints" | same test, `CONTENTS_CLOSEDDETAILS_S3 not in seen` (already existed before this unit; re-verified as still passing) | n/a -- this is a **non-regression** claim, not a new capability; its own falsification is `at438-display-contents.md`'s existing "walk-up trap" row, unchanged by this unit | Confirmed passing before and after this unit's edit in the bound worktree (`32 passed` above includes this assertion), and live-probed directly (see Live browser evidence): `S3_closeddetails_still_hidden: true`. |
| the accordion / `content-visibility:hidden` non-`<details>` cases are unaffected -- the fix narrows only the `DETAILS` branch, not `HIDES_ON` itself or the non-details path | live probe (`qa/evidence/browser-t186-details-content-2026-09-27/report.json`) | n/a -- `HIDES_ON` itself, and the non-`DETAILS` branch at `visual_order.js:78-80`, are untouched by this unit's single-hunk edit (diff-confirmed) | Live probe: `S4_cvhidden_still_hidden: true`, `S2_opendetails_still_shown: true`, `quarterly_report_control: true`. |

**Falsification method, per the maker/checker isolation rule:** the revert was applied in a
**throwaway copy outside the bound worktree**, built with `git archive` (never `tar` on the live
tree): `git stash create` produced a commit-ish snapshot of the working tree
(`9ecd054ead94c8860c51dbc04681cab32b639476`) without touching the worktree, `git archive
--format=tar <sha>` was piped into a fresh directory under the session scratchpad (so no
`__pycache__`/`.pytest_cache` could bake a stale path into a traceback), a fresh `uv` venv was
built there, the single-hunk revert was applied, and `uv run pytest
tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor
-v` was run before and after. The bound worktree was confirmed unchanged afterwards
(`git status --porcelain` showed the same three modified files, unrelated to the throwaway copy),
and the throwaway directory was deleted once the falsification was captured.

```
# BEFORE the revert (throwaway copy, fix intact) -- GREEN
$ uv run pytest tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor -v
tests\test_browser_visual_order.py .                                     [100%]
1 passed in 9.07s

# single-hunk revert applied to the THROWAWAY COPY ONLY:
#   src/autotester/browser/visual_order.js
#   -      (p => p.contentVisibility === "hidden" && HIDES_ON.test(p.display))(window.getComputedStyle(box, "::details-content"))) return false;
#   +      window.getComputedStyle(box, "::details-content").contentVisibility === "hidden") return false;

# AFTER the revert -- RED, on the named assertion
$ uv run pytest tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor -v
FAILED tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor
E   AssertionError: ('CONTENTS_DETAILSCONTENT_CONTENTS_A3', 'Quarterly report for the trainers listCONTENTS_PLAIN_S1openCONTENTS_OPENDETAILS_S2closedCONTENTS_ANIMATED_S6LASTCHILD_SIBLING_S7accCONTENTS_ACCORDION_S10firstdca3a4')
1 failed in 2.66s

$ git status --porcelain   # bound worktree, confirmed intact after the throwaway run
 M src/autotester/browser/visual_order.js
 M tests/fixtures/bidi_site/cvcontents.html
 M tests/test_browser_visual_order.py
```

## Live browser evidence

Real Chromium (151.0.7922.34), launched **headed** (`headless=False`), navigated directly to
`tests/fixtures/bidi_site/cvcontents.html` via `file://` (no HTTP server needed for this fixture),
and measured with the **shipping** `autotester.browser.observe.visual_text(page)` — not a
hand-copied JS string. Full report:
`qa/evidence/browser-t186-details-content-2026-09-27/report.json`
(`probe.py` alongside it, `after.json` the raw result).

```
{
  "chromium": "151.0.7922.34",
  "A3_reported": true,
  "A4_reported": true,
  "S3_closeddetails_still_hidden": true,
  "S4_cvhidden_still_hidden": true,
  "S2_opendetails_still_shown": true,
  "quarterly_report_control": true
}
```

This is a **detector fix in `browser/`**, not a screen in `ui/app.py` — there is no page to click
through, and the "interaction" this instrument performs is the measurement itself (six of them,
listed in `report.json`'s `interactions` array, each with `did`/`expected`/`observed`/`pass`).
This satisfies D-024's live-browser requirement for what this unit actually produced: a change to
what a real browser's paint says the page is, verified against a real, uncontrolled paint of it.

## What this unit does NOT do

- It does not touch `HIDES_ON` itself, or the non-`DETAILS` branch of `contentsRenders` (the
  `s.display === "contents"` / `box.checkVisibility()` / final `return` lines) — diff-confirmed
  single-hunk.
- It does not re-open or re-score AT-438/AT-442/AT-449/AT-450 (D-049 already re-ruled those under
  the pre-unit baseline; this unit's baseline is `72513124`, master's tip when this unit started,
  which already carries that re-ruling).
- It does not touch AT-454 (closed shadow root, `assignedSlot` null) — D-049 accepted that into
  U14(c) as a documented limitation, explicitly separate from AT-453.
- It does not touch any `ui/` route, template, or navigation path.

## Gaps stated, not hidden

- **T-186's own `done_check` (`uv run pytest tests/ -k details`) does not exercise this fix.**
  It collects exactly one, unrelated, pre-existing test (see "Confirmed: these three are the only
  full-suite failures" above). I did not rewrite it — `.goal/goal.json` is outside this manifest's
  "What changed" and fixing five tasks' `done_check`s plus a hardcoded count assertion is its own
  unit — but a checker relying on the registered `done_check` alone, rather than on this
  manifest's own verify commands, would be validating the wrong thing. Filed to
  `qa/feedback-inbox.md`.
- **No mutation-testing harness (`scripts/mutation_check.py`) was run for this unit.** The prior
  `at438-display-contents` unit built a `mutations.json` with 9 rows; I relied instead on this
  manifest's own single-hunk falsifying edit in a throwaway copy (same isolation property,
  narrower scope: one edit, not nine). A checker wanting the broader net can re-run
  `at438-display-contents`'s existing mutation suite unchanged — this unit's edit lives inside
  the same function that suite's 9 mutations already probe, and none of them target the line this
  unit changed (`fixdir3.py`'s own candidate-vs-NEW diff already proved the two are compatible in
  the checker's original measurement).
- **The `HIDES_ON` regex itself is unchanged and untested by this unit** — I inherited it as-is.
  If it is ever widened (AT-440, filed and separate), that widening would also change what this
  unit's `display:contents`/`display:inline` conjunct accepts on the pseudo, and is out of scope
  here.

## Status: ready-for-check
