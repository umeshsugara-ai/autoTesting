# Manifest — at434-demo-cases-one-per-journey

**Unit:** AT-434 — the regression demo held 44 cases, 2 journeys × 22 runs, each copy on a dead random port
**Contract:** `qa/contracts/regression-proof.md`, `qa/contracts/bench.md`, `qa/contracts/ui-flow-diagram.md`; core-invariants C3, C7, C10
**Goal task:** none — issue-driven (found by the independent live-browser validation, `qa/verdicts/live-2026-09-16-ui.md`)
**Date:** 2026-09-16
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-434 (low)
**Status:** checked-PASS (qa/verdicts/at434-demo-cases-one-per-journey.md, cycle 1, commit fb72388)

## Root cause

`Case.compute_id()` covers the steps. Every step target in the demo carries the fixture server's
**random port** (`ThreadingHTTPServer(("127.0.0.1", 0))`), so every run of
`scripts/regression_proof.py` or `scripts/bench_trial.py` minted two new case ids.
`ProjectStore.add_case`'s idempotency on id therefore never fired. There were 22 runs, giving 44
cases. /cases listed 44 rows and /flow-diagram drew 22 copies of each journey.

## What changed

- `scripts/regression_proof.py` — new `seat_demo_cases(store, cases)`. It deletes any existing case
  with the same `(project, flow_id, title)` and a different id, then calls `add_case` for the new
  ones, and returns them. `main()` uses it. The old runs and verdicts of a removed case are left
  alone, as `ProjectStore.delete_case` already documents. 199 lines.
- `scripts/bench_trial.py` — it writes the **same** project with its own `add_case` loop, so fixing
  only one script would let the other re-create the duplicates. It now imports `seat_demo_cases`
  from `regression_proof` (the same pattern as `scripts/explore_proof.py`), so the logic has one
  owner (C3). 184 lines.
- `tests/test_regression_proof.py` — 3 new tests:
  - three runs on three ports leave exactly 2 cases, and they are the latest;
  - unrelated cases are not touched: a different title in the same flow, and the same title in
    another flow;
  - bench_trial uses the shared function, with the source of `main()` inspected, because the import
    alone would not stop a bare `add_case` loop. My first version checked only the import; I
    tightened it before sabotage because it could not catch M4.
- `projects/regression-demo/cases.jsonl` (tracked synthetic demo data) — **44 → 2 rows,
  42 deletions, 0 insertions.** I did this by running `seat_demo_cases` once on the repo store with
  the base URL from the committed `project.json` (port 46661). The two survivors are exactly HEAD's
  last two rows, so `project.json` and the cases stay consistent. Line endings are unchanged.

**Why not a fixed port or a port-free target:** a fixed port can collide on a shared host (AT-391),
and a relative target is refused at run time (`check_destination`, AT-432). The stored case
therefore still names one port. What was wrong was 22 copies, not one port. This is disclosed
rather than claimed as "port-independent", which is what the issue's expected text said.

## ⚠ Incident during this unit (disclosed, remediated)

While checking that `bench_trial.py` still imports, I ran `uv run python scripts/bench_trial.py --help`.
The script has **no argument parsing**, so that command **ran a real bench trial** against the repo's
own `projects/regression-demo`. Its output was piped to `head -3`, which closed the pipe, so the run
died after the first case. What it did, measured:
- It seeded `login.broken.html` over the fixture, and its `finally` restored it. `git diff
  --ignore-cr-at-eol` was empty, so the only change was CRLF→LF.
- It opened a headed browser on the local fixture and ran one case, which wrote 4 screenshots.
- **It made one model call:** the verdict's `grader_provider` was `gemini` (result FAIL, the seeded
  bug). The evidence sent was **synthetic fixture data only**: the local demo login page and the
  public fixture values `test@example.com` / `pass123`. `regression-demo` declares no secrets. No
  Vidysea, student or real data was involved.
- It rewrote `projects/regression-demo/project.json` (new port) and `cases.jsonl` (44 → 2 on the
  new port), and created the gitignored `projects/regression-demo/runs/run-bench-01M2ND8XFSMEG15HEZ6ARGPR02/`.

**Remediation:** I ran `git checkout --` on `tests/fixtures/regression_site/login.html`,
`projects/regression-demo/project.json` and `cases.jsonl`. All three changes were mine, and all
three files were clean at the start of the session. I deleted the run directory, then redid the
cases.jsonl cleanup deliberately on the committed port, as described above. No `bench/` files were
written, because the run died before `save_bench_trial`.
**Lesson:** never probe a script with `--help` unless it parses arguments. Read `main()` first.

## How to verify

| Command | Expected |
|---|---|
| `uv run pytest tests/test_regression_proof.py -o addopts= -q` | `9 passed` (before the fix: `3 failed, 6 passed`, AttributeError on `seat_demo_cases`) |
| `uv run pytest tests/test_regression_proof.py tests/test_bench.py -o addopts= -q` | `15 passed` |
| `wc -l projects/regression-demo/cases.jsonl` and `git diff --stat projects/regression-demo/cases.jsonl` | `2`; `42 deletions` only |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -o addopts= -q -rx` | see Full suite |

## Capability coverage

All rows were reproduced in an isolated `git archive HEAD` extract with the 2 scripts and the test
copied in and its own `uv sync`. `regression_proof.__file__`, `bench_trial.__file__` and
`autotester.store.project_store.__file__` were confirmed inside the extract. Each anchor matched
exactly once. The baseline was `9 passed` before the edits and again after restoring.

| Capability claimed | Check that isolates it | Falsifying edit (single hunk) | Observed |
|---|---|---|---|
| Stale copies of a journey are removed | `test_rerunning_on_a_new_port_keeps_one_case_per_journey` | `regression_proof.py`: `store.delete_case(existing.id)` → `pass` | **2 failed** — the port test (titles list) and the unrelated test (`6 == 4`) |
| A journey is matched by flow **and** title, not flow alone | `test_seating_leaves_unrelated_cases_alone` | the `if` condition → `any(existing.flow_id == f for (_, f, _) in journeys)` | **1 failed** — `case_fcc96e3d8e31` (same flow, other title) was deleted |
| …and not by title alone | same test | the `if` condition → `any(existing.title == t for (_, _, t) in journeys)` | **1 failed** — `case_e71458464f23` (same title, other flow) was deleted |
| bench_trial cannot bring the duplicates back | `test_bench_trial_seats_the_same_demo_cases_the_same_way` | `bench_trial.py`: the `seat_demo_cases(...)` line → the old `build_cases` + `add_case` loop | **1 failed** — `'seat_demo_cases(' in main` |
| The new cases are actually written | port test + unrelated test | `regression_proof.py`: drop the final `for case in cases: store.add_case(case)` | **2 failed** — `[] == [...]`, `2 == 4` |

**Two sabotage errors of my own, corrected before these rows:**
- My first M2/M3 changed only the key set comprehension. The membership test still built a 3-tuple,
  so it never matched and both behaved exactly like M1. Their red proved nothing about isolating
  flow or title, and I rewrote them as above.
- The first harness crashed mid-M4 on a cp1252 console encode and left the extract's
  `bench_trial.py` mutated. I restored it from the working tree (`cmp` identical) and re-ran all
  rows with `PYTHONIOENCODING=utf-8`.

## Live browser evidence (maker SMOKE — the checker must run its own Mode D)

`qa/evidence/browser-at434-2026-09-16-maker-smoke/report.json`. The server ran from the extract on
an isolated root holding the cleaned demo data.
- /cases → **2 rows**. /flow-diagram → **1** distinct `127.0.0.1:<port>`, each journey title once.
  0 console errors.
- **Detection control:** the same count on HEAD's 44-case data (a separate root) gives **22**
  origins and 22 mentions of each title, so the "1" above is a real measurement.
- Not covered: the scripts themselves were not re-run end to end. That run is a headed browser plus
  a live model call, and it is exactly what the incident above did by accident.

## Full suite

**Two runs, both disclosed.** The command for each was `uv run pytest -p no:cacheprovider -o addopts= -q -rx`,
with output redirected in full to a fresh file.

1. **Run 1 — RED.** `1 failed, 1325 passed, 2 skipped, 32 xfailed in 416.69s`, exit=1. The failure
   was `tests/test_cli_harness_safety.py::test_running_every_command_leaves_the_repository_untouched`:
   `running the CLI surface rewrote ['docs\\SNAPSHOT.md']`. That guard fingerprints files by
   `(mtime_ns, size, sha256)` (AT-186), so it fires on any **write**, even one with identical bytes.
   Evidence about the cause:
   - `docs/SNAPSHOT.md` was git-clean afterwards, so its content was identical to HEAD.
   - Its mtime was **21:05:03**, inside run 1's window.
   - The test run alone straight afterwards gave `4 passed`.
   - This unit touches no code that writes `docs/`.
   - The other maker session's AT-438 cycle-3 checker was dispatched at 21:00 in the same working tree.
2. **Run 2 — GREEN.** `1326 passed, 2 skipped, 32 xfailed, 1 warning in 449.86s (0:07:29)`,
   exit=0. That is 1323 + this unit's 3. **After run 2, `docs/SNAPSHOT.md`'s mtime was still
   21:05:03.** The same code running the same suite did not write it, so run 1's red came from a
   write outside this suite (AT-391, shared-tree contention). I infer the other session's checker,
   but that is not proven. All 32 XFAIL lines in run 2 are `tests/test_browser_scroll_invariance.py`
   cases whose reasons name AT-416 / AT-417.
