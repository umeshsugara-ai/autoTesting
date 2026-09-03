# Contract — First real Pathlynks run (T-050)

**Covers:** goal task T-050. **Owner:** /checker. **Criticality:** HIGH — the first proof the
whole pipeline (project → case → execute → grade) closes end-to-end against a real product in a
real, visible browser, not just fixtures. Directly gates T-090/T-100/T-110/T-120.
**Depends on:** `core-invariants.md` (all), `browser-and-secrets.md` (B1-B9), `pathlynks-onboarding.md`
(O1-O4, dependency — same credential boundary), `execute.md` (E1-E5), `grade.md` (G1-G5).

## Purpose

Hand-write 3 Pathlynks login cases — one per kind (`best`/`worst`/`edge`) — run each through
`stages/execute.py::run_case` in a **headed, visible** browser (Umesh's explicit per-use
approval, 2026-09-03), and grade each through `stages/grade.py::grade` with a **real** judge
provider (not `MockProvider`). This is the "3 hand-written Pathlynks cases (best/worst/edge)
verdicted in a headed browser" the goal task names, and the north star's first real data point
(bugs found / false-positive rate / time all become measurable only once real verdicts exist).

## Human gate cleared

Umesh approved the live run explicitly this session (AskUserQuestion: "T-050 needs to run 3 real
cases... Proceed now, or build a different unblocked unit first?" → "Yes, run it now, headed").
`headed=True` is applied as an in-memory override for this run only — `projects/pathlynks/project.json`
itself is not mutated (stays `headed=false`, the unattended-run default), matching T-030's own
note that "a future human-supervised exploration can override per-run."

## Criteria

### F1 — Three real cases, one per kind, content-addressed
`projects/pathlynks/cases.jsonl` gains exactly 3 `Case` rows via `ProjectStore.add_case`:
`kind=BEST`/`case_class=HAPPY` (correct email+password → dashboard), `kind=WORST`/
`case_class=AUTH_WRONG_CREDS` (correct email, deliberately wrong literal password → login
rejected), `kind=EDGE`/`case_class=INPUT_EMPTY` (submit with both fields empty → client-side
validation, no navigation). No case's `steps` contains a raw secret literal — only
`{{SECRET:KEY}}` placeholders for the real credential, and a plain (non-secret) literal for the
deliberately-wrong password.

### F2 — Each case actually ran in a headed browser with real evidence
A `Run` row (`trigger=MANUAL`) plus 3 `RawResult` rows exist under
`projects/pathlynks/runs/<run_id>/`, each with `evidence` containing at least a screenshot per
step and the launch was genuinely headed (`headless: False` in the session's actual
`launch_options()` call for this run, confirmed by the maker's own run log — not merely claimed).

### F3 — Each case is graded by a real provider, not the mock
`stages/grade.py::grade` is called once per case with an `AnthropicProvider` (or another
non-mock provider actually available in this environment) as the judge — `Verdict.grader_provider`
is never `"mock"` for any of the 3 verdicts, and never `"rule"` unless that case's `Outcome` was
genuinely `BLOCKED_HITL`/`ERRORED` (G2's existing deterministic short-circuit, unchanged by this
contract). A `projects/pathlynks/runs/<run_id>/<case_id>.verdict.json` exists per case.

### F4 — The verdicts make sense given what actually happened
This criterion is judged, not computed: the checker reads each case's real evidence (screenshots,
the captured post-submit URL) and confirms the `Verdict.result` is a defensible reading of it —
the BEST case landing on `/dashboard` should not verdict FAIL; the WORST case never leaving the
sign-in page (or showing a rejection) should not verdict PASS on "successfully logged in." A
verdict that contradicts its own cited evidence is a finding, not a pass.

### F5 — Zero secret hits, write policy respected
`scripts/check_no_secrets.py` run over every file this unit touches (manifest, run evidence
directory, cases.jsonl, verdict files) reports 0 leaks. `write_policy=read_only` is respected —
only login-form submits happened; no data was created, edited, or deleted in the target product.

## No-fire list

- Coverage/screen-diff reporting (T-090's job — this unit runs 3 hand-written cases, it does not
  discover new ones).
- A UI report view (T-100).
- The counsellor role, or any flow beyond login (a follow-up, not blocking this unit — same
  scoping T-030 used: "one is enough to prove the mechanism", extended here to "one role, one
  flow, three case kinds").
- Vision/image content actually reaching the judge — `AnthropicProvider` sends text-only prompts
  (per `agent-loop.md`'s no-fire list); the judge reasons from the evidence *list* (screenshot
  filenames, the captured post-submit URL string, DOM action descriptions), not pixel content.
  The captured URL is the primary discriminating signal for this contract's cases by design.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-050 — no contract existed before this cycle.
