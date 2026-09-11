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
