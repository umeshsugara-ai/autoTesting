# Verdict — at339-credential-guard-case-folding

**Unit:** AT-339 — the credential guard matched case-SENSITIVELY
**Contract:** `qa/contracts/ui.md` (U8, U9) · `qa/contracts/core-invariants.md` (C2, C7)
**Date:** 2026-09-11
**Cycle checked:** 1
**Checker:** Mode A, fresh context, bound to `d:/autoTesting`. No access to the maker's reasoning.

## VERDICT: PASS

```
VERDICT: PASS
SCOREBOARD: 2/2 criteria met (U8, U9), 2/2 invariants hold (C2, C7)
FAILURES (if any): none
LIVE-BROWSER: qa/evidence/browser-at339-credential-guard-case-folding-2026-09-11-checker/
ISSUES-WRITTEN: AT-345 (high), AT-346 (medium), AT-347 (medium), AT-348 (low); AT-339 open -> fixed
EXPLANATION: Every verify command reproduced in this checker's own shell, including the
mutation run with per-test kill attribution. The maker declared a SKIP on live browser
evidence; this checker ran Mode D itself and confirmed the AT-339 bypass is closed in a
real Chromium against its own uvicorn. Four residuals were found — three of them
adversarial extensions of the same transform family, one a manifest bookkeeping error —
and all are filed rather than charged, on the same reading under which AT-074 was filed
against, not charged to, the unit that first introduced U8.
```

## What I re-ran (nothing below is read from the manifest)

| Command | My result | Manifest's claim | Match |
|---|---|---|---|
| `uv run pytest -q` | exit 0, zero `F`, 2 skipped | `1111 passed, 2 skipped` | yes |
| `uv run ruff check src tests scripts` | `All checks passed!` exit 0 | same | yes |
| `uv run autotester doctor` | `doctor: clean` exit 0 | same | yes |
| `uv run pytest tests/test_ui_credential_transforms.py -q` | **7 passed**, exit 0 | **"expected: 10 passed"** | **NO — AT-348** |
| `uv run python scripts/mutation_check.py qa/evidence/at339-.../mutations.json` | `6/6 mutations killed`, exit 0 | same | yes |

## C7 — mutation attribution, checked by hand

I did not read the exit code alone. For each of the six mutations I read the harness's
`claims to kill` / `actually failed` pair and confirmed the **named** test appears in the
failure list:

| Mutation | Named test in FAILED? |
|---|---|
| case folding removed | yes — `test_a_case_and_separator_transform_of_a_credential_is_refused` |
| separator folding removed | yes — both named tests |
| folded check not consulted by the field guard | yes — `test_a_folded_credential_in_one_field_is_blamed_on_that_field`, and it was the **only** failure, so attribution is exact |
| folded check not consulted by the joined guard | yes — `test_a_folded_credential_split_across_two_fields_is_refused`, sole failure |
| floor removed (`>= 0`) | yes — `test_a_short_env_value_does_not_start_refusing_ordinary_text`, sole failure |
| floor raised to 100 | yes — both named tests |

All six exited `1` (tests ran and failed), never 2/3/4, so no collection error was mistaken
for a kill. `_check_in` asserted a green baseline before mutating, and `_sandbox` copies
outside the repo — I confirmed the live tree was unchanged after the run.

**Do the two message-discriminating tests pin a real property, or restate the
implementation?** They pin a real property. The maker's own honest finding is that removing
`contains_folded` from *either* call site alone still refuses the submission, so detection is
genuinely redundant and a naive test could not tell the two sites apart. The two tests
therefore assert on the **user-visible diagnosis**, not on the code path: one asserts the
refusal says *"the slug looks like it contains a real credential"* and **not** *"split
across"*; the other asserts the inverse for a value straddling two adjacent Value boxes. That
is a property a user experiences — a false "split across two fields" message for a value
sitting whole in one box is unactionable — and it is exactly what each call site uniquely
provides. Mutations 3 and 4 each produced a **single** failure, the named test, which is the
strongest attribution result in the run. Not a restatement.

I also independently checked the premise behind the split test: the join order is
title → targets → values → expects, so splitting across title and a Value box puts a Target
between the halves and the value genuinely does not reassemble contiguously. The maker's
correction of its own first draft is right, and the test as written (two adjacent Value
boxes) is the honest version.

## Mode D — live browser (the maker's declared SKIP, run by me)

Own `uvicorn` on port 8412, own Chromium, scratch `AUTOTESTER_ROOT` under `.work/` seeded
with a synthetic credential. The real repo `.env` was never used for a leak probe; its nine
key **names** were read only for the false-positive sweep below, never a value.
Evidence: `qa/evidence/browser-at339-credential-guard-case-folding-2026-09-11-checker/report.json`
plus `home-index-credentials-rendered.png`.

- **Control — the AT-339 bypass is closed.** `POST /onboard` with slug
  `zebra-quilt-apikey-31` for the live value `ZEBRA_QUILT_APIKEY_31` → **400**, and the body
  carries the **per-field** message (`"the slug looks like it contains a real credential"`),
  not the joined one. No directory created. This is the defect, reproduced closed, live.
- **Console errors: 2, both explained** — `400 (Bad Request)` on the two deliberate refusals
  (the duplicate-credential-key refusal and the control above). Zero unexplained.

## U8 / U9 — judged on evidence

**U9 holds.** All three `project.json`-writing routes still pass their user text through
`_refuse_unsafe_submission` before any write (read in `ui/helpers.py`, exercised live on
`POST /onboard`). Matching still runs over **every** `.env` value — I confirmed the redactor
is built from `SecretStore`'s full `_all_values`, and 8 of the 9 real keys carry a non-empty
value, all 8 above the folded floor. The AT-078 exemption is intact and still narrow
(`value in exempt`, and exempt fields are dropped from the join).

**U8 holds.** The case form passes no `exempt` set, so it remains structurally unexemptable.

**False positives — the thing folding could realistically have broken.** Against the **real**
nine-key `.env` I ran the exact guard predicate over 15 ordinary strings a tester would type
(counsellor login prose, a real-looking signin URL, `PATHLYNKS_USER_EMAIL` as literal text,
`a-b-c-d-e-f-g-h-i-j`) and over **every** on-disk project's own `name`, `base_url` and a
rename-with-unchanged-base-URL: **zero refusals**. The widening is bounded in practice, and
U9's "must not brick a project's own data" clause survives it. The floor plus the exemption
are doing their job.

**C2** — `doctor: clean`; the 300-line split into a new test file is the reason the new file
exists and the manifest states it. **C1/C3** unaffected; no duplicate concept, no `*_v2`.

## The floor (MIN_FOLDED_LEN = 8) — is 8 defensible?

Independently measured rather than argued. With the guard predicate reconstructed exactly:

| secret length | exact value | its uppercased form |
|---|---|---|
| 6 | REFUSED | **ACCEPTED** |
| 7 | REFUSED | **ACCEPTED** |
| 8 | REFUSED | REFUSED |
| 9 | REFUSED | REFUSED |

So the maker's claim that **AT-002 is untouched is true as stated** — the real value is
refused at any length by `is_clean` — and I verified it directly, not from the manifest. What
the floor does cost is that a credential shorter than 8 folded characters gets **no** case
protection: a 6-char password typed with different capitalisation is accepted. That is a real
residual, but it is the disclosed, reasoned half of a heuristic widening, the test
`test_a_short_env_value_does_not_start_refusing_ordinary_text` pins the other direction, and
two mutations pin the floor from both sides. I am not charging it: refusing every string
containing a 3-letter `.env` value's letters would make the product unusable, and the manifest
argues the tradeoff out loud instead of hiding it. Recorded here so a later unit that wants to
lower the floor knows what it buys.

## Findings — filed, not charged

Each was reproduced by me; none is a violation of U8/U9 as written, which pin refusal of a
**raw** `.env` value and of its concatenation. Precedent is explicit: AT-074 (percent-encoding
and whitespace) was filed against, not charged to, the unit that introduced U8, and AT-339
itself was filed against a PASSing at079-080. I follow it.

- **AT-345 (high)** — four more trivially-reversible transforms still reach git-tracked
  `project.json`/`cases.jsonl`, because `_FOLD_STRIP` is `[\s\-_.]` and `casefold()` does no
  NFKC. Live on my own server: `'+'` as the separator (**accepted**, renders as the project
  link text on the home index), **U+200B zero-width between every character** (accepted — and
  it renders as the *exact* credential, so a human reading the index sees it), full-width
  Latin, and Turkish dotless `ı`. `~ / :` likewise accepted at unit level. U+212A Kelvin
  **is** caught. The zero-width case is materially worse than AT-339 itself, which is why this
  is high rather than medium.
- **AT-346 (medium)** — the new fold and the AT-074 variant list **do not compose**:
  `contains_folded` is applied to the raw text only, never to each decoded variant, so
  `zebra%5Fquilt%5Fapikey%5F31` and `zebra%2Dquilt%2Dapikey%2D31` pass both checks. Each
  guard covers exactly the half the other does not. One line at each call site closes it
  (`any(redactor.contains_folded(v) for v in _credential_variants(value))`), and it sits
  inside the code this unit touched.
- **AT-347 (medium)** — the maker's explicit open question: is a folded credential reaching a
  model prompt a real hole? **Yes, and it is reachable** — AT-345/AT-346 show accepted forms
  landing in `cases.jsonl`, and a case title feeds the grading prompt. But it is not this
  unit's defect and not a C5 violation (a folded form is not the value), and the availability
  argument is sound: `assert_no_raw_secrets` *raises*, so folding there converts a false
  positive into a dead run. Filed as a scope decision with two named shapes, not as a bug.
- **AT-348 (low)** — the manifest's `expected: 10 passed` for the new test file is wrong; it
  has 7 tests and gives 7. The "Actual outputs" block omits this one command, so the only
  number in the manifest nothing re-ran is the only one that was wrong. Everything else
  reproduced exactly.

## Ledger

- `AT-339` `open` → `fixed` (checker note recording the live re-derivation; left at `fixed`,
  not `verified` — only a later re-check promotes it).
- New: `AT-345`, `AT-346`, `AT-347`, `AT-348`. **Note for the ledger's owner:** a concurrent
  session appended a different `AT-341` (critical, browser-and-secrets) while this check was
  running; I renumbered my four rows to 345-348 rather than overwrite. Pre-existing duplicate
  ids `AT-288`–`AT-291` are **not** mine and are left untouched — worth a sweep row.

## Goal

`.goal/goal.json` — the manifest declares no goal task for this unit (issue-driven), and no
matching task id exists. No goal close performed.
