# Verdict — t186-details-content

**Cycle checked:** 1
**Date:** 2026-09-27
**Checker:** claude-sonnet-subagent (fresh context, read-only toward the artifact)
**Bound root:** `D:/autoTesting`, worktree `D:/autoTesting/.claude/worktrees/agent-a5a815f4c0d62fe8b`,
branch `wave/t186-details-content`, unit commit `031d1e92` + clean merge `cec54dbe` of master
(bring-up only, confirmed by `git diff 031d1e92..cec54dbe --stat`: only other units' `qa/` artifacts,
zero touch on this unit's files).

## VERDICT: PASS

## Attack 1 — byte-level comparison of the applied expression against the validated candidate

Extracted the live line from `src/autotester/browser/visual_order.js:77`:

```
(p => p.contentVisibility === "hidden" && HIDES_ON.test(p.display))(window.getComputedStyle(box, "::details-content"))) return false;
```

Compared programmatically (Python string equality, not eyeball) against `fixdir3.py`'s `NEWL`
constant (`qa/evidence/browser-at438-display-contents-2026-09-16-checker-c3/fixdir3.py:8`):

```
NEWL = '(p => p.contentVisibility === "hidden" && HIDES_ON.test(p.display))(window.getComputedStyle(box, "::details-content"))) return false;'
```

**Result: `line == NEWL` → `True`.** They are byte-identical, not merely semantically equivalent.
The manifest's own description ("reformatted to fit house style with a leading arrow function") is,
if anything, an understatement — `fixdir3.py`'s own validated candidate was *already* the IIFE form
`(p => ...)(...)`; there was no reformatting at all, just a verbatim copy. No divergence risk: the
short-circuit order (`contentVisibility === "hidden" && HIDES_ON.test(p.display)`) and truthiness are
identical to what the prior checker validated against 26 details-shaped pages (`CAND wrong: []`).

## Attack 2 — false-positive check (does the stricter gate still hide what should stay hidden)

Ran `uv run pytest tests/test_browser_scroll_invariance.py tests/test_browser_visual_order.py -v`
myself (U14's own Verify line): **68 passed, 14 xfailed** — includes the non-regression assertions
`CONTENTS_CLOSEDDETAILS_S3`, `CONTENTS_CVHIDDEN_S4`, `CONTENTS_DETAILSCONTENTS_S12` (a `<details
style="display:contents">` with no author override on the pseudo — genuinely closed, no HIDES_ON
match) all still `not in seen`, and the accordion (`CONTENTS_ACCORDION_S10`, content-visibility
override) still `in seen`.

Confirmed live in my **own** headed Chromium run (below) — `S3_closeddetails_still_hidden: true`,
`S4_cvhidden_still_hidden: true`, `S12_detailscontents_still_hidden: true`, `S2_opendetails_still_shown:
true`. Diff-confirmed the fix touches only the `DETAILS` branch's added conjunct — `HIDES_ON` itself
(the allow-list regex) and the non-`DETAILS` branch (`s.display === "contents"` / `checkVisibility()`
/ final return) are byte-unchanged. No new false positive found.

## Attack 3 — independent falsification, my own throwaway copy

The worktree was already clean (unit committed, `git status --porcelain` empty), so `git stash
create` produces nothing to archive — used `git archive --format=tar HEAD` instead (same "throwaway
copy outside the bound worktree" property; HEAD **is** the post-unit state since the tree is clean).
Extracted to a scratch dir, `uv run pytest` built its own venv there in 4.4s (80 packages).

```
# GREEN before (my own copy, fix intact)
tests\test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor .
1 passed in 6.94s

# single-hunk revert applied to the COPY ONLY (programmatic string replace, exact same hunk
# the manifest names):
#   -  (p => p.contentVisibility === "hidden" && HIDES_ON.test(p.display))(window.getComputedStyle(box, "::details-content"))) return false;
#   +  window.getComputedStyle(box, "::details-content").contentVisibility === "hidden") return false;

# RED after
FAILED tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor
AssertionError: ('CONTENTS_DETAILSCONTENT_CONTENTS_A3', 'Quarterly report for the trainers list...firstdca3a4')
1 failed in 2.06s
```

Identical failure (same node id, same sentinel `CONTENTS_DETAILSCONTENT_CONTENTS_A3` firing first,
same error shape) to the manifest's own report — reproduced independently, not taken on trust.
Confirmed the bound worktree was never touched (`git status --porcelain` empty before and after);
the throwaway copy was deleted afterward. This is a real revert-and-reassert, not a stub — the test
asserts specific sentinel strings appear/don't appear in real rendered output, so a `return True`
stub on the detector function would fail import/collection long before reaching this assertion, and
in any case no function was stubbed — the actual conjunct was removed and the actual browser re-ran.

## Attack 4 — my own live-browser run, shipping path

Wrote my own probe (`qa/evidence/browser-t186-details-content-2026-09-27-checker/probe.py`),
launched real **headed** Chromium (confirmed same build `151.0.7922.34` as the maker's report),
navigated directly to `tests/fixtures/bidi_site/cvcontents.html` via `file://`, and called the
**shipping** `autotester.browser.observe.visual_text(page)` — not a hand-copied JS string. Own
result, saved to `qa/evidence/browser-t186-details-content-2026-09-27-checker/report.json`:

```json
{
  "chromium": "151.0.7922.34",
  "A3_reported": true,
  "A4_reported": true,
  "S3_closeddetails_still_hidden": true,
  "S4_cvhidden_still_hidden": true,
  "S2_opendetails_still_shown": true,
  "S12_detailscontents_still_hidden": true,
  "quarterly_report_control": true
}
```

Matches the maker's own report field-for-field (plus one extra sentinel I added, S12, which also
holds). This is a backend detector fix with no `ui/` route — the "interaction" is the measurement
itself, same as the maker's framing, and I ran it myself rather than reading their JSON.

## Attack 5 — persona-walk skip

Manifest: `skip (backend-only: … src/autotester/browser/visual_order.js; no screen, navigation
path, or user-facing flow in ui/app.py touched)`. Tested against the actual changed paths
(`git diff 031d1e92^..031d1e92 --stat`): `src/autotester/browser/visual_order.js`,
`tests/fixtures/bidi_site/cvcontents.html`, `tests/test_browser_visual_order.py`, plus
evidence/manifest/feedback-inbox additions. None is under `ui/`, `pages/`, or `components/` — this
is `autotester`'s own browser-side text-detector engine, consumed by `ui/app.py` but not itself a
screen. **Ruling: the skip is justified, not a rationalization.** No `false-persona-skip` finding.

## `done_check` acceptance ruling

T-186's registered `done_check` (`uv run pytest tests/ -k details`) collects exactly **one**
unrelated, pre-existing test (`test_browser_unreadable.py::…[closed-details]`) and does not touch
this unit's actual new assertions (whose test name contains no literal "details" substring match
issue aside — confirmed independently: `uv run pytest tests/ -k details --collect-only` — 1
collected). **This done_check is not sufficient acceptance for T-186 and is not what this PASS
relies on.** This PASS is grounded in the manifest's own cited commands (`pytest
tests/test_browser_visual_order.py`, the combined U14 verify line, `ruff`, `doctor`, full `pytest`),
all of which I re-ran myself above. **T-186 should be re-registered with a node-id-scoped
`done_check`** (e.g. `uv run pytest
tests/test_browser_visual_order.py::test_display_contents_text_is_seen_but_never_through_a_hiding_ancestor`)
— but that rewrite is correctly **not** done inside this 2-cycle-capped unit. `ISS-at638-remainder-2`
(already filed, already named T-186 explicitly, already queued at `qa/QUEUE.md:843` as
`iss-at638-2-done-check-repair`, blocked on the in-flight wave) is the right home for it. No new
issue filed here — filing a second one would duplicate an already-queued, already-scoped fix.

## Diff scope (step 4c)

`git diff 031d1e92^..031d1e92 --stat`: 8 files, all either the three named "What changed" files, or
expected artifacts (manifest, feedback-inbox entry, evidence dir). No deletion of any existing
function, class, export, route, test, or config key. No file touched outside the manifest's claim.

## Contract / decision cross-check

Read `qa/contracts/ui.md` U14(b)/(c) in full, and `docs/DECISIONS.md` D-048 (gate
`at438-u14b-baseline`, answered `a+b+c`) and D-049 (the amendment applying it) in full. Confirmed:
pre-change baseline = master `72513124` (unit's branch point, not an earlier cycle of this unit —
moot here since this is cycle 1); AT-453 explicitly named as **not** added to U14(c), staying
charged and capped at 2 cycles (option b); `qa/gates/at438-u14b-baseline.md` carries the
`Answered:` line matching D-048's text. Everything the manifest claims about its own authority is
verified against the actual contract/decision text, not taken on the manifest's word.

## Capability coverage

4/4 rows reproduced. Rows 1-2 (A3/A4) reproduced independently in my own throwaway copy (Attack 3).
Row 3 (non-regression, ordinary closed details) re-verified in the bound tree's own test run and my
own live probe. Row 4 (accordion/content-visibility:hidden unaffected) diff-confirmed (`HIDES_ON`
and the non-DETAILS branch byte-unchanged) and live-probed.

## SCOREBOARD

4/4 capability rows evidenced. U14(a) (scroll-invariance) unaffected by this diff, re-verified
passing. U14(b) (no new false negative) satisfied — A3/A4 now reported. U14(c) (does-not-see list)
correctly left unchanged — AT-453 was never on it and stays off it. No new false positive found.

## FAILURES

None at >80% confidence.

## Full-suite verification (my own run, exit code captured directly, no pipe)

```
$ uv run pytest > checker-full-pytest.txt 2>&1; echo EXITCODE:$? >> checker-full-pytest.txt
3 failed, 2033 passed, 6 skipped, 14 xfailed, 15 warnings in 882.99s (0:14:42)
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
EXITCODE:1
```

Exactly the three failures the manifest named (AT-627, load-sensitive, pre-existing; two
`test_goal_done_checks.py` failures the maker itself found and correctly filed to
`qa/feedback-inbox.md` rather than fixing — orchestrator-traced to commit `f9e7d406`, already
tracked as `ISS-at638-remainder-2`). **No fourth failure.** None of the three touches this unit's
diff. `uv run ruff check src tests scripts` → `All checks passed!` (my own run). `uv run autotester
doctor` → `doctor: clean` (my own run).

## CAPABILITY-COVERAGE: 4/4 rows reproduced
## LIVE-BROWSER: qa/evidence/browser-t186-details-content-2026-09-27-checker/report.json
## ISSUES-WRITTEN: none (AT-453 moved open → verified in this verdict; ISS-at638-remainder-2 already covers the done_check defect, not duplicated)
## EXECUTOR: claude-sonnet-subagent (manifest's Executor) (checker: claude-sonnet-subagent, self != executor)
## EXPLANATION

The applied expression is byte-identical to the checker-validated `fixdir3.py` candidate — no
reformat risk. Independent falsification (my own throwaway copy, `git archive HEAD`) reproduces the
exact reported GREEN/RED pair. My own headed-Chromium run through the shipping `visual_text()`
matches the maker's report and adds one extra non-regression sentinel (S12), also holding. No new
false positive. The persona-walk skip is justified against the actual diff. T-186's registered
`done_check` is confirmed insufficient and is correctly not relied on for this PASS; its repair is
already filed and queued (`ISS-at638-remainder-2`) and is out of scope for this capped unit. Full
suite reproduces exactly 3 pre-existing, unrelated failures with no fourth.
