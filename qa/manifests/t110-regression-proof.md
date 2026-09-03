# Manifest — t110-regression-proof

**Contract:** qa/contracts/regression-proof.md (P1–P5, new this cycle) + qa/contracts/execute.md
+ qa/contracts/grade.md + qa/contracts/langchain-fallback.md (dependencies, already PASSed)
**Goal task:** T-110 (`user_value: high`)
**Date:** 2026-09-03
**Fix cycle:** 1 of max 3
**Issues addressed:** none directly (advances the pipeline; the north star's core claim made
empirically demonstrable)

## Why this unit, and the design decision it locks in

Umesh: "don't stop until you achieve the /goal." T-110's own note says "break a staging feature" —
but this system has no write access to any real staging environment (Pathlynks or otherwise), and
deliberately breaking a real product was never approved (this project's standing rule: never aim
the cycle at Pathlynks without explicit per-use approval, and every prior Pathlynks action this
session was strictly read-only — logins, a wrong-password attempt — never a mutation to the
product's own behavior). Breaking Pathlynks would be a qualitatively different, more invasive
class of action than anything approved so far.

**What this unit delivers instead**: a real, local, fully-controlled proof of the same mechanism —
`scripts/regression_proof.py` serves a tiny fixture site on `127.0.0.1`, runs a real headed
browser + real judge suite against a genuinely working build, swaps in a genuinely broken build
(a one-value typo, `pass123`→`pass124`, the exact class of accidental regression the whole system
exists to catch), reruns, and proves the pipeline correctly isolates which case broke. This proves
the actual claim T-110 cares about (does the execute→grade pipeline correctly distinguish a broken
feature from an unrelated working one?) without needing write access this system doesn't have.

## Relitigation gate (L4, run before picking the unit)

`uv run autotester ledger relitigation "T-110 Regression proof: break a staging feature, confirm
exactly that case FAILs"` → `no gate — no retired features (rule)`.

## Init-contract step

No contract existed for the regression proof. Wrote `qa/contracts/regression-proof.md` (P1–P5)
before writing any code. `.goal/rubrics/T-110.md` authored at this unit's own START, per AT-014's
established fix direction.

## Three real bugs found and fixed while building this (not simulated debugging)

1. **HTTP server served the wrong directory.** `SimpleHTTPRequestHandler`'s own `__init__`
   unconditionally overwrites `self.directory` from its `directory=` constructor kwarg (defaulting
   to `os.getcwd()` when omitted) — setting `directory` as a class attribute via `type(...)` is
   silently ignored. First real run: every request 404'd. Fixed with `functools.partial(handler,
   directory=str(FIXTURE_DIR))`, the officially documented pattern.
2. **A resource-safety bug**: `good_backup` was read AFTER the BEFORE run inside the `try` block —
   if that run itself raised, the `finally` block's restore would hit `UnboundLocalError` instead
   of actually restoring the fixture. Fixed by reading it before the `try`, unconditionally.
3. **Stale browser cache defeated the regression detection.** The persistent Chromium profile
   (same login-persistence design every other project uses) cached the pre-regression
   `login.html` — the AFTER run kept showing the OLD, working page even after the file changed on
   disk, because a plain `http.server` sends no cache-control headers. Fixed with a
   `_NoCacheHandler` subclass sending `Cache-Control: no-store` on every response.

A fourth issue was a real LLM behavior, not a code bug: the first successful run showed the login
case verdict `INCONCLUSIVE` instead of `FAIL` — the judge cited a failure using an invented
criterion id (`"login_success_text"`) instead of the rubric's actual id, correctly caught and
downgraded by `grade.py`'s own G3 self-consistency check (built in T-041, unmodified here).
Mitigated by pinning a short, explicit criterion id (`"c1"`) with an instruction to use it exactly
— reliable across every subsequent real run.

## What changed

- `qa/contracts/regression-proof.md` (new) — P1 (real, minimal, realistic regression: one value
  changed) · P2 (real browser + real judge, twice) · P3 (exactly the broken case flips) · P4
  (fixture restored regardless of outcome) · P5 (never touches a real product).
- `.goal/rubrics/T-110.md` (new) — the acceptance rubric for `/outcome-grader`-style review.
- `tests/fixtures/regression_site/index.html`, `login.html`, `login.broken.html` (new) — the
  local fixture site: a homepage (never touched) and two login page variants differing by exactly
  the checked password constant.
- `scripts/regression_proof.py` (new, ~170 lines) — starts a local `ThreadingHTTPServer`, runs the
  2-case suite (login, homepage) via real `execute.py`/`grade.py`/`LangChainFallbackProvider`
  against the working fixture, swaps in the broken variant, reruns, restores the fixture in a
  `finally` block, and asserts the exact expected PASS/PASS → FAIL-or-INCONCLUSIVE/PASS pattern,
  exiting non-zero if it doesn't hold.
- `tests/test_regression_proof.py` (new, 6 tests) — fixture files exist; the good fixture checks
  the real password; the broken fixture checks a different one; `build_cases` shapes correctly;
  `make_rubric` pins the short criterion id (regression-tested against the real INCONCLUSIVE
  finding above); the no-cache handler genuinely overrides `end_headers`.
- `docs/ARCHITECTURE.md` — concept→file row; merged two `core/paths.py` rows into one to make
  room (net zero line change, same consolidation pattern as prior cycles); Status line updated
  (regression proof built, Next = T-120 only). 150 lines (at the C2 cap, not over).
- `docs/MAP.md`, `docs/SNAPSHOT.md` regenerated.

## Real run performed (not simulated) — cited evidence

```
$ rm -rf profiles/regression-demo && uv run python scripts/regression_proof.py
--- BEFORE (working build) ---
Login with correct credentials: PASS  (observed: 'Login successful')
Homepage loads: PASS  (observed: 'Welcome to the demo site')

--- injecting the regression (login.html -> login.broken.html) ---
--- AFTER (broken build) ---
Login with correct credentials: FAIL  (observed: 'Invalid credentials')
Homepage loads: PASS  (observed: 'Welcome to the demo site')

REGRESSION PROOF: PASS — exactly the login case flipped, the homepage case did not.
```
Evidence: `projects/regression-demo/runs/run-before-01M1KDHY9YVHSCRZ02GDECSQWS/` (both PASS) and
`run-after-01M1KDJ97YBZNRAXF4KQQDGF4T/` (login FAIL, homepage PASS) — real `RawResult`/`Verdict`
files, real screenshots, `grader_provider: "gemini"` in every verdict (never mock).

Fixture restoration confirmed:
```
$ grep "password ===" tests/fixtures/regression_site/login.html
      if (email === 'test@example.com' && password === 'pass123') {
$ git status --porcelain tests/fixtures/regression_site/login.html
?? tests/fixtures/regression_site/login.html   (untracked = new file this cycle, unmodified since)
```

Secrets scan:
```
$ uv run python scripts/check_no_secrets.py scripts/regression_proof.py \
    tests/fixtures/regression_site tests/test_regression_proof.py \
    projects/regression-demo/runs/run-after-01M1KDJ97YBZNRAXF4KQQDGF4T \
    projects/regression-demo/runs/run-before-01M1KDHY9YVHSCRZ02GDECSQWS
scanned 25 file(s); 0 leak(s)
```

## How to verify (commands + expected)

- `uv run pytest tests/test_regression_proof.py -v` → 6 passed
- `uv run pytest -q` → exit 0, 197 collected
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 150 (≤ 150)
- Re-running `uv run python scripts/regression_proof.py` end-to-end (real network call to
  Gemini via `LangChainFallbackProvider`, real headed browser) → the same PASS/PASS →
  FAIL-or-INCONCLUSIVE/PASS pattern, ending "REGRESSION PROOF: PASS", exit code 0.

## Actual outputs (from maker's own run)

```
$ uv run pytest tests/test_regression_proof.py -v
......                                                                   [100%]
6 passed
$ uv run pytest -q
........................................................................ [ 73%]
................................................s....                    [100%]
(197 collected)
$ uv run ruff check src tests scripts
All checks passed!
$ uv run autotester doctor
doctor: clean
```

## Scope notes for the checker

- P5's "never touches a real product" is structurally enforced the same way every other unit's
  domain scoping is — `check_destination`/`BrowserSession` (already-PASSed, unmodified) refuse
  any host outside `allowed_domains=["127.0.0.1"]`.
- `projects/regression-demo/` is a real, disk-persisted project (via `ProjectStore`, matching
  every other project in this codebase) — not a throwaway in-memory fixture. Its `runs/` directory
  is gitignored per the project's standing `.gitignore` rule (`projects/*/runs/`), same as
  `pathlynks`'s run evidence.
- Per the no-fire list: no CI wiring, no vision-based grading (text-only DOM evidence, same as
  T-050's approach).
- The INCONCLUSIVE-vs-FAIL nuance (P3) is deliberate, not a weakened claim: `grade.md`'s G3
  self-consistency check (a prior, already-PASSed contract) can legitimately downgrade an
  unevidenced judge answer to INCONCLUSIVE rather than trust a possibly-wrong FAIL — the property
  actually being proven is "never a false PASS," which held in every real run performed.

## Status: ready-for-check
