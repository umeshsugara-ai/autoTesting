# Verdict — ui-secrets-declaration

**Date:** 2026-09-07
**Contract:** qa/contracts/ui.md
**Manifest:** qa/manifests/ui-secrets-declaration.md
**Cycle checked: 1**
**Checker:** fresh Mode A subagent, bound to `d:/autoTesting`, no builder context.

**Note on the prior attempt:** a previous checker died mid-run before writing a verdict. Nothing it
produced was trusted or reused. Baseline re-established at the start of this run: the repo-root
`.env` contained no `SCRATCH_PW` and no probe residue (verified by grep), and no stale scratch
project existed under `projects/` — the maker's cleanup is confirmed good. This check started from
zero.

## VERDICT: PASS

**SCOREBOARD: 7/7 criteria met, 0 failures.** (ui.md declares no `[I*]` invariants of its own; the
dependency invariants exercised here — the U3 credential boundary and `Project`'s `extra="forbid"` —
both hold.)

---

## What I re-ran myself (nothing below is the maker's pasted output)

| Command | My result |
|---|---|
| `docker compose exec -T autotester uv run pytest -q` | **333 passed, 1 skipped**, 0 failures |
| `docker compose exec -T autotester uv run pytest -q tests/test_ui_secrets_declaration.py` | **11 passed** — matches the claim |
| `docker compose exec -T autotester uv run ruff check src tests scripts` | `All checks passed!` |
| `docker compose exec -T autotester uv run autotester doctor` | `doctor: clean` |
| `docker compose exec -T autotester uv run autotester map` | **no diff** to `docs/MAP.md` — the manifest says it was "regenerated"; regenerating again is a no-op, so MAP is genuinely current. The module's first docstring line is unchanged, which is why there is no diff to see. |

Plus a live end-to-end probe against `http://localhost:8010` in the running container, using a
throwaway project `chk-scratch` (created via `POST /onboard`, **deleted at the end** — see Cleanup).

---

## Criterion-by-criterion

### U3 — the env editor never renders a real secret value · **MET** (the priority item)

Judged on four independent lines of evidence, not on the module's docstring.

1. **`SecretRef` structurally cannot carry a value.** `schema/project.py:11-39` — the fields are
   `key`, `description`, `domains`, `mask_in_screenshot`. There is no value field, and
   `model_config = ConfigDict(extra="forbid")`, so one cannot be smuggled in as an extra.
2. **The declare route ignores any extra posted field.** Probed hostilely: posted `CHK_PROBE_KEY`
   with three extra fields `value`, `secret` and `password`, each carrying the canary
   `LEAKCANARY9999`. Result `303`; the persisted `projects/chk-scratch/project.json` contained
   **zero occurrences** of the canary. This is structural rather than incidental — `declare_secret`
   binds only four named `Form(...)` params, so an unlisted field is never read at all, and even if
   it were, `extra="forbid"` would reject it.
3. **A declared key never causes a VALUE to render.** Fetched `/projects/chk-scratch/edit`,
   `/projects/chk-scratch/env` and `/projects/chk-scratch` — canary count **0 in all three**.
4. **The strongest test available: a project with real values on disk.** `pathlynks` declares four
   `SecretRef`s (`PATHLYNKS_COUNSELLOR_EMAIL/PASSWORD`, `PATHLYNKS_USER_EMAIL/PASSWORD`) *and* the
   repo-root `.env` holds real values for all four. I scanned the rendered `/env` and `/edit` HTML
   for every `.env` value of length >= 6. **No credential value appears in either page.** The pages
   carry only the key name and a `Set` / `Not set` pill.

   One scan hit required investigation and is **dismissed**: `PATHLYNKS_USER_LOGIN_URL`'s value
   matched. It is `https://pathlynks.vidysea.com/signin`, byte-identical to the project's own
   `base_url`, and it appears in the U7 edit form's `base_url` input — not in the secrets card. It
   is not a declared `SecretRef`, it is not a credential, and `project.json` already stores that
   same string in cleartext. Pre-existing U7 behaviour, correct, not attributable to this unit.

`erp`, the project this unit exists to unblock, now renders `ERP_EMAIL` and `ERP_PASSWORD` as
`Not set` on `/env`, and the "declares no credentials" empty state is gone. Confirmed live by me,
not read from the manifest.

### U5 — user-supplied values are HTML-escaped, on the new form surface · **MET**

Probed with a description carrying every dangerous character:
`quote" single' <script>alert('xss')</script> end`. The rendered row came back as:

    <td class='meta'>quote&quot; single&#x27; &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt; end</td>

`"` to `&quot;`, `'` to `&#x27;`, `<`/`>` to entities. `html.escape` is called with its default
`quote=True` at every one of the four render points in `_secret_row`, and on `default_domains` in
`_secrets_card` (which lands inside a single-quoted `value='...'` attribute — the `'` escaping is
exactly what makes that safe). **Zero raw `<script` occurrences across all six pages I fetched**,
including against a project whose `name` is `<script>alert(1)</script>&'"X`.

**The `action=` URL interpolation is the sharpest part of this criterion, and it holds.** The key is
placed unquoted-in-path at `routes_project_edit.py:48`:
`action='/projects/{safe_slug}/secrets/{key}/delete'`. Safety rests entirely on `SecretRef`'s
`^[A-Z][A-Z0-9_]*$` pattern, which admits only `A-Z`, `0-9` and `_` — no `/`, `%`, `.`, `..`, space,
quote or angle bracket can ever reach that string. I did not take that on reading; I probed the
boundary, and all were refused **400 with nothing written to disk**:

| Submitted key | Result |
|---|---|
| `A' onmouseover=x` | 400 — pattern |
| `A"><img src=x>` | 400 — pattern |
| `A/../../etc` | 400 — pattern (path traversal in the action URL is unreachable) |
| `A B`, `lower_case`, `_LEADING`, `1DIGIT` | 400 — pattern |
| 70 x `A` | 400 — `_reject_value_like` ("looks like a value, not a name") |
| *(omitted entirely)* | 422 — FastAPI required-field |

Since only pattern-conforming keys can ever be persisted, and `Project` re-validates every
`SecretRef` on load, a key read back from disk is equally constrained. The `escape()` applied to it
is belt-and-braces, correctly applied anyway.

### C3 / "one concept, one place" — validation is `SecretRef`'s own · **MET, and the one extra rule is justified**

The route re-implements nothing. The 400 bodies I got back carry pydantic's own wording verbatim —
`"String should match pattern '^[A-Z][A-Z0-9_]*$'"` and `"Value error, secret key looks like a
value, not a name"` — which is only possible if the pattern, the length rule and the blank-domain
rule are enforced by the model and merely surfaced by `except ValidationError`. The route adds no
regex, no length check and no domain-shape check of its own.

The single extra rule — refusing an empty `domains` list — I verified is a real gap in the model and
not redundancy, by executing both halves in-container:

    SecretRef(key='EMPTY_SCOPE', domains=[])  -> VALIDATES OK
      {'key': 'EMPTY_SCOPE', 'description': None, 'domains': [], 'mask_in_screenshot': True}
    SecretRef(key='X', domains=[''])          -> ValidationError   (_reject_blank_domains)

So `domains=[]` genuinely passes today, and `browser/secrets.py` confirms the deferred failure the
manifest claims: *"An empty return makes `resolve()` raise `SecretScopeError`"* ->
`raise SecretScopeError(f"cannot resolve a secret for destination {url_or_host!r}")`. Such a key
would be declarable, would appear enterable on the Credentials page, and would fail only at typing
time inside a run. Refusing it at declaration is fail-fast on a real hole, not a duplicated
validator. Live-confirmed that the rule is correctly narrow: `domains="  ,  , "` -> 400 *"name at
least one host this credential may be typed into"*, while `domains="example.com, ,sub.example.com"`
-> 303 (the blank is dropped, the good ones survive), so legitimate input is not rejected.

### No second write path to `.env` · **MET**

`grep -n "\.env" src/autotester/ui/routes_project_edit.py` returns **five hits, all inside
docstrings** — lines 5, 19, 57, 161, 186. No code reference at all. The module imports no
`SecretStore`, no `env_editor`, no `parse_env`, no `repo_root`; its only store call is
`ProjectStore.save_project`. A repo-wide grep confirms `ui/env_editor.py::set_env_value` is still
the only function that writes `.env` (its two callers, `routes_credentials.py:65` and
`routes_settings.py:67`, both pre-date this unit and go through it).

Behavioural proof rather than grep alone: `md5sum .env` was **identical before and after** the
entire probe sequence — declares, deletes, refusals and all — at
`1dcec82fda94c7c2611d4d662c3d09ec`. Undeclaring `OKKEY2` returned 303 and left `.env`
byte-identical, exactly as the docstring promises.

### Blast radius · **MET**

- All five on-disk projects load through `ProjectStore.load_project()` with `Project`'s
  `extra="forbid"` in force: `erp`, `pathlynks`, `regression-demo`, `vidysea-erp` (and the scratch
  project, since removed) — **all OK**, none raised.
- A project with `secrets: []` behaves exactly as before: `vidysea-erp` and `regression-demo` both
  still render *"This project declares no credentials"* on `/env`, and the new card shows the honest
  empty state *"No credentials declared yet — this project can only test pages that need no login."*
  rather than an error or a bare table.
- **U7 regression (same file, so re-checked in full):** `POST /projects/erp/edit` with an
  out-of-scope `base_url` still returns 400 naming the host (*"its base URL host 'evil.example.net'
  is not covered by allowed domains ..."*); a blank name -> 400; an empty domain list -> 400; and
  `project.json` was unchanged after all three refusals. A **successful** edit preserved `secrets`
  (`['ERP_EMAIL','ERP_PASSWORD']`), `write_policy` and `providers` through `model_copy` — the U7
  field-preservation rule survives `secrets` becoming editable elsewhere on the same page.

### U1, U2, U4, U6 · **MET (unaffected, verified rather than assumed)**

- **U1** — no UI-only representation added; the new routes persist a real `schema.project.SecretRef`
  inside the same `projects/<slug>/project.json` via `ProjectStore.save_project`. I read the file
  back and it is CLI-shaped.
- **U2** — every new route calls `_load_project_or_404`; probed `POST /projects/no-such-proj/...` ->
  **404**, on both declare and delete. State is read live per request (a fresh `ProjectStore` per
  call).
- **U4** — no run/report code imported or touched; full suite green.
- **U6** — the add-a-case flow is untouched; its tests pass in the full run.

### Manifest claims audited

*"Issues addressed: none"* — consistent with the ledger (no open row was closed by this unit). The
manifest's own end-to-end narrative (BEFORE/AFTER on `erp`) I reproduced independently and it is
accurate. Every line under "Actual outputs" reproduced.

---

## Findings filed (neither is a criterion violation; neither blocks PASS)

- **AT-068** · low · the declare-secret 400 echoes the raw submitted key back
  (`{"detail":"cannot declare 'hunter2': ..."}`), and the card's own hint names pasting the *value*
  into the Key field as the anticipated user error. It is a JSON body, so not an XSS, and nothing is
  persisted — but it is the single place in this unit where a would-be credential is repeated back
  rather than dropped.
- **AT-069** · low · the module docstring at line 13 cites ledger id `AT-068` as this unit's tracker,
  but no such row existed when the code was written (max was `AT-067`), and `AT-068` has now been
  allocated to an unrelated defect — so the pointer resolves to the wrong thing. Cite the manifest
  instead.

## Observations (questions, not failures)

- The declared `domains` scope is **not** constrained to the project's `allowed_domains`, so a key
  can be scoped to a host the browser may never visit. I judged this harmless rather than a gap:
  `browser/session.py::check_destination` gates navigation independently, so an out-of-scope entry
  can only ever narrow where a value is typed, never widen it. Prefilling the scope with
  `allowed_domains` is the right ergonomic answer. Raised only so the decision is on record.
- CSRF on these new POST forms is absent — explicitly in the contract's no-fire list for a localhost
  single-operator tool, so not counted against the unit.

---

## Cleanup performed (stated explicitly, per dispatch)

- **Nothing was ever written to the repo-root `.env`.** I deliberately never exercised
  `POST /projects/{slug}/env`; the value-leak probes used a canary in the *declaration* form and in
  rendered HTML only. `md5sum .env` is unchanged from before the check
  (`1dcec82fda94c7c2611d4d662c3d09ec`), and
  `grep -nE "LEAKCANARY|CHK_PROBE|SCRATCH_PW|OKKEY" .env` returns nothing.
- **The scratch project `projects/chk-scratch/` was deleted** (`rm -rf`); `ls projects/` is back to
  `erp`, `pathlynks`, `regression-demo`, `vidysea-erp`.
- **`projects/erp/project.json` was left with its two legitimate declared keys** (`ERP_EMAIL`,
  `ERP_PASSWORD`, scoped to `vidysea.com` / `www.vidysea.com`), as instructed. The refused-edit
  probes left it unchanged, and the one successful edit restored identical values.
- No real credential value was entered anywhere at any point.

## Commit action taken

Per the AT-055 lesson: the maker's source was **uncommitted** when this check began
(`src/autotester/ui/routes_project_edit.py` modified; `tests/test_ui_secrets_declaration.py` and
`qa/manifests/ui-secrets-declaration.md` untracked). I committed them myself with a narrow pathspec
covering exactly those three plus `docs/MAP.md` (which had no diff, so it contributed nothing).
`projects/`, `.work/` and `.env` were **not** committed.

## Conclusion

The security properties this unit had to earn are earned. A value cannot enter through the
declaration path (structurally — the model has no field for one and forbids extras), cannot be
smuggled through an extra form field (probed with three), and does not render on any page — proven
against a project holding four real credentials on disk, not merely a synthetic one. The new
`action=` URL surface is safe because the key pattern is genuinely restrictive, which I probed at
the boundary rather than inferred. Validation delegates to `SecretRef`, and the one added rule
closes a real hole the model leaves open. `.env` is untouched by this module, by grep and by
checksum.
