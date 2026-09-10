# Manifest — t161-unified-project-intake

**Status:** ready-for-check  
**Contract:** `qa/contracts/ui.md` + `qa/contracts/browser-and-secrets.md` + `qa/contracts/core-invariants.md`  
**Goal task:** T-161 (`user_value: high`, critical)  
**Date:** 2026-09-10  
**Fix cycle:** 2  
**Implementation commit:** `4c09990` + fix `d92af87`  
**Decision:** D-025 (supersedes D-024)
**Issues addressed:** AT-284

**Cycle 2:** Both blind cycle-1 checkers found the same pre-guard secret-echo failure: a newly
submitted hostname-shaped credential could be interpolated by reachable-URL validation before it
entered the redactor. `d92af87` moves that validator after `_guard_intake` and adds the exact HTTP
reproduction. Full suite reached 100% after the fix; the focused cycle-2 security set passed 33/33.

## Submitted behavior

- `/onboard` is one no-CLI form for URL/domain boundary, repeatable test-account credentials,
  optional evals, conditions/business rules, use cases and source declarations.
- Credential values are accepted in masked password inputs and written only to the shared,
  gitignored root `.env`; project artifacts retain domain-scoped `SecretRef`s only.
- The `.env` batch is fully validated before persistence and committed via a same-directory
  mode-0600 temporary file, flush/fsync and atomic replace. Duplicate existing lines all rotate.
- Credential keys cannot collide with an existing `.env` key or any other project's declared key,
  including unset declarations. Re-onboarding cannot overwrite an existing project.
- Evals, conditions, use cases and declared URL/video/doc/text sources become canonical,
  content-addressed `Source` rows; duplicates are idempotent and non-video declarations do not
  falsely offer video analysis.
- Every repeated row and every non-secret field is validated before artifacts are written. The
  secret guard sees the union of pre-existing root secrets and newly submitted values.

## Verification commands the checker must re-run

```text
uv --cache-dir .work/uv-cache run pytest -p no:cacheprovider --basetemp=.work/pytest-t161-checker -q
uv --cache-dir .work/uv-cache run ruff check src tests scripts
uv --cache-dir .work/uv-cache run autotester doctor
git diff --check 4c09990^ 4c09990
```

Maker results: full suite reached 100% with two expected platform skips; Ruff clean; doctor reports
only the unrelated untracked root `AGENTS.md`. The senior-software-engineer review found and drove
fixes for three credential/atomicity defects, then returned `Approve` with no material test gaps.

## Required independent browser check (Mode D)

Use a fresh visible browser against `4c09990` + `d92af87`; do not reuse prior evidence. At minimum:

1. Open `/onboard` and verify all intake categories coexist in one usable form.
2. Submit a rich fake project with a scoped credential reference (no real credential), at least one
   eval/condition/use case and a URL/Drive declaration.
3. Verify the project and Sources pages show persisted truth, while no raw credential value renders.
4. Attack re-onboarding, cross-project duplicate ownership, and the AT-284 hostname-shaped secret
   in allowed-domains refusal; all must refuse without partial artifacts or secret echo.
5. Record unexplained browser console errors.

Maker browser evidence:
`qa/evidence/browser-t161-unified-intake-2026-09-10-maker/report.json`.

## Contract-maintenance request

Fold D-025/T-161's one-form intake, cross-project key ownership, all-secret guarding and atomic
batch-write requirements into checker-owned criteria before judging. Do not weaken U1-U11 or B1-B9.

## Scope boundary

Judge implementation commits `4c09990` + `d92af87` plus this manifest. Ignore unrelated runtime
artifacts (`AGENTS.md`, `.codex/`, `.goal/*`, `qa/.last-tick`, and pre-existing `projects/*`).
