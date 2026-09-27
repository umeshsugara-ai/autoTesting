# Verdict — t191-run-video

**Date:** 2026-09-27
**Cycle checked:** 1
**Unit:** t191-run-video (T-191, AT-587)
**Bound root:** D:/autoTesting, worktree `.claude/worktrees/agent-a8d7c6e7cb6f8905a`,
branch `wave/t191-run-video`, judged against `eac530a2` (unit commit; `b0b760ab` merge of
master on top is bring-up only, not judged).
**Checker:** fresh Claude Opus 5 subagent, Anthropic session (no `ANTHROPIC_BASE_URL` override;
executor independence holds — checker != executor, which was `/maker build subagent, Claude
Opus 5`).

## VERDICT: FAIL

## Scoreboard

7/8 criteria met on their own terms (V1–V8, minus the one this FAIL is about);
0/1 invariants hold that matters here (C7's "a wrong answer must not be worse than the bug
it fixes" — this unit's fix for the stray-video bug introduces a worse one).

**The unit is FAILed on a single, independently reproduced defect: `_sweep_orphan_videos`
(session.py, new in this unit) can delete a legitimate, already-finished sibling case's video
in a real parallel run — silent evidence loss, in exactly the feature this unit exists to
build.** This is not a criterion V1–V8 states in words (none of them anticipate concurrent
siblings sharing a scratch directory), but it is squarely within core-invariants C7's guard —
"a wrong answer here deletes evidence, which is worse than the bug it fixes" — and it is squarely
new code this unit shipped, wired into real production paths (`ui/routes_runs.py`
`video_enabled=True`, `ui/run_execution.py` `record_video=True` on the parallel route).

## The four attack points, in the order given

### 1. The dead download-link gap — ruling: would be PASS-with-issue on its own, not a FAIL

Independently confirmed the maker's claim and went further. `stages/report_export.py::
_video_link_html` (`report_export.py:216-229`) is the only place `EvidenceKind.VIDEO` is ever
rendered as a link, reachable only through `export_html`, which has exactly two callers in
`src/`:

- `ui/routes_report.py::download_report_html` (`routes_report.py:279-287`) — confirmed dead on
  arrival for every real download. It writes the export via `_reserved_temp_path(".html")`
  (`ui/helpers.py:170`, an OS temp dir, **not** `run_dir` — confirmed by reading the function:
  `directory=None` at this call site), serves it as a browser download via `FileResponse`, and
  deletes the server-side temp copy immediately via `BackgroundTask(out.unlink, missing_ok=True)`.
  The href in the downloaded HTML is a bare run-relative path (`v.path`, e.g. `case_x.webm`,
  confirmed at `report_export.py:229`) — it resolves relative to wherever the downloaded file
  lands (the user's Downloads folder), where the video never exists, deterministically, every
  time.
- `cli.py::report_html` — works only if the operator manually sets `--out` to a path literally
  inside the run directory; undocumented, untested, not how `--out` is normally used.

**New finding beyond the manifest's own disclosure:** the live web UI's own per-run page,
`ui/routes_report.py::run_view` (`/projects/{slug}/runs/{run_id}`), **never surfaces
`EvidenceKind.VIDEO` at all** — `_step_flow` (`routes_report.py:64-93`) filters strictly on
`EvidenceKind.SCREENSHOT`. Grepped every route module in `src/autotester/ui/`: no route other
than the two `export_html` callers above ever reads a `VIDEO` evidence item. So today there is
no verified, working path — live UI or download — by which a human using the product as shipped
ever reaches a working video link.

**Ruling:** V1–V8 as literally written are satisfied — V8 asks only for the link *shape*
(run-relative href, never embedded), and RE3's D-050 exception text already names the precondition
("needs its file to sit beside the run") as accepted, not promised. This is a real product gap
that undercuts the goal task's own stated purpose ("a 15-20 minute walkthrough a human can
watch"), but the fix is a design decision in files this unit never touched
(`routes_report.py`/`cli.py`) and explicitly out of scope per the contract's own plan-decision 7.
**Filed as `ISS-t191-run-video-2` (severity high), not charged against this unit's PASS/FAIL.**
Do not let this be the reason the unit fails — it isn't; the reason is point 2 below.

### 2. `_sweep_orphan_videos` — re-derived independently, and the maker's safety reasoning is wrong under concurrency

Read `session.py::close()`/`_sweep_orphan_videos()` and `video.py::begin_case_video`/
`end_case_video` directly. The maker's premise — "every legitimate case video is already moved
OUT of `_video_scratch` by the time `close()` runs, so anything still there belongs to no
case" — is correct **only for one session's own sequential cases**. It is false the moment a
second session shares the same `run_dir`, which is exactly what
`stages/parallel_run.py::default_session_factory` does for every parallel-run sibling (confirmed:
`paths = ProjectPaths(f"{project.slug}-parallel-{case.id[:12]}")` differs per sibling, but
`run_dir` passed to `BrowserSession(...)` is the **same** object for every sibling — see
AT-572's own comment at `parallel_run.py:245-259`). Since `video_dir = run_dir / VIDEO_DIR_NAME`
is derived only from `run_dir`, every sibling records into the **same physical
`_video_scratch` directory**, and `BrowserSession.close()` runs
`shutil.rmtree(run_dir / VIDEO_DIR_NAME, ignore_errors=True)` unconditionally the instant *any*
sibling finishes its own case — with zero awareness of siblings still recording into that shared
directory.

`VideoMixin.end_case_video()` finalizes a case in three separate, non-atomic statements:
`page.close()` (which is what makes Playwright actually flush the finished `.webm` into
`_video_scratch`) → `Path(video.path())` → `temp_path.replace(final_path)`. Between the first
and third of those, the file is a completed, ordinary, unlocked file sitting in the shared
scratch dir — exactly the state a sibling's concurrent `rmtree` can catch.

**Reproduced live, not just reasoned about.** Built a script
(`repro_sweep_race.py`, scratch, not committed) using two real `BrowserSession` instances against
real headless Chromium, each run in its own `threading.Thread` — mirroring
`stages/parallel_run.py::run_cases`'s actual `ThreadPoolExecutor` model exactly — sharing one
`run_dir`. Thread B finalizes its page (real recording, confirmed present on disk in the shared
`_video_scratch`) and blocks on a `threading.Event` at the precise point `end_case_video()` would
next call `.replace()`. Thread A finishes its own case normally (own video renamed out cleanly),
then calls `session_a.close()`. Output:

```
[B] finished recording existed right after B's page.close(): True
[A] end_case_video returned: case_a.webm
[sweep] scratch dir exists after A.close(): False
[B] B's own temp file still present when B resumed (post-sweep): False
[B] B was able to rename its finished video to safety after the sweep: False
RESULT: RACE CONFIRMED -- sibling A's close()/_sweep_orphan_videos() deleted B's
already-finished, not-yet-renamed video before B could move it to safety.
```

**This is not a contrived, one-in-a-million window.** `stages/parallel_run.py::
plan_parallel_run` computes `ram_slots = (measured_free_mb - 2048) // (512 + 128)`; on this very
machine's own measured free RAM (~3.5 GB, per this dispatch's machine note), that already
evaluates to **2** — i.e. `plan.n = 2`, which routes execution through `_run_cases_in_parallel`
(the vulnerable path), is the *default* planned concurrency on a moderately-loaded box, not an
edge case requiring a heavily loaded one.

**Consequence:** a FAIL or INCONCLUSIVE case's video — the entire evidentiary point of this
unit — can be silently destroyed because an unrelated sibling case in the same parallel run
happened to finish first. `end_case_video()` swallows this as an ordinary "no video" (`None`),
so nothing errors, nothing logs, and `_finalize_video` never even sees a `video_rel` to decide
about. **This is a wrong answer that is worse than the stray-video bug it replaced** — the stray
bug left an extra untracked file; this bug deletes real evidence a human was supposed to review.

**Ruling: FAIL.** Filed as `ISS-t191-run-video-1`, severity **critical**. Remedy options named in
the issue: a per-session-unique scratch subdirectory, a sweep that only removes files it can
positively attribute to its own session, or an atomic finalize sequence.

### 3. V1–V8 falsification table — fully re-derived independently

Confirmed the worktree was clean (`git status --porcelain`, no output) before starting, extracted
a throwaway copy via `git archive HEAD | tar -x -C <scratch>` (no `.git` in the archive, so
reverts were done via pristine file backups taken before each edit rather than `git checkout`),
ran `uv sync --frozen`, confirmed `uv run pytest tests/ -k video` green in the copy first
(76 passed), then applied each single-hunk falsifying edit from the manifest exactly as written,
one at a time, reverting before the next:

| V | edit applied | result |
|---|---|---|
| V1 | `video.py`: fresh-page swap → `self._page or self._context.new_page()` | FAIL (PASS case's video not pruned) — confirmed |
| V2 | `run_case_pipeline.py`: prune condition → `if False and (...)` | FAIL (PASS case's video kept) — confirmed |
| V3/V4 | `video.py`: `add_init_script` → `add_style_tag` | FAIL, all 3 masking-live tests (different exact failure mode than the manifest's — a `TargetClosedError` rather than an assertion mismatch — but the check unambiguously reddens) — confirmed |
| V5 | `video_retention.py`: `sorted(..., key=_ordering_key)` → `..., reverse=True` | FAIL, both ordering tests — confirmed (this is also the "independent falsification of retention ordering" the dispatch asked to be re-run) |
| V6a | `parallel_run.py`: dropped the `+ VIDEO_OVERHEAD_MB` term | FAIL, `assert 5 < 5` exactly as the manifest reported — confirmed |
| V6b | `run_case_pipeline.py`: `over_budget = result.duration_s > MAX_VIDEO_DURATION_S` → `over_budget = False` | FAIL, video not deleted — confirmed |
| V7 | `session.py`: added a second `options["record_video_dir"] =` inside `start()` | FAIL, `['launch.py', 'session.py'] == ['launch.py']` — confirmed exactly | 
| V8 | `report_export.py`: `<a href>` → `<video controls src='data:...;base64,SABOTAGE'>` | FAIL, href assertion — confirmed |

All 8 rows are genuine, reproducible falsifications; no vacuous pass observed. Every file was
restored to its pristine backed-up state after each row (verified with `diff -q` against the
pre-edit backup for all six touched files), and the bound worktree's `git status --porcelain`
was re-confirmed clean throughout and after — never touched by any of this.

### 4. Masking guarantee — verified in real Chromium, and `screenshot()` does NOT share the fragility

Re-ran `tests/test_video_masking_live.py` myself (not the maker's pasted output) against real
headless Chromium: 3/3 passed, confirming all three legs (computed-style sampling across the
hold, byte-absence in the `.webm`, and the ffmpeg `ssim` frame-diff) independently.

**On the disclosed deviation from "reuse the screenshot masking path":** read
`browser/evidence.py::screenshot()` directly. It calls `self.page.add_style_tag(content=MASK_CSS)`
**immediately before** each `self.page.screenshot(...)` call — synchronously, back-to-back, on
whatever document is current *at that instant*. It never has to survive a navigation, because it
is never asked to: it re-applies fresh before every discrete capture, unlike video's single
continuous recording spanning many navigations. **`screenshot()` does not share the
navigation-fragility weakness** — the two mechanisms solve genuinely different problems
(point-in-time vs. continuous), and `add_init_script`/`MutationObserver` for video is the correct,
justified divergence, not corner-cutting. No new finding here.

**On the MutationObserver timing gap the manifest discloses (proven only against
`login_site`'s plain HTML, never a slow-hydrating SPA):** accepted as a disclosed, reasoned gap
rather than a blocking finding — the retry has no timeout and cannot silently succeed halfway
(it either installs the style tag or keeps retrying forever via the observer), so the failure
mode of an untested slow-hydrating page is "the mask takes longer to attach," not "the mask
silently never attaches and nobody notices." Worth a future test against a real SPA fixture, not
worth blocking this cycle over, and moot regardless given the FAIL above.

## Capability coverage

8/8 rows independently reproduced by the checker (table above). No `UNVERIFIED` rows.

## Live browser

Real Chromium was driven directly by the checker for: `tests/test_video_masking_live.py` (3/3,
via pytest), the full `tests/ -k video` re-run (76/76, via pytest), and the sibling-sweep race
reproduction (`repro_sweep_race.py`, scratch, two real `BrowserSession`s + real Chromium + real
threads, not committed). **Not done this cycle:** a live walkthrough of the actual FastAPI web UI
(the report/run pages, the Download button) to visually confirm finding #1 (`ISS-t191-run-video-2`)
end-to-end — that finding is already conclusively established by direct route-code inspection
(`_reserved_temp_path`'s `directory=None`, `BackgroundTask(out.unlink)`, `run_view`'s
`_step_flow` filtering strictly on `SCREENSHOT`), and since the unit already FAILs on an
unrelated, independently-reproduced defect, spending the time on a full UI walkthrough would not
change this cycle's outcome. Recommend doing that walkthrough on the cycle that actually attempts
a PASS.

## Pre-existing failures

Independently re-ran `uv run pytest tests/ -k video` (76 passed), `uv run ruff check src tests
scripts` (all checks passed), `uv run autotester doctor` (clean) myself — all green, matching the
manifest. The full `uv run pytest` re-run was kicked off by the checker directly (not the
maker's pasted output) and is still completing at time of writing due to real-Chromium-heavy
tests on a memory-constrained, multi-agent-shared box; its output will be attached to this
verdict's evidence trail once complete. This does not block the FAIL ruling above, which rests
on the sweep-race finding alone, independently and completely reproduced.

## Credential boundary

Confirmed fake secrets only (`fixture-user-9137`, `fixture-pass` — grepped both test files
directly). Confirmed via `git show --stat eac530a2` that no `.webm` file and nothing under
`.work/` is part of the commit.

## Executor independence

EXECUTOR: /maker build subagent (Claude Opus 5) (checker: claude-opus-subagent, this session,
no `ANTHROPIC_BASE_URL` override).

## Issues written

- `ISS-t191-run-video-1` (critical) — the sweep-race evidence-loss defect. This is why the unit
  FAILs.
- `ISS-t191-run-video-2` (high) — the video link is unreachable through any shipped path (broader
  than the manifest's own download-route-only disclosure). Not chargeable against this unit;
  follow-on work.

## What the maker should do next cycle

Fix `ISS-t191-run-video-1` (a per-session scratch subdirectory is the simplest correct shape:
`run_dir / VIDEO_DIR_NAME / <a value unique to this session>`, so no sibling's sweep can ever
touch a directory another session is using — `_sweep_orphan_videos` then only ever needs to
delete its OWN session's subdirectory, which is unambiguously safe regardless of what siblings
are doing). Add a regression test that actually exercises TWO concurrent sessions sharing a
`run_dir` with `record_video=True` (the gap this cycle's own test suite left completely
uncovered — none of `test_parallel_run.py`/`test_ui_runs_parallel_crash_recovery.py`/
`test_ui_runs_parallel_trace.py` were extended to test video-plus-concurrency together). Leave
`ISS-t191-run-video-2` for a separate HUMAN_GATE/follow-on unit as scoped in that issue.
