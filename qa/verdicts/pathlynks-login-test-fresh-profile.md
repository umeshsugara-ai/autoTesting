# Verdict — pathlynks-login-test-fresh-profile

**Contract:** qa/contracts/pathlynks-first-run.md (F1-F5)
**Manifest:** qa/manifests/pathlynks-login-test-fresh-profile.md
**Cycle checked: 2**
**Verdict: PASS**

## What cycle 1 found (context, not re-litigated)

Cycle 1 FAILed because a fixed `POST_SUBMIT_WAIT_MS = 4000` sleep raced Pathlynks' own async
post-login redirect: on the second of two consecutive runs, the BEST case's evidence was captured
while the app was still mid-transition (a "Logged in successfully" toast visible, but
`landed_url` still the sign-in page), producing a false FAIL. The checker's explicit instruction
for cycle 2 was to re-verify with more than 2 runs, given "looked fine after 1-2 runs" was
exactly what broke last time.

## Cycle 2 fix verified in the code (not just the manifest's prose)

Read `scripts/run_pathlynks_first_cases.py` in full.

- `_wait_for_redirect_or_timeout` (lines 107-123) is a genuine poll, not a disguised fixed sleep:
  it loops `while elapsed < POST_SUBMIT_MAX_WAIT_MS`, checking `session.page.url != signin_url`
  each iteration and sleeping only `POST_SUBMIT_POLL_MS` (250ms) between checks, returning the
  instant the URL changes. `POST_SUBMIT_MAX_WAIT_MS = 8000` (line 44) is a real bounded ceiling,
  not infinite — the loop always terminates.
- The comparison URL is the case's own step-1 NAVIGATE target, not a hardcoded string:
  `run_one_case` (line 130) sets `signin_url = case.steps[0].target` before calling
  `_wait_for_redirect_or_timeout(session, signin_url)` (line 133) — every case's own sign-in URL,
  correctly scoped per case.
- It is wired in place of the old fixed sleep: `run_one_case` calls `run_case(case, session)`
  then `_wait_for_redirect_or_timeout(...)` before taking the `{kind}-final` screenshot and
  recording the post-submit URL — no `wait_for_timeout(POST_SUBMIT_WAIT_MS)` call remains
  anywhere in the file (confirmed by full read).
- Cycle 1's two fixes are unchanged and still both present: `login_test_paths =
  ProjectPaths("pathlynks-login-test")` (line 184) + `shutil.rmtree(login_test_paths.profile_dir,
  ignore_errors=True)` (line 185) for cross-run staleness, and `run_order = sorted(cases, key=...)`
  putting BEST last (line 186) for within-run staleness. `paths = ProjectPaths("pathlynks")`
  (line 154) still only drives `.env`/`run_dir`, never passed to `BrowserSession` — the real
  shared `profiles/pathlynks/` profile remains untouched by this script.

## Independent reproduction — more skeptical than cycle 1's own bar

`rm -rf profiles/pathlynks-login-test`, then `uv run python
scripts/run_pathlynks_first_cases.py` **4 times in a row, no cleanup between any run** (cycle 1's
failure surfaced on run 2 of 2 — I ran twice again after that with zero deviation):

| Run | worst | edge | best | run id |
|---|---|---|---|---|
| 1 (fresh profile) | PASS | PASS | PASS | run-01M1N79T9XVGD7K6SZQJ13DPM3 |
| 2 (no cleanup) | PASS | PASS | PASS | run-01M1N7BBQX09VEWDR4EXG6ZBGY |
| 3 (no cleanup) | PASS | PASS | PASS | run-01M1N7CYY9Z21WBYNZF468MJXA |
| 4 (no cleanup) | PASS | PASS | PASS | run-01M1N7EE6GRBZ4RK4Q0QYK0ZF5 |

All 4 runs: `outcome=completed`, grader `gemini` (real, non-mock, satisfies F3), identical
PASS/PASS/PASS pattern every time — no inconsistency, no `INCONCLUSIVE`/`errored`.

**Screenshot evidence, visually inspected (Read tool) — `13-best-final.png` from run 4**
(`projects/pathlynks/runs/run-01M1N7EE6GRBZ4RK4Q0QYK0ZF5/13-best-final.png`): a genuine
post-redirect dashboard — left sidebar nav (Dashboard/My Space/Explore Careers/.../Logout), "YOUR
PROGRESS" / "Level 1" panel, "Know Yourself / Career Selection / Profile Building" quest cards,
"YOUR GRADE — Grade 10, CBSE Board, Vidysea" panel, plus the green "Logged in successfully" toast
still visible in the corner. This is not a mid-transition frame — it is the actual authenticated
dashboard, confirming the redirect genuinely completed before capture this time (unlike cycle 1's
run 2, which showed the same toast over the still-rendering sign-in form).

## Static hygiene — all clean, re-run myself

- `uv run pytest -q` → all green (2 skipped, rest pass).
- `uv run ruff check src tests scripts` → "All checks passed!".
- `uv run autotester doctor` → "doctor: clean" (cycle 1's unrelated stale-MAP.md drift is gone
  too; not this unit's concern either way).

## Reports regenerated against my own latest real run (not the maker's pasted output)

- `uv run autotester report excel pathlynks --out <tmp>/checker2.xlsx` — 3 rows, all
  `completed`/`PASS`, `1/1` criteria met, real durations (1.44s/2.0s/0.7s), grader `gemini`. No
  `INCONCLUSIVE`.
- `uv run autotester report html pathlynks --out <tmp>/checker2.html` — 3 `PASS` badges (word-
  boundary grep confirms exactly 3 occurrences, no FAIL/INCONCLUSIVE).
- `uv run python scripts/check_no_secrets.py scripts/run_pathlynks_first_cases.py
  <tmp>/checker2.xlsx <tmp>/checker2.html qa/manifests/pathlynks-login-test-fresh-profile.md` →
  "scanned 4 file(s); 0 leak(s)".

## Judgment

The polling mechanism is real (bounded, per-case-scoped, genuinely observing the redirect signal
rather than guessing a duration), both cycle-1 fixes remain intact and unchanged, and 4
consecutive real runs — two more than the manifest's own claim and specifically targeting the
"looked fine after 1-2 runs" failure mode from cycle 1 — produced an identical, correct
PASS/PASS/PASS pattern with visually-confirmed post-redirect evidence. F1-F5 all hold:
content-addressed cases (F1, unchanged since cycle 1), real headed evidence (F2), real non-mock
grader (F3), verdicts that match their evidence including a visually-verified BEST screenshot
(F4), zero secret leaks and read-only write policy (F5).

**PASS — cycle 2, closing this unit.**

Note for the record: the working tree also contains unrelated, unfinished work
(`src/autotester/stages/run_case_pipeline.py`, `qa/manifests/run-case-pipeline.md`, and a
`project_store.py` rubric-storage change) from a different in-progress unit. This verdict and its
commit touch only this unit's own files — `scripts/run_pathlynks_first_cases.py`,
`qa/manifests/pathlynks-login-test-fresh-profile.md`, and this verdict file — and do not comment
on or gate that other unit.
