# Verdict — t030-pathlynks-onboarding

**Date:** 2026-09-03
**Cycle checked: 3 (LAST — max cycles reached)**
**Contract:** qa/contracts/pathlynks-onboarding.md (O1-O4, O1 amended cycle 1) + qa/contracts/core-invariants.md (C1-C8) + qa/contracts/browser-and-secrets.md (B1-B9, dependency, already PASSed)

## Preliminary — independent verification of the maker's incident claim (AT-025 checker-reliability finding)

Before doing the normal Mode A check, this cycle independently verified the serious claim in the
manifest's incident section: that the cycle-2 verdict itself leaked a real secret, and had
incorrectly cleared other real values as coincidental.

1. `git log origin/master --oneline` confirms origin/master is still at `1a94b76`
   (`chore: regenerate docs/SNAPSHOT.md after D-007`) — nothing beyond that has ever been pushed.
   Both the original cycle-1 and cycle-2 verdict commits were local-only and are now superseded by
   a soft-reset; they never reached the public remote.
2. Read the current `qa/verdicts/t030-pathlynks-onboarding.md` (Cycle checked: 2, at commit
   `ba79617`) and `qa/issues.jsonl`'s AT-025 row in full. Independently loaded `.env` myself (own
   script, values never printed) and checked every file this unit touches — manifest, verdict,
   issues ledger, contracts, adapter, knowledge.md, run evidence directory, script, tests,
   project.json, docs/FEATURES.jsonl, docs/ARCHITECTURE.md, docs/SNAPSHOT.md, goal.md,
   `.goal/goal.json`, `.goal/dashboard.html`, `qa/.last-tick` — for every currently-real `.env`
   value, both byte-exact and dot-escaped forms, using both `scripts/check_no_secrets.py` and my
   own independent Python sweep (different code path, same `.env`-derived value list). Result: the
   only match anywhere is `projects/pathlynks/project.json`'s `base_url`, which equals the
   undeclared, non-sensitive `PATHLYNKS_USER_LOGIN_URL` value — the documented AT-004-style
   false positive, explicitly out of scope for a text-secret-scan under O2. No other file, current
   verdict included, contains any real secret value in either form.
3. `git log --all -p -S<value>` for all five real values (`PATHLYNKS_COUNSELLOR_EMAIL`,
   `PATHLYNKS_COUNSELLOR_PASSWORD`, `PATHLYNKS_USER_EMAIL`, `PATHLYNKS_USER_PASSWORD`,
   `GEMINI_API_KEY`), plain and dot-escaped where applicable, run against the full local history
   (`--all`, every branch/ref, not just HEAD) — zero matching commits for every value/form. Also
   checked `PATHLYNKS_MONGO_URI` and both `*_LOGIN_URL` values for completeness — zero matches.
   Confirms: no real secret was ever committed, locally or otherwise, past or present.
4. **Explicit note for the human, independent of this cycle's PASS/FAIL:** this incident is a real
   finding about checker reliability, not just maker discipline. A prior checker instance's own
   cycle-2 verdict quoted a real secret verbatim in its own explanatory prose while narrating the
   finding, and separately misjudged three other real values as "coincidental, not a leak" — one
   escaped a byte-exact check only because it appeared in a trivially dot-escaped form. The
   maker's fix (this cycle's tightened `scripts/check_no_secrets.py`, which now checks both plain
   and dot-escaped forms and never accepts/prints a value as an argument) is a structural fix to
   that class of near-miss, not just a redaction of the one instance found. Any checker verdict
   that quotes a real value verbatim "for clarity" is itself a leak and should be treated as such
   going forward — describe findings by key name, never by value, in verdict prose.

Both prior leaking commits were confirmed never pushed; the working tree and full local history
are confirmed clean as of this cycle. This is stated here for the human's awareness per the
dispatch brief, separate from the criteria judgement below.

## Mode A check — re-run myself

- `uv run pytest -q` → 74%+100% dot bands, all passed, matches manifest's claim.
- `uv run ruff check src tests scripts` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` → 138 (≤150, C2 holds).
- `git ls-files | grep -E "\.env$"` → no output; `.env` never tracked.
- `uv run python scripts/check_no_secrets.py <every file this unit touches>` → the tool's own
  source was read line-by-line and confirmed to do what it claims: it loads `.env` itself via
  `autotester.browser.secrets.parse_env`, never accepts or prints a value, checks each value's
  plain and dot-escaped form, and exits 1 iff any target file's text contains one. Re-ran it
  myself over the manifest, verdict, issues ledger, contracts, adapter, knowledge.md, the full run
  evidence directory (all 3 screenshots — binary, content-skipped, filenames checked), script, and
  tests: 0 leaks. `project.json` was scanned separately (excluded from the manifest's own claim,
  per this unit's documented scope note) — its one hit is `base_url` matching the undeclared,
  non-sensitive `PATHLYNKS_USER_LOGIN_URL`, exactly as the manifest states; not a defect.
- Independent cross-check (my own script, not `check_no_secrets.py`'s code path): same result,
  zero real-secret matches in any target file, plain or dot-escaped.
- Full local git history (`git log --all -p -S<value>`) for all five real values: zero commits,
  past or present, confirming no secret was ever committed even transiently.

## O1 — PASS (fixed, this time structurally)

The literal `PATHLYNKS_COUNSELLOR_PASSWORD` value that leaked into the manifest's "Evidence sweep"
grep alternation in cycle 2 is gone. The manifest no longer hand-types any `.env` value anywhere —
the "Evidence sweep" section now only presents `check_no_secrets.py`'s own output (a count, never a
value), and the tool itself is structurally incapable of printing a secret (verified by reading its
47-line source in full). Both classes of leak found across cycles 1-2 (narrative prose, and a
hand-typed "example pattern" list) are addressed by the same root-cause fix: no file this unit
authors by hand ever contains a `.env` value literal again, checked mechanically rather than by
discipline. Confirmed independently, not by re-trusting the manifest's own claim.

## O2 — PASS

`projects/pathlynks/project.json` validates: `slug="pathlynks"`, `base_url` on `vidysea.com`,
`allowed_domains=["vidysea.com"]`, `write_policy="read_only"`, `headed=false` (explicit). `secrets[]`
declares exactly the 5 keys present in `.env` for this project, each scoped to `vidysea.com`.

## O3 — PASS

`scripts/onboard_pathlynks.py` (read in full, 142 lines) calls `session.fill()` only with
`{{SECRET:KEY}}`-style placeholder strings for both email and password fields — no literal ever
appears in the script's own source. 3 masked screenshots exist under
`projects/pathlynks/runs/onboard-01M1JQDHA8296D4EQ484CPKP1Z/`; `03-post-login.png` reviewed as an
image shows a "Logged in successfully" toast over a real authenticated dashboard, not a
signin-page bounce-back. `write_policy=read_only` respected — only the login submit occurred.
Independent secret sweep of the run directory and knowledge.md: 0 matches.

## O4 — PASS

`projects/pathlynks/knowledge.md` exists, follows the `/portal-explorer` template shape (Quick
Re-Run, Portal Profile, How it works, Screens reached, Gotchas, Change detection, History), records
the `user` role, login URL context (via project.json, correctly not restated as a literal where it
overlaps a declared secret), screens reached, and notes no 2FA/OTP was observed.

## C1-C8 — hold

`uv run pytest -q` (schema/core tests included), `uv run autotester doctor` (C2/C3/C4), `git ls-files
| grep -E "\.env$"` (C5, no output), `uv run ruff check` all pass. No vendor SDK imported directly
in this unit's script (`grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/` —
unaffected by this unit, still returns nothing). Artifacts are plain files under
`projects/pathlynks/`. All 8 invariants hold.

## Issue ledger

AT-025 (critical, reopened cycle 2) — verified fixed this cycle: the literal value is gone from
every file this unit touches, confirmed independently as above. Flipped `open → fixed`.

## docs/FEATURES.jsonl F-004

Row present, `unit: T-030`, `user_value: high`, reason is real and specific ("first proof the
whole credential boundary (T-011+T-010) holds against a real product, not just fixtures") — not an
auto-stamp. Confirmed.

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 8/8 invariants hold
FAILURES (if any): none
ISSUES-WRITTEN: none new; AT-025 flipped open->fixed
EXPLANATION: Cycle 3's fix is structural, not another spot-redaction: check_no_secrets.py loads
.env itself, checks plain and dot-escaped forms, and never accepts or prints a value, so the class
of defect that recurred twice (a hand-typed secret literal in maker-authored prose, disguised once
as narrative and once as a "pattern") cannot recur through this manifest's own evidence section
again. Independently re-verified with my own separate sweep and full local git history search
(git log --all -p -S<value> for all five real values, plain + dot-escaped): zero matches anywhere,
past or present, pushed or local. O2-O4 independently confirmed clean. Separately: this cycle also
confirmed the maker's incident claim about the checker's own cycle-2 verdict leaking a real value
and misjudging three others as coincidental — origin/master was never touched (still at 1a94b76),
both leaking commits were local-only and are now superseded by a clean soft-reset + recommit. This
is flagged for the human as a genuine checker-reliability finding, independent of this PASS.
```
