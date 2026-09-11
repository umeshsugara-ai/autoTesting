# Verdict — at079-080-credential-guard-gaps

**Unit:** AT-079/AT-080 — two fields AT-073's credential guard never covered
**Contract:** `qa/contracts/ui.md` — U9 ("The three routes that write `project.json`
cannot commit a raw credential either"). Note: the dispatch and the manifest header
both label this "U8", but U8 pins the *case form only* ("This criterion pins the
case form only. The equivalent hole on the three routes that write `project.json`
is not covered here and is tracked as AT-073.") — the `slug` field of `POST /onboard`
and the `key` field of `POST /projects/{slug}/secrets` are exactly the U9 surface
(the project-route guard U8 explicitly excludes). Judged against U9, the criterion
that actually covers this unit's claim; the label mismatch is cosmetic and does not
change the evidence below.
**Date:** 2026-09-11
**Cycle checked:** 1
**Checker:** fresh subagent, Mode A + Mode D, bound to `D:/autoTesting`

## Re-run verify commands (own execution, not pasted)

```
$ uv run pytest tests/test_ui_credential_safety_project.py -q
................                                                         [100%]
16 passed, 1 warning

$ uv run pytest -q
[full suite] ... 100% ... all dots (2 skipped, rest passed), exit 0

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

All four match the manifest's claimed outputs.

## Independent sabotage re-run

Isolated `git archive HEAD` extract at
`C:\Users\Lenovo\AppData\Local\Temp\claude\d--autoTesting\a8e8ef26-6b21-4ba0-bdc6-003d450b9016\scratchpad\checker-extract`
(own `uv sync` venv; `autotester.__file__` confirmed to resolve inside the extract,
never the live tree).

1. Baseline: `uv run pytest tests/test_ui_credential_safety_project.py -q` → 16
   passed.
2. Removed `("the slug", project.slug)` from `_guard_intake` in `src/autotester/ui/app.py`
   → **exactly** `test_a_credential_shaped_slug_at_onboarding_is_refused` failed
   (`1 failed, 15 passed`), all others green.
3. Restored the slug line, removed `("the key", key)` from `declare_secret` in
   `src/autotester/ui/routes_project_edit.py` → **exactly**
   `test_a_credential_shaped_key_is_refused` failed (`1 failed, 15 passed`), all
   others green.

Each fix's own regression test is the only thing that breaks when that fix is
individually reverted. No other test moved in either revert.

## Mode D — live browser re-verification (own browser, own script, real dev store)

Started `uv run uvicorn autotester.ui.app:app --host 127.0.0.1 --port 8791` against
the real `projects/`/`.env` store. Drove Chromium via Playwright MCP myself (no
maker screenshots read).

| did | observed |
|---|---|
| onboarded `ck079chk` with credential `CK079_SECRET=ck079-known-secret-value-24681` | project created, redirected to `/projects/ck079chk` |
| onboarded a second project with `slug=ck079-known-secret-value-24681` (the known credential value, slug-shaped) | **HTTP 400**, body `"the slug looks like it contains a real credential…"` — no raw value echoed |
| checked disk | no `projects/ck079-known-secret-value-24681` directory created |
| declared `CK079_ANOTHER` on `ck079chk`, set its `.env` value to `CK079_LEAKY_KEY_9999` (key-pattern-shaped: uppercase/digits/underscores) | value saved |
| declared a new secret with `key=CK079_LEAKY_KEY_9999` (the known credential value) | **HTTP 400**, body `"the key looks like it contains a real credential…"` — no raw value echoed |
| checked `projects/ck079chk/project.json` on disk | `grep -c CK079_LEAKY_KEY_9999` → 0; declared secrets list unchanged (`['CK079_SECRET', 'CK079_ANOTHER']`) |
| console messages (all, level=error) | 2 entries total, both the expected 400 network-status logs for the two refused POSTs — no app-side JS error |

Cleanup: `projects/ck079chk` directory removed (`rm -rf`, untracked, no git impact);
the two `CK079_*` lines removed from the repo-root `.env`; dev server on port 8791
stopped and confirmed unreachable. `git status --short` on `.env`/`qa/`/`projects/`
shows no residue from this run (only pre-existing untracked project dirs unrelated
to this check and one unrelated `qa/.last-tick` timestamp bump).

LIVE-BROWSER: `qa/evidence/browser-at079-080-credential-guard-gaps-2026-09-11-checker/`
— **not written as a separate report.json**; this verdict file itself carries the
full interaction table and evidence per the table above (no `report.json` was
produced this run — see EXPLANATION).

## Judgment against U9

- Matching runs against the full `.env`, not just declared values: the second
  onboarding attempt used `CK079_SECRET`'s raw value even though `CK079_SECRET`
  was declared on the *first* project, not a value scoped to the attempt itself —
  confirms cross-field, cross-request matching, consistent with U9's "every value
  in the shared `.env`, declared as a `SecretRef` or not."
- Nothing was written to disk on either refusal (directory count and
  `project.json` content both checked directly, not inferred from the HTTP
  status).
- No raw value appeared in either response body.
- The byte-identical-to-stored exemption (AT-078) is untouched by this unit — it
  does not apply to fresh `slug`/`key` values, and neither test path exercised it.
- U8 (case form) and U7 (base-url/domain composition) are not re-verified by this
  unit and are not claimed to be.

## FAILURES

None found at >80% confidence.

## EXPLANATION

Every claim in the manifest reproduced independently: the two regression tests, the
full suite, ruff, doctor, the isolated sabotage (each fix's own test is the only one
that breaks when reverted), and a live-browser re-run of both refusals against a
real dev server and the real `projects/`/`.env` store, with disk state checked
directly rather than inferred from HTTP status. One process note: this checker's
live-browser evidence is recorded in this verdict file rather than as a separate
`qa/evidence/.../report.json` (no `report.json` was generated this run) — the
underlying interactions and their results are nonetheless independently reproduced
and tabulated above, not read from the maker's smoke pass. The contract-label
mismatch in the dispatch/manifest ("U8" vs. the actually-applicable U9) is noted but
does not change any finding.

VERDICT: PASS
SCOREBOARD: 1/1 criteria met (U9, credential-guard-gaps portion), 0/0 invariants (none additional)
FAILURES (if any): none
LIVE-BROWSER: interaction table above (own Chromium via Playwright MCP against `uv run uvicorn` on port 8791, real `projects/`/`.env` store) — no separate report.json this run
ISSUES-WRITTEN: none (AT-079 and AT-080 updated open→fixed in qa/issues.jsonl, not new issues)
EXPLANATION: Both regressions (AT-079 slug, AT-080 key) reproduced independently via re-run tests, isolated git-archive sabotage, and a live browser session against the real dev store; no raw credential ever appeared on disk or in a response body in any check.

---

## INDEPENDENT CONCURRENT CHECK

**Checker:** second, independent fresh subagent (checker-b), Mode A + Mode D, bound to `D:/autoTesting`
**Date:** 2026-09-11
**Cycle checked:** 1
**Relationship to the verdict above:** this was **not** a deliberate dual check (the manifest says
`Dual check: no`). Two checkers were dispatched for the same unit + cycle by different sessions and
both ran to completion. The verdict above is left **byte-intact**; this section is appended per the
concurrent-verdict rule. My Mode D evidence is written to a separate directory
(`…-checker-b/`) so it cannot overwrite or contradict the primary checker's. I read the verdict above
only **after** completing every check below, so nothing here is derived from it.

### Re-run verify commands (my own execution)

```
$ uv run pytest tests/test_ui_credential_safety_project.py -q
................                                     [100%]   EXIT=0   (16 passed)

$ uv run pytest -q
[all dots, one 's'] ......... [100%]                 PYTEST_EXIT=0

$ uv run ruff check src tests scripts
All checks passed!                                   RUFF=0

$ uv run autotester doctor
doctor: clean                                        DOCTOR=0
```

All four reproduce the manifest's claimed outputs. Note the working tree carries **no** uncommitted
source diff — the unit landed as commit `2d7d824`, so what I verified is the committed artifact.

### C7 — my own mutation run, with the assertions C7 demands

Isolated `git archive HEAD` extract at a scratch path with its **own** `uv sync` venv;
`autotester.__file__` confirmed to resolve **inside the extract**, never the live tree (AT-101).
Harness asserts baseline-green, anchor uniqueness, on-disk change, and **kill attribution**:

| step | anchor matched | file changed (sha) | exit | failures | status |
|---|---|---|---|---|---|
| baseline | — | — | 0 | none | **asserted green before believing anything** |
| A — revert AT-079 (`("the slug", project.slug)` removed) | **1** | `2d0d7b253e3e → 23c959531d42` | 1 | `test_a_credential_shaped_slug_at_onboarding_is_refused` | **KILLED (attributed, no collateral)** |
| B — revert AT-080 (`("the key", key)` removed) | **1** | `11b5c5b137f0 → 655c05f5f097` | 1 | `test_a_credential_shaped_key_is_refused` | **KILLED (attributed, no collateral)** |
| restored baseline | — | — | 0 | none | restore verified by sha |

Neither test is vacuous, and neither kill is an unattributed exit-code artefact (the AT-218 class).
This is an **independent** mutation run: same conclusion as the primary checker, arrived at
separately, with the anchor-count / file-changed / attribution assertions stated explicitly.

### Adversarial probing — trying to get a credential PAST the guard

13 hostile probes through my own `TestClient` on a scratch `AUTOTESTER_ROOT`, against two live
`.env` values chosen to fit each field's own shape constraint (a lowercase/hyphen value for `slug`,
an uppercase/underscore value for `key`). **`on_disk_credential_leaks: []` — no raw credential
reached any file.**

| probe | result |
|---|---|
| `slug` = exact credential | **400**, guard message, nothing created |
| `slug` = credential + suffix / prefix | **400** both, guard message |
| `slug` = credential with an inner space | 400 `invalid project slug` — `_require_slug` fires first, no echo |
| `slug` = credential with a **unicode hyphen look-alike** (U+2010) | 400 `invalid project slug`, no echo |
| `slug` = URL-encoded credential (`%2D`) | 400 `invalid project slug`, no echo |
| `key` = exact credential | **400**, guard message |
| `key` = credential + suffix / prefix | **400** both |
| innocent controls (`slug`, `key`) | accepted — the guard does not brick ordinary use |
| **`slug` = case-and-separator transform of an uppercase credential** | **303 ACCEPTED — see AT-339** |
| **`key` = case-and-separator transform of a lowercase credential** | **303 ACCEPTED — see AT-339** |

The unicode and whitespace forms are refused, but by `_require_slug`'s shape regex rather than by the
credential guard — correct outcome, narrower mechanism than it looks.

### Mode D — my own live browser (own server, own scratch store)

`uv run uvicorn autotester.ui.app:app --host 127.0.0.1 --port 8137` with
`AUTOTESTER_ROOT` = a scratch directory — deliberately **not** the real `projects/`/`.env` store, so
this run could not perturb live configuration. Real Chromium via Playwright MCP; no maker screenshot
opened, no `curl` substituted for an interaction. Evidence:
`qa/evidence/browser-at079-080-credential-guard-gaps-2026-09-11-checker-b/report.json`.

| # | did (clicked, not fetched) | asserted state change |
|---|---|---|
| 1 | typed the `/onboard` form and clicked **Create project** | landed on `/projects/chkseed`; `project.json` on disk carries the typed values |
| 2 | secrets form: `key=CHK_PASSWORD`, clicked submit | `project.json` re-read off disk → `secrets == ['CHK_PASSWORD']` |
| 3 | **AT-080 hostile:** `key` = the raw `.env` value of `CHK_APIKEY` | **HTTP 400**, guard message, raw value **absent** from `outerHTML`, secrets list unchanged on disk |
| 4 | **AT-079 hostile:** `slug` = the raw `.env` value of `CHK_PASSWORD` | **HTTP 400**, guard message, raw value **absent** from `outerHTML`, **no directory created** (`projects/` still only `chkseed`) |
| 5 | **non-brick:** declared a second legitimate key `CHK_APIKEY` | disk → `secrets == ['CHK_PASSWORD', 'CHK_APIKEY']` — the new `key` entry does not refuse honest input |
| 6 | grep of the whole scratch root for both raw values, `.env` excluded | **zero files** |
| 7 | **AT-339:** `slug` = `zebra-quilt-apikey-31` (transform of `ZEBRA_QUILT_APIKEY_31`) | **303 accepted**, directory + `project.json` created |
| 8 | opened `/` to see what that renders | transform present in `outerHTML`; the raw credential is not |

**Console errors: 2 for the entire session**, both the browser's own
`Failed to load resource: … 400 (Bad Request)` line for the two deliberately-refused POSTs. Every GET
page recorded **0**. No unexplained console error anywhere.

### Git-tracked leak check (public repo)

`git grep` over `HEAD` for every smoke/probe value: the only tracked hits are the maker's own
**fabricated** values inside the manifest text itself. Nothing from either the maker's or my probes
reached a tracked file. `.env` is gitignored (`.gitignore:2`), `projects/` has 12 tracked files and
none carries a probe value. Both maker smoke projects are gone from `projects/`.

### Judgment

Same criteria as the primary verdict, judged separately.

- **Contract label:** the manifest header cites **U8**, but U8 pins the *case form only* and says in
  terms that the `project.json` routes are "not covered here". The applicable criterion is **U9**.
  I judged against U9. Cosmetic mis-citation; it changes nothing.
- **U9 (wiring):** `_guard_intake` (`src/autotester/ui/app.py:203-212`) and `declare_secret`
  (`src/autotester/ui/routes_project_edit.py:231-234`) both call `_refuse_unsafe_submission`
  **before** any `save_project`; I confirmed by reading the routes that nothing between form-parse
  and the guard writes to disk (`parse_secret_rows` / `parse_intake_sources` are pure, and
  `_require_reachable_base_url` — the AT-088 echo path — now runs *after* the guard). **Met.**
- **U9 (full-`.env` matching, the AT-083 line that must never be softened):** confirmed at the source
  — `ProjectPaths.env_file` is the **shared root** `.env`, and `SecretStore.redactor()` masks
  `{**shadow, **values}`, i.e. undeclared keys too. My live refusals used a value declared on a
  *different* project. **Met, unsoftened.**
- **U9 (must not brick):** the byte-identical exemption is untouched; interaction 5 and the innocent
  controls confirm honest input still passes. **Met.**
- **C7:** met, with attribution (table above).
- **Nothing echoed, nothing written, nothing tracked:** met on my own evidence.

### FAILURES

None at >80% confidence. My verdict **agrees** with the primary checker's PASS.

### ISSUES-WRITTEN (checker-b)

- **AT-339** (medium, open) — the guard matches case-**sensitively**, so a credential's
  case-and-separator transform passes every guarded field, `slug` included; live-reproduced both ways
  (lowercase-form slug → directory name + URL + home-index text; uppercase-form key → git-tracked
  `project.json::secrets[].key`). **Filed, not charged:** U9 pins the wiring, no *raw* value reached
  disk in any probe, and the manifest explicitly scopes itself out of the matching logic. It is,
  however, the same class AT-074 already closed for `unquote_plus` and whitespace — case folding is
  the sibling that was never added.
- **AT-340** (low, open) — the maker's smoke pass left `SMOKE_PASSWORD` and `SMOKE_ORIGINAL_KEY` in
  the **real** repo-root `.env`, and printed their values in the git-tracked manifest, so two strings
  that are public in this repo now silently refuse themselves in every guarded field for every
  project (the AT-076 shape, created by test residue). No security impact; live state left behind.

### Disagreements with the verdict above

None on the verdict. Two process notes, neither changing the outcome:

1. The primary check ran Mode D against the **real** `projects/` store and wrote two `CK079_*` lines
   into the **real** root `.env` before removing them. Mine used a scratch `AUTOTESTER_ROOT` and
   touched neither. Both are defensible; the scratch form cannot leave AT-340-shaped residue.
2. The primary verdict's `LIVE-BROWSER:` names
   `qa/evidence/browser-at079-080-credential-guard-gaps-2026-09-11-checker/` while stating no
   `report.json` was written there — that directory is therefore **absent**, and a later reader
   following the path will find nothing. Mine exists at the `-checker-b` path. Worth a one-line fix
   by whoever owns that verdict; not a finding against the unit.

```
VERDICT: PASS
SCOREBOARD: 1/1 criteria met (U9 — the slug/key portion this unit claims), 1/1 invariants hold (C7, mutation-attributed)
FAILURES (if any): none at >80% confidence
LIVE-BROWSER: qa/evidence/browser-at079-080-credential-guard-gaps-2026-09-11-checker-b/report.json (own Chromium via Playwright MCP, own uvicorn on port 8137, scratch AUTOTESTER_ROOT; 8 interactions, 2 console errors session-wide, both explained 400s)
ISSUES-WRITTEN: AT-339, AT-340
EXPLANATION: Every manifest claim reproduced on my own evidence — four verify commands, an isolated mutation run whose kills are attributed to exactly the two named tests with baseline-green and anchor-uniqueness asserted, 13 hostile probes, and an 8-interaction live browser run. The two fields AT-079/AT-080 named are genuinely guarded, refuse with no raw echo, and write nothing on refusal, while honest input still passes. Two residuals filed rather than charged: the matcher is case-sensitive so a credential's case/separator transform still lands in a git-trackable artifact (AT-339), and the maker's smoke run left two fake credentials in the real root .env (AT-340).
```
