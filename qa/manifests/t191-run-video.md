# Manifest — t191-run-video

**Executor:** /maker build subagent (Claude Opus 5), worktree `agent-a8d7c6e7cb6f8905a`, branch
`wave/t191-run-video` off `origin/master` HEAD `72513124`.
**Unit:** Run video on FAIL/inconclusive only, keep last 20, secrets masked in video exactly as in
screenshots (AT-587).
**Contract:** `qa/contracts/run-video.md` V1-V8 (init, 2026-09-26, D-050) + `qa/contracts/report-export.md`
RE3's named video-link exception (also D-050).
**Authority trail:** gate `qa/gates/meeting-run-video-scope.md` — Answered 2026-09-26T22:34:22+05:30,
Umesh via AskUserQuestion in the checker session: **A, retention 20** ("Record run video only on FAIL
or inconclusive; keep the most recent 20; secret inputs masked in video exactly as in screenshots").
Recorded in `docs/DECISIONS.md` **D-048** ("meeting-run-video-scope = A. Record video on FAIL or
inconclusive only, keep the last 20, and mask secrets as in screenshots") and **D-050** (authorizes
`qa/contracts/run-video.md` itself + the RE3 amendment).
**Goal task:** T-191
**Date:** 2026-09-27
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-587

## What changed

- `src/autotester/browser/launch.py:20-68` — `RECORD_VIDEO_SIZE = {"width": 640, "height": 400}`
  (plan-decision 2: scaled from `DEFAULT_VIEWPORT`'s aspect ratio). `launch_options()` gains a
  keyword-only `record_video_dir: Path | None = None`; when given, sets
  `options["record_video_dir"]`/`options["record_video_size"]` — **the only place in `src/` that
  ever does** (V7). Omitted by default: every existing caller (crawl explorer, manual login, every
  pre-T-191 test) is byte-for-byte unchanged (C2).
- `src/autotester/browser/video.py` (new, 139 lines) — `VideoMixin` (`begin_case_video`/
  `end_case_video`), mixed into `BrowserSession`. Playwright records per **page**, not per context,
  so "one video per case" means swapping to a fresh `context.new_page()` at case start and closing
  it at case end, never reusing the session's shared page the way screenshots do. `_MASK_INIT_SCRIPT`
  (lines 36-49) installs the masking `<style>` via `page.add_init_script()` + a `MutationObserver`
  retry, not `page.add_style_tag()` — see "The masking mechanism" below for why the obvious approach
  does not work. `VIDEO_DIR_NAME = "_video_scratch"`, `MAX_VIDEO_DURATION_S = 1200.0` (20 min, V6),
  `VIDEO_OVERHEAD_MB = 128.0` (V6).
- `src/autotester/browser/session.py:88-134` — `close()` now sweeps `_video_scratch` after the
  context closes, when `record_video` is on (`_sweep_orphan_videos`, new, 14 lines). See "The
  stray-video bug" below — this is the one real production defect this unit's own tests caught and
  fixed, not a pre-existing one.
- `src/autotester/schema/enums.py:146-148` — `EvidenceKind.VIDEO = "video"`.
- `src/autotester/stages/run_case_pipeline.py:104-127` — `_finalize_video(result, verdict, video_rel,
  run_dir)`, the single choke point (V7) that decides survival: `verdict.result is Result.PASS or
  over_budget` (V6's `MAX_VIDEO_DURATION_S` check) → `unlink(missing_ok=True)`; otherwise appends
  `Evidence(kind=EvidenceKind.VIDEO, ...)` (V8's envelope, same shape every other evidence kind
  uses). Called from both `run_and_grade_case` and `run_and_grade_case_resilient`, always after
  `session.end_case_video()` and after grading (verdict must exist first).
- `src/autotester/stages/video_retention.py` (new, 87 lines) — `prune_old_videos(store, keep=20)`
  (V5). Orders every kept video project-wide by `(run_id, case_order_within_run, case_id)` — `run_id`
  is a ULID (`core/ids.py::run_id`), lexicographically sortable by creation time, never filesystem
  `mtime` (two videos written the same second are indistinguishable by mtime). Deletes the oldest
  beyond `keep` and drops the `Evidence` row from the owning `RawResult` so a report never links a
  file that no longer exists. Idempotent (a second call with nothing new to prune deletes nothing).
- `src/autotester/stages/report_export.py:209,221-233` — `_video_link_html()` (V8): kept video is
  rendered as `<a href='{path}'>video ({path})</a>`, never base64-embedded like a screenshot (RE3's
  named D-050 exception — a 15-20 minute recording base64'd would defeat the whole point).
- `src/autotester/stages/parallel_run.py` — `plan_parallel_run(..., video_enabled: bool = False)`
  (V6a): when true, adds `VIDEO_OVERHEAD_MB` to `per_context_mb` before computing the RAM-bound
  slot count, so a recorded run plans fewer concurrent slots at the same measured free RAM.
  `video_enabled=False` is the default — every pre-T-191 caller/test is unchanged (C2, verified by
  `test_video_disabled_is_unchanged_from_before_this_unit`).
- `src/autotester/ui/routes_runs.py:26,77,130` — **real production wiring**, not just tests:
  `_execute_with_trace` now calls `plan_parallel_run(project, video_enabled=True)`; `trigger_run`
  calls `prune_old_videos(store)` after every run.
- `src/autotester/ui/run_execution.py:67,113,158` — `record_video=True` passed to every
  `BrowserSession`/`default_session_factory` construction in the real serial, parallel, and
  entry-case run paths. Recording is on for every real run through the UI, not just in tests.
- Six new test files (`tests/test_video_evidence.py` 146 lines, `test_video_masking_live.py` 182,
  `test_video_report_export.py` 85, `test_video_retention.py` 101, `test_video_ram_budget.py` 51,
  `test_video_duration_cap.py` 57) — split across files so none crosses `doctor`'s 300-line cap
  (`report_export.py` itself landed at 299).
- `tests/test_ui_runs_parallel_crash_recovery.py`, `tests/test_ui_runs_parallel_trace.py`,
  `tests/test_parallel_run.py` — accept the new `video_enabled=`/`record_video=` keyword args in
  their monkeypatched fakes (`**kwargs`), otherwise unrelated.
- `docs/MAP.md` — regenerated (`uv run autotester map`), not hand-edited.

## The masking mechanism (why it is not the obvious one line)

The plan's first draft was `page.add_style_tag(content=MASK_CSS)` right after creating the case's
fresh page, before `session.goto()` — the same mechanism `screenshot()` already uses. **This does
not survive navigation.** `add_style_tag()` injects into the CURRENT document only; a plain
`page.goto()` (virtually every case's first step) replaces that document wholesale and silently
drops the style tag. Measured directly with isolated Playwright scripts before writing the fix:
`add_style_tag` before `goto()` → `webkitTextSecurity: 'none'` the instant NAVIGATE ran;
`add_style_tag` after `goto()` with no further navigation → `'disc'`, works, but breaks the moment
a case has more than one page. `page.add_init_script()` re-runs on every document the page ever
loads — but it evaluates at `document_start`, before `document.head`/`document.documentElement` are
guaranteed to exist: a naive `document.head || document.documentElement` append raised `Cannot read
properties of null` on a fresh navigation (also measured directly, via console/pageerror listeners).
The shipped fix (`_MASK_INIT_SCRIPT`, `video.py:36-49`) retries via a `MutationObserver` until a
root exists, then installs the `<style>` element and disconnects. Verified against both a `data:`
URL and the real `login_site` fixture through a local HTTP server.

## The stray-video bug (found and fixed by this unit's own tests)

`BrowserSession.start()` always creates or reuses an initial page (`self._context.pages[0]` —
`launch_persistent_context` opens with one page whether asked or not). With `record_video_dir` set
at the context level, that initial page records too, but it is never any case's video —
`begin_case_video()`'s first call closes it as `old_page` without ever routing it through
`end_case_video()`'s rename logic. Its finalized recording sat forever in `_video_scratch` under
Playwright's own random name (`page@<hash>.webm`), an untracked, unpruned stray directly
contradicting V1 ("exactly one video file per case ... no strays"). Caught by
`test_video_is_recorded_and_kept_only_for_fail_and_inconclusive_never_pass`'s
`assert len(videos) == 2` failing with `3 == 2` and the extra name visible in the assertion diff.
**Fixed** in `session.py::close()` (`_sweep_orphan_videos`): since every legitimate case video is
already moved OUT of `_video_scratch` by `end_case_video`'s rename by the time `close()` runs,
anything still there belongs to no case — delete the whole scratch directory. Confirmed this is a
real production defect, not a test artifact, by reasoning through the code path (not just from the
test going green): `start()`'s `self._context.pages[0] if self._context.pages else
self._context.new_page()` is unconditional, and Playwright's `record_video_dir` records every page
in the context, including that one.

**A second, distinct bug was found and fixed in the test itself, not production**: the first draft
of `test_video_evidence.py::_session()` passed `tmp_path / "runs" / "run_1"` as the session's
`run_dir`, while `_finalize_video` (called from inside `run_and_grade_case`) deletes from
`store.paths.run_dir(run_id)` = `tmp_path / "projects" / "video-demo" / "runs" / "run_1"` — a
different directory. The PASS video's `unlink(missing_ok=True)` silently no-op'd against a path that
never held the file, while the real file sat untouched at the test's own ad hoc path. Fixed by
matching the convention `test_run_case_pipeline.py:104-107` already uses:
`BrowserSession(..., paths.run_dir("run_1"), ...)`. Disclosed here in full because "my test caught a
bug" and "my test was wrong" produce the identical first symptom (`assert ... not in videos` fails)
and only reading `_finalize_video`'s and `end_case_video`'s actual path arithmetic told them apart —
worth the checker re-deriving independently rather than trusting this account.

## How to verify (commands + expected)

- `uv run pytest tests/ -k video` — the goal task's own `done_check` (`.goal/goal.json` T-191,
  `expect_exit: 0`)
- `uv run pytest` — full suite
- `uv run ruff check src tests scripts`
- `uv run autotester doctor`

Each run separately, no `-q` (AT-503: pyproject's `addopts` already sets `-q`; a second `-q` makes
`-qq`, which prints no summary line).

## Actual outputs (real, pasted, this session)

```
$ uv run pytest tests/ -k video
........................................................................ [ 94%]
....                                                                     [100%]
76 passed, 1997 deselected, 1 warning in 36.91s
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
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
3 failed, 2050 passed, 6 skipped, 14 xfailed, 15 warnings in 943.94s (0:15:43)
```

**All three failures are pre-existing, none charged to this unit:**
- `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` — AT-627, named in the dispatch
  brief as a known pre-existing failure.
- `test_no_pending_task_has_a_done_check_that_cannot_fail` and
  `test_revised_goal_contract_is_registered` — **newly confirmed pre-existing** this session, not
  previously called out. Both assert `.goal/goal.json` shape: the second hardcodes
  `progress["total"] == len(data["tasks"]) == 70` and an `expected` dict stopping at T-184; the
  actual file already has 81 tasks (verified `python -c "... len(d['tasks'])"` → `81 81`).
  `git diff --stat 72513124 -- .goal/goal.json tests/test_goal_done_checks.py` is empty — **neither
  file differs from this branch's own base commit**, so the drift predates T-191 entirely and this
  unit never touched `.goal/` or this test file. Flagging because the dispatch brief only named
  AT-627; the checker should decide whether this needs its own issue row.

**Red before the fix** (the stray-video bug, `session.py::close()`'s `_sweep_orphan_videos`):
```
$ uv run pytest tests/test_video_evidence.py -k is_recorded_and_kept -s
...
assert f"{fail_case.id}.webm" in videos, "a FAIL video must be kept"
> assert len(videos) == 2  # V1: exactly one file per kept case, no strays
E   AssertionError: assert 3 == 2
E    +  where 3 = len(['case_3b2110ba785f.webm', 'case_725ffcbe73d7.webm',
       'page@27d7cea7254f8b2f8e5c11a8fb961a3c.webm'])
```
Green after the fix (see `uv run pytest tests/ -k video` above, 76/76 passed).

## Capability coverage (each V-criterion -> its isolating falsification)

Throwaway copy built OUTSIDE the worktree via `git archive HEAD | tar -x -C
<scratchpad>/t191-falsify` (after a temporary WIP commit, immediately undone with
`git reset --soft HEAD~1` so nothing is charged to branch history), `uv run pytest` synced its own
fresh `.venv` there. Every falsifying edit below is a single hunk, applied, run, then reverted
before the next row; the bound worktree's `git status --porcelain` was re-checked clean of any
`SABOTAGE` string afterward.

| V | check | falsifying edit (single hunk) | observed |
|---|---|---|---|
| V1 (per-case swap) | `test_video_is_recorded_and_kept_only_for_fail_and_inconclusive_never_pass` | `video.py`: `self._page = self._context.new_page()` → `self._page = self._page or self._context.new_page()` (reuse across cases) | FAIL: `assert 'case_f93ee0b1d8c8.webm' not in [...]` — the PASS case ends up owning the one shared real video; later cases' `end_case_video` returns `None` since their temp file was already renamed away |
| V2 (PASS pruned) | same test | `run_case_pipeline.py`: `if verdict.result is Result.PASS or over_budget:` → `if False and (...)` | FAIL: `assert 'case_e9ecee0661ab.webm' not in [...]`, "a PASS video must be pruned" |
| V3/V4 (masking survives navigation, byte+frame proof) | all 3 tests in `test_video_masking_live.py` | `video.py`: `add_init_script(_MASK_INIT_SCRIPT)` → `add_style_tag(content=MASK_CSS)` (the original broken approach) | All 3 FAIL: `masking CSS not applied before the hold: 'none'` |
| V5 (deterministic retention order) | both ordering tests in `test_video_retention.py` | `video_retention.py`: `sorted(_collect(store), key=_ordering_key)` → `..., reverse=True` | FAIL: wrong 5 files dropped (`case-c2..c6` instead of `case-a0..a4`); evidence-row-removal test fails too |
| V6a (RAM overhead) | `test_video_enabled_plans_fewer_concurrent_slots...` | `parallel_run.py`: `effective_per_context_mb = per_context_mb + (VIDEO_OVERHEAD_MB if video_enabled else 0.0)` → drop the `+ (...)` term | FAIL: `assert 5 < 5` |
| V6b (duration cap) | `test_a_case_over_the_duration_cap_drops_its_video_even_on_a_fail` | `run_case_pipeline.py`: `over_budget = result.duration_s > MAX_VIDEO_DURATION_S` → `over_budget = False` | FAIL: video not deleted, `assert not True` |
| V7 (single choke point) | `test_video_option_and_its_prune_function_each_have_a_single_choke_point` | `session.py`: added a second `options["record_video_dir"] = None` assignment inside `start()` | FAIL: `assert ['launch.py', 'session.py'] == ['launch.py']` |
| V8 (link, never embed) | `test_video_evidence_renders_as_a_link_never_embedded_as_base64` | `report_export.py`: the `<a href=...>` template → `<video controls src='data:video/webm;base64,SABOTAGE'>` | FAIL: `href="..."` no longer found in the exported HTML |

Every row is a genuine catch — no vacuous pass observed at any point.

## Live browser evidence

Real Chromium throughout (never mocked), via `_skip_if_no_chromium()` + a local `http.server`
serving `tests/fixtures/login_site`:
- `test_video_evidence.py` drives the **full production pipeline** (`run_and_grade_case`) for
  PASS/FAIL/INCONCLUSIVE cases on one shared session — proves the mechanism end-to-end, not just
  its parts in isolation.
- `test_video_masking_live.py` interleaves probes mid-recording against a **plain TEXT field**
  (`#username`, fake secret `fixture-user-9137`) — a password-type input is natively masked by the
  browser regardless of custom CSS, so proving the custom mask requires a text field.
  `getComputedStyle(el).webkitTextSecurity` sampled 3 times across the hold (before/mid/after) — all
  `'disc'`.
- **Byte-level V4 proof**: `grep`-equivalent check that the raw fake secret string never appears in
  the recorded `.webm`'s bytes.
- **Frame-level V4 proof**: `media/frames.py::extract_frame` (reused, never reimplemented — C3) pulls
  a frame during the masked hold; a comparison render with masking disabled produces a second frame;
  ffmpeg's own `ssim` filter (`ffmpeg -i a.png -i b.png -lavfi ssim -f null -`, chosen over adding a
  Pillow dependency — confirmed `PIL` not installed) reports a similarity score parsed from
  `All:<score>` in stderr; the two frames visually differ (score below the identical-frame
  threshold), proving the mask isn't merely present in the DOM but actually changes what the
  recording shows.
- **Persona walk (`.work/t191-persona-walk.py`, scratch, not committed, gitignored under `.work/`)**:
  ran a real FAIL case through `run_and_grade_case` with `record_video=True`, exported the report via
  `report_export.export_html`, then opened that exported HTML in a **separate real Chromium instance**
  (not `TestClient`) to confirm a human reviewer's browser actually renders a clickable video link:
  ```
  verdict: FAIL
  evidence kinds: [..., <EvidenceKind.VIDEO: 'video'>]
  video link found in rendered DOM: True
  href: case_b878e06ceb64.webm
  link text: video (case_b878e06ceb64.webm)
  ```
  Confirmed the underlying file is real and non-empty at its actual location
  (`.../projects/persona-video/runs/run_1/case_b878e06ceb64.webm`, 28188 bytes) — the walk's own
  naive `tmp / href` resolution came back `False` because the exported HTML was written to an
  arbitrary temp path, not beside the run directory. That is not a bug in the walk or in this
  unit — see "Known limits / gaps" below, it is the exact, already-named RE3/D-050 exception made
  concrete.

## Known limits / gaps (disclosed, not claimed)

- **The video link is dead on arrival for every real download today — this is a real product
  gap the checker should weigh, not a hidden one.** RE3's D-050 amendment already names the
  narrowing precisely: "The video link alone needs its file to sit beside the run." But
  `routes_report.py::download_report_html` (the **only** production caller of `export_html`,
  `routes_report.py:279-287`) exports to `_reserved_temp_path(".html")`, serves it as a
  `FileResponse` download, and deletes the server-side temp copy immediately
  (`background=BackgroundTask(out.unlink, missing_ok=True)`) — the video is never copied alongside
  it. So the moment a human clicks "download report.html," the resulting file's video link points
  at a path that never existed on their machine and won't exist on the server seconds later either.
  V8 is satisfied exactly as written (linked, never embedded, run-relative path) and RE3's exception
  is exactly as documented — but the human-facing consequence (a report you can download that always
  has a broken video link) may not have been what "linked" was meant to deliver. Not fixed here:
  V8's contract text does not ask for a working download experience, only for the link shape, and
  redesigning the download route (serve from a stable server path instead of a delete-on-send temp
  file? zip the video alongside? require viewing the live report page instead of downloading?) is a
  product decision beyond this unit's scope. Confirmed concretely via the persona walk above, not
  guessed.
- **`test_goal_done_checks.py` has two pre-existing failures** (`test_no_pending_task_has_a_done_check
  _that_cannot_fail`, `test_revised_goal_contract_is_registered`) from `.goal/goal.json` having grown
  to 81 tasks against the test's hardcoded assumption of 70 — confirmed via `git diff --stat` against
  this branch's own base commit as predating T-191 entirely. Not touched (out of scope, `.goal/` is
  not this unit's concern), but the dispatch brief only named AT-627 as the expected pre-existing
  failure, so flagging the other two explicitly rather than letting a "full suite green except the
  known one" claim quietly cover three failures instead of one.
- **The `MutationObserver` masking retry is timing-dependent by construction.** It is proven correct
  against this fixture (`login_site`) and a `data:` URL, both under real Chromium — but no test
  proves it against a page whose framework (React/Vue hydration, heavy client-side routing) delays
  `document.head`'s appearance far longer than this fixture's plain HTML does. The retry has no
  timeout and no upper bound on install attempts (`MutationObserver` fires on every mutation until
  `install()` succeeds), so it cannot time out and leave masking silently off — but this is reasoned
  from the code, not measured against a slow-hydrating real app.
- **No test proves retention behavior against a REAL run** (`test_video_retention.py` is entirely
  fixture/filesystem-based, seeding `.webm` files with fake byte content, never a real Playwright
  recording). The real-recording tests (`test_video_evidence.py`) and the retention tests
  (`test_video_retention.py`) are proven independently, never together in one test — i.e., no test
  runs 25 real cases and confirms the 21st-oldest real video is actually gone. Judged acceptable
  given the cost of 25 real browser cases per test run, but named rather than silently assumed.
- **`RECORD_VIDEO_SIZE` (640x400) was chosen by scaling `DEFAULT_VIEWPORT`'s aspect ratio, not
  measured against an actual 15-20 minute recording's resulting file size.** No test asserts a
  concrete file-size ceiling per minute of recording; V6's disk safety net is entirely
  duration-based (`MAX_VIDEO_DURATION_S`), not size-based. A pathological page (huge unmasked
  animation, video content) could still produce an oversized file within the duration cap.

## What the checker should attack hardest

1. **The download-route dead-link gap above** — decide whether this is in-scope for T-191 to fix
   (e.g., have `download_report_html` also stream the video, or reject the download when video
   evidence exists and direct to the live report page instead) or a follow-on issue.
2. **Re-derive the stray-video-bug fix independently.** `_sweep_orphan_videos` deletes the entire
   `_video_scratch` directory at `close()` — verify this is genuinely safe (nothing else could still
   be writing there) rather than trusting this account, and verify it actually fires in the
   `record_video=False` path (it must not — confirm `if self.record_video:` guards it, `session.py`
   near the `close()` method).
3. **The `MutationObserver` timing gap** — if the checker has access to a real hydrating SPA fixture,
   that would close the one masking gap this manifest cannot itself close.
4. **Re-run the V1-V8 falsification table independently** rather than trusting the pasted output —
   the methodology (throwaway `git archive` copy, single-hunk edits, revert-and-reconfirm) is fully
   reproducible from this manifest's exact hunks.

## Status: ready-for-check
