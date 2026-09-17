```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (C10/C7), 4/4 mutations killed
FAILURES (if any):
- none at >80% confidence against this unit's own criteria/capabilities
CAPABILITY-COVERAGE: 4/4 rows reproduced (mutation_check.py, single-hunk edits to
src/autotester/doctor.py, kill-attribution confirmed row-for-row against tests/test_doctor.py)
LIVE-BROWSER: not-applicable (changed paths: src/autotester/doctor.py, tests/test_doctor.py,
qa/manifests/at504-prose-about-the-marker-is-not-a-claim.md,
qa/evidence/at504-prose-about-the-marker-is-not-a-claim/*)
ISSUES-WRITTEN: AT-504 (closed fixed)
EXPLANATION: All manifest claims independently reproduced. `uv run pytest -q -o addopts=
tests/test_doctor.py` -> 30 passed; `uv run ruff check src tests scripts` -> All checks passed;
`uv run autotester doctor` -> doctor: clean; `mutation_check.py` -> 4/4 KILLED with each row's
actual failing test set matching the claimed `kills:` exactly, including the backtick mutation
isolated by exactly one test (`test_a_line_opening_with_the_marker_in_backticks_is_not_a_claim`)
as claimed; `probe_after.py` -> 2 violations with AT-298b's row dropped, 0 intact, restoring the
number AT-500 originally measured. Whole suite `uv run pytest -q` redirected to a file (never
tailed) -> exit 0, `[100%]` reached, zero FAILED/ERROR/`^E ` lines in the full log -- no AT-505-
style flake this run. Diff (`git show 6f97f45 --name-only`) touches only the files the manifest's
"What changed" names; no unrelated deletion.

Re-derived the over-tightening numbers myself rather than trusting the pasted ones: computed
`named` as a per-file set (matching the shipped code's own construction) under the old
substring test, the shipped `_is_marker_line`, and the naive bare `lstrip().startswith(marker)`
across every qa/manifests + qa/verdicts file. Got: shipped-vs-naive = +12 (exactly the claimed
"12 real claims" a naive tightening would have dropped), old-vs-shipped = -3 (exactly the
claimed "exactly 3 dropped"), shipped-vs-old gained = 0 (confirms the strict-subset claim: the
new predicate cannot invent a claim). My absolute total (629) sits 2 above the manifest's stated
627 -- explained by this being a live, two-loop-shared tree (the manifest's own framing) where a
couple of qa/ files landed between the maker's measurement and mine; the three structural deltas
that matter (+12, -3, 0 gained) reproduced exactly, so this is not a finding.

Verified the disclosed over-tightening evidence against the real files: at097-session-start-hook-
regression.md:259 has `**ISSUES-WRITTEN:** AT-106, AT-107`, at176-at178-render-not-scan.md:279 has
`**ISSUES-WRITTEN:** AT-192...`, at206-guards-that-guard.md:202/398 have `## ISSUES-WRITTEN: ...`
-- all three decorated forms the manifest cites are real, live claim lines, so the guard against
over-tightening is grounded in actual data, not a hypothetical.

Checked the manifest's own disclosed blind spot (a list item merely discussing the marker, e.g.
"- ISSUES-WRITTEN lines are read by the guard...") -- grepped qa/manifests and qa/verdicts for
that shape: no such line exists anywhere in the tree today, confirming the disclosure is honest
(a known, currently-inert gap) rather than a live defect being waved past.

Attacked the marker.strip("*") asymmetry named in the brief: confirmed `_MARKER_LEAD.sub` already
strips a line's own leading `**`, so for the manifest marker ("**Issues addressed:**") comparing
against `marker.strip("*")` ("Issues addressed:") is necessary -- comparing against the full
`**`-wrapped marker after the line's own `**` was just stripped can never match, which is exactly
mutation 3's kill mechanism (confirmed both of its claimed kills are manifest-marker tests). For
the verdict marker ("ISSUES-WRITTEN"), `.strip("*")` is a true no-op since the marker itself has no
asterisks; a verdict line's OWN decoration (`**ISSUES-WRITTEN:**`) is handled entirely by
`_MARKER_LEAD`, a separate mechanism. The two strips solve different problems (marker's own
literal wrapper vs. surrounding line decoration), so the asymmetry is sound and does not hide a
verdict-side gap.

Structural erosion (signal only, not a blocker): `src/autotester/doctor.py` is 287 lines against
C2's 300 cap. `git log --follow` confirms three consecutive units (385fec1 AT-496, 17d0d58 AT-500,
6f97f45 AT-504) have each added to this file. The manifest names this and defers the split rather
than doing it mid-cycle, which is the right call for a single-purpose bugfix unit; the next unit
touching this file should treat the split as its first question, per the manifest's own note.

Not UI-touching: changed paths are src/autotester/doctor.py, tests/test_doctor.py, the manifest,
and the evidence directory only -- correctly disclosed, no Mode D needed.
```
