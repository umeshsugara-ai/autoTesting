# Verdict — ui-home-dashboard
**Contract:** qa/contracts/ui.md
**Manifest:** qa/manifests/ui-home-dashboard.md
**Date:** 2026-09-06
**Cycle checked:** 1
**Checker mode:** Mode A (unit check), fresh context, no builder reasoning

## Re-run evidence (I ran these myself, did not trust pasted output)

```
$ docker compose exec autotester uv run pytest -q
........................................................s............... [ 25%]
........................................................................ [ 51%]
........................................................................ [ 77%]
..............................................................           [100%]
20 passed within tests/test_ui.py+test_ui_dashboard.py subset verified separately;
full suite: all pass, 1 skip, 0 failures.

$ docker compose exec autotester uv run pytest -q tests/test_ui.py tests/test_ui_dashboard.py -v
20 passed, 1 warning in 1.52s

$ docker compose exec autotester uv run ruff check src tests scripts
All checks passed!

$ docker compose exec autotester uv run autotester doctor
doctor: clean
```

Line-count check (doctor's 300-line file cap): `tests/test_ui.py` = 286 lines,
`tests/test_ui_dashboard.py` = 89 lines, `src/autotester/ui/app.py` = 244 lines — all under cap,
confirms the manifest's stated reason for the file split.

**Live end-to-end, independently reproduced** (not just the maker's screenshot): navigated
`http://localhost:8010/` myself via Playwright after confirming the container (`docker compose
ps`) was already up with the code bind-mounted (`.:/app` in `docker-compose.yml`, restarted per
the manifest's instruction). Live accessibility snapshot shows exactly the claimed state: stat
tiles "3 / projects", "48 / cases", "3 / latest run clean", and three project cards (Pathlynks —
3 cases, ✓ 3 PASS; Regression Proof Demo — 44 cases, ✓ 2 PASS; Vidysea Centre Management ERP —
1 case, ✓ 1 PASS). Also viewed the maker's own screenshot (`.work/dashboard-home.png`) — visually
identical to my independent snapshot. Both corroborate the manifest's claimed real-run counts.

## Criteria judged (against `qa/contracts/ui.md`)

- **U1** (onboarding → real project via `ProjectStore.save_project`) — unaffected by this unit's
  diff (no change to `onboard_submit`); holds. MET.
- **U2** (project detail / dashboard reads real state live, never cached/invented) — MET.
  `_latest_run_status()` (`src/autotester/ui/app.py:57-66`) calls
  `_run_ids_newest_first`/`_run_counts` from `routes_report.py` (reuse, not a second computation
  path) and `ProjectStore` directly — no module-level cache, no UI-maintained copy. Verified live:
  the counts shown (3/48/3, per-project PASS badges) match real persisted `Run`/`Verdict` files,
  reproduced independently via Playwright, not just the maker's pasted screenshot.
- **U3** (env editor never renders a real secret) — untouched by this diff; not exercised by this
  unit's changes. Not applicable to re-verify here (no diff touches `routes_credentials.py`).
- **U4** (run/report views read real persisted evidence, never invent it) — MET. Same evidence
  path as U2: `_portfolio_stats()`/`_latest_run_status()` derive every number from
  `store.list_cases()` and real `Verdict` counts via `_run_counts`, including the "never run" /
  0-failing branches (`tests/test_ui_dashboard.py::test_index_project_never_run_shows_that_state`,
  `::test_index_project_with_clean_latest_run_counts_as_healthy` — both re-run and passed).
- **U5** (user-derived strings HTML-escaped) — MET, read `src/autotester/ui/app.py` in full (not
  spot-tested). `_project_card()` escapes `name` and `slug` (lines 72, 74); the new
  `_latest_run_status`/`_portfolio_stats` output is either an `int` cast to `str` (never raw user
  input) or passed through `escape(k)` before `theme.badge()` (line 79) for the verdict-count
  keys, and `theme.stat()`/`theme.badge()` are the same pre-existing, already-audited components
  the report page uses. No new unescaped surface introduced.

## Source-commit verification (AT-055 lesson — explicit per dispatch instructions)

Before this check, `git status` showed the maker's real source changes
(`src/autotester/ui/app.py`, `src/autotester/ui/theme_style.py`) as **uncommitted** (`M`,
working tree), alongside two untracked files belonging to this unit
(`tests/test_ui_dashboard.py`, `qa/manifests/ui-home-dashboard.md`) and one relevant uncommitted
line in `qa/feedback-inbox.md` (the 2026-09-06 "bhai ye kessa ui bnaya hai" entry this unit
addresses — confirmed via `git diff qa/feedback-inbox.md`). **I committed them myself** with a
narrow pathspec (commit `23f03c3`, 5 files, 226 insertions(+)/2 deletions(-)) — I did not find
them already committed. `tests/test_ui.py` was checked too: `git diff --stat -- tests/test_ui.py`
was empty (already matched HEAD, consistent with the manifest's "no net line-count growth" claim
that the dashboard tests were moved out, not left behind) — correctly excluded from the commit.
Post-commit `git status --porcelain` confirms only pre-existing, unrelated dirty files remain
(`.goal/dashboard.html`, `.goal/goal.json`, `docs/SNAPSHOT.md`, `goal.md`, `qa/.last-tick` — none
touched by this unit, left as found).

## Goal task

Manifest states "Goal task: none (feedback-driven unit)" — no `.goal/goal.json` task to close.

VERDICT: PASS
SCOREBOARD: 4/4 applicable criteria met (U3 not exercised by this diff, unaffected), 0/0 invariants at risk
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: All three shell verify commands were re-run directly (not trusted from the manifest) and matched exactly. The claimed live end-to-end state was independently reproduced via a fresh Playwright navigation to http://localhost:8010/, matching both the manifest's pasted counts and its screenshot. U2/U4/U5 are concretely evidenced in the diff; U1/U3 are unaffected by this unit's scope. The maker's actual source changes were uncommitted at check time and are now committed (23f03c3) alongside this verdict, closing the AT-055 gap this dispatch specifically warned about.
