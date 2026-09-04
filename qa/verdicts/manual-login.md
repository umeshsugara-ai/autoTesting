# Verdict — manual-login

**Contract:** qa/contracts/manual-login.md (ML1-ML5) + qa/contracts/browser-and-secrets.md (B5, B9, reused unchanged)
**Manifest:** qa/manifests/manual-login.md
**Cycle checked:** 1
**Verdict: PASS**

## ML1 — No secret is required to log in manually

`src/autotester/stages/manual_login.py:38` loads `SecretStore.load(project, paths.env_file, strict=False)`.
Read `SecretStore.load` (`src/autotester/browser/secrets.py:116-136`) directly: with `strict=False`
a declared-but-missing key never raises `MissingSecret` (line 129: `if missing and strict:`) — the
store is simply built with whatever is present. Beyond the `load` call, `manual_login()`'s body
(lines 40-48) calls only `session.start()`, `session.goto(project.base_url)`,
`wait_for_human(...)`, `session.close()` — no `.resolve()`, no `._value_for()`, no read of any
`SecretRef` value anywhere in the function. ML1 holds.

Independently reproduced with a real headed browser (not mocked): wrote a throwaway script
constructing a `Project(slug="checker-manual-login-demo", base_url="http://localhost:8010/",
allowed_domains=["localhost"])` — no secrets declared — and called
`manual_login(project, paths, wait_for_human=lambda p: print(p))` against the live Docker UI
(`docker compose ps` showed `autotesting-autotester-1` up, port 8010; `curl -s -o /dev/null -w
"%{http_code}" http://localhost:8010/` → `200`). Output:
```
[auto-confirmed] A browser window is open at http://localhost:8010/.
Log in by hand, then press Enter here to save the session...
OK: manual_login completed without needing any secret
```
A real Playwright persistent Chromium context opened and closed cleanly (no exception). Confirmed
`profiles/checker-manual-login-demo/` was created with a genuine profile tree (`Default/`,
`Local State`, `Crashpad/`, `GPUPersistentCache/`, cache dirs — not a stub). Cleaned up afterward:
`rm -rf profiles/checker-manual-login-demo projects/checker-manual-login-demo` (the latter held
only an empty `runs/` dir from `paths.ensure()`); `git status --porcelain` confirms no residue.

## ML2 — Blocks for a real human action, not a fixed sleep

`manual_login.py:41-48`: `session.goto()` then `wait_for_human(...)` then `session.close()` in a
`finally`. `wait_for_human` defaults to `_default_wait` (line 25-26), a blocking `input()` — not a
`time.sleep()`. `tests/test_manual_login.py::test_manual_login_blocks_on_the_human_signal_before_continuing`
(lines 73-91) patches `start`/`goto`/`close` to append to an `order` list and asserts
`order == ["start", "goto", "wait", "close"]` — a genuine order-of-operations test, not a happy-path
stub. `test_manual_login_still_closes_if_the_human_wait_raises` (94-109) makes `wait_for_human`
raise `KeyboardInterrupt` and asserts `calls["close"]` still fired — confirms the `finally` in
`manual_login.py:47-48` is real and load-bearing, not decorative. Both tests are genuine, not
disguised happy-path checks.

## ML3 — Session genuinely persisted (B9 reused unchanged)

`session.close()` is called unmodified from `browser/session.py` — confirmed no diff exists on
that file (`git diff HEAD -- src/autotester/browser/session.py` produced no output — untouched by
this unit). The real-browser run above independently proved persistence: the profile directory
under `profiles/<slug>/` held real Chromium user-data-dir contents after `close()` returned.

## ML4 — Reachable from the CLI

`src/autotester/cli.py:174-186` adds `@app.command("login")` matching the existing command-group
pattern (see `flowspec_request_edit` immediately above it). `tests/test_cli_login.py`:
`test_login_refuses_an_unknown_project` (23-26) checks exit code 1 and "no project" in output for
an unknown slug; `test_login_calls_manual_login_for_a_real_project` (29-46) saves a real
`ProjectStore` project, monkeypatches `cli.manual_login_stage.manual_login`, and asserts the CLI
wires through to it with `"session saved"` in the output. Both are genuine assertions on real
Typer `CliRunner` output, not tautologies.

`git diff HEAD -- src/autotester/cli.py` shows only an added import
(`from autotester.stages import manual_login as manual_login_stage`) and the new `login` command
block — no existing command touched.

## ML5 — Unused DB-assertion credential no longer force-declared

`git diff HEAD -- projects/pathlynks/project.json` shows exactly one hunk: the
`PATHLYNKS_MONGO_URI` `SecretRef` block (`key`, `domains: ["vidysea.com"]`, `mask_in_screenshot`)
removed. `base_url`, `allowed_domains`, `description`, and the other 4 `SecretRef` entries are
byte-for-byte untouched (visible in the diff context — nothing else changed in the hunk or
elsewhere in the file). `browser/db.py`/`ReadOnlyCollection` itself was not touched (no diff on
that file), matching the manifest's claim and ML5's exact wording — the capability stays, only the
forced declaration is removed.

## No-fire list — verified not violated

- `browser/secrets.py`: `git diff HEAD -- src/autotester/browser/secrets.py` → no output. Untouched.
- `browser/session.py`: `git diff HEAD -- src/autotester/browser/session.py` → no output. Untouched
  (the AT-036 screenshot-retry fix referenced in `qa/issues.jsonl:36` already landed in an earlier,
  separately-checker-PASSed cycle — no trace of it in this unit's diff since there is no diff on
  this file at all in the current working tree).
- OTP/2FA `blocked_hitl` (B8): defined in `session.py`, file untouched — behavior unchanged.
- `browser/db.py`: not diffed, not removed.

## B5/B9 (browser-and-secrets.md) — still hold, unchanged

Read `qa/contracts/browser-and-secrets.md` B5 (headed by default, persistent profile at
`profiles/<slug>/`) and B9 (teardown closes only this session's own contexts, no process-wide
kill). `browser/session.py` carries no diff from this unit, and the real-browser run above
independently exercised both: a headed Chromium window opened (not headless — `Project.headed`
defaults to `True`, `src/autotester/schema/project.py:90`), used a per-slug persistent profile
directory, and closed cleanly without any `taskkill`/`pkill` in the codebase (unchanged — B9's own
grep-style guarantee was not touched by this diff).

## AT-037 — real finding, accurately described

Reproduced directly: `uv run python scripts/check_no_secrets.py projects/pathlynks/project.json`
→ `LEAK: projects\pathlynks\project.json` / `scanned 1 file(s); 1 leak(s)`. Root-caused by
inspecting `scripts/check_no_secrets.py`'s `real_values()` (it substring-matches every non-empty
`.env` value against the target file) and grepping both files directly:
`.env:16` → `PATHLYNKS_USER_LOGIN_URL=https://pathlynks.vidysea.com/signin`;
`projects/pathlynks/project.json:6` → `"base_url": "https://pathlynks.vidysea.com/signin"`. Exact
string match confirmed — this is `project.json`'s own public sign-in URL, not a credential, and
`git diff` on that file shows only the `PATHLYNKS_MONGO_URI` block removed, `base_url` untouched.
`qa/issues.jsonl:37` (`AT-037`, severity low, status open, found_by maker) matches this exactly —
real, not fabricated, correctly out of scope to fix in a login-mechanism unit, and correctly not
silently worked around.

## Independent command reproduction

```
$ uv run pytest tests/test_manual_login.py tests/test_cli_login.py -v
tests\test_manual_login.py ....                                          [ 66%]
tests\test_cli_login.py ..                                               [100%]
6 passed in 0.24s

$ uv run pytest -q
............. (all green, no failures; 2 skipped — pre-existing browser-required
skips unrelated to this unit)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

## Judgment

`manual_login()` genuinely never touches a secret (verified by reading the function body, reading
`SecretStore.load`'s `strict` branch, and a real non-mocked browser run against a live server with
zero secrets declared). It blocks on a real, order-verified human signal and always closes via a
`finally` proven by a raising-callable test. The `.env` auto-fill and OTP HITL paths are
byte-for-byte untouched (`git diff` on both files empty). The Pathlynks `project.json` edit is
exactly the one `SecretRef` block ML5 names, nothing else. AT-037 is a real, correctly-scoped,
honestly-filed finding rather than a fabrication or a silent workaround.

**PASS.**
