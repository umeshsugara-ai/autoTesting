# Verdict — at283-agents-md-root-clutter

**Date:** 2026-09-11
**Cycle checked:** 1
**Contract:** qa/contracts/core-invariants.md (C4 — repo root stays clean)
**Manifest:** qa/manifests/at283-agents-md-root-clutter.md

## What I re-ran myself

Note on state: at dispatch time, `git status` on the live tree no longer showed
`src/autotester/doctor.py` / `tests/test_doctor.py` as modified — the maker had already committed
the fix as `dd2ab83` ("fix(AT-283): AGENTS.md is a real instruction file, not root clutter") while
this check was starting. I verified this was the same diff described in the manifest
(`git show dd2ab83 -- src/autotester/doctor.py tests/test_doctor.py`) and checked HEAD rather than
a stale local diff.

- **Live tree:** `uv run autotester doctor` → `doctor: clean`, exit 0. `uv run ruff check src
  tests scripts` → `All checks passed!`, exit 0. `uv run pytest -q` (full suite, ran in background
  due to the 120s tool timeout, 2m+ wall time) → completed, `PYTEST_EXIT: 0` (1 skipped, rest
  passed/deselected, no failures).
- **Sabotage (C7), own isolated extract, never the live tree:**
  1. `git archive HEAD | tar -x` into a fresh scratch dir. Confirmed `HEAD` = `dd2ab83` (the fix
     commit) — so the extract already carried the fix baked in, no `git apply` needed.
  2. `uv sync` inside the extract; confirmed `uv run python -c "import autotester;
     print(autotester.__file__)"` resolved to a path **inside the scratch extract**, not
     `D:/autoTesting`.
  3. Baseline: `uv run pytest tests/test_doctor.py -q` → `.......` 7 passed, exit 0. Matches the
     manifest's claimed baseline exactly.
  4. Reverted the allowlist entry (removed `"AGENTS.md"` from `ALLOWED_ROOT_ENTRIES`, the exact
     inverse of the fix) via Edit on the extracted copy only.
  5. Re-ran: `......F` — **exactly one failure**,
     `test_a_second_ai_tools_instruction_file_is_not_root_clutter`
     (`AssertionError: assert not True`), the other 6 stayed green. This is precisely the predicted
     result and matches the manifest's own reproduction narrative, independently reproduced.
- Confirmed the changed paths are `src/autotester/doctor.py` and `tests/test_doctor.py` only
  (`git show dd2ab83 --stat`) — no UI/route/template touched, so Mode D does not apply. Manifest's
  "not UI-touching" claim confirmed from the changed paths myself, not trusted.
- Read `AGENTS.md` at the repo root: it is a real, substantive Codex-CLI project-instruction file
  mirroring `CLAUDE.md`'s content (router table, design rules, commands) with tool-appropriate path
  substitutions — not scratch, not evidence, consistent with the manifest's characterization.
- Cross-checked the ledger: AT-283 was `open` (found_by checker-sweep); AT-336 was already
  `dismissed`/`duplicate_of: AT-283` by an earlier checker run (at255-256-280-ledger-reconcile
  cycle), so no action needed there. I flipped AT-283 `open → fixed` in `qa/issues.jsonl` with a
  `checker_note` citing this verdict (only a later re-check may move it `fixed → verified`, per
  protocol — not done here).

## Criteria judged

- **C4 (repo root stays clean):** MET. `ALLOWED_ROOT_ENTRIES` now includes `AGENTS.md` alongside
  the pre-existing `CLAUDE.md`; `doctor` reports clean; a stray file (e.g. a log) still trips
  `root-clutter` per the pre-existing `test_root_clutter_is_flagged`, unaffected by this change.
- **C2 (readable, size limits):** MET. `doctor.py` is 193 lines (was ~190), `test_doctor.py` is 66
  lines — both well under the 300-line cap; the added test is well under 50 lines.
- **C7 (verification independent, sabotage-assertion / zero-failure / baseline clauses):** MET,
  per the independent re-run above — anchor matched once, file changed, non-zero-failure result
  attributed to the correct named test, baseline confirmed green first.
- **C3 (one concept, one place):** No new duplicate definition introduced by this diff.

## On the "should this have been gated" question

Formed an independent view, since the dispatch asked for one: **no, this did not need a
HUMAN_GATE**, and it is not really the same shape as AT-110 or AT-253.

AT-110 and AT-253 are both gated because closing them **unilaterally picks a side of a real
product tradeoff with an ongoing cost**: AT-110 is a cryptographic-strength/security-posture
choice (keyed HMAC vs. accepted "evidence not proof" posture); AT-253 would turn on real model
calls with real latency/cost on every broken case, changing runtime behaviour going forward. Both
gates explicitly reason from "this changes runtime/security behaviour," not from "this touches the
declared layout."

AT-283 has neither property. `AGENTS.md` already existed at the repo root, untracked, before this
unit — the manifest states it was "supplied for D:/autoTesting and explicitly not to be edited or
removed," i.e. its presence was already a settled fact, not something this unit introduced. The
change only corrects `doctor`'s allowlist to match a file that already exists and was already
sanctioned, symmetric to how `CLAUDE.md` (a different AI tool's identical-purpose file) is already
allowed. It changes no runtime behaviour, no security posture, and is fully reversible by editing
one set literal. I also checked the one on-disk precedent for this exact mechanism — D-0xx (the
video-learning decision) authorized `ALLOWED_ROOT_ENTRIES += plan.md` as one bundled line item
inside a larger feature decision, not as its own standalone gate — so the repo's own history treats
allowlist entries as ordinary, bundleable changes, not gate-worthy on their own.

One thing worth a human look, though not a contract violation and not blocking this PASS:
`AGENTS.md`'s content substantially duplicates `CLAUDE.md`'s content (router table, design rules,
commands, with tool-specific path edits) rather than one file referencing the other. That is a
content-drift risk in spirit close to C3 ("one concept, one place") even though C3's text and its
`doctor.py` instrument are scoped to Python symbols, not markdown. Not filing this as an issue —
it is a suggestion for future work no criterion requires (no-fire list item 4), surfaced here only
because the dispatch asked for an independent opinion on the surrounding decision.

VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 0/0 additional invariants at issue
FAILURES (if any): none
LIVE-BROWSER: not-applicable (src/autotester/doctor.py, tests/test_doctor.py — no UI/route/template changed)
ISSUES-WRITTEN: none (AT-283 status flipped open → fixed in qa/issues.jsonl; AT-336 already dismissed by a prior checker)
EXPLANATION: Independently reproduced in a fresh isolated git-archive(HEAD) extract with its own uv venv — module resolved inside the extract, baseline 7/7 green, reverting the allowlist entry failed exactly the one predicted test. Full live-tree suite (doctor, ruff, pytest -q) all green. Not a HUMAN_GATE-shaped decision like AT-110/AT-253: no runtime-behaviour or security-posture tradeoff, just correcting the allowlist to match an already-sanctioned, pre-existing file.
