# Verdict — t191-video-reachable

**Date:** 2026-09-28
**Cycle checked:** 1
**Unit:** t191-video-reachable (ISS-t191-run-video-2, part of T-191)
**Bound root:** D:/autoTesting, worktree `.claude/worktrees/agent-a2368e46e4392412e`,
branch `wave/t191-video-reachable`, judged against the branch tip at the time of check
(7 commits off `master` `12597de3`, unmerged/unpushed).
**Checker:** fresh subagent, read-only toward the artifact; executor independence holds
(checker != the maker/build agent that wrote this unit).

## VERDICT: FAIL

## SCOREBOARD

- Capability table: 15/16 rows independently verified as claimed (C1, C2, C4, C5, C6 (as
  fixed), C7–C16 all reproduced or held under attack beyond what the manifest itself tried).
  **C3 does not hold**: the negative-case test for "no video link when there is no video
  evidence" is vacuous — it cannot redden against the exact falsifying edit the manifest
  itself names.
- `run-video.md` V1–V8: 8/8 met on their own terms.
- `ui-report.md` UR1–UR6: 6/6 met (video link renders via `_video_section`, links not embeds
  per D-050, no other report regressions).
- `report-export.md` RE1–RE6: 6/6 met; `download_report_html`'s pre-existing broken video
  link is unchanged byte-for-byte, which is acceptable for *this* unit per the open,
  explicitly non-blocking `qa/gates/t191-video-download-route.md` gate ("Blocks: nothing").
- `core-invariants.md` C1–C12: 11/12 hold. **C7 fails**: "a guard with no [enumerated,
  falsifying] row is an unenumerated claim. It fails the unit on its own, even when every
  test is green." C3's test is exactly such a row — present in the table, absent in fact.

**The unit is FAILed on one finding: a vacuous negative-case test (C3), independently
reproduced by the checker, that core-invariants.md C7 makes fatal on its own regardless of
every other criterion holding.** Everything else attacked — the UNC/ADS/percent-encoding/
drive-rooted/mid-path-traversal/corrupted-envelope path-safety shapes, the guard's ordering,
secrets masking, retention, and a live Mode D browser session — held up under independent,
harder attack than the manifest itself supplied.

## FAILURES

### C3 — vacuous test (primary, fatal)

`tests/test_ui_video_route.py::test_run_view_shows_no_video_link_when_there_is_no_video_evidence`
asserts `.webm" not in response.text` after seeding a run with
`store.save_result(RUN_ID, RawResult(case_id=case.id, outcome=Outcome.COMPLETED))` — no
`evidence=` kwarg. `schema/run.py`'s `RawResult.evidence` defaults to `Field(default_factory=list)`,
so the run under test carries **zero evidence of any kind**, not merely zero video evidence.
`ui/routes_report.py::_video_section` filters `evidence` for `EvidenceKind.VIDEO` and returns
`""` if none match — but with an empty `evidence` list, it returns `""` whether that filter
line exists, is inverted, or is deleted outright. The assertion is true independent of the
guarded behavior.

**Independently reproduced in a throwaway git-archive copy of this branch's HEAD** (never the
bound worktree): removed the `if e.kind is EvidenceKind.VIDEO` filter from `_video_section` —
the exact falsifying edit the manifest itself describes for this capability — and re-ran
`tests/test_ui_video_route.py`. All 6 tests, including this one, stayed **GREEN**. This is the
third vacuous test in this build (the manifest's own cycle already self-found and fixed two,
C5 and C6, before submitting for check) — the class core-invariants.md documents as recurring
at least 6 times in this project's history (AT-218 and its citations).

Filed as **AT-654** (high severity) in the worktree's `qa/issues.jsonl` — this is the FAIL
driver.

**Fix shape:** seed the fixture with a non-video `Evidence` row (e.g. `EvidenceKind.SCREENSHOT`)
alongside the no-video case, so the filter is actually exercised; confirm it reddens with the
filter removed and stays green with it restored.

### C15 — investigated, NOT a defect (checker's own initial suspicion retracted)

Dispatch flagged the drive-rooted-path guard (C15, `C:\Windows\System32\drivers\etc\hosts`)
as an "unverified shape" to attack. Initial throwaway experiments (removing the
`is_relative_to` containment check and the `.suffix != ".webm"` check, while accidentally
*not* having actually removed the leading-guard string check in that pass) produced a
misleading "still passes" result that looked like a second vacuous test. Redone cleanly: with
the string guard (`video_path[0] in "\\/" or ":" in video_path`) removed on top of the other
two already-removed checks — leaving only `is_file()` — the test correctly **reddens**
(`AssertionError: assert WindowsPath('C:/Windows/.../hosts') is None`), confirming
`Path("C:/Windows/...")` really does resolve to the real, readable hosts file when only
`is_file()` guards it. Restoring the string guard alone (the `:` check) makes the test pass
again. **This confirms the manifest's own claim — "C15 covered by the same guard as C14 (the
`:` check)" — is correct.** No issue filed; retracted rather than let a methodology slip
become a false finding.

## CAPABILITY-COVERAGE

16 rows in the manifest's capability table; 15 independently confirmed load-bearing via
falsification (throwaway-copy edit → RED, restore → GREEN, or a harder attack than the
manifest itself supplied); 1 (C3) confirmed vacuous. No capability claimed with zero
falsification evidence either way (no INCONCLUSIVE rows).

Attacks run beyond what the manifest itself tried, all refused safely with no leak and no
unhandled 500-shape crash: forward-slash UNC, NTFS ADS, empty/whitespace/tab-prefixed paths,
percent-encoding off-by-one in both directions, mixed literal+encoded traversal, mid-path
backslash traversal, and corrupted (not merely absent) run envelopes (invalid JSON, wrong
schema, mismatched id) via a real `TestClient`.

Verify commands re-run independently, matching the manifest exactly:
- `uv run ruff check src tests scripts` — All checks passed, exit 0.
- `uv run autotester doctor` — clean, exit 0.
- `uv run pytest` (no `-q`, AT-503) — `1 failed, 2086 passed, 6 skipped, 14 xfailed, 15
  warnings in 1597.47s (0:26:37)`, exit 1. The 1 failure is the pre-authorized `AT-627` flake
  (confirmed open/pre-authorized in `qa/issues.jsonl` before accepting it) — not a hidden
  regression, no duplicated-summary or exit-code-masking hazard present.

Diff scope confirmed exactly as manifest claims: `routes_video.py` (new), `routes_report.py`
(+16/-2, `_video_section` addition only), `app.py` (+2, router registration),
`test_ui_video_route.py` and `test_ui_video_route_traversal.py` (new). `report_export.py`
confirmed byte-for-byte unchanged (empty diff against base) — `download_report_html`'s
pre-existing broken video link is untouched, which is acceptable for this unit per the
explicit non-blocking gate. Independent measurement: `report_export.py` is 299 lines, not the
gate's stated "exactly 300, zero headroom" — a minor, non-blocking evidence inaccuracy, not
re-filed as a separate issue (folded into this note).

## LIVE-BROWSER (Mode D)

Mandatory and completed. Seeded a real scratch project/run/video fixture, launched a real
uvicorn server against the worktree's own unmutated code, drove a real Playwright browser
session:
- Run page renders the video link (`🎥 video (...)`) exactly as `_video_section` emits it.
- Clicking it serves real bytes: `200` on the initial request, `206 Partial Content` on the
  follow-up range request (video-element seek behavior).
- Zero console errors on the video-touching page.
- Unknown-run 404 page: one pre-existing, unrelated console entry, not new to this unit.
- Report page: clean, no console errors.

This independently satisfies the mandatory Mode D requirement without relying on the maker's
own screenshots or `curl`.

## ISSUES-WRITTEN

Filed to the worktree's `qa/issues.jsonl` (`D:/autoTesting/.claude/worktrees/agent-a2368e46e4392412e/qa/issues.jsonl`):

- **AT-654** (high, `vacuous-test`) — the C3 finding above; primary FAIL driver.
- **AT-655** (low, `manifest-field-missing`) — the manifest omits the `Persona walk:` field
  SKILL.md 5bb expects for a UI-touching unit. Non-blocking, process hygiene only.

**Known id collision, documented not renumbered:** at dispatch time AT-654 was the checker's
next free id; by the time this verdict was written, the root ledger (`D:/autoTesting/qa/issues.jsonl`,
outside this worktree) had independently advanced to its own AT-654 (a different entry, the
D-029 dev-only-vs-production-Pathlynks gate — see `git log`: `3c9cb374`, `6cfefd83`). This
worktree's `qa/issues.jsonl` is a stale fork of master at `12597de3` with only local
`ISS-t191-run-video-*` rows appended, so its own highest id was AT-649, not AT-654 — the two
AT-654s live in different files and will need reconciliation at merge time, consistent with
this project's ten already-documented `id_collision` pairs. Not renumbered here per the
standing instruction.

## EXECUTOR

Checker's own subagent identity: fresh session, no prior context with this unit's build,
structurally read-only toward the bound worktree (all mutation happened in a throwaway
git-archive copy under `%TEMP%`, deleted after use, never the bound tree). No merge performed
— that is the orchestrator's job on a PASS, and this cycle is a FAIL.

## EXPLANATION

This build is strong: the security guard (`_safe_video_path`) is genuinely well-ordered
defense-in-depth, independently confirmed against a wider attack surface than the manifest
itself tried, including a class of attack (corrupted run envelopes) the manifest didn't
address at all. The live Mode D session confirms the feature actually works end-to-end for a
real user. The scope is narrow and clean — nothing touched outside the declared file list,
nothing deleted, the one pre-existing defect this unit chose not to fix (the download-route's
broken link) is explicitly gated as non-blocking by its own decision file.

The unit still fails, because `core-invariants.md` C7 is written exactly to catch this
situation: a capability table can read 16/16 green and still ship an unverified claim if one
of those sixteen rows is defended by a test that would pass no matter what the code does. That
is what C3 is. This is not a nitpick or a process formality — it is the specific failure mode
this project has been burned by repeatedly (AT-218's six prior citations), and the fix is a
one-line fixture change (add a non-video `Evidence` row), not a redesign. Cycle 2 should be a
fast turnaround.

The C15 sub-investigation is included above in full, including the checker's own initial
methodology slip and its correction, in the interest of not asserting a finding the checker
could not stand behind under its own re-check — the manifest's claim on C15 holds.
