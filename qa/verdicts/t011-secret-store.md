# Verdict — t011-secret-store

**Date:** 2026-09-03
**Mode:** A (unit check) — fix cycle 3 of 3 (last)
**Bound project root:** `D:/autoTesting` — all paths read/written resolve inside it.
**Manifest:** `qa/manifests/t011-secret-store.md` (Status: ready-for-check, Fix cycle 3 of max 3)
**Contracts judged:** `qa/contracts/browser-and-secrets.md` B1–B4 (B5–B9 = T-010, out of unit)
+ `qa/contracts/core-invariants.md` C1–C8, both as amended in cycle 2.
**Adapter:** `qa/adapter.json` — `verify.kind = shell`; every command I ran is allowlisted there
or is a manifest-declared command.
**Prior verdicts:** cycle 1 FAIL (AT-001..005), cycle 2 FAIL (AT-006, AT-007, AT-008).
**Cycle checked: 3**

## VERDICT: PASS

All three cycle-2 findings independently reproduced as closed. All four B criteria and all eight
core invariants hold on evidence I produced myself. No regression against the cycle-2 probes. No
new finding of any severity that a criterion requires.

---

## What I re-ran myself (no pasted output trusted)

| Command | My result | Manifest claimed | Match |
|---|---|---|---|
| `uv run pytest tests/test_secrets.py -q` | exit 0, 24 tests (24 `def test_` in file) | exit 0, 24 passed | ✅ |
| `uv run pytest -q` | exit 0, 50 tests (3+9+6+8+24) | exit 0 (50) | ✅ |
| `grep -rn "projects/<slug>/.env" docs src` | no output (rc=1) | no output | ✅ |
| `uv run ruff check src tests` | exit 0, `All checks passed!` | same | ✅ |
| `uv run autotester doctor` | exit 0, `doctor: clean` | same | ✅ |
| `git ls-files \| grep -E "\.env$"` | no output (rc=1) | `(none)` | ✅ |
| `uv run pytest tests/test_schema.py tests/test_core.py -q` (C1, C5) | exit 0, 17 passed | not claimed | ✅ |
| `grep -rE "^(import\|from) (anthropic\|google)" src/autotester/stages/` (C8) | no such dir — vacuous | not claimed | n/a |
| `wc -l docs/ARCHITECTURE.md` | 121 | 121 | ✅ |

Read in full: `src/autotester/browser/secrets.py` (196 lines), `src/autotester/schema/project.py`,
`docs/ARCHITECTURE.md`, `tests/test_secrets.py:195-215` (the two new tests), `git status`/`diff --stat`.

## Cycle-2 findings — re-probed, each one (scratch script under the session scratchpad, `uv run python`)

### AT-006 (S3) — parse_env comment handling — **fixed, verified**
`_clean_value` (`secrets.py:59-70`): a leading quote is closed at the next matching quote and the
remainder dropped; unquoted values are split on `\s#`. Eleven inputs:

| input | got | expected |
|---|---|---|
| `PW=abc\t# note` | `abc` | ✅ (cycle-2 failure) |
| `PW="abc" # c` | `abc` | ✅ (cycle-2 failure) |
| `PW='abc' # c` | `abc` | ✅ |
| `PW=abc  \t # x` | `abc` | ✅ |
| `PW=a#b` | `a#b` | ✅ fragment preserved |
| `PW="a #b"` | `a #b` | ✅ quoted `#` preserved |
| `PW="a'b"` | `a'b` | ✅ |
| `PW=""` | `` | ✅ |
| `PW=x\\y` | `x\\y` | ✅ |
| `PW="unterminated # x` | `"unterminated` | residual, not a criterion (no closing quote = garbage in) |

Pinned by `test_at006_tab_comment_and_quoted_then_comment`.

### AT-007 (S2) — host_of vs WHATWG — **fixed, verified**
`host_of` (`secrets.py:73-88`) returns `""` on any backslash in the raw input or any `urlparse`
userinfo; `resolve()` already raises `SecretScopeError` on `""` (AT-001). I cross-checked **35
destinations** through both `host_of()` and node v24.13.1 `new URL(u).hostname`:

| destination | `host_of` | WHATWG (node) | verdict |
|---|---|---|---|
| `https://evil.test\@pathlynks.test` (the cycle-2 leak) | `""` refused | `evil.test` | ✅ closed |
| `https://pathlynks.test@evil.test` | `""` refused | `evil.test` | ✅ closed |
| `https:\\pathlynks.test` | `""` refused | `pathlynks.test` | ✅ safe |
| `https://evil.test:@pathlynks.test` | `""` refused | `pathlynks.test` | ✅ safe |
| `https://@pathlynks.test` | `""` refused | `pathlynks.test` | ✅ safe |
| `https://user:pw@pathlynks.test`, `%2F@`, `%5C@`, U+2044`@` | `""` refused | `pathlynks.test` | ✅ safe |
| `https://pathlynks.test\evil.test`, `/\@x` | `""` refused | `pathlynks.test` | ✅ safe |
| `https://evil.test#@…`, `?@…`, `/@…`, `/..@…` | `evil.test` | `evil.test` | ✅ consistent, refused by scope |
| `https://pathlynks.test#@evil.test`, `?@`, `/@` | `pathlynks.test` | `pathlynks.test` | ✅ consistent |
| `https://pathlynks%2Etest`, `pathlynks．test` (U+FF0E), `evil.test。pathlynks.test` (U+3002), `０x7f.1` | un-normalised string | normalised host | safe direction — `host_of` output never matches a declared domain, so refused while the browser would visit the legit/other host |
| `https://pathlynks.test ` (trailing space) | `pathlynks.test ` | `pathlynks.test` | safe direction — refused |
| `https://evil.test%40pathlynks.test`, `%00.evil.test`, `xn--pathlynks.test` | non-matching | `<INVALID>` | refused |
| `https://PATHLYNKS.test/x`, `:443`, `[::1]`, trailing dot, `\t`, `\n` | agree | agree | ✅ |

**Every destination where the two parsers disagree in the leak direction is now refused.** The
remaining disagreements are false refusals (fail closed), which B3 explicitly permits. Pinned by
`test_at007_backslash_and_userinfo_destinations_fail_closed` (4 destinations + 2 direct asserts).
T-010 must still pass the browser's post-navigation `page.url` to `resolve()` — carried in B3's
wording, not charged here.

### AT-008 (S3) — ARCHITECTURE.md / SecretRef docstring — **fixed, verified**
- `grep -rn "projects/<slug>/.env" docs src` → nothing.
- `docs/ARCHITECTURE.md:37` — table row `The credential boundary (load .env, resolve per host, mask) | browser/secrets.py::SecretStore`.
- `:75-77` security §1–2: repo-root `.env`, parser-ambiguous destinations fail closed, undeclared values masked.
- `:88` storage block: `.env` at root; `:117-119` Status: `browser/secrets.py` built, Next = `browser/session.py`.
- 121 lines ≤ 150. `schema/project.py:14` docstring: "lives only in the repo-root `.env`".

Ledger: AT-006, AT-007, AT-008 flipped `open → fixed`, `fixed_date` + `verified_date` = 2026-09-03,
re-check evidence appended to each row.

## Regression check against cycle-2 probes
AT-001..005 behaviour re-exercised implicitly by the 24-test suite (empty host, short secret, inline
comment, shadow masking, `strict=False`) — all green; nothing that passed in cycle 2 now fails.

---

## Criterion-by-criterion

### B1 — Loading — **MET**
Repo-root `.env` via `ProjectPaths.env_file`; only declared keys usable (`load`, `secrets.py:112-131`);
missing declared key → `MissingSecret` naming the key, no env fallback (no `os.environ` in module);
undeclared → `store.undeclared`, `UndeclaredSecret` on resolve, still masked via `_shadow`. ✅

### B2 — Placeholders only — **MET**
`resolve` returns a value only on a scoped host, otherwise raises; `guard_prompt` raises on any
raw value regardless of length. "Never persisted by a caller" has no consumer yet — carries to T-010. ✅

### B3 — Domain scoping enforced — **MET**
Narrower-than-allowlist scoping, suffix/lookalike attacks, empty host, blank domains, and now
parser-divergent destinations (userinfo, backslash) all refused — evidenced above by 35 cross-parser
probes. "Navigating outside `allowed_domains`" = B6 / T-010. ✅

### B4 — Evidence is clean — **MET**
`redactor()` masks every `.env` value, declared or not; `__repr__` renders keys only;
`masked_field_keys()` feeds the screenshot hook (capture itself is B7). ✅

### Core invariants — **8/8**
- **C1** ✅ `test_schema.py` 8 passed; `SecretRef` is Pydantic, `extra="forbid"`, validators on the model.
- **C2** ✅ `doctor` clean; `secrets.py` 196 lines, every module docstringed; ARCHITECTURE.md 121 lines and the concept→file table now carries the credential boundary (AT-008 closed).
- **C3** ✅ no duplicate concept, no drift filenames; `browser/` reasoned in the manifest.
- **C4** ✅ `doctor` root-clutter clean.
- **C5** ✅ `test_core.py` 9 passed; `git ls-files` shows no `.env`; placeholder-only design; substitution scoped to `SecretRef.domains`.
- **C6** ✅ not exercised by this unit; nothing regressed.
- **C7** ✅ every command re-run in a fresh context; manifest pasted real output that reproduced.
- **C8** ✅ vacuous (no `stages/`); no vendor import in `browser/`.

## SCOREBOARD

**4/4 contract criteria met (B1, B2, B3, B4), 8/8 invariants hold.**

## Residuals (recorded, NOT findings — no criterion requires them)
- `_clean_value` on an unterminated quote returns the raw prefix (`"unterminated`). Garbage in.
- `host_of` does not percent-decode or IDNA-normalise hosts, so `pathlynks%2Etest` / `pathlynks．test`
  are refused even though the browser would land on the legit host. Fail-closed; if T-010 feeds
  `page.url` (already normalised by Chromium) this never triggers.

## Contract maintenance
None this cycle. No criterion touched.

## Issues written
None new. AT-006, AT-007, AT-008 → `fixed` (verified 2026-09-03).

## /goal wiring
T-011 closed via `goal_cli.py done --task-id T-011` citing this verdict.

## Next
Maker: flip the manifest to `checked-PASS`. Unit T-010 (`browser/session.py`, B5–B9) is next; it must
call `store.resolve(value, page.url)` with the browser's own post-navigation URL.
