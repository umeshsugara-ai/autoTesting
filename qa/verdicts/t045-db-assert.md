# Verdict — t045-db-assert

**Checked:** 2026-09-03 · Mode A · Cycle checked: 1
**Contract:** qa/contracts/db-assert.md (D1-D5) + core-invariants.md + browser-and-secrets.md
(B1-B9, dependency) + execute.md (E1-E5, dependency)
**Manifest:** qa/manifests/t045-db-assert.md

## Re-run evidence (all executed independently in this session, not pasted)

- `uv run pytest tests/test_db.py -v` -> **5 passed, 1 skipped** in 0.21s. Matches manifest.
- `uv run pytest` (full suite, no -q so the summary line prints) -> **120 passed, 1 skipped**.
  `uv run pytest -q --collect-only`-style dot count (28+1skip+49 = 78 dots across the two -q
  progress lines) is consistent; manifest's "121 collected (120 passed + 1 skipped)" is correct
  wording (120+1=121).
- `uv run ruff check src tests scripts` -> "All checks passed!"
- `uv run autotester doctor` -> "doctor: clean"
- `wc -l docs/ARCHITECTURE.md` -> 141 (<=150)
- `uv run python -c "from autotester.browser.db import ReadOnlyCollection; print(sorted(m for m
  in dir(ReadOnlyCollection) if not m.startswith('_')))"` -> `['count_documents', 'find',
  'find_one']` — exact match to manifest's claim.
- `git diff HEAD -- src/autotester/schema/enums.py` -> additive only, one line (`DB = "db"`
  appended to `EvidenceKind`), no existing member touched.
- `pyproject.toml` / `uv.lock` -> `pymongo>=4.9.0` declared as a real dependency (not a silent
  lazy import), `pymongo==4.17.0` resolved and locked.
- `scripts/check_no_secrets.py qa/manifests/t045-db-assert.md qa/contracts/db-assert.md` ->
  "scanned 2 file(s); 0 leak(s)".
- Environment check before running anything: `env | grep -i mongo` in this session's shell
  returned nothing — `PATHLYNKS_MONGO_URI` and `AUTOTESTER_LIVE_MONGO_TEST` are both unset by
  default here, matching D5's premise that the gated test is genuinely opt-in.

## D1 — read-only by construction (read `src/autotester/browser/db.py` in full)

Read the entire file (58 lines). `ReadOnlyCollection.__init__` stores `self._collection`; its
only other members are `find`, `find_one`, `count_documents` — each a thin delegating read call
to the wrapped object (`.find()`, `.find_one()`, `.count_documents()`). No `insert*`, `update*`,
`delete*`, `drop*`, `replace*`, `remove*`, or any other method exists anywhere in the class body
— confirmed both by reading the source directly and by independently re-deriving
`dir(ReadOnlyCollection)` filtered to public names, which returns exactly the three methods.
`connect_read_only(uri, db_name, collection_name)` constructs a raw `pymongo.MongoClient`
internally but returns only `ReadOnlyCollection(client[db_name][collection_name])` — the raw
client/database/collection object is never returned or exposed to the caller. **D1 holds.**

## D2 — connection string never logged

`connect_read_only`'s only reference to `uri` is passing it straight into `MongoClient(uri)`; no
`print`, `logging`, `repr`, or string formatting touches it anywhere in the file. Confirmed by
direct source read plus the manifest's own regex-based test
(`test_connect_read_only_source_never_logs_the_uri`), independently re-run. `PATHLYNKS_MONGO_URI`
is already declared as a `SecretRef` on `projects/pathlynks/project.json` (line 41,
`domains: ["vidysea.com"]`, `mask_in_screenshot: true`) — confirmed by reading the file directly;
this unit adds no new secret declaration. **D2 holds.**

## D3 — document becomes evidence only redacted

`assert_document` builds `summary` as a plain f-string containing the query and found/not-found
state, then returns `Evidence(kind=EvidenceKind.DB, path=redactor.scrub(summary), ...)` —
`redactor.scrub` runs before the value is placed on the `Evidence` object, not after. The test
(`test_assert_document_evidence_is_redacted`) plants a real value (`SECRET =
"s3cr3t-session-token"`) into a fake document and asserts it does not appear in `ev.path`;
independently re-run and passed. **D3 holds.**

## D4 — observation only, no judgement

`assert_document` returns an `Evidence` object; it never returns or raises pass/fail. The
"not found" case (`test_assert_document_not_found_is_evidence_not_an_exception`) returns evidence
with "not found" in the summary rather than raising — re-run, passed. **D4 holds.**

## D5 — no live connection in the default suite (scrutinized per dispatch instructions)

`tests/test_db.py`'s only real-connection test is
`test_connect_read_only_against_a_real_uri`, decorated:
```
@pytest.mark.skipif(
    not os.environ.get("AUTOTESTER_LIVE_MONGO_TEST"),
    reason="live Mongo connection requires explicit opt-in ...",
)
```
Confirmed this session's shell has neither `AUTOTESTER_LIVE_MONGO_TEST` nor
`PATHLYNKS_MONGO_URI` set (`env | grep -i mongo` returned nothing) before running anything, then
ran `uv run pytest tests/test_db.py -v` and independently observed the skip land on exactly this
test (6 collected, 5 passed, 1 skipped — the skipped one is this test by elimination since it is
the only `@pytest.mark.skipif` in the file). Every other test in the file uses `FakeCollection`,
never `pymongo.MongoClient`. Running the full suite (`uv run pytest`) as-is opens no socket to
the real Pathlynks Mongo instance. **D5 holds — the maker's reasoning for building T-045 instead
of T-050 is not contradicted by what actually ships.**

## Manifest metadata check

`Issues addressed: none` is accurate — no open ledger issue names this feature; nothing to
cross-check against.

## Tracking metadata (checker authority, per dispatch)

`.goal/goal.json`'s T-045 `done_check` pointed at `tests/test_execute.py` (a stale placeholder
predating this unit). Corrected in place to
`{"type": "cmd", "cmd": "uv run pytest tests/test_db.py -q", "expect_exit": 0}` — the actual
verify command for this unit's deliverable, matching the manifest's own recommendation. Closed
T-045 via `python D:/ai_os/.claude/skills/goal/scripts/goal_cli.py done --root "d:/autoTesting"
--task-id "T-045"` (result: `{"ok": true, "task": "T-045", "percent": 53}`).

## VERDICT

```
VERDICT: PASS
SCOREBOARD: 5/5 criteria met (D1-D5), 0/0 additional invariants checked beyond D1-D5 (no
  core-invariants/browser-and-secrets/execute criterion is newly exercised by this unit beyond
  what D1-D5 already restate)
FAILURES (if any): none
ISSUES-WRITTEN: none
EXPLANATION: ReadOnlyCollection independently confirmed to expose exactly find/find_one/
  count_documents with no mutating method anywhere in the class; connect_read_only never returns
  the raw client. The only real-connection test is genuinely gated behind
  AUTOTESTER_LIVE_MONGO_TEST, unset by default in this environment, so running the suite as-is
  never touches live Pathlynks Mongo. All manifest verify commands re-run and matched. Fixed the
  stale T-045 done_check and closed the goal task.
```
