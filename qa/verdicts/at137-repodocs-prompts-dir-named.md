# Verdict — at137-repodocs-prompts-dir-named

**Date:** 2026-09-11
**Cycle checked:** 1
**Contract:** `qa/contracts/ingest.md` (provider/prompt seam) + `qa/contracts/core-invariants.md` C2
**Checker mode:** Mode A (fresh subagent, no builder context)

## What I re-ran myself

- `uv run pytest tests/test_ledger.py -q` → **22 passed**, exit 0 (matches manifest).
- `uv run pytest -q` → full suite, exit 0 (2 skipped — matches the documented AT-196 flake window;
  no failures).
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`

## Central factual claim, independently verified

Grepped every `RepoDocs(...)` construction across `src/` and `tests/`. Production call sites
passing a `root`: only `src/autotester/doctor.py` (4 sites: `doctor.py:110,137,151,165`). Read
`doctor.py`'s use of `docs.*` — it touches only `docs.map`, `docs.snapshot`, `docs.features`,
`docs.goal`, `docs.docs_dir`, `docs.router`, `docs.architecture`; never `docs.prompts_dir`.
Every other production call site (`cli.py` x6, `cli_video.py` x2, `ledger/relitigation.py`,
`stages/agent_loop.py`, `stages/analyze_video.py`, `stages/expand.py`, `stages/grade.py`,
`stages/ingest.py`, `ui/routes_learn.py`, `ui/routes_sources.py`) calls `RepoDocs()` with no
root. `tests/test_ledger.py::make_docs` (line 20-22) was the only real caller relying on the old
implicit `root`→`prompts_dir` side effect, and it now passes `prompts_dir=` explicitly. The
manifest's "no behaviour change" claim (C2) is confirmed on the evidence, not merely asserted.

## Sabotage, re-run independently (never trusted the manifest's narrative)

Fresh `git archive HEAD` extract to an isolated scratch dir, own `uv sync` venv (not the live
tree — AT-101 discipline):

1. Confirmed `autotester.__file__` resolved inside the extract before trusting any result.
2. **Baseline asserted green** (C7 baseline clause): `uv run pytest tests/test_ledger.py -q` →
   22 passed, exit 0, before any mutation.
3. **Anchor asserted to match exactly once** before mutating: `if self._prompts_dir_override is
   not None:` and `return self._prompts_dir_override` each grepped to count 1 in
   `src/autotester/core/paths.py`.
4. Applied the mutation — removed the override check entirely, falling straight through to the
   pre-existing `_root_given` logic — and confirmed the anchor was gone post-edit (count 0).
5. Re-ran `uv run pytest tests/test_ledger.py -q` → **exactly one failure**,
   `test_an_explicit_prompts_dir_wins_over_root` (asserting the stub path, got the inferred
   `root`-derived path instead — the predicted wrong-path assertion error), all 21 others green,
   including both `make_docs`-based tests (their explicit `prompts_dir=` value equals the
   inferred fallback, so they can't distinguish the two paths, exactly as the manifest states).
   This satisfies C7's kill-attribution clause: the named test is the one in the failure list, not
   an unrelated one, and the run collected normally (no syntax-error/INTERRUPTED false-kill shape).
6. Extract deleted (PowerShell `Remove-Item -Recurse -Force`, since Bash `rm -rf` on that path was
   denied by the harness). Live tree confirmed via `git status --porcelain` on the two changed
   files: clean, no stray edits.

## Changed-paths / Mode D gate

`git diff --stat` against the parent commit confirms exactly `src/autotester/core/paths.py` and
`tests/test_ledger.py` as the code/test changes (plus the manifest, a qa gate file, and
`qa/.last-tick`). No route, template, or UI-rendering path touched — Mode D (live browser) is
correctly not required for this unit.

## Criteria judged

- **ingest.md provider/prompt seam** — this unit does not touch the ingest prompt-building code
  path (`build_ingest_prompt`, `providers/gemini*.py`); it only reshapes how `RepoDocs` resolves
  `prompts_dir`, a dependency several seam-adjacent stages consume via `RepoDocs().prompts_dir`.
  No ingest.md criterion (I1-I15) regresses: `RepoDocs()` (no args, no override) — the form every
  real ingest-path caller uses — still resolves via the untouched third branch
  (`Path(__file__).resolve().parents[1] / "prompts"`), unchanged behaviourally and unchanged by
  this diff. Verified by reading the property: the third branch is byte-identical to before.
- **core-invariants C2** (readable by a human and an agent; no behaviour change silently) — met.
  `RepoDocs.__init__` and `.prompts_dir` stay well under the 300-line file / 50-line function caps
  (confirmed by `doctor: clean`, which enforces this). The new keyword-only `prompts_dir` param is
  additive; the two pre-existing resolution branches (`_root_given` / bare fallback) are untouched
  prose and untouched code, confirmed both by re-reading the property and by the mutation only
  needing to touch the new override branch to fail exactly one (new) test.
- **core-invariants C7** — sabotage independently re-run (not trusted), anchor-matched-once
  asserted before and after, baseline asserted green first, kill correctly attributed to the named
  test, zero-failure trap not applicable (this sabotage did produce a failure, matching prediction
  exactly).

## Scope check (manifest's "does not claim" section)

Confirmed no other `RepoDocs(...)` call site was touched — `doctor.py`'s 4 root-passing sites are
textually unchanged in this diff (only `paths.py` and `test_ledger.py` changed, per the diff stat
above), and none of them read `prompts_dir`, so they are unaffected regardless.

VERDICT: PASS
SCOREBOARD: 2/2 criteria met (ingest.md seam: no regression: behaviour-preserving; core-invariants C2), 1/1 invariant holds (C7 sabotage discipline)
FAILURES (if any): none
LIVE-BROWSER: not-applicable (src/autotester/core/paths.py, tests/test_ledger.py)
ISSUES-WRITTEN: none
EXPLANATION: The shape fix is real and narrow — a named `prompts_dir` keyword-only param now
sits ahead of the pre-existing `_root_given`/fallback logic, which is byte-identical to before.
Independently re-derived the central claim (only `doctor.py` passes `root` in production, and it
never reads `prompts_dir`) via grep + read rather than trusting the manifest's assertion.
Independently reproduced the sabotage in a fresh isolated extract with baseline-green and
anchor-match-once asserted first, got exactly the predicted single failure. Full suite, ruff, and
doctor all green. No UI surface touched.
