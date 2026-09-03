# Verdict — issue-batch-at012-023-024

**Manifest:** qa/manifests/issue-batch-at012-023-024.md
**Contract:** qa/contracts/core-invariants.md (C1, C3, C6)
**Cycle checked:** 1
**Verdict: PASS**

## Independent verification (re-run myself, not pasted)

```
$ uv run pytest tests/test_store.py -v
tests\test_store.py ..............                                       [100%]
14 passed in 0.30s

$ uv run pytest -q
.........................................s.............................. [ 35%]
........................................................................ [ 70%]
.....................................................s.......            [100%]
(no failures; 2 skipped — pre-existing, unrelated to this unit)

$ uv run ruff check src tests scripts
All checks passed!

$ uv run autotester doctor
doctor: clean
```

Per-file collection count (`uv run pytest --collect-only -q`) sums to 205
(4+6+11+9+6+6+6+6+8+12+8+10+20+4+8+6+6+6+8+24+14+17 = 205), matching the
manifest's "205 collected" claim, with `test_store.py` itself at 14. All
matches the manifest's pasted output — reproduced, not just trusted.

## AT-024 — real fix, judged correct

Read `src/autotester/store/project_store.py` in full (156 lines).

- `__init__` (line 36-40) adds `_source_ids`/`_case_ids`/`_request_ids: set[str] | None = None`.
- `add_source` (50-58), `add_case` (71-79), `add_request` (122-130) all follow the identical
  pattern: populate the cache from the corresponding `list_*()` only when `None`, then do an
  in-memory `in` check, append, and update the set. The manifest's claim that `add_request` was
  fixed alongside the other two even though AT-024's title only named `add_source`/`add_case` is
  confirmed by direct read — same bug class, same fix shape, correctly generalized rather than
  narrowly scoped.
- `list_sources`/`list_cases`/`list_requests` (60-61, 81-82, 132-133) are unchanged one-line
  `read_jsonl(...)` calls — no caching, always fresh from disk. Confirmed by reading each method
  body directly, not by trusting the manifest's claim.
- Staleness check: a cache is populated once per `ProjectStore` instance and only ever grows
  (`.add(id)` on every successful append within that instance) — it is never used to *decide*
  what `list_*()` returns, only to short-circuit `add_*`'s own idempotency check. The only way
  this cache could diverge from disk in a way that matters is a hand-edit that *removes* an id
  from the underlying JSONL between two `add_*` calls on the same long-lived instance, which
  would make `add_*` wrongly skip a re-append — a narrow, honestly-disclosed edge case in the
  manifest's "Scope notes," not a hidden one, and it does not regress any existing behavior
  (the pre-fix code had the same instance-local blind spot for a concurrent hand-edit mid-run,
  since even the old code's read happened once at call time, not continuously).
- Regression tests are real proof, not happy-path-only:
  - `test_add_case_does_not_rescan_the_file_on_every_call` (tests/test_store.py:134-158)
    monkeypatches the module-level `read_jsonl` symbol actually used by `project_store.py` (not a
    decoy import) with a call-counting wrapper, runs 5 sequential `add_case` calls with distinct
    ids, and asserts `len(calls) == 1` — this would fail under the old O(n)-per-add code (5 reads)
    and passes under the fix. It also asserts `list_cases()` still returns all 5 fresh, proving
    `list_*()` was not accidentally cached too.
  - `test_add_case_cache_does_not_hide_a_case_added_by_another_process` (161-174) creates two
    independent `ProjectStore` instances on the same directory, adds a case through each, and
    asserts both instances' `list_cases()` see both cases — directly tests the cross-instance
    staleness risk this kind of cache pattern is most likely to introduce, and it passes.
  - Ran both directly (above): both pass. This is genuine regression coverage of the exact defect
    class, not incidental.

C1/C3/C6: no new schema, no duplicate concept, `list_*()` (the read path artifacts rely on for
human-editability, C6) is untouched. Consistent with the contract.

## AT-023 — documentation correction, judged honest

Read the tail of `qa/manifests/t020-filestore.md`. The original lines (36: "13 tests", 44/46:
"13 passed"/"94 tests") are left untouched in place. A dated `## Correction (2026-09-03,
resolving AT-023)` section is appended at the end of the file stating the actual counts (12 test
functions, 93 collected), citing the same `--collect-only -q` command as proof, and explicitly
noting no functional violation. This matches the project's own historical-evidence-record
discipline (manifests are append-only-in-spirit) rather than silently rewriting the original
numbers — confirmed by direct read, not by trusting the manifest's own description of what it did.

## AT-012 — verify-only, claim holds

Read current `qa/.last-tick`: one line,
`2026-09-03T23:15:00+05:30 · ADVANCED · docker-live-ui closed (checker cycle 1 PASS, pushed 4207cff)`
— single overwritten line, consistent `+05:30` offset, confirming the manifest's description.
`git log --oneline -10 -- qa/.last-tick` shows the file only ever gets touched by "chore: stamp
.../maker tick" commits authored directly (5f2a1a5, f13268a, 0ad2034, etc.) — no CI script or
generator writes it, consistent with "no code path to patch." The original AT-012 finding's
mixed-format lines are confined to git history (old commits), not the live file — the claim that
there is nothing to fix today is correct on independent inspection, not just on the maker's say-so.

## qa/issues.jsonl

Confirmed directly: AT-024 `"status": "fixed"` with a `FIXED 2026-09-03: ...` note appended after
the original finding text (not replacing it) citing the cache fix and both new tests by name.
AT-023 and AT-012 both `"status": "verified"` with `RECONCILED 2026-09-03: ...` notes appended the
same way, original finding text intact above each. Ledger discipline honored.

## Judgment

- AT-024's fix is correct: no meaningful staleness or duplicate-write risk introduced: `list_*()`
  stays the single source of truth for reads, the cache only accelerates the `add_*` idempotency
  check, and both new tests target the actual failure modes this pattern could introduce
  (repeated re-scan cost, and cross-instance masking) rather than just re-testing idempotency
  itself (which the pre-existing `test_add_source_is_idempotent_on_content_address` /
  `test_add_case_is_idempotent_when_a_flowspec_regenerates` already covered).
- AT-023 is handled honestly: original self-reported counts preserved, correction appended and
  dated, not silently rewritten.
- AT-012's "nothing to fix" claim is true on independent inspection of the current file and git
  history — not a code path that should have been patched.
- All four verify commands in the manifest reproduce cleanly under my own run.

**PASS.**
