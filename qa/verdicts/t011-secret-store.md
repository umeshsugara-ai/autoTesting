# Verdict — t011-secret-store

**Date:** 2026-09-03
**Mode:** A (unit check) — fix cycle 2
**Bound project root:** `D:/autoTesting` — all paths read/written resolve inside it.
**Manifest:** `qa/manifests/t011-secret-store.md` (Status: ready-for-check, Fix cycle 2 of 3)
**Contracts judged:** `qa/contracts/browser-and-secrets.md` B1–B4 (B5–B9 = T-010, out of unit)
+ `qa/contracts/core-invariants.md` C1–C8. **B1 and C5 judged against the wording AMENDED in this
check** (repo-root `.env`; undeclared = ignored for use, still masked) — see "Contract maintenance".
**Adapter:** `qa/adapter.json` — `verify.kind = shell`; every command I ran is allowlisted there
or is a manifest-declared command.
**Prior verdict:** cycle 1, FAIL (AT-001..AT-005).
**Cycle checked: 2**

## VERDICT: FAIL

All five cycle-1 findings are closed — each independently reproduced as fixed, not taken from
the manifest. The unit then failed on **one new demonstrated release** on the same criterion
that failed last time (B3): a URL Python's `urlparse` and Chromium disagree about. Plus two S3
hygiene findings. Everything is a two-line fix; cycle 3 is the last.

---

## What I re-ran myself (no pasted output trusted)

| Command | My result | Manifest claimed | Match |
|---|---|---|---|
| `uv run pytest tests/test_secrets.py -q` | exit 0, 22 passed | exit 0, 22 passed | ✅ |
| `uv run pytest -q` | exit 0, 48 passed | exit 0 (48) | ✅ |
| `uv run ruff check src tests` | exit 0, `All checks passed!` | same | ✅ |
| `uv run autotester doctor` | exit 0, `doctor: clean` | same | ✅ |
| `git ls-files \| grep -E "\.env$"` | no output (rc=1) | `(none)` | ✅ |
| `uv run pytest tests/test_core.py -q` (C5) | exit 0, 9 passed | not claimed | ✅ |
| `grep -rE "^(import\|from) (anthropic\|google)" src/autotester/stages/` (C8) | no such dir — vacuous | not claimed | n/a |

Every pasted output reproduced exactly.

Read in full: `src/autotester/browser/secrets.py` (175 lines), `src/autotester/core/redact.py`,
`src/autotester/schema/project.py`, `src/autotester/core/paths.py`, `tests/test_secrets.py`,
`.gitignore`, `.env.example`, `docs/ARCHITECTURE.md`, `git diff` of `doctor.py` + `test_core.py`.

## Cycle-1 findings — re-probed, each one

| Issue | My cycle-2 reproduction | Status |
|---|---|---|
| AT-001 empty host / blank domain | `resolve()` raises `SecretScopeError` for `""`, `"   "`, `"://broken"`, `"?x=1"`, `"#frag"`, `"//"`, `"http://"`, `"\x00"`. `SecretRef(domains=[""])` and `[" . "]` rejected at declaration. **Bonus:** bypassing the validator with `SecretRef.model_construct(domains=[""])` still fails closed at `resolve()` — defence in depth is real. | **fixed** |
| AT-002 short secret | 3-char and 1-char declared values: `guard_prompt` raises, `Redactor.scrub` masks. `_MIN_SECRET_LEN` gone from both sites. The test that encoded the bug was replaced, not deleted-and-forgotten. | **fixed** |
| AT-003 inline comment | `parse_env("PW=abc # note")` → `abc`; quoted `#` and URL fragments preserved. | **fixed** (variants → AT-006) |
| AT-004 undeclared in redactor/guard | `STRAY=strayvalue123` masked, prompt-guarded, `UndeclaredSecret` on resolve, absent from `keys()`/`__contains__`/`repr`. Two projects sharing one `.env`: each masks the other's value, neither can resolve it. | **fixed** |
| AT-005 strict=False | Empty-value key and absent file under `strict=False` both raise `MissingSecret` at `resolve()`. Pinned by test. | **fixed** |

Ledger: AT-001..005 flipped `open → fixed`, `fixed_date` + `verified_date` = 2026-09-03.

## New adversarial probes (scratch script, `uv run python`; 30+ cases)

| # | Attack | Result |
|---|---|---|
| N1 | Two projects, one root `.env`: cross-resolve the other's key | ✅ refused; each masks the other's value |
| N2 | Same value declared AND shadowed — attribution/masking | ✅ masked |
| N3 | `scrub_obj` on nested dict/list/tuple with `None`/int | ✅ clean |
| N4 | Host confusion ×11: suffix, userinfo (both directions), path/query/fragment lookalikes, punycode, IPv6, trailing dot, `%00`, `%2F@`, `\@` | 🔴 **one leak** — `https://evil.test\@pathlynks.test` (below) |
| N5 | Placeholder variants (`{{secret:PW}}`, spaced, doubled, nested) on a wrong host | ✅ passthrough or refused; no value escapes |
| N6 | Mixed placeholder, one key missing — value in exception/traceback? | ✅ absent |
| N7 | `MissingSecret` message content | ✅ names key + path only |
| N8 | `ProjectPaths("x").env_file` | ✅ `D:\autoTesting\.env` (repo root) |
| N9 | `assert_no_raw_secrets` with `""`/`None` in the secret list | ✅ no false positive |
| N10 | Overlapping values, longest-first | ✅ both masked, correctly attributed |
| N11 | `SecretRef.domains` normalisation (`.Foo.TEST` → `foo.test`) | ✅ |
| A3′ | `PW=abc\t# note` and `PW="abc" # c` | ⚠️ wrong value loaded (AT-006, S3) |

### The B3 failure — AT-007 (S2)

`host_of()` (`secrets.py:60-63`) uses `urllib.parse.urlparse`, which treats `evil.test\` as
userinfo and reports host `pathlynks.test`. The WHATWG URL standard — what Chromium and
Playwright implement — treats `\` as `/` in special schemes: host **`evil.test`**, path
`/@pathlynks.test`. Verified both sides:

```
python  urlparse('https://evil.test\\@pathlynks.test').hostname  -> 'pathlynks.test'
node    new URL('https://evil.test\\@pathlynks.test').host       -> 'evil.test'
probe   store.resolve('{{SECRET:PW}}', 'https://evil.test\\@pathlynks.test') -> RETURNED the value
```

So a step (LLM-generated, or prompt-injected from a page) carrying that destination gets the
credential released while the browser goes to the attacker. B3 says scoping is enforced against
the current page host and is "enforced, not advisory" — this is the same class of hole as AT-001:
the gate trusts one parser's opinion of the host. `%2F@` and `pathlynks.test@evil.test` are
consistent on both parsers and are NOT leaks (the cycle-1 probe only covered the safe direction).

**Fix direction (two lines, fail closed):** in `host_of()`, return `""` when the raw input contains
`\` or when `urlparse` yields any username/password — the empty host already raises since AT-001.
Add both as tests. Contract B3 now records this edge case explicitly. T-010 must also pass the
browser's own post-navigation `page.url` to `resolve()`, never the step's intended URL.

---

## Criterion-by-criterion

### B1 — Loading (amended wording) — **MET**
- Loads the repo-root `.env` via `ProjectPaths.env_file` (`core/paths.py:39-45`), keyed by the
  project's declared `SecretRef[]` (`secrets.py:95-115`). N8 confirms the path. ✅
- Missing declared key → `MissingSecret` naming the key; no empty-string fallback; no
  `os.environ` read anywhere in the module. ✅
- Undeclared key: reported, unresolvable, **still masked** (`_shadow`, `_all_values`). Matches the
  amended "ignored for use, still masked". ✅

### B2 — Placeholders only — **MET**
- `resolve` returns a value only on a scoped host, else raises; mixed failures never return a
  partial string (N6). ✅
- "never stored/logged/returned to a persisting caller": still no consumer of `resolve`/`redactor`/
  `guard_prompt` in `src/` (grepped) — unfalsifiable at T-011, carries to T-010. Not charged.
- Raw secret in a prompt raises regardless of length (AT-002 closed). ✅

### B3 — Domain scoping enforced — **NOT MET** (AT-007)
- Narrower-than-allowlist scoping, lookalikes, suffix attacks, empty host, blank domains, IPv6,
  punycode, trailing dot: all refused. ✅
- 🔴 Backslash-userinfo destination releases the secret for a host the browser will not visit.
  Demonstrated above.
- "Navigating outside `allowed_domains` is refused by the session" = B6 / T-010; not charged here.

### B4 — Evidence is clean — **MET** (screenshot half deferred to B7 by the contract itself)
- `redactor()` masks every value in `.env`, declared or not, any length; `__repr__` renders keys
  only. ✅ Residual (not a finding): `vars(store)` holds plaintext — inherent to in-memory secrets.
- `masked_field_keys()` supplies the screenshot hook; B7 owns the capture. ✅

### Core invariants — **7/8**
- **C1** ✅ Pydantic + `extra="forbid"`; new `domains` validator lives on the schema model.
- **C2** 🔴 **NOT MET — AT-008 (S3).** Files/functions within limits and every module has a
  docstring, `doctor` exit 0 — but the third bullet, "`docs/ARCHITECTURE.md` … concept→file table
  matches reality", does not hold: the table (`:30-41`) has no row for the credential boundary
  the unit added, `:74` and `:85` still place `.env` under `projects/<slug>/`, `:116` still says
  "Next: browser/", and `schema/project.py:14` repeats the old path. The user's mid-cycle path
  change is the cause; the doc was not moved with the code.
- **C3** ✅ `doctor` duplicate-concept/drift rules clean; `browser/` reasoned in the manifest.
- **C4** ✅ `doctor` clean. (`.env.example` at root passes because the root-clutter rule skips
  dotfiles, `doctor.py:80` — noted, not a finding; `.gitignore` un-ignores it explicitly.)
- **C5** ✅ (amended wording) — `**/.env` ignored, `git ls-files` empty, `test_core.py` 9 passed;
  placeholder-only discipline is the module's whole design.
- **C6** ✅ not exercised; nothing regressed. **C7** ✅ re-derived in a fresh context.
- **C8** ✅ vacuous — no `stages/`; no vendor import in `secrets.py`.

## SCOREBOARD

**3/4 contract criteria met (B1, B2, B4), 7/8 invariants hold.** B3 fails on AT-007; C2 on AT-008.

## Contract maintenance performed in this check (I am the contracts' owner)

| Inbox entry | Decision | Reason |
|---|---|---|
| Umesh: `.env` at repo root | **Folded** → B1, C5 (routine) | User's own instruction; non-safety-weakening — per-project declaration + domain scoping unchanged, `**/.env` already gitignored. |
| AT-004 B1-vs-B4 tension | **Folded** → B1 "ignored for use, still masked" (routine) | Tightens B4, does not weaken B1's no-use rule; behaviour reproduced. |
| Umesh: Mongo/DB in `.env` | **Left unfolded**, marked | Belongs to a future `execute` contract; no B/C criterion covers backend assertions. |
| AT-007 edge case | **Recorded** in B3 (routine tighten) | Makes "browser's host, fail closed on parser disagreement" contractual. |

No criterion was softened. B3 was tightened while the unit is failing it — tightening is the
permitted direction.

## Issues written

| id | sev | status | title |
|---|---|---|---|
| AT-001..005 | S1/S2/S3×3 | **fixed** (verified 2026-09-03) | cycle-1 findings, all reproduced closed |
| AT-006 | S3 | open | `parse_env`: tab-before-`#` and quoted-value-then-comment load the wrong value |
| AT-007 | S2 | open | `host_of` vs WHATWG: backslash-userinfo URL releases the secret for `evil.test` |
| AT-008 | S3 | open | ARCHITECTURE.md + SecretRef docstring stale on `.env` location; table lacks `browser/secrets.py` |

## What the maker should do next (cycle 3 of 3 — last)

1. **AT-007** — `host_of()`: `if "\\" in url: return ""`; after parsing, `if parsed.username is not
   None or parsed.password is not None: return ""`. Two tests (backslash form, plain `user@host`
   form — note `pathlynks.test@evil.test` must STILL be refused, now by the userinfo rule).
2. **AT-006** — `_clean_value`: split on `\s#` and handle `"quoted" # comment`. One test.
3. **AT-008** — one table row, two line edits, the Status line, the docstring. Keep ≤150 lines.

Do not touch B3's wording to close this. Scope stays T-011; B5–B9 remain T-010.
