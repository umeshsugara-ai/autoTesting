# Verdict — t050-pathlynks-first-run

**Date:** 2026-09-03
**Cycle checked:** 2
**Contract:** qa/contracts/pathlynks-first-run.md (F1-F5)
**Manifest:** qa/manifests/t050-pathlynks-first-run.md (Fix cycle: 2)

## Re-run evidence (all commands re-executed independently, nothing pasted trusted)

- `uv run pytest -q` → exit 0, all pass (1 pre-existing skip), matches manifest's claim.
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `uv run python scripts/check_no_secrets.py projects/pathlynks/runs/run-01M1K941M7AQ7RWMYPF378TDQT
  scripts/run_pathlynks_first_cases.py projects/pathlynks/cases.jsonl
  src/autotester/providers/langchain_fallback.py` → exit 1, 1 leak:
  `projects\pathlynks\cases.jsonl`. Cross-checked independently: `.env`'s `PATHLYNKS_USER_LOGIN_URL`
  equals `projects/pathlynks/cases.jsonl`'s literal navigate target
  `https://pathlynks.vidysea.com/signin`, and `projects/pathlynks/project.json`'s `base_url`
  field is the identical string — the same false-positive class already checker-PASSed for
  `project.json` in `t030-pathlynks-onboarding`. Not a real leak. F5 met.
- `projects/pathlynks/project.json` read directly: `"headed": false` on disk, confirming the
  manifest's claim that the in-memory `headed=True` override in `run_pathlynks_first_cases.py`
  never touched the persisted default.

## F1 — three cases, one per kind (re-verified)

Read `projects/pathlynks/cases.jsonl` directly: 3 `Case` rows —
`kind=best/case_class=happy`, `kind=worst/case_class=auth_wrong_creds`,
`kind=edge/case_class=input_empty`. No step carries a raw secret literal — email/password use
`{{SECRET:PATHLYNKS_USER_EMAIL}}`/`{{SECRET:PATHLYNKS_USER_PASSWORD}}`; the WORST case's wrong
password is the literal `Wr0ng-Password-Deliberately-Not-Real!`, correctly not a secret (no such
declared key). **F1 met** (unchanged from cycle 1, independently reread this cycle).

## F2 — headed browser, real evidence (re-verified)

`src/autotester/browser/session.py:68` (`launch_options`) sets `"headless": not project.headed`;
`run_pathlynks_first_cases.py::main` builds `headed_project = project.model_copy(update={"headed":
True})` and passes it to `BrowserSession`, while `projects/pathlynks/project.json` itself still
reads `"headed": false` (confirmed above). Read `run.json` in the cited cycle-2 run dir:
`trigger: manual`, all 3 case_ids present. Screenshots exist per step in the run directory
(01–13 numbered PNGs). **F2 met.**

## F3 — real judge, not mock (independently re-verified this cycle, the crux of this re-check)

Read all 3 `*.verdict.json` files in
`projects/pathlynks/runs/run-01M1K941M7AQ7RWMYPF378TDQT/` directly:

- `case_35b17ccece2d.verdict.json` (BEST) — `result: PASS`, `grader_provider: "gemini"`
- `case_a5ea57c0961a.verdict.json` (WORST) — `result: PASS`, `grader_provider: "gemini"`
- `case_b1cb019ebb56.verdict.json` (EDGE) — `result: PASS`, `grader_provider: "gemini"`

All 3 corresponding `RawResult` files (`case_*.json`, non-verdict) show `outcome: "completed"` for
all 3 cases, so per `grade.py`'s own logic (`grade()`: `BLOCKED_HITL`→`provider_id="rule"`,
`ERRORED`→`provider_id="rule"`, otherwise the real judge is called and `provider_id=judge.id`),
`grader_provider="gemini"` (never `"mock"`, never `"rule"`) is exactly correct for all 3 — none
was blocked or errored, so `"rule"` would have been a bug, and none of them show it.

Independently confirmed *why* "gemini" is the real winning tier, not a fabricated label: read
`.env` directly — `ANTHROPIC_API_KEY` is empty, `GEMINI_API_KEY` is set (39 chars). Read
`src/autotester/providers/langchain_fallback.py::_default_chain()`: the chain only appends an
`"anthropic"` tier when `ANTHROPIC_API_KEY` is truthy (it is not), and appends a `"gemini"` tier
when `GEMINI_API_KEY`/`GOOGLE_API_KEY` is truthy (it is) — so with today's `.env`, `"gemini"` is
structurally the first (and only) reachable tier. `LangChainFallbackProvider._try_tier` sets
`self.id = name` only after a real `model.invoke(prompt)` call returns a successfully-parsed
structured object — there is no path that stamps `"gemini"` without a real Gemini API round
trip. T-055 (the provider itself) already carries its own independent checker-PASS verdict at
`qa/verdicts/t055-langchain-fallback.md` (cycle 1, PASS, re-ran `tests/test_langchain_fallback.py`
fresh: 10 passed) — this check did not re-litigate T-055's own contract, only confirmed T-050's
specific 3 verdicts genuinely used it. **F3 met.**

## F4 — verdicts are defensible given the evidence (independently re-judged, not carried forward)

Read all 3 `RawResult` (non-verdict) JSON files directly:

- **BEST** (`case_35b17ccece2d.json`): final evidence entry is `{"kind":"url",
  "path":"https://pathlynks.vidysea.com/dashboard", "label":"post-submit URL"}` — genuinely
  unmasked (does not match any declared/undeclared secret pattern), landed off the sign-in page
  onto `/dashboard`. Verdict: `PASS`, `criteria_met: 1/1`, `failures: []`. Matches — a PASS here
  is the only defensible reading.
- **WORST** (`case_a5ea57c0961a.json`): final evidence entry is `{"kind":"url",
  "path":"[REDACTED]:PATHLYNKS_USER_LOGIN_URL", "label":"post-submit URL"}` — still masked as the
  sign-in page, i.e. the wrong-password attempt did not leave the login page. Verdict: `PASS`,
  `note`: "The final URL evidence confirms the browser remained on the sign-in page, meeting the
  landed criterion for a worst-case scenario." This correctly matches the rubric's own criterion
  text (`make_rubric()`: "For WORST/EDGE cases: the final URL evidence shows the browser is
  STILL on the sign-in page ... login was rejected") — the rubric defines "still on sign-in" as
  the PASS condition for WORST, and the judge's note cites exactly that evidence. Defensible.
- **EDGE** (`case_b1cb019ebb56.json`): final evidence entry is the same masked
  `[REDACTED]:PATHLYNKS_USER_LOGIN_URL` — still on sign-in after an empty submit. Verdict: `PASS`,
  `note`: "The final URL evidence shows the browser is still on the sign-in page, which satisfies
  the criterion for an edge case." Same reasoning, correctly matches its own cited evidence.

One observation, not a defect: `case_35b17ccece2d.verdict.json` (BEST) has no `note` field at
all, while WORST/EDGE do. Traced to `grade.py::_verdict`/`Judgment.note` being optional
(`note: str | None = None`) — the manifest's claim that "each [verdict cites] real evidence...
e.g. the WORST case's note" is accurate as written (it cites WORST specifically, not "all
three"), so this is not a manifest overstatement, just worth noting that BEST's PASS is
defensible on its own evidence (`/dashboard` landing) even without a textual note, since the
rubric has exactly one criterion (`landed`) and `criteria_met: 1/1` with an empty `failures`
list is internally consistent per `grade.py::_inconsistency`'s own self-consistency check
(`PASS but failures is non-empty` would have downgraded it to `INCONCLUSIVE` had it been
inconsistent — it was not). **F4 met** — all three verdicts are a defensible reading of their
own cited RawResult evidence; none contradicts what its evidence shows.

## F5 — zero secret hits, write policy respected (re-verified)

Covered above under re-run evidence: 1 reported hit, confirmed as the documented
`base_url`/`PATHLYNKS_USER_LOGIN_URL` false-positive class, not a real leak.
`write_policy=read_only` respected — traced `run_pathlynks_first_cases.py` and
`execute.py::run_case`: only `navigate`/`fill`/`click` actions against the login form; no
create/update/delete call anywhere in this unit's code path. **F5 met.**

## Result

VERDICT: PASS
SCOREBOARD: 5/5 criteria met, 0/0 invariants applicable this unit (dependency contracts not
re-litigated here — B1-B9/E1-E5/G1-G5/O1-O4 stay owned by their own contracts)
FAILURES: none
ISSUES-WRITTEN: none (AT-033 closed below, not superseded by a new issue)
EXPLANATION: All 5 criteria are independently reverified true on evidence this checker read
itself. F1/F2/F5 were already solid in cycle 1 and remain so. F3 is now genuinely met: all 3
verdicts carry `grader_provider="gemini"`, and tracing `.env` + `langchain_fallback.py`'s chain
construction confirms "gemini" is the structurally-correct, only-reachable real tier today (no
path exists to fabricate that label without a real API round trip) — T-055, the provider itself,
already carries its own independent PASS. F4 is met: each of the 3 verdicts' PASS result and
cited note (where present) matches its own RawResult evidence exactly — BEST's unmasked
`/dashboard` URL, WORST/EDGE's still-masked sign-in URL, both against the rubric's own explicit
"landed" criterion text. This closes AT-033 for real.

## Actions taken on PASS

- AT-033 flipped `open → fixed` in `qa/issues.jsonl`.
- Goal task T-050 closed via `goal_cli.py done`.
- `docs/FEATURES.jsonl` row appended (reason: first real, fully-graded end-to-end proof of the
  pipeline against a real product).
- `docs/SNAPSHOT.md` regenerated.
