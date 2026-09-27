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
manifest. The full `uv run pytest` was also kicked off by the checker directly (not the maker's
pasted output) and has since completed:

```
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
2 failed, 2067 passed, 6 skipped, 14 xfailed, 15 warnings in 1172.88s (0:19:32)
```

Both failures are the manifest's own disclosed, independently-confirmed-pre-existing
`.goal/goal.json` drift (81 tasks vs. the test's hardcoded 70 — `ISS-at638-remainder-2`, already
filed, already queued as its own unit). AT-627
(`test_run_once_kills_a_real_hung_process_and_its_real_grandchild`) did **not** fail this run —
consistent with it being load-sensitive rather than deterministically broken; its absence here is
not a regression, and its presence would not have been one either. **No fourth failure, no
failure chargeable to this unit** — the full-suite result confirms the manifest's own account
exactly. This does not change the FAIL ruling above, which rests entirely on the independently
reproduced sweep-race finding.

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

---

# CYCLE 2 — INDEPENDENT RE-CHECK (2026-09-27)

**Cycle checked:** 2
**Judged commit:** `2dcb4cd3` (the cycle-2 fix + regression test), with `1615a6b8` on top as a
bring-up merge of master (bystander commit, not judged — the merge resolved one append-only
`qa/issues.jsonl` conflict by keeping all four rows from both sides, confirmed by inspection, not
this unit's work).
**Checker:** fresh Claude Sonnet 5 subagent, Anthropic session, no `ANTHROPIC_BASE_URL` override
(executor independence holds — checker != executor, cycle 2's build seat).
**Scope:** this cycle fixed exactly one thing, `ISS-t191-run-video-1` (critical). Cycle 1's V1–V8
falsification table (8/8 genuine), the masking proof's three legs, and `screenshot()`'s
non-shared navigation-fragility are **not reopened** — nothing in the cycle-2 diff touches them.
`ISS-t191-run-video-2` (dead download link) is correctly untouched, per scope.

## VERDICT: PASS

## Scoreboard

8/8 V1–V8 criteria still met (unchanged this cycle, not re-litigated); the one invariant cycle 1
FAILed on (C7 — "a wrong answer must not be worse than the bug it fixes", violated by the
sweep-race evidence-loss defect) now holds. `ISS-t191-run-video-1` is independently confirmed
fixed, not merely reported fixed.

## 1 — Is the fix safe by construction, as claimed? Yes, verified on every path.

Traced every `BrowserSession(...)` construction site in `src/`:
`ui/run_execution.py:67` (`_run_entry_case`, dedicated wiped profile), `:113`
(`_run_cases_serially`'s one shared session), and `stages/parallel_run.py::default_session_factory`
(`:257`, `_factory(case)` — confirmed it calls `build(...)` fresh **per case**, then `.start()`
once, and returns the started session; `_run_one`/`run_cases` then close it in a `finally` after
exactly one case). `self._video_scratch_id = uuid.uuid4().hex[:12]` is minted once in
`BrowserSession.__init__` — since every one of these paths constructs a **new** `BrowserSession`
instance per session-lifetime (the serial route's one shared session runs multiple cases through
the *same* instance, which is fine: no sibling shares its `run_dir` in that route), and no path
calls `.start()` twice on one instance or runs two cases through one `_factory`-produced session,
the id is genuinely unique across every case that could ever share a `run_dir` with another. This
is not merely "looks unique" — I falsified it directly (see §3).

**Parent-directory leak check:** `run_dir / VIDEO_DIR_NAME` (the parent of the per-session
subdirectories) is never swept by anyone once a session closes — each session's
`_sweep_orphan_videos` only ever `rmtree`s its own `<id>` subdirectory. After every session in a
run has closed, the parent directory is left behind, empty. This is a real, disclosed behavior
change from pre-fix (which `rmtree`'d the whole bare `_video_scratch` on any close), but it is
**not** an unbounded leak: `run_dir` is itself scoped to one run (`core/paths.py::run_dir(run_id)`),
so the empty leftover directory's lifetime is bounded by however long that run's own directory is
kept, and it holds zero bytes. Not a finding — noted for the record since the dispatch asked.

## 2 — V1 orphan-leak re-verified independently, under the new nested path, via a stub (not just "tests still pass")

Built a throwaway copy via `git archive HEAD | tar -x` into a scratch dir OUTSIDE the bound
worktree, `uv sync --frozen`'d its own venv (fast, shared package cache). Confirmed GREEN in the
copy first (both `tests/test_video_parallel_sweep.py` and
`test_video_evidence.py::test_video_is_recorded_and_kept_only_for_fail_and_inconclusive_never_pass`),
proving the copy real, before any falsification.

Stubbed `_sweep_orphan_videos` to an unconditional `return` (no-op) — a stronger, more direct
falsification than a revert, since it removes the sweep mechanism entirely rather than reverting
one path expression. Result:

```
$ uv run pytest tests/test_video_evidence.py -k is_recorded_and_kept -v
FAILED tests/test_video_evidence.py::test_video_is_recorded_and_kept_only_for_fail_and_inconclusive_never_pass
E   AssertionError: assert 3 == 2
E    +  where 3 = len(['case_787e11370038.webm', 'case_d94af0c1df71.webm',
       'page@b32ab3611df0144251b096ed5a2a63fc.webm'])
```

Identical failure shape to cycle 1's pre-fix reproduction (`3 == 2`, the same `page@<hash>.webm`
orphan). This proves the per-session-scoped sweep still does real, load-bearing work against the
orphan-leak V1 was written for — the narrower scope (own subdirectory only, not the whole bare
dir) did not quietly stop catching the thing it exists to catch. Reverted the stub, re-confirmed
GREEN, `diff -q` against the pristine backup confirmed byte-identical restoration.

## 3 — Falsification-duty re-run myself: both a revert AND a stub, per the dispatch's mandate

**(a) Revert-style** (the manifest's own row): `scratch = self.state.run_dir / VIDEO_DIR_NAME /
self._video_scratch_id` → `scratch = self.state.run_dir / VIDEO_DIR_NAME` in the throwaway copy.

```
$ uv run pytest tests/test_video_parallel_sweep.py -v
FAILED ... AssertionError: B's already-finished video must survive A's teardown of a SHARED
run_dir -- ISS-t191-run-video-1
assert False
 +  where False = exists()
 +    where exists = WindowsPath('.../shared_run/case_b.webm').exists
```
RED, for the row's own named reason — confirmed.

**(b) Stub-style** (this checker's addition, per the dispatch's "also try stubbing, not only
reverting", AT-548/549/550/at335 caution): `self._video_scratch_id = uuid.uuid4().hex[:12]` →
`self._video_scratch_id = "STUB-not-unique"` (a constant, not a fresh id per session) — a subtler,
more targeted falsification of the *uniqueness* claim specifically, distinct from the path-nesting
claim (a) tests.

```
$ uv run pytest tests/test_video_parallel_sweep.py -v
FAILED ... AssertionError: B's already-finished video must survive A's teardown of a SHARED
run_dir -- ISS-t191-run-video-1
assert False
 +  where False = exists()
```
Also RED, for the same named reason. This is a genuine, distinct falsification the manifest never
attempted — it proves the test actually depends on `_video_scratch_id` being unique **per
session**, not merely on the presence of a nested path segment (a stub that kept nesting but
removed uniqueness could in principle have slipped past a check that only exercises (a)). Reverted,
re-confirmed GREEN, restored file confirmed byte-identical to the bound worktree's via `diff -q`.

**Bound worktree integrity throughout:** `git status --porcelain` on
`D:/autoTesting/.claude/worktrees/agent-a8d7c6e7cb6f8905a` confirmed clean before this check
started, after every falsification round-trip in the throwaway copy, and at the end — no file in
the bound tree was ever edited by this check, `git stash` was never used.

## 4 — Determinism under real load: held, 10/10

Ran `tests/test_video_parallel_sweep.py` 10 times in the bound worktree: 6 in isolation, then 4
more while a real `uv run pytest` full-suite run (real-Chromium-heavy, the same one whose results
are below) was already active in the background on this same memory-constrained box. All 10
passed. The `threading.Event`-based ordering (never `sleep`) held under genuine concurrent load,
not just in a quiet environment — the determinism claim stands.

## 5 — `session.py` at exactly 300 lines: confirmed genuinely clean, not clean by luck

`wc -l src/autotester/browser/session.py` → **300**, `uv run autotester doctor` → `doctor: clean`
(re-run by me, not trusted from the manifest). This is the doctor's file-length cap with **zero**
headroom — the very next line added to this file, for any reason, breaks the design-rules gate.
**Flagging per the dispatch's instruction:** the next change to `session.py` must split it (e.g.
the video-scratch concern could move fully into `video.py`'s `VideoMixin`, or a lifecycle/actions
split). Not a defect in this unit — a note for whoever touches this file next.

`video.py`: `wc -l` → **147** (not 149 as the manifest states — the manifest's own arithmetic is
off by 2; the actual diff is a 1-line docstring sentence replaced by a 9-line one, net +8 from
139). Trivial prose imprecision, well under the 300 cap either way, not a finding.

## 6 — Disclosed `git stash` violation: no corruption, filed as a note not a blocking finding

Compared `f2370b86`'s diff against the maker's own account and against what the cycle-1 verdict
already says. The commit's diff is a clean, self-consistent append to the "Pre-existing failures"
section — it replaces the manifest's own "...is still completing at time of writing..." placeholder
sentence with the actual completed full-suite output (`2 failed, 2067 passed`, the same two
`.goal/goal.json`-drift tests) and a short closing paragraph. Nothing in the diff is inconsistent
with, or goes beyond, what the cycle-1 checker's own verdict independently reports having run at
that point in its own check. No corruption: the addition is exactly what it claims to be, and
nothing else in the file changed.

**Ruling:** this is a real process violation (the dispatch explicitly forbade `git stash` against
the bound worktree, and the shared-stash hazard is real — this is the same worktree the
`checker-temp-at540` entry sits on the stash stack for, one accidental `stash pop` away from
disaster) — but the maker disclosed it unprompted, in detail, with the exact commit SHA and a
correct account of what happened and why it was risky, and verified before/after that the
falsification-duty check itself used the safe `git archive` primitive instead. That is exactly the
self-disclosure behavior this pair is built to reward, not punish as concealment. **Filing it as a
low-severity process note, not a blocking finding: `ISS-t191-run-video-3`, severity low, type
`process-violation`, status `wontfix`** (no code fix applies — it's a one-time process lapse,
already disclosed, already not repeated in the same manifest's own falsification-duty work) — the
record exists so a future sweep doesn't have to re-derive this. Does not affect the PASS ruling.

## 7 — Regression test's own credential boundary

Grepped `tests/test_video_parallel_sweep.py`: no `.fill()` call anywhere, no secret-shaped value,
only `page.goto()` against the local fixture server. Confirmed clean.

## 8 — My own full-suite run (not the maker's pasted output)

Ran `uv run pytest` myself, in the background, to completion (1152.70s / ~19m13s):

```
FAILED tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild
FAILED tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail
FAILED tests/test_goal_done_checks.py::test_revised_goal_contract_is_registered
3 failed, 2068 passed, 5 skipped, 14 xfailed, 15 warnings in 1152.70s (0:19:12)
```

**No fourth failure — exactly the three the dispatch pre-named as non-chargeable:**
- `test_revised_goal_contract_is_registered` — the disclosed `81 == 70` `.goal/goal.json`-drift
  (`ISS-at638-remainder-2`), confirmed by reading the actual assertion failure myself.
- `test_no_pending_task_has_a_done_check_that_cannot_fail` — failed with offenders
  `['T-190', 'T-191']`. Read the actual assertion: this is a **static property of
  `.goal/goal.json`'s existing task definitions** for T-190 and T-191 (their `done_check` commands
  are worded such that they'd pass on this branch's tip regardless of task state, now that the
  video/persona-advisory features already exist on it) — `.goal/goal.json` is untouched by this
  unit's diff (confirmed earlier via `git show --stat 2dcb4cd3`), so this is the same
  pre-existing `ISS-at638-remainder-2` class the dispatch named, with more detail than the
  manifest bothered to quote, not a new defect. Also correctly not chargeable.
- `test_run_once_kills_a_real_hung_process_and_its_real_grandchild` (AT-627) — fired this run
  (`FileNotFoundError` reading a grandchild's pid file that a real spawned subprocess didn't write
  in time), exactly the "load-sensitive, may fire under load" behavior the dispatch pre-authorized
  as non-chargeable. Unrelated to anything in `src/autotester/browser/`.

`5 skipped` vs. the manifest's `6` — a one-count environmental difference (not investigated
further; a skip is not a failure and this unit's diff carries no skip-condition logic).

## Capability coverage (cycle 2)

1/1 new row independently reproduced (§3 above, two ways: revert and stub). The V1–V8 table from
cycle 1 is unchanged and was not re-run row-by-row this cycle (nothing in the cycle-2 diff touches
V1–V8's mechanisms; re-litigating all 8 again would be verifying code that did not change).

## Live browser

Real Chromium, real `threading.Thread`s, driven by me in the throwaway copy for both
falsification legs (§2, §3) and 10x in the bound worktree for determinism (§4). No UI
route/screen/template is in the cycle-2 diff (`git show --stat 2dcb4cd3`: only `session.py`,
`video.py`, the new test file, and the manifest) — confirmed against the actual diff, not taken on
the manifest's word, so the "Persona walk: skip (backend-only)" claim holds and Mode D's
UI-walkthrough requirement does not apply this cycle. `LIVE-BROWSER:` evidence lives in this
verdict's inline transcripts above (no separate `qa/evidence/browser-t191-run-video-*-checker/`
directory was needed since no UI surface changed — nothing to screenshot beyond the pytest
transcripts already inline here).

## Credential boundary

Confirmed clean (§7). No `.webm` file and nothing under `.work/` in the cycle-2 commit
(`git show --stat 2dcb4cd3`: only the four expected files) or added by my own check
(`git status --porcelain` clean throughout and after).

## Executor independence

EXECUTOR: /maker build subagent (manifest's cycle-2 "Executor" line: claude-sonnet-subagent)
(checker: claude-sonnet-5-subagent, this session, no `ANTHROPIC_BASE_URL` override).

## Issues written / updated

- `ISS-t191-run-video-1` (critical) — flipped `open` → `fixed`, `regression_check: "uv run pytest
  tests/test_video_parallel_sweep.py"`, per this cycle's independent verification. Stays `fixed`
  (not `verified`) per the ledger rule — `verified` requires a **later**, separate re-check.
- `ISS-t191-run-video-2` (high) — confirmed still `open`, untouched, correctly out of scope this
  cycle.
- `ISS-t191-run-video-3` (low, new, `wontfix`) — the disclosed `git stash` process violation (§6),
  filed for the record, not blocking.

## What Umesh should know

Nothing gates this PASS. Two things worth his attention on a future cycle, neither urgent: (1)
`session.py` is at the doctor's 300-line cap with zero headroom — the next touch to this file must
split it; (2) `ISS-t191-run-video-2` (the video link is unreachable through any shipped path today)
remains open and high-severity — it does not block T-191 as scoped, but it means the feature's
stated purpose ("a 15-20 minute walkthrough a human can watch") is not yet deliverable
end-to-end; worth a HUMAN_GATE/follow-on unit when there's room for it.

