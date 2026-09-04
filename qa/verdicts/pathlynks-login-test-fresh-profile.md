# Verdict — pathlynks-login-test-fresh-profile

**Contract:** qa/contracts/pathlynks-first-run.md (F1-F5)
**Manifest:** qa/manifests/pathlynks-login-test-fresh-profile.md
**Cycle checked: 1**
**Verdict: FAIL**

## What was verified and confirmed correct

1. **Diff scope, exactly as claimed.** `git diff --stat` shows only
   `scripts/run_pathlynks_first_cases.py` changed (15 insertions, 5 deletions) — no changes to
   `src/autotester/core/paths.py`, `src/autotester/browser/session.py`, or
   `src/autotester/stages/manual_login.py`. `git status --porcelain` confirms `profiles/pathlynks/`
   (the shared profile) is not even a tracked/dirty path — untouched.

2. **Both described fixes are genuinely present** in `scripts/run_pathlynks_first_cases.py`:
   - Line 166: `login_test_paths = ProjectPaths("pathlynks-login-test")` — a dedicated profile
     object, distinct from the real `paths = ProjectPaths("pathlynks")` at line 136, which still
     drives `.env`/`run_dir` only (confirmed: `paths` is never passed to `BrowserSession`, only
     used via `secrets = SecretStore.load(headed_project, paths.env_file)` at line 137 and
     `run_dir = paths.run_dir(run_id)` at line 140).
   - Line 167: `shutil.rmtree(login_test_paths.profile_dir, ignore_errors=True)` before
     `session.start()`.
   - Line 168 + 170: `run_order = sorted(cases, key=lambda c: 0 if c.kind is not CaseKind.BEST else 1)`
     restored, and `BrowserSession(headed_project, secrets, run_dir, login_test_paths)` correctly
     receives the dedicated profile object, not `paths`.
   - This structurally matches the manifest's description of both independently-necessary fixes.

3. **Cross-run staleness is fixed.** `rm -rf profiles/pathlynks-login-test &&
   uv run python scripts/run_pathlynks_first_cases.py` (my own independent run,
   `run-01M1N6MKBBBP8W8EK49Q3030PJ`) produced genuine `outcome=completed` for all 3 cases —
   `worst=PASS`, `edge=PASS`, `best=PASS` — none `errored`/`INCONCLUSIVE`. The original bug (all 3
   cases hitting an already-authenticated redirect) is gone.

4. **Static hygiene is clean:** `uv run pytest -q` all green (2 skipped, rest pass);
   `uv run ruff check src tests scripts` → "All checks passed!";
   `uv run python scripts/check_no_secrets.py scripts/run_pathlynks_first_cases.py
   <my xlsx> <my html> qa/manifests/pathlynks-login-test-fresh-profile.md` → "scanned 4 file(s);
   0 leak(s)".
   (`uv run autotester doctor` shows one `stale-generated: docs/MAP.md` violation — confirmed via
   `git diff --stat -- docs/MAP.md` showing no pending changes to that file, i.e. this drift
   predates this manifest and is unrelated to it; not counted against this unit.)

## Why this is a FAIL: the manifest's central claim did not reproduce

The manifest's own "how to verify" section states the critical test is: *"twice in a row →
genuine PASS/PASS/PASS ... both times"* and calls this **"the critical determinism check the
whole fix is about."** I ran exactly that check, independently:

- **Run 1** (`run-01M1N6MKBBBP8W8EK49Q3030PJ`, fresh profile): `worst=PASS`, `edge=PASS`,
  `best=PASS`.
- **Run 2** (`run-01M1N6P2S23X603K5J1B4J44GZ`, immediately after, no cleanup — same command the
  manifest itself prescribes): `worst=PASS`, `edge=PASS`, **`best=FAIL`**.

This is not the old bug (`errored`/`INCONCLUSIVE` from a stale, pre-authenticated session) — the
outcome is `completed` and the grader is a real non-mock provider (`gemini` via
`LangChainFallbackProvider`), satisfying F3's letter. But it is a **different, newly-observed
determinism failure**, and it is exactly the failure mode this checker task was told to hunt for
skeptically ("treat 'looks plausible' with real skepticism").

**Evidence — `13-best-final.png` (run 2), visually inspected via the regenerated HTML report
(`best-final` panel, top card):** the right-hand panel shows a green **"Logged in successfully"**
toast, but the browser is still rendering the sign-in form and the captured `landed_url` (per
`case_35b17ccece2d.verdict.json`) is still `PATHLYNKS_USER_LOGIN_URL`, not a dashboard. The
preceding screenshot (`12-step04-click.png`) shows the button mid-async state ("Logging in...").
Read together, this shows **login genuinely succeeded**, but the app's client-side redirect to
the dashboard had not yet fired when the script captured the URL — i.e. `POST_SUBMIT_WAIT_MS =
4000` (scripts/run_pathlynks_first_cases.py:44) is not always enough, and this run happened to
land on the slow side of that race. The grader then correctly read the (prematurely-captured)
evidence and produced a defensible `FAIL` against what the URL evidence showed at that instant —
so F4 is satisfied for the verdict-vs.-evidence relationship, but the underlying **evidence
capture is non-deterministic**, which breaks F2's "real evidence" promise in spirit and squarely
contradicts the manifest's own headline claim that the fix produces "the SAME genuine pattern"
run after run.

`report excel pathlynks` and `report html pathlynks`, regenerated against my own run 2 (not the
maker's pasted output), confirm the same: xlsx row for the BEST case is
`('Login with correct credentials', 'best', 'happy', 'completed', 'FAIL', '0/1', 1.41, 'gemini',
'Criteria 0/1 met.')`; the html report's "best-final" screenshot is genuinely a login-page
screenshot with the success toast, not a dashboard.

## Judgment

The two fixes described (dedicated wiped profile + BEST-last ordering) are real, correctly wired,
and demonstrably solve the original cross-run/within-run staleness bug — that part of the
manifest is accurate and well-evidenced. `profiles/pathlynks/` is genuinely untouched.

But the manifest's closing claim — determinism proven by two runs in a row — did not hold under
my independent re-run, which is the specific test this checker task was dispatched to perform.
A fixed `page.wait_for_timeout(POST_SUBMIT_WAIT_MS)` racing the app's post-login redirect is a
real, reproducible flakiness source in the same script this unit touches, and it produces a false
`FAIL` on the BEST case — a false-positive bug (of exactly the kind the project's north star
measures) baked into the very report Umesh asked about.

**FAIL — fix cycle 1.** Recommended fix for cycle 2: replace the fixed `POST_SUBMIT_WAIT_MS`
sleep for the BEST case (or all cases) with an explicit wait for navigation away from the sign-in
URL (e.g. `page.wait_for_url(lambda url: url != base_url, timeout=...)` or polling
`page.url` with a longer bound), so the captured `landed_url` reflects where the app actually
ends up rather than an arbitrary sampling instant — then re-run the same twice-in-a-row
determinism check before requesting the next check.
