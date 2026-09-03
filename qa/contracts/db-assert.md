# Contract — Read-only DB assertions (T-045)

**Covers:** goal task T-045. **Owner:** /checker. **Criticality:** MEDIUM — extends EXECUTE's
evidence kinds; not itself user-facing yet.
**Depends on:** `core-invariants.md` (all), `browser-and-secrets.md` (B1-B9), `execute.md`
(E1-E5, dependency — `Evidence`/`RawResult` shapes).

## Purpose

Let a case's evidence include a read-only backend check (e.g. "did the signup actually create a
user document?") without ever giving the system a way to write to production data. This is the
inbox item flagged unfolded in `browser-and-secrets.md`'s amendment log
("`PATHLYNKS_MONGO_URI`... belongs to a future execute contract").

## Criteria

### D1 — Read-only by construction, not by convention
`browser/db.py::ReadOnlyCollection` exposes exactly three methods (`find`, `find_one`,
`count_documents`) and has no `insert*`/`update*`/`delete*`/`drop*`/`replace*` method anywhere in
its class body — a caller physically cannot mutate through it, matching the standing Vidysea
pattern (`lib/mongo.py::ReadOnlyCollection`) this contract names directly. `connect_read_only`
returns only a `ReadOnlyCollection`, never the raw pymongo `Collection`/`Database`/`MongoClient`.

### D2 — The connection string is a secret, never logged
`connect_read_only(uri, ...)` never prints, logs, or stores `uri`. `PATHLYNKS_MONGO_URI` is
declared as a `SecretRef` on the project exactly like the login credentials (already true as of
T-030's `project.json`) — this contract does not change how it is resolved, only how it is used
once resolved.

### D3 — A document becomes evidence only redacted
`assert_document` returns an `Evidence` with `kind=EvidenceKind.DB` whose `path` has passed
through the project's `Redactor` (`SecretStore.redactor()`) before being returned — any secret
value a document happens to contain (e.g. a stored session token) is masked exactly like a
screenshot or DOM string (B4/B7's guarantee extended to this new evidence kind).

### D4 — Observation only, no judgement
`assert_document` records whether a document was found for a query — it never returns a
PASS/FAIL. Whether "found" or "not found" satisfies a case's rubric is `grade.py`'s job, given
this evidence like any other (core-invariants C7 extended to the new evidence kind).

### D5 — A live connection is never made by an automated test
Tests exercise `ReadOnlyCollection`/`assert_document` against a fake collection object — no test
in the default suite opens a real socket to Mongo. Any test that would genuinely connect using
`PATHLYNKS_MONGO_URI` is skipped unless a human opts in explicitly (an env var gate), mirroring
`test_browser.py`'s real-Chromium-launch test being skipped when Chromium is absent — except
here the gate is "opted in", not "capability present", because a live connection to Pathlynks'
database is exactly the kind of action this project's standing rules require per-use human
approval for, not something an automated build should do on its own initiative.

## No-fire list

- Write operations of any kind — out of scope by design (D1), not a future task either; a
  write-capable Mongo path does not exist and is not planned.
- Query language/aggregation pipeline support beyond the three exposed methods.
- Connection pooling/retry/timeout tuning (pymongo defaults are fine for a test tool).
- Wiring `EvidenceKind.DB` into `stages/execute.py::run_case`'s step dispatch table — that is a
  FlowSpec/Case-authoring concern (a `Step` would need a way to express "assert this document
  exists"), not required for this contract to close.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · init · contract created for T-045, the follow-on named in
  `browser-and-secrets.md`'s amendment log ("Mongo/DB credential... belongs to a future execute
  contract, not B1-B9").
