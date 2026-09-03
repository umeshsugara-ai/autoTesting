# Manifest — t011-secret-store

**Contract:** qa/contracts/browser-and-secrets.md (criteria B1–B4) + qa/contracts/core-invariants.md
**Goal task:** T-011
**Date:** 2026-09-03
**Fix cycle:** 3 of max 3 (LAST)
**Issues addressed:** AT-006 (S3), AT-007 (S2), AT-008 (S3) — this cycle; AT-001..005 verified fixed in cycle 2

## Cycle 3 — fixes for verdict `qa/verdicts/t011-secret-store.md` (Cycle checked: 2)

- **AT-007 (S2)** "host_of() trusts urlparse; `https://evil.test\@pathlynks.test` resolves the secret while Chromium navigates to evil.test" →
  `browser/secrets.py::host_of` now returns `""` (which `resolve()` already refuses, AT-001) when the raw
  input contains a backslash **or** `urlparse` yields any username/password. Exactly the two-line
  fail-closed fix the verdict prescribed. Test: `test_at007_backslash_and_userinfo_destinations_fail_closed`
  (4 destinations + 2 direct `host_of` asserts).
- **AT-006 (S3)** "comment stripping only recognises space-hash; quoted value followed by a comment keeps its quotes" →
  `_clean_value` rewritten: a leading quote is closed at the *next* matching quote and the remainder
  dropped; unquoted values split on `\s#` (any whitespace). URL fragments (`a#b`) untouched.
  Test: `test_at006_tab_comment_and_quoted_then_comment`.
- **AT-008 (S3)** "ARCHITECTURE.md + SecretRef docstring still say projects/<slug>/.env; no table row for the credential boundary; Status stale" →
  `docs/ARCHITECTURE.md`: security §1–2 rewritten for repo-root `.env` + fail-closed hosts + masked
  undeclared values; storage block shows `.env` at root; concept→file table gains
  `browser/secrets.py::SecretStore`; Status updated. 121 lines (cap 150).
  `schema/project.py::SecretRef` docstring corrected. `grep -rn "projects/<slug>/.env" docs src` → none.

## Cycle 2 — fixes for verdict `qa/verdicts/t011-secret-store.md` (Cycle checked: 1)

Each finding quoted, then the fix and the test that pins it:

- **AT-001** "Domain gate fails OPEN on an empty host" →
  `browser/secrets.py::resolve` now raises `SecretScopeError` when `host_of()` returns `""`
  (fail closed), and `schema/project.py::SecretRef._reject_blank_domains` refuses blank entries at
  declaration and normalises case/leading-dot. Tests: `test_at001_empty_host_fails_closed`,
  `test_at001_blank_domain_is_rejected_at_declaration`.
- **AT-002** "guard_prompt does NOT raise on a raw secret shorter than 4 chars" →
  `core/redact.py`: removed `_MIN_SECRET_LEN` from both `Redactor` and `assert_no_raw_secrets`;
  any non-empty declared value counts. The old test asserting short values were ignored was
  replaced by `test_redactor_masks_even_very_short_declared_values` (it encoded the bug).
  Test: `test_at002_short_secret_is_still_guarded_and_masked`.
- **AT-003** "parse_env does not strip trailing inline comments" →
  `browser/secrets.py::_clean_value` strips ` #…` from unquoted values only; quoted values and
  `#` without a preceding space (URL fragments) are preserved.
  Test: `test_at003_inline_comment_is_stripped_from_unquoted_values`.
- **AT-004** "Undeclared .env values are absent from the Redactor" → resolved toward B4:
  `SecretStore` keeps undeclared values in a `_shadow` map that feeds `redactor()` and
  `guard_prompt()` but can never be `resolve()`d. Contract tension (B1 vs B4) logged in
  `qa/feedback-inbox.md` for the checker to amend B1's wording.
  Test: `test_at004_undeclared_values_are_masked_but_never_resolvable`.
- **AT-005** "`strict=False` has no test coverage" →
  Test: `test_at005_non_strict_load_still_fails_closed_at_resolve`.

**Also in this cycle (user instruction mid-cycle, verbatim in the inbox):** the credential file is
now **repo-root `d:/autoTesting/.env`** (`core/paths.py::ProjectPaths.env_file`), one file shared
across projects with per-project namespaced keys. `.env.example` added at root. **Contract B1
still says `projects/<slug>/.env` — this is a known contract/code divergence awaiting checker
fold, flagged in the inbox; please judge B1 on the *behaviour* (declared-key validation, missing-key
error, undeclared handling), which is unchanged.**

## What changed

- `src/autotester/browser/__init__.py` — new package docstring only.
- `src/autotester/browser/secrets.py` (new, 152 lines) — the credential boundary:
  - `parse_env` — minimal `KEY=value` parser (comments, quotes, `export ` prefix). Deliberately
    no interpolation: a credential file needing a featureful parser is one with surprises.
  - `SecretStore.load(project, env_path, strict=True)` — loads `.env`, keeps only keys the project
    declares, raises `MissingSecret` naming any declared-but-absent key, records undeclared keys in
    `store.undeclared` without making them usable (B1).
  - `SecretStore.resolve(value, url_or_host)` — the only way a value leaves this class. Substitutes
    `{{SECRET:KEY}}` only when the host matches that `SecretRef`'s `domains`; otherwise raises
    `SecretScopeError` / `UndeclaredSecret` (B2, B3).
  - `guard_prompt` — wraps `core.redact.assert_no_raw_secrets`; raises rather than masking-and-sending (B2).
  - `redactor()`, `masked_field_keys()`, and a `__repr__` that never renders a value (B4).
- `src/autotester/doctor.py:22-26` — added `CLAUDE.md`, `qa`, `.goal` to `ALLOWED_ROOT_ENTRIES`.
  These are legitimate layout entries created by `/maker init` after the rule was written; the
  doctor was flagging its own project's required files.
- `tests/test_secrets.py` (new, 16 tests) — one per criterion including the negative paths.

## Two defects my own gates caught (recorded rather than hidden)

1. **`ruff RUF012`** — `undeclared: list[str] = []` was a mutable **class** attribute, so every
   `SecretStore` would have shared one list. Real bug, not a style nit. Moved to `__init__`.
2. **`autotester doctor`** — root-clutter fired on `CLAUDE.md` and `qa/`. The allowlist was stale.

## How to verify (commands + expected)

- `uv run pytest tests/test_secrets.py -q` → expected: exit 0, 24 passed
- `uv run pytest -q` → expected: exit 0 (50 tests)
- `grep -rn "projects/<slug>/.env" docs src` → expected: no output
- `uv run ruff check src tests` → expected: exit 0, "All checks passed!"
- `uv run autotester doctor` → expected: exit 0, "doctor: clean"
- `git ls-files | grep -E "\.env$"` → expected: no output (no credential file tracked)

## Actual outputs (from maker's own run, cycle 3)

```
$ uv run pytest -q
..................................................                       [100%]
exit=0

$ uv run ruff check src tests
All checks passed!
exit=0

$ uv run autotester doctor
doctor: clean
exit=0

$ git ls-files | grep -E "\.env$" || echo "(none)"
(none)
```

## Scope notes for the checker

- B5–B9 (`browser/session.py`) are **not** in this unit — that is T-010, next.
- No live host is contacted; every test uses a constructed `Project` and a temp `.env`.
- No Pathlynks credential exists anywhere in the repo yet; T-030 gates on the human for a test account.

## Status: checked-PASS

Verdict: `qa/verdicts/t011-secret-store.md` (Cycle checked: 3, PASS, 4/4 + 8/8; commit 8fe0bbf). Goal task T-011 closed by the checker.
