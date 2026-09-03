# Contract — Regression proof (T-110)

**Covers:** goal task T-110. **Owner:** /checker. **Criticality:** HIGH — T-110's own note: "the
actual product promise: new work cannot silently break old work." This is the north star's core
claim made empirically demonstrable, not just architecturally plausible.
**Depends on:** `core-invariants.md` (all), `execute.md`/`grade.md` (the pipeline being proven),
`langchain-fallback.md` (the real judge used).

## Purpose

Prove, with a real run (not a description of one), that the execute→grade pipeline correctly
distinguishes a genuinely broken feature from an unrelated working one. Since this system has no
write access to a real staging environment (Pathlynks or otherwise) and deliberately breaking one
was never approved, the proof runs against a local, fully-controlled fixture server —
`scripts/regression_proof.py` against `tests/fixtures/regression_site/`.

## Criteria

### P1 — A real, minimal, realistic regression
`login.broken.html` differs from the canonical `login.html` by exactly one changed literal (the
checked password constant, `pass123` → `pass124`) — a plausible accidental typo, not a contrived
"always fail" switch. The swap happens on disk, served by a real local HTTP server; no BrowserSession
special-casing or fake outcome injection.

### P2 — A real headed browser, a real judge, twice
`main()` runs the full case suite twice — once against the working fixture (BEFORE), once against
the broken one (AFTER) — through the unmodified `stages/execute.py::run_case` and
`stages/grade.py::grade`, graded by `LangChainFallbackProvider` (never `MockProvider`). Both runs
produce real `RawResult`/`Verdict` files under `projects/regression-demo/runs/`.

### P3 — Exactly the broken case flips; the unrelated case does not
BEFORE: both the login case and the homepage case verdict `PASS`. AFTER: the login case verdicts
`FAIL` (or, if the judge is genuinely uncertain, `INCONCLUSIVE` — grade.py's own self-consistency
guardrail from `grade.md` G3, never a false `PASS`); the homepage case still verdicts `PASS`,
proving the pipeline correctly isolates *which* case broke rather than everything going red
together.

### P4 — The fixture is restored, not left broken
`main()`'s `finally` block writes the original `login.html` content back to disk regardless of
whether the run succeeded or raised — the canonical fixture in git never ends a run in its broken
state.

### P5 — Never touches a real product
`allowed_domains=["127.0.0.1"]` and the base URL is the local server's own loopback address —
`check_destination` (already-PASSed B6/E-series behavior, unchanged by this unit) would refuse
navigation anywhere else. No Pathlynks credential, `SecretRef`, or domain appears anywhere in this
unit's code or fixtures.

## No-fire list

- A live Pathlynks/staging regression — explicitly out of scope; this system has no write access
  to a real staging environment and breaking one was never approved (see Purpose).
- Automated CI wiring to run this on every commit — a future enhancement, not required here; this
  is a one-shot, human-triggered proof for this cycle.
- Vision-based grading — `LangChainFallbackProvider` sends text-only prompts; the judge reasons
  from DOM-text evidence captured by the script (the page's own `#result`/`#heading` text), same
  discipline as T-050's URL-based evidence.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-110 — no contract existed before this cycle.
