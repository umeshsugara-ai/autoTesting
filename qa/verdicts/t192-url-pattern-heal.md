# Verdict — t192-url-pattern-heal

**Cycle checked:** 1
**Date:** 2026-09-27
**Checker:** claude-sonnet-subagent (fresh context, this session) — not the executor. Executor
was the maker orchestrator inline (self-declared), so executor independence holds trivially.
**Bound root:** D:/autoTesting (main checkout, master)

## VERDICT: PASS

## The crux — narrowing vs. substitution

Gate `qa/gates/t135-url-pattern-data-migration.md` answer **B** ("re-run Analyze on erp… costs a
vision run") was approved by Umesh 2026-09-26. The maker ran `uv run autotester ingest map erp`
instead — no `analyze`, no vision call. I traced this independently, not from the manifest's paste:

- `src/autotester/cli_video.py::analyze_cmd` (L222-264) calls `stages/analyze_video.py::analyze`,
  which is the only stage that spends model calls. `map_product_cmd` (L271-284) calls
  `stages/product_map.py::build_screen_map`, which only reads `store.load_analysis(source_id)` from
  disk — no provider, no network, confirmed by reading both functions in full.
- `projects/erp/sources/src_c6bb964cfff8/observations/*.json` and `analysis.json` all carry mtime
  **2026-09-09**, unchanged. `screenmap.json` alone carries **2026-09-27**. This is direct proof no
  model call or network request happened.
- `screen_url_pattern` (`core/urls.py:131`) is called from exactly three places
  (`stages/ingest.py:137`, `stages/product_map.py:40,60`, `stages/explore_status.py:52`) — never
  from `adjudicate.py`, which copies `AnalysedScreen.url` verbatim (`into.url = other.url`,
  `adjudicate.py:117-118`). So `analysis.json`'s raw url is deliberately never touched, and the
  ONE place the fix applies is exercised by `ingest map`, not by `analyze`.
- All three corrupted rows verified to share `frame_ref`/`visits.source_id ==
  src_c6bb964cfff8` (re-read from `screenmap.json` directly, not the manifest's table).
- The cached observation `sources/src_c6bb964cfff8/observations/gemini__ingest_video_v1.md__00.json`
  contains the literal string `"vidysea.com/erp/trainers"` (confirmed by direct read) — the
  corruption is in raw model output, not introduced downstream, and re-requesting it (via `analyze`)
  would return the same string.

**Ruling: this is a legitimate, loudly-disclosed narrowing of B, not a covert substitution.** The
gate's own qualifying language for choosing B over A was "heals through the normal pipeline, no
bespoke script touching real data" and "exercises the fixed producer end to end" — `ingest map` is
an existing, non-bespoke pipeline command and it is the literal call site of the fixed producer,
more precisely than `analyze` (which never touches `screen_url_pattern` at all). The maker did not
hide this: it is the headline of the manifest, and the vision call is left genuinely unspent (mtimes
prove it), not silently claimed as consumed.

**But:** the specific command named in the gate's Answered line and in T-192's own goal-task title
("one Analyze re-run … approved single vision call") was never put back to Umesh before acting. A
HUMAN_GATE exists precisely to keep this class of decision — which mechanism touches real project
data — with the human, even when the builder's technical case turns out to be right. I filed
**ISS-t192-url-pattern-heal-1** (medium, non-blocking) recommending one line of ratification from
Umesh, rather than treating my own approval of the technical case as a substitute for his. This does
**not** fail the unit: the result is correct, safe, evidenced, and reversible, and blocking a
verified 3-field repair pending a rubber-stamp would be disproportionate.

## Supporting claims — independently verified

1. **Single source** — confirmed by reading `screenmap.json` directly: all three screens'
   `visits[].source_id` and `frame_ref` point to `src_c6bb964cfff8`.
2. **Corruption is in raw model output** — confirmed: the cached observation JSON contains
   `"vidysea.com/erp/trainers"` verbatim (grep, not paste).
3. **`screen_url_pattern` is the single normalisation boundary, `analysis.json` correctly untouched**
   — confirmed by reading `adjudicate.py`'s merge (copies `url` raw) and grepping every call site of
   `screen_url_pattern`. `analysis.json` for `src_c6bb964cfff8` still holds
   `"vidysea.com/erp/trainers"` in 3 places — correct, not a missed repair, per the "one concept, one
   place" design the docstring states.

## Blast radius — independently diffed, not pasted

Wrote my own before/after field-level diff (`.work/t192/screenmap.before.json`, sha256
`46e97134a81d27892db9113d436984d92e520aae5f4a894bc279739726057ebf` — hash re-verified by me,
matches) against the current `screenmap.json`: **exactly 3 fields changed, all `url_pattern`, on the
3 named screens.** 8 screens before/after, 0 added/removed, 3 journeys unchanged and byte-equal. The
only other top-level diff is `created_at` (expected — every rebuild restamps it). The one remaining
`"vidysea.com/erp/trainers"` string in the file is in the `url` field (raw observed url), confirmed
by regex scan — correctly left alone.

`git diff-tree --name-status c58be92e` shows the unit's own commit touched **only**
`qa/manifests/t192-url-pattern-heal.md`. `git diff HEAD --stat` shows nothing under `src/`, `tests/`,
`scripts/`, or `docs/` changed. No function/test/config deletion anywhere (4c clean).

## `done_check` — not accepted, correctly

T-192's registered `done_check` (`uv run autotester doctor`, exit 0) is Goodhartable — confirmed the
maker does **not** cite it as acceptance. It states the structural diff as the real acceptance
criterion instead, which I judge sufficient given the diff and live-render evidence above. Doctor
was re-run by me anyway (`doctor: clean`) as one of the three required verify commands, not as
acceptance.

**`done_check` tension, ruled:** `tests/test_goal_done_checks.py::test_no_pending_task_has_a_done_check_that_cannot_fail`
is red partly because of T-192's own `done_check`, filed as `ISS-at638-remainder-2` (already open,
covers 5 tasks, pre-existing, not introduced or worsened by this unit — T-192 changed zero code and
zero goal-task definitions). **T-192 can PASS while that test is red**: the checker is the actual
judge of this unit (via the structural diff + live render, independent of any `done_check`), the
red test is a symptom already tracked with its own remediation owner, and fixing 5 tasks' Goodhartable
`done_check`s is explicitly out of this unit's scope per its own manifest. Folding that fix into
T-192 would be scope creep the manifest already correctly declined.

## Live browser walk — done by me, real Chromium, not curl

Started the app myself (`uv run uvicorn autotester.ui.app:app --host 127.0.0.1 --port 8971`),
navigated a real visible Chromium (Playwright MCP) to `http://127.0.0.1:8971/projects/erp/product-map`,
and took an accessibility snapshot + full-page screenshot. Result: **"Trainers", "Trainers List", and
"Trainers List - Edit Drawer" all render `<code>/erp/trainers</code>`.** 8 screens, 3 journeys
rendered; **0 console messages (0 errors, 0 warnings)**. This is exactly the gate's motivating claim
("render to a human today on `/projects/erp/product-map`"), now confirmed fixed live, not just in
stored JSON.

Evidence: `qa/evidence/browser-t192-url-pattern-heal-2026-09-27-checker/report.json` and
`product-map.png` (full page).

## Idempotency — done by me

Re-ran `uv run autotester ingest map erp`. `screenmap.json`'s hash changes on every run because
`created_at` restamps each rebuild — but the actual data is stable: diffing the re-run's output
against the pre-heal snapshot shows the **same 3 healed `url_pattern` fields and nothing else**, no
regression back to the corrupted form. Idempotent in substance (all durable data fields), not
byte-identical (a timestamp ticks forward each rebuild, which is expected behavior for a rebuild
command, not a defect).

## Durability of the untracked artifact — ruled acceptable

`projects/erp/screenmap.json` is gitignored (`.gitignore:72`), and so is **the entire
`projects/*/sources/` tree** including `analysis.json` and cached observations
(`.gitignore:67`) — this is a pre-existing, repo-wide convention (public repo, D-007), not something
unique to this unit. No `screenmap.json` has ever been committed anywhere in this repo's history
(checked `git log --diff-filter=A --all`). Requiring T-192 to solve project-wide data durability as
a precondition for its own 3-field repair would be disproportionate scope creep. The pre-image at
`.work/t192/screenmap.before.json` is sufficient undo capability for this unit; a durable backup
strategy for `projects/*/` data generally is a legitimate future unit, not a blocker here.

## Known pre-existing failures — reproduced myself, list is complete

Ran `uv run pytest`, `uv run ruff check src tests scripts`, `uv run autotester doctor` as three
separate commands (not piped/grouped):

- `ruff check`: **All checks passed!**
- `autotester doctor`: **doctor: clean**
- `pytest` (full suite, 991.51s): **3 failed, 2033 passed, 6 skipped, 14 xfailed** — the three
  failures are exactly `tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`
  (AT-627) and the two `tests/test_goal_done_checks.py` tests named in the dispatch
  (`ISS-at638-remainder-2`). No new failures, none introduced or worsened by this unit (it changed
  zero source/test files). Also ran the manifest's own targeted subset independently:
  `tests/test_urls.py tests/test_product_map.py tests/test_migrate_url_patterns.py` → **60 passed**,
  matching the manifest exactly.

## Capability coverage

`not-applicable` — the manifest adds no test and changes no code (confirmed by the diff above); the
behavior relied on is covered by the existing 60 tests re-run above, and the checker's own
independent tracing (this document) substitutes for a falsification table on a zero-code data
repair.

```
VERDICT: PASS
SCOREBOARD: 8/8 claims evidenced (source attribution, raw-output corruption, single normalisation
boundary, blast radius = 3 fields, live render, idempotency-in-substance, known-failures list,
no-code diff scope); 0 invariants violated
FAILURES: none
CAPABILITY-COVERAGE: not-applicable (zero-code data repair; behavior covered by 60 pre-existing
tests, re-run and passing)
LIVE-BROWSER: qa/evidence/browser-t192-url-pattern-heal-2026-09-27-checker/ (real Chromium via
Playwright MCP, 0 console errors, /erp/trainers confirmed rendered on all 3 screens)
ISSUES-WRITTEN: ISS-t192-url-pattern-heal-1 (medium, non-blocking — gate-mechanism substitution
disclosed but never put back to Umesh before acting; recommend one-line ratification)
EXECUTOR: maker orchestrator inline (manifest's stated executor) (checker: claude-sonnet-subagent)
EXPLANATION: Data repair verified correct at every layer checked independently (source, mtimes,
diff, live render, idempotency). The one open question is process, not correctness: the maker
substituted a technically-equivalent, well-evidenced, disclosed mechanism for the one Umesh
literally named, without asking first. Ruled a legitimate narrowing given the gate's own stated
criteria, but filed as a non-blocking finding because that class of decision belongs with Umesh, not
with either the maker's judgment or mine.
```

## On `projects/erp/screenmap.json` staying untracked

Deliberately leaving it untracked, matching this repo's own repo-wide convention that all
`projects/*/` derived/generated data (including the very `analysis.json`/observations this repair
reads from) stays outside git. Committing just this one project's `screenmap.json` would be an
inconsistent one-off carve-out with no stated reason; if project-data durability needs solving, it
should be solved for all of `projects/*/` in one deliberate unit, not piecemeal by whichever unit
happens to touch one file next.

## Note on `qa/contracts/core-invariants.md` C10 (commit-before-verdict)

T-192's commit `c58be92e` landed directly on `master`, not on a `wave/<slug>` branch, ahead of this
check. C10 (D-048) requires branch-before-check for units. I did **not** file this as a finding: the
commit touches only `qa/manifests/t192-url-pattern-heal.md` (confirmed via
`git diff-tree --name-status`), identical in shape to the surrounding bookkeeping commits
(`chore(qa): stamp the tick`, `qa(checker): file ISS-…`) that this repo's own current practice
commits directly to master without a wave branch. C10's own rationale ("two loops share this working
tree and one index… a bare commit could include what the other loop staged") targets code-change
units needing merge isolation; a manifest-only, zero-code data-repair commit doesn't create that
risk. Recommend the checker clarify C10's scope for code-free manifest commits in a future routine
amendment, but I don't have >80% confidence this is a violation as applied here, so it is not a
FAILURES line.
