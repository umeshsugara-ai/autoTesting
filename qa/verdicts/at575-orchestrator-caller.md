# Verdict — at575-orchestrator-caller

**Date:** 2026-09-25 · **Head checked:** 9bfcd8e (code 26d7d93, base master 76dfbde) · **Cycle checked: 1** (manifest Fix cycle: 1 of 3) · **Issues addressed (claimed):** AT-575

```
VERDICT: FAIL
SCOREBOARD: AT-575 expected clause met (a real CLI entry point drives run_or_resume, tested through the CLI; secrets reach StageContext; resume after interruption proven through the entry point; D-018 consent before any trace); C3 / design rule "one concept, one place" not met
FAILURES:
- [C3 / design rule "a class or function defined in two modules is a bug"] sev: medium · cli_orchestrate.py::_require_crawl_consent is a statement-for-statement copy of cli_crawl.py::_preflight_consent (checker AST comparison: statement bodies identical, same parameters; only the name and docstring differ). It's the D-018 consent gate, a security check, now in two copies that will drift the first time one is tightened. The module docstring also claims the existing primitives are "reused as-is", which isn't true of this one. doctor misses it because its duplicate rule matches public names only and these are private and differently named. · fix: delete _require_crawl_consent and call cli_crawl._preflight_consent (import it, or move it to a shared spot both commands import); keep test 4 as is, it will still pin exit 2 with no trace. · issue: AT-575 (stays open)
CAPABILITY-COVERAGE: 3/3 re-run rows reproduced (2, 3, 4), each in its own throwaway copy; green before, red on the named assertion after. Row 1 (command unmounted) is self-evident and wasn't re-run.
LIVE-BROWSER: not-applicable (changed paths: src/autotester/cli.py, src/autotester/cli_orchestrate.py, tests/test_cli_orchestrate.py, docs/MAP.md; no UI route, no template)
ISSUES-WRITTEN: none
EXECUTOR: claude-sonnet-subagent (checker: claude-opus-session, checker seat)
EXPLANATION: Everything AT-575 asks for works and is proven through the real CLI entry point. The one defect is a copied security gate where the existing one should be called, which is cheap to fix. Nothing else blocks.
```

## Questions (not failures)

1. **Resume in explore mode re-runs the consent preflight** even when DISCOVER is already done and only MODEL remains. `require_consent` doesn't use up the approval, so it costs nothing while the approval is valid, but an expired approval would block a resume that will never open a browser. Intended?
2. **Mode is recomputed on resume.** `choose_mode(sources)` builds the runner dict from the current sources, while `run_or_resume` resumes from the stored state's mode. If a teaching source is added or removed between two invocations with the same `--run-id`, the runners can mismatch the stored stages. Worth a guard: build runners from the stored state's mode when resuming.

## The maker's flags

- **(a) Capability rows done in place in the committed worktree:** the tree is clean at 9bfcd8e (`git status` empty), but this is the third time (at560, at576-577, at575). I reproduced rows 2-4 myself in separate copies. Rows belong in throwaway copies only.
- **(b) Two consent seams:** confirmed. Row 4 (preflight removed) goes from exit 2 to exit 1, with "discover failed — ApprovalRequired" as a failed checkpoint. The deeper `run_crawl` gate still refuses, but AT-111's "a refused run leaves no trace" is lost. So the preflight is load-bearing, which is exactly why it must be the one shared function and not a copy.
- **(c) Full suite:** I ran it; see below.

## What I re-ran

- `ruff` clean · `doctor` clean (copy).
- Targeted: `test_cli_orchestrate.py` + `test_orchestrate.py` + `test_orchestrate_runners.py` -> `14 passed`.
- **Every non-browser test file** (copy): `1 failed, 1570 passed, 5 skipped`; the one failure is the `.git`-dependent `test_uploaded_recordings_are_gitignored`. Net: all green.
- Row 2 (`run_id or` dropped): `assert None is not None` (state.json never lands at the requested run dir), in the resume test and the fresh-run test.
- Row 3 (`secrets=` dropped): "StageContext fell back to an unredacted Redactor({}) — RT6 gate is dark".
- Row 4 (preflight removed): `assert 1 == 2`, "discover failed — ApprovalRequired … no approval exists".
- Duplicate check: AST statement bodies of `cli_crawl._preflight_consent` and `cli_orchestrate._require_crawl_consent` are identical.
- Diff scope 76dfbde..26d7d93: 4 files + MAP regeneration, all listed; the only removed line is cli.py's import line (widened).

## Status: FAIL (cycle 1) — maker fix cycle 2.
