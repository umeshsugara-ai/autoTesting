# Verdict — t050-pathlynks-first-run

**Date:** 2026-09-03
**Cycle checked:** 1
**Contract:** qa/contracts/pathlynks-first-run.md (F1-F5)
**Manifest:** qa/manifests/t050-pathlynks-first-run.md

## Re-run evidence (all commands re-executed independently, not trusted from the manifest)

- `uv run pytest tests/test_run_pathlynks_first_cases.py -v` → 6 passed.
- `uv run pytest -q` → exit 0, all pass (1 pre-existing skip); `--collect-only -q` totals
  4+3+11+9+6+6+6+12+20+4+4+6+8+24+12 = 135, matches manifest's "135 collected (was 129, +6)".
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 146 (≤150, matches manifest).
- `uv run python scripts/check_no_secrets.py projects/pathlynks/runs/run-01M1K3QVCWQESZX05KWCWPH5B3 scripts/run_pathlynks_first_cases.py projects/pathlynks/cases.jsonl` →
  1 leak, `projects/pathlynks/cases.jsonl` — matches manifest's claim exactly.
- Read `projects/pathlynks/cases.jsonl` directly: 3 `Case` rows, `kind=best/case_class=happy`,
  `kind=worst/case_class=auth_wrong_creds`, `kind=edge/case_class=input_empty`. No step carries a
  raw secret literal — email/password use `{{SECRET:PATHLYNKS_USER_EMAIL}}` /
  `{{SECRET:PATHLYNKS_USER_PASSWORD}}`; the WORST case's wrong password is the literal
  `Wr0ng-Password-Deliberately-Not-Real!`, correctly not a secret (no such declared key). F1 met.
- Read all 3 `RawResult` files in the cited run dir: each case's `evidence` list is correctly
  scoped to only that case's own steps (confirms the manifest's bugfix #3 — no cross-case
  carryover). BEST's final entries: `screenshot 13-best-final.png`, `url
  https://pathlynks.vidysea.com/dashboard` (unmasked, `label: post-submit URL`). WORST/EDGE's
  final URL entries are both `[REDACTED]:PATHLYNKS_USER_LOGIN_URL` (still on sign-in). `run.json`
  shows `trigger: manual`, all 3 case_ids present.
- Viewed the 3 screenshots directly: `13-best-final.png` shows a real "Logged in successfully"
  toast over an authenticated dashboard greeting ("Good afternoon, MtLiteraJabalpur!").
  `05-worst-final.png` shows a real "Invalid credentials" error banner, still on the PATHLYNKS
  sign-in page. `08-edge-final.png` shows real "Email, mobile, or Student ID is required" /
  "Password is required" client-side validation, still on sign-in. All three match the manifest's
  narration and are a defensible, non-contradictory reading of the evidence. F2 met.
- Traced `headed=True` end to end: `scripts/run_pathlynks_first_cases.py::main` builds
  `headed_project = project.model_copy(update={"headed": True})` (an in-memory copy only —
  `projects/pathlynks/project.json` on disk still reads `"headed": false`, confirmed by reading
  it directly) and passes it into `BrowserSession`. `src/autotester/browser/session.py:68`
  (`launch_options`) sets `"headless": not project.headed`, so this run genuinely launched
  headed. Combined with the real screenshots above, F2's "genuinely headed" clause is
  independently substantiated, not just claimed.
- Cross-checked the one `check_no_secrets.py` leak against precedent: `projects/pathlynks/cases.jsonl`'s
  navigate target is the literal `https://pathlynks.vidysea.com/signin`, which equals the real
  (undeclared-as-secret) value of `PATHLYNKS_USER_LOGIN_URL` in `.env`. Independently re-ran
  `check_no_secrets.py` against `projects/pathlynks/project.json` (same `base_url` field) and got
  the identical single-leak pattern — and `qa/verdicts/t030-pathlynks-onboarding.md` already
  checker-PASSed this exact class of false positive for `project.json`. Same reasoning applies
  here: not a real leak, correctly not a secret. F5's "zero real leaks" clause is met; the one
  reported hit is the documented false positive. `write_policy=read_only` respected — code trace
  confirms only `fill`/`click` steps run against the login form; no create/edit/delete calls
  anywhere in `run_pathlynks_first_cases.py` or `execute.py::run_case`.
- Confirmed `ANTHROPIC_API_KEY` is empty in `.env` (read directly) and no Gemini provider exists
  (`src/autotester/providers/` holds only `anthropic.py`, `base.py`, `mock.py`) — the manifest's
  stated reason for the F3/F4 gap is real, not a cover story.
- No `*.verdict.json` file exists anywhere under the cited run directory (`ls` of the run dir:
  only 3 `RawResult` JSONs, `run.json`, and screenshots) — F3 and F4 are structurally unmet: there
  is no `Verdict` for any case, so there is nothing for F4 to judge as defensible or not.

## Judgment call (F3/F4 deferral vs contract as written)

This is the crux the manifest asks the checker to decide. F1, F2, and F5 are genuinely,
independently met — real cases, real headed-browser evidence, real screenshots that match their
claimed outcomes, no real secret leak, write policy respected. The deferral of F3/F4 is
legitimate and human-directed (a working AnthropicProvider key does not exist, no Gemini provider
has been built yet, and Umesh chose — per the manifest's account of this session's
AskUserQuestion, which this checker cannot independently verify since it has no access to this
session's transcript — to wait for a proper multi-provider redesign rather than have the maker
throw together a single-vendor judge). This is architecture discipline, not laziness, and it is
recorded honestly rather than papered over.

But the checker's own governing rule is unambiguous and pre-dates this unit:
"**PASS requires every criterion evidenced.** No partial PASS; that's a FAIL with a scoreboard."
The contract as written states 5 criteria with no partial-credit clause, and the checker's hard
rules explicitly forbid softening a criterion to fit what shipped — that path is reserved for a
criticality-gated amendment, decided by Umesh, away from any pending verdict, never self-applied
by a checker in the moment because the shortfall is sympathetic. There is no Verdict for any of
the 3 cases; F3 and F4 are not weakly met, they are unmet — the artifacts they require (verdict
JSON files) do not exist. Treating "we chose not to build the mock-avoiding version" as
equivalent to "criterion satisfied" would be exactly the self-certification risk this checker
exists to catch, regardless of how well-reasoned the deferral is.

The honest and correct path is: **FAIL this cycle on the scoreboard (3/5), track F3/F4 as an open
issue (AT-033, filed) rather than silently re-litigated, and let the maker route it either as a
follow-on unit (call `grade()` against the existing RawResult evidence once a real judge exists —
no browser re-run needed, which is exactly what this manifest's own design already sets up) or as
a routine/critical contract amendment splitting execution from grading — decided outside this
verdict.** This keeps the browser-execution work's real value on record (it is not thrown away;
F1/F2/F5 are independently reverified true above) without inflating this cycle's PASS/FAIL
signal.

## Result

VERDICT: FAIL
SCOREBOARD: 3/5 criteria met, 0/0 invariants applicable this unit (dependency contracts not
re-litigated here)
FAILURES:
- [F3] No `Verdict` exists for any of the 3 cases — `stages/grade.py::grade` was never called
  (no working non-mock provider available: `ANTHROPIC_API_KEY` empty, no Gemini provider built
  yet) · fix: dispatch a follow-on unit that calls `grade()` against the existing RawResult
  evidence once a real judge provider exists, or a contract amendment splitting execution from
  grading · issue: AT-033
- [F4] Unjudgeable — there is no `Verdict.result` to check against evidence, since none was
  produced · fix: same as F3, F4 becomes checkable the moment a real Verdict exists · issue:
  AT-033
ISSUES-WRITTEN: AT-033
EXPLANATION: F1 (3 correctly-shaped cases, no secret leak), F2 (real headed-browser run, evidence
matches claimed outcomes on independent screenshot review), and F5 (zero real secret leaks,
write-policy respected) are all independently reverified true. F3 and F4 are structurally unmet —
no Verdict artifact exists for any case — because of a legitimate, human-directed architectural
deferral (no working judge provider). The contract grants no partial credit and this checker's
own hard rules forbid softening a criterion to match a sympathetic shortfall, so the unit is FAIL
this cycle with an open issue (AT-033) tracking the F3/F4 gap toward a follow-on unit or a
routine/critical contract amendment, rather than a silent re-ask or a self-applied PASS.
