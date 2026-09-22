# Verdict — t162-drive-2b (Cycle checked: 1) — SECOND INDEPENDENT CHECK (dual check, `.b`)

**Date:** 2026-09-23
**Contract:** `qa/contracts/source-adapters.md` (ACTIVE, D-035) + `core-invariants.md` + `ingest.md`
**Manifest:** `qa/manifests/t162-drive-2b.md` (Fix cycle: 1)
**Unit commit:** `2485ca2` (branch `wave/t162-drive-2b`, base `20baf0e`)
**Project root:** `D:/autoTesting/.worktrees/t162-drive-2b` (bound)
**Independence note:** this is the second, blind checker of the dual check. Per instruction I did
NOT read `qa/verdicts/t162-drive-2b.md` (the primary) at any point — every finding below was
derived from the contract, the manifest, and my own re-execution.

## What I re-ran myself

1. `PYTHONUTF8=1 uv run pytest tests/test_source_adapters_drive.py` → `6 passed in 1.21s`. Matches.
2. `PYTHONUTF8=1 uv run ruff check src tests scripts` → `All checks passed!`. Matches.
3. `PYTHONUTF8=1 uv run autotester doctor` → `doctor: clean`. Matches.
4. `PYTHONUTF8=1 uv run pytest` (bare, full suite) → `1568 passed, 5 skipped, 32 xfailed, 1 warning
   in 644.42s (0:10:44)`, exit 0. Matches the manifest's pasted output exactly (0 failed/errored).
5. `git diff 20baf0e...2485ca2 --stat` and full diff on every changed non-new file
   (`schema/enums.py`, `sources/adapters.py`, `stages/ingest.py`, `sources/__init__.py`) — read in
   full. `schema/base.py` is untouched (confirmed absent from the diff) — SA4's "no new schema
   field" claim holds; `Provenance` is the pre-existing type.
6. `git show --name-only --format= 2485ca2` — 9 paths, all a subset of the manifest's "What
   changed" + `qa/manifests/t162-drive-2b.md` + `docs/MAP.md` (generated). C10 holds.
7. `pyproject.toml`/`uv.lock` diff — empty. No new dependency; `httpx>=0.28.1` was already declared
   pre-unit (`pyproject.toml:13`). Dependency-discipline claim holds.
8. File sizes: `enums.py` 300 lines exactly, `drive.py` 204, `drive_register.py` 197 — all ≤300
   (C2). `doctor: clean` independently confirms.
9. `grep -inE "print\(|logging\.|log\.(info|debug|warning|error)"` over both new modules → zero
   matches. Confirms the manifest's SA3 no-log claim by direct code read, not by trusting the
   docstring.

## Capability coverage — all 5 SA rows independently reproduced

Throwaway copy: `src/+tests/+scripts/+pyproject.toml+uv.lock` copied to a scratch dir outside the
bound tree; `.venv` shared via a Windows junction (`New-Item -ItemType Junction`) to the bound
tree's own venv. Copy confirmed GREEN before any edit (`6 passed in 0.27s`), and byte-identical to
the bound tree's three touched source files after all reverts (`diff -r` empty on all three) — the
bound tree was never edited.

| Row | Edit applied | Result | Matches manifest? |
|---|---|---|---|
| SA1 | `register_document(..., url=drive_file.id, ...)` → `url=None` | RED: `AssertionError: assert None == 'doc-1'` | Yes, exact |
| SA2 | `adapters.register_document`'s dedupe guard `if existing is not None:` → `if False and existing is not None:` | RED: `AssertionError: assert True is False` | Yes, exact |
| SA5 | `_register_unfetchable`'s `notes=f"{_EXTRACTION_ERROR_PREFIX}: ..."` → `notes=f"unreadable: ..."` | RED: `.startswith("extraction_error")` fails on `'unreadable: could not fetch...'` | Yes, exact |
| SA4 | `Provenance(produced_by=..., inputs=[parent.id])` → `inputs=[]` | RED: `AssertionError: assert [] == ['src_59e3babe3bae']` | Yes, exact |
| SA3 | `HttpDriveClient.list_folder`: `DriveFile(f["id"], f.get("name","file"), ...)` → `DriveFile(f["id"], headers["Authorization"], ...)` | RED: `AssertionError: assert 'ACCESS_BEARER_TOKEN_QWER' not in ...` — bearer token landed in `label` and on-disk `sources.jsonl` | Yes, exact (token traced into both `label` and the sha256-content field via the injected file name, same as claimed) |

Each edit was single-hunk, single-file, named in "What changed," applied/reverted one at a time,
with the 6-test file green again after every revert — confirmed myself, not merely read.

**SA3 extra scrutiny (why this unit is dual-checked):** read `drive.py` and `drive_register.py`
in full. The refresh token and client secret are held only as `(key, resolver)` pairs on
`HttpDriveClient` (`self._client_secret_key`, `self._refresh_token_key`, `self._resolver`);
`_access_token()` calls `self._resolver(...)` only inline inside the token-exchange POST body and
returns only the short-lived access token, never storing it on `self`. Only the Drive **file id**
travels into `Source.url` (`drive_register._dispatch_by_suffix` and the three `_register_*`
helpers). `assert_no_raw_secrets` is exercised directly in
`test_drive_credential_never_reaches_stored_sources` and passes on the real on-disk
`sources.jsonl`. No `print`/`log`/`logging` anywhere in either module (grepped, see above).

## One evidentiary gap found (core-invariants C7)

**[C7] sev: low.** `tests/test_source_adapters_drive.py` adds a 6th test,
`test_device_code_exchange_returns_refresh_token_offline` (lines 166-188), exercising
`request_device_code`/`exchange_device_code`. `core-invariants.md` C7's Verify clause is
unconditional for **any** unit that "adds or rewrites a test": *"pastes its mutation run, with a
green asserted baseline and a named failing test per mutation."* The manifest explicitly declines
this for the 6th test ("it is a mechanism-presence test... so it has no separate falsifying row"),
which conflates the checker-protocol's 4b capability-coverage duty (scoped to the 5 numbered SA
rows) with C7's separate, broader per-test mutation duty (scoped to any added/rewritten test,
independent of whether it maps to a capability row). Nothing in C7's text or its amendment-log
history (five prior occurrences, all in this same file) carves out an exception for a "mechanism"
test.

I closed the gap myself rather than take the manifest's word: single-hunk mutation on
`exchange_device_code` (`return resp.json()["refresh_token"]` → `return "WRONG_TOKEN"`), reverted
after. Result: **RED for the right reason** —
`AssertionError: assert 'WRONG_TOKEN' == 'NEW_REFRESH_TOKEN'` at the test's own assertion line —
confirming the test is real, not vacuous. Copy reverted to byte-identical with the bound tree
afterward.

**This does not indicate a defect in the code or the test** — the property holds and I proved it.
It is a paperwork gap: the manifest should have pasted this same mutation + RED and did not. Given
core-invariants' own preamble ("a unit that violates any criterion here fails its check regardless
of what its own feature contract says") and the checker protocol's "PASS requires every criterion
evidenced... no partial PASS," I am recording this as the reason this cycle is not a clean PASS,
while making clear it is a one-line fix (paste the mutation row above) with zero code risk.

## Diff-scope (4c) and Issues addressed

- No function/class/export/test/config key was deleted or renamed outside the unit's claim.
- Only paths in "What changed" plus `qa/manifests/*` and generated `docs/MAP.md` were touched.
- "Issues addressed: none" — confirmed; no open ledger row references DRIVE/Drive/t162-drive.
- Not UI-touching (confirmed from changed paths: no `ui/`, route, or template file) — Mode D
  correctly not invoked.
- `.goal/goal.json` T-162's `done_check` (`uv run pytest tests/test_source_adapters.py`) does not
  itself exercise the new `tests/test_source_adapters_drive.py` file (tests were split out, same
  as the EMAIL phase before it) — noted, not filed as a finding against this unit: it is pre-existing
  structural debt from the AUDIO/EMAIL split, not introduced here, and the manifest's own bare
  `uv run pytest` re-run (which I reproduced) covers the full suite including this file.

## Scoreboard

5/5 SA capability rows independently reproduced and matched. 6/6 SA criteria (SA1-SA6) evidenced
directly from code + re-run tests. 9/10 core-invariants criteria (C1-C6, C8-C10) evidenced clean;
C7 evidenced by the checker rather than the manifest, as detailed above.

```
VERDICT: FAIL
SCOREBOARD: 6/6 SA criteria met, 9/10 core-invariant criteria evidenced (C7 gap below)
FAILURES (if any):
- [C7] sev: low · manifest omits the required mutation-run evidence for the 6th added test (test_device_code_exchange_returns_refresh_token_offline) · fix: paste the single-hunk mutation `return resp.json()["refresh_token"]` -> `return "WRONG_TOKEN"` in exchange_device_code and its RED (`AssertionError: assert 'WRONG_TOKEN' == 'NEW_REFRESH_TOKEN'`), reverted -- checker already confirmed this kills cleanly, no code change needed · issue: (not filed -- primary owns the ledger this dual check)
CAPABILITY-COVERAGE: 5/5 rows reproduced (SA1, SA2, SA4, SA5, SA3 all GREEN-before -> RED-for-the-named-reason -> reverted GREEN-after, in a throwaway copy outside the bound tree)
LIVE-BROWSER: not-applicable (no ui/, route, or template path in the diff -- source-adapter layer only)
ISSUES-WRITTEN: none (dual check -- primary owns the ledger; the C7 gap above is listed here for the primary/maker to fold)
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All 6 SA criteria (SA1-SA6) are fully evidenced and independently reproduced, including the SA3 credential boundary this dual check exists to scrutinize -- direct code read plus a live mutation confirm no token value ever reaches a stored Source, a log, or disk. The full suite (1568 passed, 5 skipped, 32 xfailed, 0 failed) and diff-scope (C10) are both clean. The single reason this is not a clean PASS is a core-invariants C7 evidentiary gap: the unit's 6th added test has no mutation-run pasted in the manifest, only a prose exemption that does not match C7's unconditional wording. I independently ran that exact mutation and it kills cleanly (real, non-vacuous test) -- so the fix is one pasted paragraph in the manifest, not a code change, and this should clear on a same-day re-submit.
```
