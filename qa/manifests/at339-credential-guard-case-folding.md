# Manifest — at339-credential-guard-case-folding

**Unit:** AT-339 — the credential guard matched case-SENSITIVELY
**Contract:** `qa/contracts/ui.md` (U9 — credential safety on routes that write `project.json`) ·
`qa/contracts/core-invariants.md` (C2, C7)
**Goal task:** none — issue-driven
**Date:** 2026-09-11
**Fix cycle:** 1 of max 3
**Dual check:** no
**Issues addressed:** AT-339 (medium, fixed)

## What was wrong

A checker reproduced this live while checking `at079-080-credential-guard-gaps`: for the real
`.env` value `ZEBRA_QUILT_APIKEY_31`, the slug **`zebra-quilt-apikey-31` was ACCEPTED**. It became
the on-disk directory name, every page URL, and text on the home index.

`Redactor.is_clean` is a plain substring test. `_credential_variants` had been taught
percent-encoding (AT-074) and stray whitespace (AT-071/AT-074), but never **case**. A transform
anyone can reverse in their head walked straight through the guard AT-079 had just tightened.

**Why three previous credential units missed it, which is the part worth keeping:** every test in
the suite used `REAL_PASSWORD = "hunter2-this-is-the-real-one"` — already lowercase-with-hyphens,
the one casing where a case-sensitive substring test happens to work. The fixture agreed with the
bug. Adding a `.casefold()` entry to `_credential_variants` would also have done nothing, because
the stored value would still have been compared in its original case: folding only works if **both
sides** fold, and only the redactor holds the values.

## What changed

- `src/autotester/core/redact.py` — `fold_credential(text)` (casefold + drop `\s-_.`),
  `MIN_FOLDED_LEN = 8`, and `Redactor.contains_folded(text)`. Kept deliberately separate from
  `is_clean`, and **not** used by `scrub`: you cannot mask a transform, because the literal bytes
  are not there to replace. Redaction and "could a reader recover a credential from what we are
  about to store?" are different questions.
- `src/autotester/ui/helpers.py` — both guard call sites consult `contains_folded` alongside the
  existing variants; `_credential_variants`' docstring now says why case is NOT handled there.
- `tests/test_ui_credential_transforms.py` — **new file**, split from
  `test_ui_credential_safety_project.py` at doctor's 300-line cap (C2). One question: which FORMS
  of a credential does the guard recognise? 5 moved tests + 5 new.

## The floor, and why it is not a fudge

Folding is a **heuristic widening** — it deliberately matches strings that are not byte-equal to
any secret. Unfloored, a short `.env` value would start refusing ordinary text that merely contains
its letters (`A-B` folds to `ab`). So folded matching requires ≥ 8 folded characters.

**Exact and variant matching stay floorless**, so AT-002 — *"a three-character password is a bad
password, but leaking it is still a leak"* — is untouched: a short real value is still refused, by
`is_clean`. A test pins both halves, and two mutations pin the floor from both directions (remove
it → ordinary text starts being refused; raise it past the credential → the bypass reopens
quietly).

## Both call sites are redundant for DETECTION — kept for the MESSAGE

Honest finding from the first mutation run: removing `contains_folded` from *either* call site
SURVIVED. Every route goes through `_refuse_unsafe_submission`, which runs the per-field check and
then the joined check over the same text, so for a single-field submission either alone still
refuses.

Redundant detection is not a reason to keep both. The **message** is, and no test pinned it:
per-field says *"the slug looks like it contains a real credential"*; the joined guard says a
credential is *"split across"* the named fields — false and unactionable when the value sits whole
in one box. Two tests now distinguish them, and both mutations die.

Writing the split-across-fields test also corrected my own premise: my first version split the
value across the title and a Value box, which the guard **accepted** — correctly, because the join
is ordered title → targets → values → expects, so a Target box sits between the halves and the
value does not reassemble contiguously on disk. A refusal there would have been a false positive,
not a catch. The test now uses two adjacent Value boxes.

## Deliberate scope boundary

`assert_no_raw_secrets` — the hard gate before a model prompt — was **not** changed to fold. It
answers a different question (are RAW secret bytes in this payload) and folding there would refuse
legitimate prose. Whether a folded credential reaching a prompt is also a leak is a real question
and is left for the checker to raise on its own evidence rather than settled quietly here.

## How to verify (commands + expected)

- `uv run pytest -q` → expected: exit 0, no failures
- `uv run ruff check src tests scripts` → expected: `All checks passed!`
- `uv run autotester doctor` → expected: `doctor: clean`
- `uv run pytest tests/test_ui_credential_transforms.py -q` → expected: 7 passed
  (AT-348: this said 10. It was the one verify command whose ACTUAL output I never pasted,
  so the number was written from intent rather than from a run — the AT-306 class again.)
- `uv run python scripts/mutation_check.py qa/evidence/at339-credential-guard-case-folding/mutations.json`
  → expected: `6/6 mutations killed` (C7)

## Actual outputs (from maker's own run)

```
$ uv run pytest
1111 passed, 2 skipped, 1 warning in 186.36s (0:03:06)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean

$ uv run python scripts/mutation_check.py qa/evidence/at339-credential-guard-case-folding/mutations.json
KILLED  case folding removed - the AT-339 bypass is open again
KILLED  separator folding removed - stripping the hyphens walks through
KILLED  the folded check is never consulted by the field guard
KILLED  the folded check is never consulted by the joined-fields guard
KILLED  the folded-length floor is removed - short values refuse ordinary text
KILLED  the floor is raised past the real credential - the bypass reopens quietly
6/6 mutations killed
```

Full log: `qa/evidence/at339-credential-guard-case-folding/mutations.out`.

## Live browser evidence

**SKIP — stated gap, not a pass.** This unit changes a guard reached through the UI, so a live pass
is warranted; the maker did not run one this cycle. The behaviour is covered by `TestClient` tests
that drive the real routes and assert disk state, and the original AT-339 bypass was itself found
by a checker in a live browser. **The checker should run Mode D and treat its own result as
authoritative** — a checker's live pass is the validation here regardless, since the maker never
validates its own ship.

## Status: checked-PASS (cycle 1, verdict qa/verdicts/at339-credential-guard-case-folding.md)
