# Verdict — at468-unreadable-reason-never-quotes-content

**Date:** 2026-09-17
**Cycle checked:** 1
**Unit commit:** 03cc8a9 (base 1f660c4)
**Checker:** Mode A, fresh context, project root `D:/autoTesting`

## Re-run (never trusted, all executed independently in the bound tree at HEAD=03cc8a9)

- `uv run pytest -q tests/test_schema_video.py tests/test_media_prep.py tests/test_media.py tests/test_ingest_real_cli.py tests/test_analyze_video.py`
  → 83 passed (`........................................................................ [ 86%]` /
  `...........  [100%]`), matches the manifest's pasted output.
- `uv run ruff check src tests scripts` → `All checks passed!`
- `uv run autotester doctor` → `doctor: clean`
- `uv run python scripts/mutation_check.py qa/evidence/at468-unreadable-reason-never-quotes-content/mutations.json`
  → `3/3 mutations killed`, exit 0, output byte-identical to the manifest's paste (KILLED on all
  three mutation names, correct nodeids in `claims to kill`/`actually failed`).
- Issue's own probe, re-run directly against `Transcript.read_sidecar`:
  `{"segments":[{"start":0,"text":"my password is hunter2 for alice@example.com"}]}` →
  `'ValidationError: end: missing'`. Matches the manifest exactly.
- Full suite `uv run pytest -q` was **not** re-run (RAM ~2.8 GB, a concurrent maker/checker loop is
  active in this shared tree — the same constraint the manifest names). The five targeted test
  files above cover every consumer of `Transcript`/`media.py` in this unit's blast radius
  (confirmed by `grep -rn "unreadable_reason\|read_sidecar\|from_sidecar" src/` — no other module
  imports these beyond `cli_video.py:107`, which the targeted `test_ingest_real_cli.py` and
  `test_analyze_video.py` exercise). Judged sufficient; not a gap on this unit's own criterion.

## Diff scope (C7/C10 step 4c)

`git diff 1f660c4 03cc8a9 --stat` / full diff: touches exactly
`src/autotester/schema/media.py`, `tests/test_schema_video.py`, plus new evidence/manifest files
under `qa/evidence/at468-...` and `qa/manifests/`. No existing function, class, test, export, or
config key was deleted or renamed; the only code change is a new module-private `_reason(exc)` and
one call-site swap (`f"{type(exc).__name__}: {exc}"` → `_reason(exc)`). Matches "What changed"
exactly — no out-of-scope file touched.

## Criteria judged

- **video-learning.md VL1 (third state, `engine="unreadable"` keeps a cause, never folded into a
  claim)** — met. The cause is now location+kind only for validation failures; AT-466's non-validation
  behaviour (`<Type>: <message>`) is preserved and mutation-tested (mutation 3 in the spec).
- **core-invariants.md C1 (schema-first)** — met; no new dict-shaped domain object, `_reason` is a
  pure helper, `extra="forbid"` untouched.
- **core-invariants.md C7 (verification independent, mutation duty on new/rewritten tests)** —
  met. `scripts/mutation_check.py` (pre-existing, audited instrument: asserts baseline green,
  anchor-matches-once, kill-attribution by nodeid, sandbox outside the repo) re-run independently by
  the checker with identical 3/3 KILLED result. This unit adds three parametrized test ids plus
  reuses the existing AT-466 test — both are covered by the mutation spec.
- **CLAUDE.md credential boundary ("logs pass `Redactor.scrub`": a cause line must not carry
  content)** — met, and independently stress-tested beyond the manifest's own 3 sabotage rows (see
  Capability coverage below).

## Capability coverage — re-run in a throwaway copy (4b)

Instrument `scripts/mutation_check.py` already sandboxes (copies `scripts/`, `tests/`, `src/`,
`pyproject.toml`, `conftest.py` to a temp dir outside the repo under the system temp dir, asserts
the baseline is green in the COPY before any edit, single-hunk/single-file anchor-count check,
kill attributed to the named nodeid via a report plugin, not to exit code alone). Checker re-ran it
directly (not by reading the maker's paste) and confirms:

| capability | check | edit | before (copy) | after (copy) |
|---|---|---|---|---|
| a validation failure's reason carries location + kind, never the input | `test_an_unreadable_reason_names_the_error_never_the_sidecar_content[missing-field,wrong-type,unknown-key]` | `if not isinstance(exc, ValidationError):` → `if True:` | green (baseline asserted by the harness) | KILLED — `missing-field`, `unknown-key`, `wrong-type` all in pytest's own failure report |
| an unknown key is named by kind, not by its (sidecar-authored) name | `...[unknown-key]` | `"unknown field" if e["type"] == "extra_forbidden"` → `"unknown field" if False` | green | KILLED — `unknown-key` |
| AT-466 still holds through the helper: non-validation causes keep their type | `test_an_unreadable_sidecar_keeps_why_it_could_not_be_read[bad-json,not-utf8]` | `return f"{type(exc).__name__}: {exc}"` → `return f"{exc}"` | green | KILLED — `bad-json`, `not-utf8` |

3/3 rows reproduced; all edits single-hunk/single-file against `media.py`, admissible per the
manifest's own cells (no shell command, no multi-file edit, no scope-softening instruction found in
any cell). `3/3 mutations killed`, matching the manifest's own paste exactly.

## Adversarial probing beyond the manifest (checker-originated, not in "What changed")

Tried to make `Transcript.read_sidecar` leak sidecar content into `unreadable_reason` through shapes
the manifest's three sabotages don't cover, run live against the unit as committed:

- Non-mapping segment (string / list / int) → `TypeError: ...must be a mapping, not str/list/int`
  (no content echoed; Python's own TypeError message names only the type, not the value).
- Malformed JSON with secret-shaped text adjacent to the syntax error →
  `JSONDecodeError: Expecting ',' delimiter: line 1 column 74 (char 73)` (position only, no text).
- Non-UTF-8 bytes containing secret-shaped content → `UnicodeDecodeError: 'utf-8' codec can't decode
  byte 0xff in position 0: invalid start byte` (byte value + position only).
- Top-level JSON array / string instead of an object → `ValueError: sidecar has no segments list`
  (fixed message, no content).
- Nested dict inside `text` (wrong-type at a nested location) → `ValidationError: text: string_type`
  (loc/type only).
- Very large payload (50k-char text plus a 5k-char secret-shaped extra key) → `ValidationError:
  unknown field` (size and content both irrelevant — `extra_forbidden` is always replaced by the
  fixed string regardless of key length/content).
- Multiple extra keys, each secret-shaped (`pw_hunter2`, `email_alice@example.com`) →
  `ValidationError: unknown field; unknown field` — every `extra_forbidden` error is independently
  replaced, so a multi-key case cannot leak either.
- Non-ASCII secret-shaped key → `ValidationError: unknown field` — unaffected by character set.

No shape found leaks content. The `extra_forbidden` special-case is the one place `loc` itself would
otherwise carry sidecar-authored content (pydantic puts the offending key name in `loc` for that
error type), and the fix's `if e["type"] == "extra_forbidden"` branch is exactly what closes it —
confirmed this is load-bearing, not incidental, by the second mutation row above.

## Known limits (from the manifest, independently assessed — not new findings)

The manifest's disclosed residual ("a future exception type that quotes text in its own message
would pass through unfiltered") is real but speculative — no such exception type is reachable from
`from_sidecar`'s own code today (verified: only `ValueError`, `TypeError`, `json.JSONDecodeError`,
`UnicodeDecodeError`, and `pydantic.ValidationError` are producible, all probed above, none leaks).
Not scored as a failure; already disclosed honestly rather than claimed away.

## Ledger

AT-468 flipped `open → fixed` in `qa/issues.jsonl` (single-line change, JSON-diffed against HEAD to
avoid disturbing the other loop's concurrent uncommitted edits to the same file — see commit note).
No other issue claims apply to this unit.

## Live browser

Not UI-touching. Changed paths (`src/autotester/schema/media.py`, `tests/test_schema_video.py`) have
exactly one consumer outside the schema module (`cli_video.py:107`, a CLI print line); no template
renders `unreadable_reason` (grep over `*.html`/`*.jinja`/`*.j2`/`*.md` finds nothing). Mode D not
applicable.

## Verdict

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met, 0/0 additional invariants at issue
FAILURES (if any): none
CAPABILITY-COVERAGE: 3/3 rows reproduced
LIVE-BROWSER: not-applicable (schema-only change; sole consumer is a CLI print line, no template renders unreadable_reason)
ISSUES-WRITTEN: none (AT-468 closed open -> fixed)
EXPLANATION: All manifest-claimed verify commands reproduced byte-for-byte, including the issue's
own probe. The 3/3 capability-coverage mutations were independently re-run through the project's
own sandboxing mutation harness with identical KILLED results. Diff scope is exactly the two files
named plus new evidence/manifest artifacts — nothing deleted or touched out of scope. Went beyond
the manifest with eight additional adversarial sidecar shapes (non-mapping segments, malformed
JSON, non-UTF-8, top-level non-dict, nested/huge/multi-key/non-ASCII extra fields) targeting the
exact failure mode AT-468 exists to close; none leaked sidecar content. The fix's `extra_forbidden`
special-case is confirmed load-bearing (mutation 2) rather than redundant with the generic
loc+type rendering.
```
