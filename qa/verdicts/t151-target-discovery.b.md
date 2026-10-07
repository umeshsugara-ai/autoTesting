# Verdict B — t151-target-discovery (cycle 2, repair checker, coordinator B)

Cycle checked: 2
Date: 2026-10-07
Bound to: D:/autoTesting (worktree D:/autoTesting/.worktrees/t151-target-discovery, HEAD a9307c2e, base 2fae2504)
Policy: proportional-verification/2026-10-06.6 · Tier L, dual check (coordinator B, blind to A)
Archive: the cycle-1 verdict was renamed to qa/verdicts/t151-target-discovery.b.r1-1.md before this file was written.

## Check plan (step 0)

Diff = security/path-escape/credential boundary plus a dependency bump (pyyaml==6.0.3), no UI. Plan: (1) re-run the two failed cycle-1 criteria end to end; (2) re-run the manifest's capability table row by row in isolated copies; (3) lint, doctor, obsidian grep; (4) one full suite in a separate detached worktree; (5) diff scope read. No browser, no persona walk (backend-only). Coordinator ran serially (no sub-checkers); parallelism was across isolated copies in one runner process. SERIAL: none shared (suite ran in its own worktree, falsification in copies under the scratch directory).

## Criterion 1 — floor / capability coverage table (cycle-1 failure: 4 rows survived)

Method: one throwaway copy per row (src, tests, scripts, pyproject from the detached suite worktree at a9307c2e), only the named test nodes, baseline then single-hunk mutant then restored (restored file byte-identical). The whole batch ran twice (rows/ and rows2/ in scratch) with the same results. The red assertion was read and is the one the check is named for.

| Row | mutant | green -> red -> green | assertion that fired |
|---|---|---|---|
| R01 split_lines | `return text.splitlines()` | 2 -> 2 failed -> 2 | `[6, 8, 10] == [5, 6, 8]` (reader), scan analogue |
| R02 reader tag line | `line=line + 1` | 1 -> 1 failed -> 1 | `{7, 8} == {6, 7}` |
| R03 reader frontmatter line | `line=line + 1` | 1 -> 1 failed -> 1 | same node, frontmatter bracket |
| R04 never executed | `exec(compile(...))` before parse | 1 -> 1 failed -> 1 | "scanned code must be parsed, never executed" |
| R05 Markdown only | `.txt` admitted | 1 -> 1 failed -> 1 | documents == [] |
| R06 alias refused | `if False` | 2 -> 1 failed, 1 passed -> 2 | `[] == ['yaml_alias']` (cyclic case still caught by the `_metadata` guard, as the manifest says) |
| R07 reader signal cap | cap `>= 10**9` | 1 -> 1 failed -> 1 | `[] == ['signal_budget']` |
| R08 scan signal cap | cap `> 10**9` | 1 -> 1 failed -> 1 | `[] == ['signal_budget']` |
| R09 reader in-loop deadline | `_guard` deadline body `pass` | 1 -> 1 failed -> 1 | "the deadline must stop emission, not only the final check" |
| R10 reader post-redaction deadline | `if False and ...` | 2 -> 1 failed, 1 passed -> 2 | `assert not run.complete` |
| R11 scan post-redaction deadline | `if False and ...` | 2 -> 1 failed, 1 passed -> 2 | same node |
| R12 parse_depth | `except KeyError` | 2 -> 2 failed -> 2 | uncaught RecursionError (the refusal is gone) |
| R13 credential list | cycle-1 lists restored | 13 -> 13 failed -> 13 | `[] == ['credential_file']` |
| R14 no Provider call (unchanged test) | `Provider.act(None, "")` in `scan` | 1 -> 1 failed -> 1 | "deterministic read path called a provider" |
| R15 metadata only (unchanged test) | regex also matches `[[x]]` | 1 -> 1 failed -> 1 | `['hidden','rag','safe'] == ['rag','safe']` |
| R16 path escape (unchanged test) | escape check `if False` | 2 -> 2 failed -> 2 | `assert not result.complete` (symlink and junction) |

All 16 table rows (the manifest's 13 mutant rows plus the three "checker re-verifies" rows) now have a committed defender that goes red under its mutant and green on restore. The four cycle-1 survivors (reader line+1, exec, `.txt`, non-cyclic alias) are R02/R03, R04, R05, R06: all killed.

Not met: X17, a changed line that the manifest claims and that no committed test defends. The manifest's "What changed" says `discover.py::_emit` "enforces `max_signals` ... and the deadline per Signal". The mutant that disables the per-Signal deadline check in `_emit` (discover.py, the `if time.monotonic() - started >= scope.limits.wall_clock_s:` / `_refuse(... "wall_clock_s" ...)` / `return False` block inside the `for kind, line, detail in facts:` loop) SURVIVES. Evidence I ran myself: in an isolated copy the three nodes (test_deadline_is_rechecked_after_the_final_redaction x2 + test_import_flood_is_a_visible_signal_budget_refusal) pass 3/3 with the mutant, and so do all 90 tests of tests/test_discover.py + tests/test_discover_hardening.py (`90 passed`). The line is behaviour-bearing: a probe test (clock advanced 1 s per `Redactor.scrub`, 500-line `import openai` file, `wall_clock_s=5`) passes on the baseline and fails on the mutant with `AssertionError: 501` scrub calls (baseline stops under 50). The reader's in-loop check has a defender (R09); the scan path's equivalent has none. The criterion requires "the deadline checked inside the emission loop", and the scan path is an emission loop. FAIL on the floor (an enumerated, changed-this-cycle claim with a surviving edit). Fix direction: one test in tests/test_discover_hardening.py mirroring `test_deadline_is_checked_inside_the_tag_emission_loop` but driving `scan` with an import flood (the probe above is a ready template; it must stay <= the 300-line cap of its file, which has 142 lines of room).

## Criterion 2 — C5 output bound (cycle-1 failure: unbounded signal flood)

- Flood ends in a visible refusal. Probe (scratch/probe.py, real code in the suite worktree, default `ScanLimits`): `"#a " * 20000` through `read_context` -> `refusals == ['signal_budget']`, `complete == False`, 0 signals, 0 documents, 0.04 s. A 3000-line `import openai` file through `scan` -> `['signal_budget']`, `complete == False`, 0 signals. Multi-file reader (flood + two 1500-tag files) -> refusal for the flood and for the file that would exceed the 2000 total, 1500 signals kept, `complete == False`. 30 files x 100 imports through `scan` -> 2000 signals, 10 `signal_budget` refusals, `complete == False`. So the total is bounded by `max_signals` and the incompleteness is visible. Defenders R07, R08 kill the cap mutants.
- Deadline inside the reader's emission loop: R09 killed. Deadline after final redaction: R10 (reader) and R11 (scan) killed. Deadline inside the scan's `_emit` loop: not defended (X17 above).
- Result: the behaviour is correct, and every committed defender the manifest claims is real; the one undefended piece is the scan-side in-loop deadline.

## Other mandatory evidence

- ruff (`ruff check src tests scripts`, suite worktree venv): All checks passed. `autotester doctor`: `doctor: clean`. `grep -rniE obsidian pyproject.toml`: exit 1 (AI8 grep clause holds).
- Affected tests: test_discover.py + test_discover_hardening.py: 90 passed in a copy (baseline for X17). Counts match the manifest (63 + 27).
- Full suite (exactly one, separate detached worktree D:/autoTesting/.worktrees/t151-b-suite at a9307c2e, `uv run pytest`, no -q, no -x, PID 57552, started 2026-10-07T09:21:36+05:30): `4 failed, 2286 passed, 6 skipped, 14 xfailed, 15 warnings in 4963.90s (1:22:43)`. The four failures: tests/test_crawl_inventory_live.py::test_a_logged_in_crawl_maps_every_route_and_names_the_one_it_refused (`wall_clock_s` stop), tests/test_mc_sessionstart_loop_status.py::test_hook_prints_the_report_and_exits_zero_on_a_healthy_log and ::test_hook_prints_unhealthy_line_only_on_an_asleep_log_and_still_exits_zero (PowerShell hook output missing the expected line), tests/test_redact_wrap_perf.py::test_redact_scan_stays_under_a_generous_bound_on_a_500kb_corpus (3.95 s vs a 3 s bound). `git diff 2fae2504 a9307c2e` over src/autotester/core, those four test files is empty: the diff does not touch them or the code they test. Targeted isolated re-run of those nodes (reason: attribute the failures, not a second suite) at 10:48-10:53: the crawl and both hook tests pass; the redact perf test still fails at 3.74 s on this heavily loaded machine (two suites and a falsification batch were running). No failure involves a file or module this unit changed; the three timing failures are load-induced and the cycle-1 checker saw the same hook timeouts under load. They do not drive the verdict. The suite is not a reason for FAIL.
- Diff scope (4c): `git diff 2fae2504...HEAD --stat`: every changed src/tests/dependency path is named in the manifest's "What changed" (credential_files.py, text_lines.py, discover.py, read_context.py, schema/ai_target.py, prompts, mock.py `act` hunk +14 only, pyproject.toml, uv.lock, tests). No existing function, export or test was deleted in product code; the large deletion count is the rewritten manifest itself. mock.py change is the D-065-authorised `act` hunk.
- Security notes: credential denylist now covers .envrc .npmrc .netrc .pypirc .htpasswd *.jks *.keystore *.p8 id_ecdsa credentials.yml secrets.yaml service-account.json token.json and R13 shows refusal without opening. Path escape (symlink and Windows junction) refused (R16).

## Findings

PROPOSED-ISSUE: {"severity":"medium","feature":"t151-target-discovery","title":"scan _emit per-Signal deadline check has no committed defender (C5 output bound)","evidence":"src/autotester/stages/discover.py _emit: mutating the per-Signal wall_clock_s check to `if False` leaves 90/90 tests green; a clock-advancing probe shows 501 vs <50 scrub calls","status":"open","found_by":"checker-unit"}
PROPOSED-ISSUE: {"severity":"low","feature":"ai-target","title":"AI1 Verify grep `Provider` on stages/discover.py cannot exit 1 by construction: classify_target (plan-approved placement) lives in discover.py and imports Provider/ProviderError; the semantic claim (no Provider call on the signal-emission path) holds and is defended by R14. Contract Verify clause should be narrowed to the emission path (checker-owned amendment)","evidence":"grep -n Provider src/autotester/stages/discover.py -> lines 15, 253, 278","status":"open","found_by":"checker-unit"}
PROPOSED-ISSUE: {"severity":"low","feature":"suite-load","title":"tests/test_redact_wrap_perf.py 3 s bound, test_mc_sessionstart_loop_status.py hook tests and test_crawl_inventory_live.py wall-clock are load-sensitive and failed in a full suite under concurrent load; unrelated to T-151","evidence":"suite 4 failed of 2296 on a loaded machine; isolated rerun: 3 of 4 pass, redact perf 3.74s","status":"open","found_by":"checker-unit"}

## Block

VERDICT: FAIL
SCOREBOARD: C5-bound 0/1 (floor row for scan in-loop deadline undefended; behaviour correct) · cycle-1 table rows 4/4 now killed · AI1 met (defender R14; Verify grep literal noted as PROPOSED-ISSUE) · AI8 met (R15, R05, obsidian grep exit 1) · invariants hold
TIER: L (credential, path-escape and approval boundary plus dependency bump, per manifest; confirmed from discover.py/credential_files.py and uv.lock in the diff)
FAILURES:
- [C5 output bound / floor] sev: medium · the scan-path per-Signal deadline check in discover.py `_emit` is a claimed, changed line whose disabling mutant survives all 90 committed affected tests (checker probe: 501 scrub calls on the mutant vs <50) · add one committed defender in tests/test_discover_hardening.py that advances the clock inside `scan`'s emission and asserts `not complete` and a bounded signal-processing count · issue: P1
CAPABILITY-COVERAGE: 16/17 rows reproduced (R01-R16 green-red-green, restored identical); X17 survives
LIVE-BROWSER: not-applicable (changed paths: src/autotester/schema, stages, prompts, providers/mock.py, tests, pyproject.toml, uv.lock; no UI surface)
ISSUES-WRITTEN: none (dual check; PROPOSED-ISSUE lines above)
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent; self != executor)
EXPLANATION: Both cycle-1 failures are mostly closed: every table row now has a committed defender that reddens under its mutant and restores green, and an unbounded flood ends in a visible `signal_budget` refusal with `complete=False` on both the reader and the scanner. One claimed piece is still not defended: the scan path's in-loop deadline check, which survives every committed test. Because this is the cycle-2 limit the maker rewrites the brief or the feature goes to a HUMAN_GATE; the fix is a single test. The wall budget (45 min) was exceeded (97 min) because the machine ran two full suites plus a first falsification batch that I had to repeat after a runner bug; no mandatory evidence is missing.
Metrics: start=2026-10-07T03:48:13Z end=2026-10-07T05:25:00Z wall_min=97 agent_min=unavailable blocked_min=0 suite_runs=1 repeat_runs=2 mutations=17 cycle=2 resumes=0 tokens=unavailable policy=2026-10-06.6
