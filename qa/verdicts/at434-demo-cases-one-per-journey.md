# Verdict — at434-demo-cases-one-per-journey

**Checker:** /checker Mode A + Mode D (fresh subagent), bound to `D:\autoTesting`
**Date:** 2026-09-16
**Manifest:** `qa/manifests/at434-demo-cases-one-per-journey.md`
**Cycle checked: 1**

```
VERDICT: PASS
SCOREBOARD: 11/11 criteria met, 10/10 invariants hold
FAILURES (if any): none
CAPABILITY-COVERAGE: 5/5 rows reproduced
LIVE-BROWSER: qa/evidence/browser-at434-demo-cases-one-per-journey-2026-09-16-checker/report.json
ISSUES-WRITTEN: AT-434 open -> fixed (row edited in qa/issues.jsonl; not committed, the file holds other sessions' hunks)
EXPLANATION: The seating function removes stale copies by (project, flow_id, title), and my own mutations show each part of the key is needed. Both scripts share that one function, and the demo data is exactly HEAD's last two rows with deletions only. In my own headed browser, /cases shows 2 rows and /flow-diagram shows 1 origin with each journey once, with 0 console errors. The same detector on HEAD's data measured 44 rows and 22 origins. The fix gives one case per journey, but the case still names a port, so it is not the "port-independent" the issue text asked for. The manifest discloses this, and I accept it: a fixed port collides (AT-391) and a relative target is refused (AT-432).
```

Criteria counted: regression-proof P2/P4/P5 (the touched `main()` path still uses `build_cases`, the unchanged judge and `finally` restore, and a loopback base URL) · bench K2/K5 (bench `main()` is unchanged apart from seating; bench/ files untouched) · ui-flow-diagram FD1/FD2/FD4 (measured live) · the AT-434 expectation of one case per journey · the data-change claim · the incident-remediation claim · full suite green. Invariants C1–C10.

## What I re-ran (bound tree, my own output)

| Command | Result |
|---|---|
| `uv run pytest tests/test_regression_proof.py -o addopts= -q` | `9 passed` |
| `uv run pytest tests/test_regression_proof.py tests/test_bench.py -o addopts= -q` | `15 passed` |
| `uv run ruff check src tests scripts` | `All checks passed!` |
| `uv run autotester doctor` | `doctor: clean` |
| `uv run pytest -p no:cacheprovider -o addopts= -q -rx` (once, sequential, in the background) | `1326 passed, 2 skipped, 32 xfailed, 1 warning in 269.12s`, exit=0. All XFAIL lines are AT-416/417 scroll-invariance cases. |
| line counts | regression_proof.py 199 · bench_trial.py 184 · test_regression_proof.py 124 (all ≤300) |

**The manifest's disclosed run-1 red** (`test_cli_harness_safety`: rewrote docs/SNAPSHOT.md) did not reproduce: my own full run was green. The maker's evidence was mtime-inside-window, bytes identical, the test green alone, and an unchanged mtime after run 2. That is enough to attribute the red to a concurrent write rather than this unit, and this unit touches no code that writes `docs/`. Not a finding.

## Data change (projects/regression-demo/cases.jsonl)

- `git diff`: 42 `-` lines, 0 `+` lines. The working file has 2 rows.
- With CR stripped, `git show HEAD:… | tail -2` is byte-identical to the working file: the survivors are HEAD rows 43–44. (A raw `cmp` differs only by CRLF. `git ls-files --eol` shows `i/lf w/crlf` and `core.autocrlf=true`, so this is normal checkout behaviour, not a change.)
- Both surviving rows name `127.0.0.1:46661`, and the committed `project.json` base_url is `http://127.0.0.1:46661/index.html`, so they are consistent. HEAD held 22 distinct ports.
- Ids are `case_cf844a2b645c` (flow_login, "Login with correct credentials") and `case_8c1ec91abecf` (flow_home, "Homepage loads").

## Incident remediation claims (verified on disk)

- `projects/regression-demo/project.json`: git-clean (port 46661 = HEAD).
- `tests/fixtures/regression_site/`: git-clean.
- `projects/regression-demo/runs/`: no `run-bench-*` directory (count 0).
- `projects/regression-demo/bench/`: exactly the 3 tracked files, git-clean, nothing new.
- The one Gemini judge call went out and cannot be undone. The disclosed payload was synthetic fixture data (a local login page, `test@example.com`/`pass123`, and a project with no secrets). I accept this as a disclosed, bounded incident, not a finding against the unit.

## Capability coverage (throwaway copy, outside the bound tree)

The copy was `git archive HEAD` extracted to the scratchpad, with the 3 changed files copied in and its own `uv sync`. I deleted the tracked projects/erp, pathlynks and vidysea-erp from the copy before running anything. `regression_proof.__file__`, `bench_trial.__file__`, `autotester.__file__` and `project_store.__file__` all resolved inside the copy.

The harness asserted three things for each row: a green baseline (`9 passed`) in the copy before the edit, an anchor that matched exactly once and a file that changed, and a restore that was byte-identical afterwards. The final run in the copy was `9 passed`.

| Row | Mutated result | Named test in the failure list |
|---|---|---|
| M1 `delete_case` → `pass` | 2 failed | port test ✔ (and the unrelated test) |
| M2 `if` → flow-only | 1 failed | `test_seating_leaves_unrelated_cases_alone` ✔: `assert 'case_fcc96e3d8e31' in {…}`, so **mine** (same flow, other title) was deleted |
| M3 `if` → title-only | 1 failed | same test ✔: `'case_e71458464f23'` (other_flow, same title) was missing, so the right case fired. I recomputed both ids from the test's Case definitions. |
| M4 bench seating line → old `add_case` loop | 1 failed | `test_bench_trial_seats_the_same_demo_cases_the_same_way` ✔ |
| M5 drop the final `add_case` loop | 2 failed | port test ✔ and unrelated test ✔ |

## Mode D (my own browser)

**Instrument:** headed Playwright Python (chromium). I did not use the MCP.

**Servers:** uvicorn from the copy.
- :8044 served `AUTOTESTER_ROOT=root-after`, holding the working-tree cases.jsonl, project.json and bench/.
- :8046 served `root-head`, holding the same paths from HEAD.
- Neither root contains a `.env`.

**Results:**
- **after:** /projects/regression-demo returned 200 with the flow-diagram link present. /cases returned 200 and shows 2 title inputs, 2 Rename buttons and 2 Delete buttons, with each title once. I clicked through to /flow-diagram, which shows 1 distinct origin (`127.0.0.1:46661`), 2 leaves with each journey once, and 2 flow trees.
- **HEAD control:** 44 inputs, 44 Rename and 44 Delete buttons, 22 origins, 44 leaves (22 per title). My detector does see the defect.

**Console errors:** 0 on all 6 pages. A separate probe (`console.error('checker-probe')`) was captured by the same listener, so the zero is a real measurement.

**Cleanup:** I stopped both servers (0 listeners left on 8044/8046) and closed the browser.

## Design judgement

The replacement key (project, flow_id, title) is right for a script-owned synthetic demo. `Case.compute_id` hashes project, flow, case_class and steps but not the title, so the id cannot be the key, and title+flow is the stable human-facing identity the UI renders. Mutations show both parts are needed.

Residual risks. None rises to a failure, because `regression-demo` belongs to these scripts:
- A case someone adds to regression-demo with the same flow_id and title but different steps or `case_class` would be deleted on the next script run. `case_class` is not in the key, so a WORST case titled identically would also be deleted.
- A human rename of a demo case escapes the key. The next run then re-adds a copy, which is benign duplication, not deletion.
- Old runs and verdicts are kept, as `delete_case` documents.

## Commit scope note

This commit carries only this verdict file and my evidence `report.json`. It does not include the unit's code or data, or `qa/issues.jsonl`, which holds other sessions' uncommitted hunks. The AT-434 row edit is on disk for the maker's close-out commit.
