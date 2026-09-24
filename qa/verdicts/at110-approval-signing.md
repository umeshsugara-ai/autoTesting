# Verdict — at110-approval-signing

**Date:** 2026-09-24 · **Checker:** /checker Mode A + Mode D, sole direct checker (in-session, real re-runs + real browser) · **Bound root:** D:/autoTesting/.worktrees/at110-approval-signing
**Cycle checked: 1** (manifest Fix cycle: 1 of 3) · **Dual check:** no
**Executor independence:** manifest Executor = claude-sonnet-subagent; checker = claude (different context, not the writer) — self != executor holds; no ANTHROPIC_BASE_URL override.

## VERDICT: PASS

```
VERDICT: PASS
SCOREBOARD: CN3 met (forgery now resisted by a keyed HMAC + the mandated overclaiming-prose correction); CN1–CN2, CN4–CN9 not regressed (targeted consent suite 85 passed, diff scope clean, no criterion-bearing code removed)
CAPABILITY-COVERAGE: 7/7 — rows 1–2 reproduced with LIVE single-hunk falsifying edits in a throwaway copy (each red on the NAMED assertion, green-before/green-after-revert confirmed); rows 3–7 verified by inspection of the shipped assertion + green named test (3,7 re-run green) and as declared non-executable/architectural claims (4 key-never-printed: shipped approve_cmd never reads os.environ for the key — only a docstring mentions it; 5 no-overclaiming-prose: grep of src/ clean; 6 .env.example: line 38 `AUTOTESTER_APPROVAL_KEY=` empty)
LIVE-BROWSER: qa/evidence/browser-at110-approval-signing-2026-09-24-checker/report.json — Mode D PASS, 0 console errors: the "Approvals in force" card shows the signed row and HIDES a forged/unsigned row for the same target, with an honest "1 more … not honoured" note
ISSUES-WRITTEN: none (unit is clean; AT-110 moved open -> fixed)
EXECUTOR: claude-sonnet-subagent (checker: claude, sole direct)
EXPLANATION: at110 closes the AT-110 forgery case that CN3 explicitly deferred to an Umesh decision. That decision is on disk — qa/gates/at110-approval-forgery.md is answered "if needed tho krr dee — option a (HMAC keyed from .env)" (2026-09-24). The implementation is sound: core/ids.py adds sign_payload/verify_payload (HMAC-SHA256 over the same canonical JSON content_hash uses, keyed from AUTOTESTER_APPROVAL_KEY, hmac.compare_digest for constant-time compare), both failing CLOSED (SigningKeyMissing) on a missing key; core/consent.py._reject_reason refuses a missing/unsigned/mis-signed row on three fail-closed paths; RunApproval.sign() is explicit grant-time-only (never auto-signs on load, so a forged row read by a key-holder is never quietly re-signed) and is_signed_and_verified fails closed. The overclaiming "cannot be edited to widen itself" prose CN3 required correcting is gone from src/ and replaced with the honest guarantee (tamper-proof against anyone without the .env key; NOT proof against an agent that can edit the checking code itself). I re-ran the 85-test targeted security suite (green), reproduced the two central security falsifications live (forgery refused; missing-key refuses granting), and confirmed the UI card behaves correctly in a real browser.
```

## What I re-ran (2026-09-24)

- `uv run pytest tests/test_approval_signing.py tests/test_consent.py tests/test_approve_cli.py tests/test_approve_target_match.py tests/test_env_loading.py tests/test_ui_crawl_approval.py tests/test_ui_crawl_approval_list.py tests/test_crawl_real_cli.py tests/test_explore_consent.py` -> **85 passed** (my run, 9.42s — matches the maker's 85)
- `uv run ruff check src tests scripts` -> **All checks passed!** · `uv run autotester doctor` -> **doctor: clean**
- Read core/ids.py, core/consent.py, schema/approval.py, cli_crawl.py, ui/routes_crawl_approval.py diffs in full — crypto + fail-closed logic correct.
- Confirmed the AT-110 gate is answered by Umesh (feedback-inbox 872 + qa/gates/at110-approval-forgery.md `Answered:` line, option a).

## Capability-coverage (reproduced live in a throwaway copy with its own venv, outside the worktree)

| row | falsifying edit (single hunk, named file) | red-after (named assertion) |
|---|---|---|
| 1 forgery/legacy refused | consent.py: `if not signed_and_verified:` -> `if False:` | `Failed: DID NOT RAISE ApprovalRequired` (test_the_at110_forgery_repro_is_now_refused + test_a_legacy_..._refused_to_re_grant) — the gate stopped refusing |
| 2 missing key refuses granting | ids.py `_signing_key`: `key = os.environ.get(...)` -> `... or "SABOTAGE-default-key"` | `assert 0 == 1` (exit_code — the grant silently succeeded) + DID NOT RAISE SigningKeyMissing |
| 3 naive edit still refused | (shipped `is_intact` check + test green) | test_the_naive_edit_case_stays_refused + test_an_approval_edited_to_widen_itself_is_refused re-run green |
| 4 key value never printed | (inspection) | shipped approve_cmd never interpolates os.environ key into output; only a docstring names the env var |
| 5 no overclaiming prose in src | (inspection) | `grep -rniE` of the three stale phrases over src/ -> clean |
| 6 .env.example declares key, no value | (inspection) | `.env.example:38` = `AUTOTESTER_APPROVAL_KEY=` (empty) |
| 7 legacy row never auto-signed on load | (inspection) | sign() is explicit; model_post_init mints only `id`, never a signature; test_loading_a_legacy_row_never_auto_signs_it green |

Both live edits (rows 1–2) were reverted immediately; the copy re-ran green (12 passed) after both reverts.

## Diff-scope (4c, base = HEAD accfa9e; unit uncommitted at check time)

19 files, no `--diff-filter=DR` deletions/renames, no removed `def`/`class`/`export`/route/test lines. All 19 are in the manifest's "What changed" (core/ids.py, core/consent.py, schema/approval.py, cli_crawl.py, ui/routes_crawl_approval.py, scripts/check_crawl_approval.py, scripts/explore_proof.py, .env.example, tests/conftest.py + 10 existing test files each gaining `.sign()` on their fixture RunApproval, no assertion changed). Clean.

## Issues addressed

- **AT-110** (the forgery case) — verifiably closed by this unit: forgery-refusal reproduced live, prose corrected, Umesh's design decision (option a) honoured. Moving AT-110 `open -> fixed` in the ledger.

## Observations (not findings)

- The full `uv run pytest` was RAM-deferred by the maker (0.74 GB free) and I did not run it either (0.45–0.69 GB free, sibling checks queued). This is the AT-558 worktree-environment limitation already on the ledger, not an at110 defect; the unit's actual blast radius (consent/approval/crawl/UI) is green across the targeted suites I re-ran, and the diff removes nothing.
- qa/gates/at110-approval-forgery.md still carries `Status: OPEN` in its header even though its `Answered:` line is present (bookkeeping only; the answer is on disk, so this is not the D-006 "gate answered off-disk" failure). Cosmetic; flag for a gate-status tidy on merge.

## Status: PASS — maker to merge wave/at110-approval-signing and push (D-007).
