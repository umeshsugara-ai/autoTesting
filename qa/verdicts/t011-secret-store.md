# Verdict — t011-secret-store

**Date:** 2026-09-03
**Mode:** A (unit check)
**Bound project root:** `D:/autoTesting` — all paths read/written resolve inside it.
**Manifest:** `qa/manifests/t011-secret-store.md` (Status: ready-for-check, Fix cycle 1 of 3)
**Contracts judged:** `qa/contracts/browser-and-secrets.md` B1–B4 (B5–B9 = T-010, out of unit)
+ `qa/contracts/core-invariants.md` C1–C8
**Adapter:** `qa/adapter.json` — `verify.kind = shell`; every command I ran is allowlisted there
or is a manifest-declared command.
**Cycle checked: 1**

## VERDICT: FAIL

Two demonstrated exploits against the two criteria that ARE the credential boundary (B2, B3).
Everything else in the unit is genuinely strong — the shape of the class, the fail-closed
defaults, the negative-path tests, the `__repr__` discipline. The failures are narrow holes,
not a wrong design.

---

## What I re-ran myself (no pasted output trusted)

| Command | My result | Manifest claimed | Match |
|---|---|---|---|
| `uv run pytest tests/test_secrets.py -q` | exit 0, 16 passed (`................`) | exit 0, 16 passed | ✅ |
| `uv run pytest -q` | exit 0, 42 passed | exit 0, 42 tests | ✅ |
| `uv run ruff check src tests` | exit 0, `All checks passed!` | same | ✅ |
| `uv run autotester doctor` | exit 0, `doctor: clean` | same | ✅ |
| `git ls-files \| grep -E "\.env$"` | no output (rc=1) | no output | ✅ |
| `uv run pytest tests/test_core.py -q` (C5) | exit 0, 9 passed | not claimed | ✅ |
| `grep -rE "^(import\|from) (anthropic\|google)" src/autotester/stages/` (C8) | no such directory — vacuous | not claimed | n/a |

Every pasted output in the manifest reproduced exactly. No fabrication, no summary-in-place-of-output.
The manifest is honest, including its self-reported two caught defects.

I also read, in full: `src/autotester/browser/secrets.py`, `src/autotester/core/redact.py`,
`src/autotester/schema/project.py`, `tests/test_secrets.py`, `.gitignore`,
`src/autotester/doctor.py:18-32`.

## Adversarial probes I ran against the boundary

Written to a scratch script and executed under `uv run python`. Eight attempts to get a real
secret value out of `SecretStore` into a prompt, a log, an artifact, a traceback, or a wrong host.
**Two succeeded.**

| # | Attack | Result |
|---|---|---|
| E1 | Raw 3-char secret placed in a prompt string | 🔴 **LEAKED** — `guard_prompt` returned normally; `Redactor.scrub` left it verbatim |
| E2 | `SecretRef(domains=[""])` + unparseable destination (`resolve(..., "")`) | 🔴 **LEAKED** — returned `supersecretvalue`, no exception |
| E3 | `load(strict=False)` then resolve a missing key | ✅ fails closed (`MissingSecret`) |
| E4 | `PW=abc # note` inline comment | ⚠️ wrong value loaded → redactor masks the wrong string |
| E5 | Host confusion: `https://a.test@evil.test/`, `a.test.evil.test`, `//a.test\@evil.test`, `EVIL.test?r=a.test`, port | ✅ all resolve to the attacker host and are refused; no userinfo or suffix confusion |
| E6 | Force an exception and inspect the traceback for the value | ✅ absent; `__repr__` clean (note: `vars(store)` still holds plaintext — inherent, see below) |
| E7 | Stray undeclared credential in the same `.env`, then log it | ⚠️ unmasked (AT-004) |
| E8 | Mixed placeholder `{{SECRET:PW}} and {{SECRET:NOPE}}` — hoping for a partial return | ✅ raises before returning; no partial string escapes |

---

## Criterion-by-criterion

### B1 — Loading — **MET**
- Loads `.env` keyed by declared `SecretRef[]` (`secrets.py:82-102`). ✅
- Missing declared key raises `MissingSecret` naming the key (`:96-98`); reproduced by
  `test_declared_key_missing_from_env_raises_and_names_the_key` and by the absent-file test.
  No empty-string fallback, no cross-project env fallback — `parse_env` reads only the given
  path and never touches `os.environ`. ✅ (I checked specifically for an `os.environ` fallback;
  there is none. Good.)
- Undeclared key ignored + reported via `store.undeclared`, never usable (`:100-101`,
  `__contains__`). ✅

### B2 — Placeholders only, in every direction — **NOT MET** (AT-002)
- `resolve(step_value, host)` accepts `{{SECRET:KEY}}` and returns the value only on a matching
  host, else raises. ✅ Probe E8 confirms no partial substitution escapes on a mixed failure.
- "never stored, logged, or returned to a caller that persists it": no consumer of `resolve` /
  `redactor()` / `guard_prompt` exists anywhere in `src/` yet (I grepped) — nothing to violate it,
  so this bullet is unfalsifiable at T-011 and carries to T-010. Not counted against the unit.
- 🔴 **"a raw secret value in a prompt raises rather than being masked-and-sent" — does not hold
  unconditionally.** `core/redact.py:15` sets `_MIN_SECRET_LEN = 4`, applied inside
  `assert_no_raw_secrets` (`:69`) and `Redactor.__init__` (`:28`). A declared secret of 1–3
  characters is silently allowed straight into a model prompt. Reproduced (E1).
  The floor is correct for *scanning* arbitrary text; it is wrong for *known-exact declared
  values*, where the caller knows precisely which strings are forbidden. Fix in code —
  do not amend the criterion.

### B3 — Domain scoping is enforced, not advisory — **NOT MET** (AT-001)
- Narrower-than-allowlist scoping is genuinely enforced: `test_secret_scoped_narrower_than_the_
  project_allowlist_is_still_refused` proves a secret scoped to `auth.pathlynks.test` is refused
  on `app.pathlynks.test` even though the project allows the parent. That is the hard half of B3
  and it is correct. Lookalike (`notpathlynks.test`) and userinfo (`a.test@evil.test`) attacks
  both fail closed. ✅
- 🔴 **The gate fails OPEN on an empty host.** `_host_matches(host, domain)` at `:61-63` returns
  `host == domain`, so `_host_matches("", "")` is `True`. `host_of()` returns `""` for any
  unparseable `url_or_host`, and `resolve()` never rejects an empty host. `SecretRef.domains`
  (`schema/project.py:22`) has no validator forbidding empty entries. So a project config
  carrying a blank domain string — a stray comma in JSON, a trailing entry — turns a malformed
  destination into a credential release. Reproduced (E2). The control's safety currently depends
  on config hygiene, which is the definition of "advisory".
  **Fix direction:** raise unconditionally when `host_of()` yields `""`, and reject empty/blank
  entries in `SecretRef.domains` at the schema layer. Two lines, defence in depth.
- "Navigating outside `allowed_domains` is refused by the session": `browser/session.py` does not
  exist (only `__init__.py` and `secrets.py`). This bullet is duplicated verbatim as **B6** under
  T-010, so I attribute it there rather than failing T-011 on a module the unit does not claim.
  Flagged for the T-010 check, not charged here.

### B4 — Evidence is clean — **PARTIAL, not charged as a failure**
- `redactor()` masks every *loaded* value and renders `[REDACTED]:KEY` (key name, not value). ✅
- `__repr__` never renders a value; verified in a real traceback (E6). ✅
  *Residual note, not a finding:* `store._values` / `vars(store)` still hold plaintext, so a
  framework that renders locals (`pytest --showlocals`, Sentry, `rich` tracebacks) would expose
  them. Inherent to holding secrets in memory; worth a comment when logging lands in T-010.
- Screenshot masking explicitly defers to B7/T-010 by the contract's own cross-reference;
  `masked_field_keys()` supplies the hook and is tested. Correctly out of unit.
- Two masking gaps filed as S3 rather than as B4 failures: short values (AT-002, already charged
  under B2) and undeclared `.env` values (AT-004 — B1 says ignore, B4 says mask everything;
  that tension is the contract's, not the maker's, so I am not charging it).

### Core invariants C1–C8 — **8/8 hold**
- **C1** schema-first — `SecretRef`/`Project` are Pydantic with `extra="forbid"`; `secrets.py`
  introduces no dict/dataclass domain shape. `tests/test_schema.py` green in the full run. ✅
- **C2** readable — `secrets.py` 155 lines, `test_secrets.py` 160, longest function well under 50;
  module + every public method carries a docstring stating its one job. `doctor` exit 0. ✅
- **C3** one concept one place — `doctor` duplicate-concept and drift-filename rules exit 0; new
  package `browser/` is stated with a reason in the manifest; no `*_v2.py`-class filenames. ✅
- **C4** root clean — `doctor` exit 0. The maker widened `ALLOWED_ROOT_ENTRIES` (`doctor.py:22-26`)
  to admit `CLAUDE.md`, `qa`, `.goal`. **I scrutinised this as a possible rule-softening to pass a
  failing gate and it is not:** C4's own text names `qa` and `.goal` as declared layout entries and
  `CLAUDE.md` as a config file. The allowlist was stale against the contract, and it was edited in
  place. Legitimate. ✅
- **C5** secrets never reach a model/log/artifact — `tests/test_core.py` 9 passed; `.gitignore`
  covers `**/.env`, `**/.env.*`, `profiles/`, `.work/`, `projects/*/runs/`;
  `git ls-files | grep -E "\.env$"` empty. Placeholder-only discipline is the module's whole
  design. ✅ *(The two exploits above are B2/B3 failures of the mechanism's edges, not C5
  structural violations — no secret field exists on any schema model, which is what C5 asserts.)*
- **C6** artifacts human-editable — not exercised by this unit; nothing regressed. ✅
- **C7** verification independent — I re-derived every result myself in a fresh context; the
  manifest pastes real output, not a summary. `uv run pytest -q` exit 0. ✅
- **C8** provider-agnostic — `src/autotester/stages/` does not exist yet; `secrets.py` imports no
  vendor SDK. Vacuously holds; no-fire list covers later-phase absence. ✅

## SCOREBOARD

**2/4 contract criteria met (B1, B4-partial-by-design), 8/8 invariants hold.**
B2 and B3 fail on demonstrated exploits.

## Issues written

| id | sev | title |
|---|---|---|
| AT-001 | S1 | Domain gate fails open on empty host (`_host_matches("","")` → True) |
| AT-002 | S2 | `guard_prompt`/`Redactor` ignore secrets shorter than `_MIN_SECRET_LEN` |
| AT-003 | S3 | `parse_env` keeps trailing inline comments → wrong value AND wrong redaction target |
| AT-004 | S3 | Undeclared `.env` values are not in the Redactor |
| AT-005 | S3 | `load(strict=False)` branch untested |

## What the maker should do next (cycle 2)

1. **AT-001 first** — `resolve()` raises when `host_of()` returns `""`; add a `SecretRef.domains`
   validator rejecting blank entries. Add both as tests.
2. **AT-002** — drop the length floor for known-exact declared values in `assert_no_raw_secrets`
   (keep it for heuristic scanning if the scanner ever grows one). Add a test with a 3-char secret.
3. AT-003 / AT-005 are cheap; AT-004 needs a contract decision (B1-ignore vs B4-mask) and should
   go to `qa/feedback-inbox.md` rather than being guessed at.

**Do not soften B2 or B3 to close this.** A failing artifact is evidence about the artifact.

## Note on the fix cycle

This is cycle 1 of max 3. The unit is close — the architecture, the fail-closed defaults, and the
negative-path test discipline are all right. Two edge holes in a CRITICAL control is a FAIL, but a
cheap one.
