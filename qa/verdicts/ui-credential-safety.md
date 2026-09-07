# Verdict — ui-credential-safety

**Date:** 2026-09-07
**Contract:** qa/contracts/ui.md (U1–U7)
**Manifest:** qa/manifests/ui-credential-safety.md
**Cycle checked:** 1
**Mode:** A (fresh subagent, no builder context), bound to `d:/autoTesting`

```
VERDICT: PASS
SCOREBOARD: 7/7 criteria met, 0/0 invariants hold (ui.md declares no [I*] of its own)
FAILURES: none
ISSUES-WRITTEN: AT-070 (high), AT-071 (medium), AT-072 (low)
EXPLANATION: Every verify command reproduces exactly as the manifest claims, including all
four live probes against the running container, and all seven U-criteria are evidenced —
this unit touches only the case-creation and run-precondition paths and breaks none of them.
It is nevertheless PASSed with a caution I want on the record: the control it adds is real but
partial. The guard is wired to `step_value` alone, so the same credential typed into the case
title, the target box or the expect box — all on the same form row — is accepted and written
in cleartext to a git-TRACKED file in a public repo (AT-070, high). No U-criterion covers
credential safety in cases, which is why this is an issue and not a FAIL, but Umesh should
read the guarded box as "one box", not "the form", before typing real ERP credentials.
```

## What I re-ran myself (nothing taken from the manifest on trust)

| Command | My result |
|---|---|
| `docker compose exec -T autotester uv run pytest -q` | exit 0, 343 collected: 342 passed, 1 skipped, 0 failures |
| `docker compose exec -T autotester uv run pytest -q tests/test_ui_credential_safety.py` | `........` = 8 passed, exit 0 |
| `docker compose exec -T autotester uv run ruff check src tests scripts` | `All checks passed!` |
| `docker compose exec -T autotester uv run autotester doctor` | `doctor: clean` |

Live, against the running app from inside the container (`localhost:8000`), with an md5 taken
of `projects/erp/cases.jsonl` and `projects/pathlynks/cases.jsonl` before and after:

1. `POST /projects/erp/cases step_value={{SECRET:NOT_DECLARED}}` → **400** "this project has not
   declared a credential called 'NOT_DECLARED'…"
2. `POST /projects/pathlynks/cases step_value=<the real PATHLYNKS_USER_PASSWORD read out of
   .env>` → **400** "that looks like a real credential…" — the value was read and posted entirely
   inside the container and never printed
3. `GET /projects/erp/cases/new` → offers `{{SECRET:ERP_EMAIL}}` and `{{SECRET:ERP_PASSWORD}}`,
   with `list='declared-credentials'` present
4. `POST /projects/erp/run` (values unset) → **400** "these credentials have no value yet:
   ERP_EMAIL, ERP_PASSWORD. Enter them on the project's Credentials page…"

Both `cases.jsonl` hashes were byte-identical afterwards. All four match the manifest's claimed
outputs.

## 1. Can the raw-value guard be bypassed?

Probed in-container against a scratch `AUTOTESTER_ROOT` with a declared `DEMO_PASSWORD` whose
`.env` value was `hunter2-this-is-the-real-one`. Honest results:

| Probe | Caught? | Why |
|---|---|---|
| the exact value | **yes** | `is_clean` → `value in text` |
| the value with surrounding whitespace | **yes** | `_build_steps` strips *before* the guard — confirmed at `routes_cases.py:116`, `_refuse_unsafe_value(value.strip(), …)` |
| the value as a SUBSTRING of a longer string (`prefix-<value>-suffix`) | **yes** | `is_clean` is containment, not equality — the substring direction that matters is covered |
| an UNDECLARED `.env` value from another project (the shadow set) | **yes** | `redactor()` is built from `_all_values()` = shadow + declared (`browser/secrets.py`), so a key this project never declared is still refused |
| the value **split across two step rows** | **NO** | the guard runs once per row; `hunter2-this-i` + `s-the-real-one` both stored, and they reassemble byte-for-byte. **AT-071** |
| the value in **`step_target`** | **NO** | persisted as `{"target":"hunter2-this-is-the-real-one"}`. **AT-070** |
| the value in **`step_expected`** | **NO** | persisted as `{"expected":{"visible_text":["hunter2-…"]}}`. **AT-070** |
| the value in the **case title** (not on the dispatch's list, found while reading) | **NO** | persisted as the title, *and* reaches the grade prompt. **AT-070** |

A correction on method: the split-across-rows probe first *appeared* to be caught. It was not —
my own scratch `.env` also carried `SHORT=a`, and the second half contains an `a`. I re-ran it
with a clean `.env` before reporting. A checker that cannot reproduce a pass cleanly does not
report one.

**Is the value-only application a real hole?** Yes, and it is the finding of this check. The
three unguarded boxes are on the same form row as the guarded one, so this is a slip a careful
person makes, not an attack. The manifest's own justification for the guard — "`cases.jsonl` is
not gitignored" — applies verbatim: I confirmed `.env` is ignored (`**/.env`) while
`projects/pathlynks/cases.jsonl` is **tracked**, in a repo the project's own CLAUDE.md records
as public. The title case is the worst of the three, because U6 mandates `rationale=None`, so
`run_case_pipeline.claim_of` falls back to the title and feeds it into the grade prompt — where
the very `guard_prompt` this unit just wired raises an **unhandled** `ValueError`, so the leak
also bricks every subsequent run with a 500 instead of a clean refusal.

## 2. Is `Redactor.is_clean` the right primitive?

It is the right *shape* — exact containment over known-declared values, no heuristics, so it
cannot invent a false credential out of nowhere. There is **no minimum length**, and
`core/redact.py:20-24` says so deliberately (AT-002: "a three-character password is a bad
password, but leaking it is still a leak"). I agree with the direction: it fails **closed**.

The cost is the message, not the refusal. With a scratch `.env` holding `DEMO_TOKEN=test`:
`'test'` → 400, `'latest news'` → 400, `'contest entry'` → 400, `'Bengaluru'` → 303. The user
is told "that looks like a real credential", which for `latest news` is false and offers no way
forward. This is reachable today, not hypothetically: the repo-root `.env` carries
`PATHLYNKS_USER_LOGIN_URL`, a non-secret URL, so any step value containing it is now refused as
a credential — and that same URL already appears, legitimately, as a navigate target inside the
tracked `projects/pathlynks/cases.jsonl`. Filed as **AT-072** (low), with the fix direction of
naming the matched declared key in the message.

## 3. `guard_prompt` wiring

- `grade()` genuinely calls it on the UI path. Constructed the case directly: a rubric criterion
  carrying the raw value, graded with `secrets=<store>` → `ValueError: refusing to proceed: raw
  secret value present in payload`, **before** the judge is called. The same call with no
  `secrets` → no raise, judge invoked, verdict `PASS`. So the gate fires exactly where it is
  wired and nowhere else.
- It **raises, it does not scrub** — verified directly on `SecretStore.guard_prompt`: a clean
  prompt returns unchanged; a declared raw value, a shadow raw value, and a raw value embedded as
  a substring each raise. The exception message contains no value.
- The three script callers are truly unaffected: `scripts/bench_trial.py:101`,
  `scripts/regression_proof.py:111` and `scripts/run_pathlynks_first_cases.py:139` all call
  `grade(rubric, result, run_id, judge)` positionally with no `secrets`; the parameter is
  keyword-optional and defaults to `None`. `run_case_pipeline.py:101` is the one caller that
  passes `secrets=session.secrets`, and `BrowserSession.__init__` does set `self.secrets`.
- One consequence worth naming rather than celebrating: because it raises, a secret that got
  into a case title (AT-070) converts a leak into a hard 500 on every run. Failing closed is
  correct; failing closed *unhandled* is how AT-070 becomes visible to a user as "the app is
  broken" rather than "your credential is in the repo".

## 4. `has_value` says nothing about the value

`SecretStore.has_value` is `bool(self._values.get(key))` — verified it returns a real `bool`
(`bool True`, and `False` for a declared-but-unset key), never the value or a length. `__repr__`
still refuses to render values (checked: the real value is not in `repr(store)`). It cannot be
used to probe a value: the only signal is set/not-set, which the UI already shows on the
Credentials page by design (U3).

The run refusal names **keys only** — reproduced live: "these credentials have no value yet:
ERP_EMAIL, ERP_PASSWORD. Enter them on the project's Credentials page (/projects/erp/env) before
running." No value, no length, no shape. And it is genuinely a *precondition*:
`_require_declared_values` is called at `routes_runs.py:96`, before the `BrowserSession(...)`
/`session.start()` at :103, so no browser is launched.

## 5. Blast radius

- **The `routes_cases.py` → `case_form.py` split moved code without changing it.** Read the diff:
  `STEP_ROWS` and `_options` are byte-identical; `_step_row` is identical apart from the one
  intentional, manifest-declared addition (`has_secrets` param → `list='declared-credentials'`).
  No behaviour was smuggled into the move.
- **The datalist is absent for a project declaring nothing.** `_credential_datalist` returns `""`
  on empty `project.secrets`, the `has_secrets` flag suppresses the `list=` attribute, and the
  extra hint paragraph is conditional — so that page is byte-identical to before. Covered by
  `test_a_project_with_no_credentials_gets_no_picker`, which I re-ran.
- **All existing case tests still hold** — the full 343-test suite is green (342 passed, 1 skipped), including
  `test_ui_add_case.py` and `test_ui_case_management.py`.
- **U5 (escaping) is not weakened by the new HTML.** `SecretRef.key` is pattern-locked to
  `^[A-Z][A-Z0-9_]*$` (`schema/project.py:20`), and `_credential_datalist` escapes it anyway, so
  no user-controlled string reaches the new markup.
- `docs/MAP.md` is regenerated and lists `ui/case_form.py`; `doctor: clean` confirms the 300-line
  cap that motivated the split is now satisfied.
- Cosmetic only, not a finding: the split left ~7 consecutive blank lines at
  `routes_cases.py:45-51`. Ruff and doctor pass; ui.md's out-of-scope rule says no churn on
  cosmetics.

## Criterion-by-criterion

| # | Verdict | Evidence |
|---|---|---|
| U1 | met | `POST /onboard` → `ProjectStore.save_project`; untouched by this unit; onboarding exercised in every probe fixture and in the live erp/pathlynks projects |
| U2 | met | `_load_project_or_404` reads live per request and 404s an unknown slug; untouched |
| U3 | met | `routes_credentials.py` / `env_editor.py` untouched by this unit; `create_case` reads `.env` through `SecretStore` and never renders a value — the only new `.env` reader, and it emits a bool-shaped refusal. No new write path to `.env` |
| U4 | met | `routes_report.py` untouched; the only change in the run path is a pre-flight refusal that runs before any result is produced |
| U5 | met | new markup escapes every interpolated value; `SecretRef.key` is regex-locked; live `GET /projects/erp/cases/new` shows only the intended `{{SECRET:…}}` options |
| U6 | met | case creation still persists a real `Case` via `ProjectStore.add_case` with `kind` derived from `case_class` and `rationale=None`; all five refusals (blank title, zero steps, unknown class, unknown action, unknown project) still hold in the suite; **strengthened** here — a real credential in the value box is now a sixth refusal with nothing written (hashes unchanged live) |
| U7 | met | `_require_reachable_base_url` untouched; still composes `host_of` + `allows_domain` |

No contract amendment this cycle. AT-070 names a defect no U-criterion covers; following this
contract's own precedent (U6 after AT-057, U7 after AT-058), the criterion gets written when the
fix lands, not before.

## Cleanup

I wrote **nothing** into the repo-root `.env` — every scratch `.env` lived under a container
`tempfile.mkdtemp()`. `git status` on `.env` is clean and `projects/` still holds exactly
`erp`, `pathlynks`, `regression-demo`, `vidysea-erp` — no scratch project was created in the
repo. `projects/erp/project.json`'s ERP_EMAIL / ERP_PASSWORD declarations are untouched. Probe
scripts are in `.work/checker-ui-cred/` (gitignored).
