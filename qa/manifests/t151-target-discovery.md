# Manifest — t151-target-discovery
**Contract:** qa/contracts/ai-target.md (AI1, AI8 bind T-151; core-invariants C5/C7)
**Goal task:** T-151
**Date:** 2026-10-07
**Fix cycle:** 1 of max 2
**Dual check:** required   <!-- credential refusal, path-escape and approval gating are a security boundary -->
**Persona walk:** skip (backend-only: no human screen; Track C below-the-UI discovery)
**Issues addressed:** none
**Executor:** claude-sonnet-subagent
**Executor rationale:** plan-review fixes applied by a maker subagent in the t151 worktree; no external executor worthy.

## What changed
- src/autotester/schema/ai_target.py (new, 122 lines) — Signal/ReadScope/ScanLimits/Classification models, all `extra="forbid"` (authorized by D-017 What).
- src/autotester/stages/discover.py (new, 287) — deterministic scan with file:line signals; `classify_target` names the kind through `Provider.act` (D-017: model names, never chooses checks).
- src/autotester/stages/read_context.py (new, 147) — Markdown frontmatter+tags only; no backlink graph, no Dataview, no vault-index library.
- src/autotester/prompts/ai_target_classify_v1.md (new, 7) — classify prompt file. **Not yet authorized on disk.**
- src/autotester/providers/mock.py:55-70 — `act` hunk only (deterministic Classification when no response is queued). Unrelated signature reflow reverted. **Not yet authorized on disk.**
- pyproject.toml / uv.lock — `pyyaml==6.0.3`. **Not yet authorized on disk.**
- tests/test_discover.py (new, 300) — 63 cases; SIM105 fixed with `contextlib.suppress`.
- Removed from this branch as non-T-151: D-061 (AT-113) and F-067 (T-171) hunks; docs/DECISIONS.md and docs/FEATURES.jsonl now equal master bd2fe8f4.

## Verification scope
Policy-Version: proportional-verification/2026-10-06.6
Tier: L (dependency bump + credential, path-escape and approval boundary)
Base / checked state: master bd2fe8f4 + branch codex/t151-target-discovery HEAD (re-bind SHA and dirty diff hash at Mode A)
Gate answers: OPEN HUMAN_GATE `qa/gates/t151-dependency-authorization.md` (on master): pyyaml dependency, prompt file, mock.py `act` hunk. Required change 3 (DECISIONS entry) waits on the answer. No ready-for-check until it is answered.
Affected tests / full-suite trigger: tests/test_discover.py only (63). The builder runs no full suite; the checker decides on the full-suite trigger (new dependency touches uv.lock).
Metrics: start=2026-10-07T00:00:00Z end=2026-10-07T00:30:00Z wall_min=30 agent_min=unavailable blocked_min=0 suite_runs=0 repeat_runs=0 mutations=0 cycle=1 resumes=0 tokens=unavailable policy=2026-10-06.6

## How to verify (commands + expected)
- `uv run ruff check src tests scripts` → expected: All checks passed
- `uv run pytest tests/test_discover.py` → expected: 63 passed
- `uv run autotester doctor` → expected: no T-151 violation (8 violations are pre-existing on master bd2fe8f4: D-061 cited by AT-733/AT-113/SNAPSHOT docs whose entry is only in root's uncommitted tree, ledger-row-missing T-171, stale SNAPSHOT)
- `grep -rniE obsidian pyproject.toml` → expected: no output, exit 1

## Actual outputs (from maker's own run, 2026-10-07)
- ruff: `All checks passed!`
- pytest tests/test_discover.py: `63 passed in 0.99s`
- doctor: `8 violation(s)`, none in T-151 files (cap check: discover.py 287, read_context.py 147, ai_target.py 122, test_discover.py 300 lines).
- obsidian grep: no output, exit=1.

## Capability coverage (each new claim -> its isolating falsification)
Falsification evidence is reused from independent checker runs (no new mutation groups). Some named defenders (test_target_is_never_executed_before_import, test_reader_signal_lines_match_exact_source, test_noncyclic_alias_exact_refusal, test_denial_class_and_formatted_chain_are_safe, G4-*) are checker scratch oracles run against the same source, not nodes of tests/test_discover.py. Records: `qa/verdicts/t151-target-discovery-repair-scoped-cycle1.md` (groups 2-4) and the retained results.json files under `qa/evidence/t151-independent-*-2026-10-05/`. Planning prose: `.work/t151-planning-notes.md` (gitignored).

| Criterion | capability | the check that covers it | the falsifying edit | observed |
|---|---|---|---|---|
| AI1 | every Signal names a real file:line | test_signals_match_real_lines_without_importing_target; test_reader_signal_lines_match_exact_source (verdict group 2) | scan citation line +1; reader metadata line +1 | baseline 65 passed -> KILLED (3 failures; reader line mutant 1 failure) -> restore 65 passed |
| AI1 | no Provider call on the signal-emission path | test_discovery_never_calls_provider | inserted `Provider.act` into scan; into read_context | KILLED (21 and 25 failures) -> restore green. Literal Verify grep hits `classify_target` (naming, D-017 authorized); checker amends AI1 Verify scope at Mode A |
| AI1 | target code is parsed, never executed | test_target_is_never_executed_before_import | `exec(text)` before AST parse | KILLED, 10 failures, exact sentinel RuntimeError |
| AI8 | frontmatter and tags only; no backlink graph, no Dataview, no vault-index dependency | test_context_is_metadata_only_and_secrets_are_scrubbed; G4-22..24 body/backlink/Dataview exclusion (verdict group 4) | persist body text; emit backlink names; admit non-Markdown | 28/28 single-hunk mutants KILLED, 34 baseline cases green before and after; `grep -rniE obsidian pyproject.toml` exit 1 |
| C5 secrets | dirty signal and encoded root secret refused before any provider call | test_dirty_signal_is_refused_before_provider; test_non_ai_encoded_root_secret_is_refused | remove dirty-signal guard; remove non-AI root guard | results.json: both KILLED, attributed=True, baseline 35 passed, restored 35 passed |
| C5 secrets | metadata and provider errors never echo a raw secret | test_context_is_metadata_only_and_secrets_are_scrubbed; test_provider_error_never_echoes_raw_secret | disable metadata literal scrubbing; disable ProviderError sanitization | both KILLED, attributed=True |
| C5 / approval | signed READ approval and scope preflight before any file open | test_all_roots_are_preflighted_before_any_open; test_denial_class_and_formatted_chain_are_safe | disable scope preflight; approval-exception sanitation | scope-preflight KILLED (cycle1); approval-exception KILLED (repair-results.json, 77 baseline -> restored 77) |
| C5 / bounds | physical read budget and final deadline are visible, never silent | test_rejected_files_still_consume_physical_read_budget; test_final_parser_overrun_is_not_complete | disable physical-byte accounting; disable final deadline (scan and context) | physical-budget, scan-final-deadline, context-final-deadline all KILLED |
| C5 / YAML | alias, depth and node bombs refused; safe_load only | test_unsafe_or_excessively_nested_yaml_is_refused; test_noncyclic_alias_exact_refusal | delete AliasEvent detection | alias-independent-results.json: baseline pass -> 1 failed -> restored pass (initial cycle1 run INCONCLUSIVE, superseded by this isolated proof) |
| C5 / path-escape | symlink and junction escape refused | test_symlink_escape_is_refused | none run | UNVERIFIED -- native symlink/junction escape mutation not run (verdict matrix marks it UNPROVEN) because the mutation needs a real reparse point; carried to Mode A, no issue id yet |
| (dependency) | pyyaml==6.0.3 is the only new dependency | pyproject.toml:26 | n/a | HUMAN_GATE open (qa/gates/t151-dependency-authorization.md) |

## Live browser evidence
Not UI-touching — no surface changed (src/autotester/schema/ai_target.py, stages/discover.py, stages/read_context.py, prompts/ai_target_classify_v1.md, providers/mock.py, tests/test_discover.py, pyproject.toml). Discovery reads local Markdown and code files only; no browser, network or live model.

## Evidence kept / removed
Kept: results.json per run, probe/mutation scripts, native-tool-receipt.md and the verdicts. Removed (git rm, commit e7033787): 87 raw per-test XML/txt dumps from the four t151-* evidence directories.

## Status: building
