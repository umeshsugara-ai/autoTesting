# Verdict — t110-regression-proof

**Contract:** qa/contracts/regression-proof.md (P1–P5)
**Manifest:** qa/manifests/t110-regression-proof.md
**Cycle checked:** 1
**Date:** 2026-09-03
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`

## What I re-ran myself (never trusted pasted output)

1. Read `scripts/regression_proof.py` in full. Confirmed the three claimed bug fixes are present
   in the current code state:
   - `functools.partial(_NoCacheHandler, directory=str(FIXTURE_DIR))` (line 64) — the documented
     workaround for `SimpleHTTPRequestHandler.__init__` overwriting `self.directory`.
   - `good_backup = LOGIN_GOOD.read_text(...)` (line 149) is read *before* the `try:` block
     (line 151) — confirms the resource-safety fix (no `UnboundLocalError` risk in `finally`).
   - `_NoCacheHandler` (lines 46–56) overrides `end_headers()` to send
     `Cache-Control: no-store` on every response.
2. Read `tests/fixtures/regression_site/login.html` and `login.broken.html` in full. They differ
   by exactly the claimed one literal (`pass123` vs `pass124`); identical DOM ids
   (`#email`/`#password`/`#submit`/`#result`), identical JS structure otherwise.
3. Cleared `profiles/regression-demo` and ran the script myself, live:
   `uv run python scripts/regression_proof.py` — real headed browser, real network call to
   Gemini via `LangChainFallbackProvider`. My own output:
   ```
   --- BEFORE (working build) ---
   Login with correct credentials: PASS  (observed: 'Login successful')
   Homepage loads: PASS  (observed: 'Welcome to the demo site')
   --- injecting the regression (login.html -> login.broken.html) ---
   --- AFTER (broken build) ---
   Login with correct credentials: FAIL  (observed: 'Invalid credentials')
   Homepage loads: PASS  (observed: 'Welcome to the demo site')
   REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
   ```
   Exit code 0.
4. After my own run, confirmed `tests/fixtures/regression_site/login.html` still reads
   `password === 'pass123'` — fixture correctly restored by the `finally` block, not left broken.
5. Read the actual `RawResult`/`Verdict` JSON files from MY OWN run's directories —
   `projects/regression-demo/runs/run-before-01M1KDR5JKCJA2KBDK2SJQNZ08/` and
   `run-after-01M1KDRFZGPF091JRS5WXMX92R/`. Every verdict carries `"grader_provider": "gemini"`
   (never mock). BEFORE: both cases `PASS`. AFTER: login case `FAIL`, homepage case `PASS`.
6. Re-ran, myself:
   - `uv run pytest tests/test_regression_proof.py -v` → 6 passed
   - `uv run pytest -q` → exit 0 (all pass, 2 skipped, no failures)
   - `uv run ruff check src tests scripts` → All checks passed!
   - `uv run autotester doctor` → doctor: clean
   - `uv run python scripts/check_no_secrets.py scripts/regression_proof.py tests/fixtures/regression_site tests/test_regression_proof.py <my before/after run dirs>` → scanned 25 file(s); 0 leak(s)
   - `wc -l docs/ARCHITECTURE.md` → 150 (≤150 cap)
7. `grep -rn "pathlynks\|SecretRef" scripts/regression_proof.py tests/fixtures/regression_site/*.html` → no matches (exit 1). No Pathlynks credential, `SecretRef`, or domain anywhere in this unit's code or fixtures. `allowed_domains=["127.0.0.1"]` confirmed in `main()`.

## Scope judgment (T-110 note "break a staging feature" vs. this unit's local-fixture substitution)

The contract's own Purpose section states this system has no write access to a real staging
environment and that deliberately breaking one was never approved — this unit instead proves the
identical underlying claim (does execute→grade correctly distinguish a broken feature from an
unrelated working one?) against a fully local, self-served fixture. This is a defensible, honest
substitution consistent with this project's standing rule (never aim at Pathlynks without
explicit per-use approval) and the same class of scope call already made and accepted at T-050
(grading deferral), T-060 (no-real-video disclosure), and T-090 (no-real-url_pattern disclosure).
The contract text itself (P1–P5) is written to be satisfied by exactly this local-fixture
approach, so judging against P1–P5 as written is judging against the contract, not against a
looser reading of the goal-task note.

## Criteria

- **P1** (real, minimal, realistic regression) — MET. Verified the one-literal diff directly.
- **P2** (real headed browser, real judge, twice) — MET. Verified via my own live run + verdict
  JSON files (`grader_provider: "gemini"`).
- **P3** (exactly the broken case flips) — MET. BEFORE PASS/PASS, AFTER FAIL/PASS in my own run.
- **P4** (fixture restored) — MET. Verified `pass123` present after my own run.
- **P5** (never touches a real product) — MET. `allowed_domains=["127.0.0.1"]`; no Pathlynks
  reference anywhere in code/fixtures.

## Rubric (`.goal/rubrics/T-110.md`, done_check: rubric_ref)

All 5 rubric criteria satisfied by this checker's own reproduced evidence (same evidence as
above — real run, real verdict files, real vendor, fixture restored, no real product touched). No
separate `/outcome-grader` dispatch needed; this re-run independently reproduces exactly what it
would grade.

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 0/0 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: Re-ran the full proof live (cleared browser profile, real headed browser, real
Gemini judge) and independently reproduced the exact BEFORE PASS/PASS -> AFTER FAIL/PASS pattern,
confirmed grader_provider is "gemini" in every verdict from my own run, confirmed the fixture was
restored to pass123 afterward, and confirmed no Pathlynks/SecretRef reference exists anywhere in
the unit. Full suite (pytest, ruff, doctor) all green. The local-fixture substitution for "break a
staging feature" is a defensible, contract-scoped judgment call consistent with T-050/T-060/T-090
precedent and the contract's own Purpose section.
```
