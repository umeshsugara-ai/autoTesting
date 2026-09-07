# Verdict — track-a1-video-schema

**Contract:** qa/contracts/core-invariants.md (C1, C2, C3, C6) — schema-only unit
**Manifest:** qa/manifests/track-a1-video-schema.md
**Cycle checked: 1**
**Date:** 2026-09-07
**Checker:** /checker Mode A (fresh context, no builder reasoning)
**Bound root:** d:/autoTesting

```
VERDICT: PASS
SCOREBOARD: 4/4 criteria met (C1, C2, C3, C6), 0/0 invariants (I6-I9/VL* land with A2/A3 per plan)
FAILURES (if any): none
ISSUES-WRITTEN: none new — AT-089, AT-090 (pre-existing, checker-sweep-filed) confirmed genuinely
resolved and moved open -> verified below
EXPLANATION: Every verify command was re-run by the checker itself in the container (staleness
guard passed: bind-mounted source, container start predates the commit but serves live files) and
reproduced the manifest's claimed output exactly, including the exact pass/skip/fail counts
extracted byte-by-byte since this pytest build prints no terminal summary line. D-014's additive
field list was diffed line-for-line against the committed change and nothing exceeds it. Issue.id
content-addressing, extra="forbid" strictness, and the new StepNotExecutable path are all backed
by real, independently-inspected tests rather than manifest prose.
```

## Commands re-run by the checker (not the maker's paste)

| Command | Result |
|---|---|
| `docker compose exec -T autotester uv run pytest -q` | exit 0 — counted directly from the progress-dot stream: **385 passed, 1 skipped, 0 failed** (this pytest/plugin combination prints no final summary line in this container; verified by byte-counting `.`/`s`/`F` in the recorded run rather than trusting a missing line) |
| `docker compose exec -T autotester uv run pytest tests/test_schema.py tests/test_schema_video.py tests/test_store.py tests/test_execute.py tests/test_ingest.py -q` | exit 0, all pass |
| `docker compose exec -T autotester uv run ruff check src tests scripts` | `All checks passed!` |
| `docker compose exec -T autotester uv run autotester doctor` | `doctor: clean` |
| `docker compose exec -T autotester uv run autotester map` | regenerated; `git diff --stat docs/MAP.md` → no diff, already committed in ce1b624 |
| `docker compose exec -T autotester uv run python -c "...Transcript.from_sidecar(...)..."` | `6 22.0` — matches manifest exactly |

**Staleness guard:** container `autotester` started `2026-09-07T11:52:46Z`; commit `ce1b624` is
`17:50:11 +0530` = `12:20:11Z`, i.e. *after* container start. Checked `docker-compose.yml`:
`volumes: [".:/app"]` is a live bind mount (not a build-time COPY), so the running container reads
current source regardless of when it started — confirmed by the newest source file mtimes
(`schema/screenmap.py` etc., all from this commit) actually being visible and exercised inside the
container's own test run. No stale-image risk here.

## Scrutiny items demanded by the dispatch

### 1. Committed diff matches manifest's prose — VERIFIED

`git show --stat ce1b624`: 21 files changed, exactly the files the manifest lists (schema/enums.py,
new observation.py/media.py/analysis.py/issue.py/screenmap.py, flowspec.py, project.py,
core/paths.py, store/project_store.py, stages/execute.py, stages/ingest.py, the two test files,
the new fixture, docs/MAP.md, docs/SNAPSHOT.md, .goal/goal.json, .goal/dashboard.html, .gitignore).
No file outside this list, no undisclosed change. The manifest's own commit hash (`ce1b624`) and
the follow-up manifest-only commit (`0eba245`) both exist in `git log` and both match their stated
content.

### 2. Schema strictness (`extra="forbid"`) on the new models — VERIFIED

`schema/base.py`'s `Artifact` sets `model_config = ConfigDict(extra="forbid", use_enum_values=False)`
and every new BaseModel in `observation.py`, `media.py`, `analysis.py`, `issue.py`, `screenmap.py`
repeats `ConfigDict(extra="forbid")` individually (checked file-by-file — 15 of 15 new classes
carry it). `tests/test_schema_video.py` exercises this concretely on three different models
(`TranscriptSegment`, `ObservedIssue`, `Issue`) each rejecting an injected unknown field with
`ValidationError` — read directly, not just cited.

### 3. `Issue.id` is genuinely content-addressed and stable — VERIFIED

`schema/issue.py:47-59` (`model_post_init`) hashes `{project, source_id, screen(casefolded),
category, bucket=round(at_s/5), title(normalised)}` via `core.ids.content_id`. Read the three
tests directly: `test_issue_id_is_stable_across_created_at_and_severity` (two issues built with
identical fields but different `created_at`/severity would collide — the model doesn't even take
those as hash inputs), `test_issue_id_differs_when_title_differs`, and
`test_issue_id_buckets_nearby_timestamps_together` (12.0s and 12.4s bucket together at
round(x/5)=2, 13.4s buckets separately at 3) — all three pass and their assertions genuinely test
the claimed behaviour, not a tautology.

### 4. No dict-shaped domain object introduced (C1) — VERIFIED

Grepped `dict[` across every `src/autotester/schema/*.py`. Two hits, both pre-existing and outside
this commit's diff: `bench.py:58` (`def score(...) -> dict[str, float]`, a function return type,
not a stored domain shape) and `enums.py:69` (`KIND_BY_CLASS: dict[...]`, a fixed lookup table, not
an artifact field). None of the five new schema files contain a `dict[`/raw-dict domain field —
`VideoAnalysis.flows`/`screens`/`issues` and `ScreenMap`/`Journey.stops` all use the typed models
(`ObservedFlow`, `AnalysedScreen`, `AnalysedIssue`, `JourneyStop`) the manifest says it corrected
its own first draft to use. Confirmed by reading `analysis.py` and `screenmap.py` directly.

### 5. `Screen`/`FlowSpec`/`Source` got exactly D-014's additive fields, nothing else — VERIFIED

Read D-014's full text in `docs/DECISIONS.md` and diffed it against `git show ce1b624` for these
three files line-for-line:
- `flowspec.py`: `Screen += source_ref: SourceRef | None`; `FlowSpec += app_overview: str | None`.
  Nothing else added to either class; the diff's only other change to this file is the *removal*
  of `ObservedStep/ObservedFlow/ObservedScreen/VideoObservation` (moved to `observation.py`, per
  D-014 item 2, discharging the file's 300-line cap).
- `project.py`: `Source += recorded_on: str | None`. Nothing else.
Both match D-014's "(4) Screen += source_ref; Source += recorded_on" clause exactly — no
additional undisclosed field on any of the three models.

### 6. `stages/execute.py`'s new `StepNotExecutable` path — VERIFIED with a real test, not prose

`_ACTIONS[step.action]` → `_ACTIONS.get(step.action)` with an explicit `StepNotExecutable` raise
when `None`, caught by the existing generic `except Exception` in `run_case` (unchanged branch),
producing `Outcome.ERRORED`. `tests/test_execute.py:269-277` builds a real `Step(action=SCROLL)`
(an enum member added in this same commit with no handler yet), runs it through `run_case`, and
asserts `Outcome.ERRORED` — read directly, not just cited. This is a genuine regression test for
the exact seam the manifest describes, not an assertion resting on prose.

### 7. AT-089 / AT-090 claimed corrections — VERIFIED REAL, not overclaimed

- **AT-090** (checker-sweep-filed, `e362214`): claimed `autotester doctor` failure from duplicate
  `ObservedStep/ObservedFlow/ObservedScreen/VideoObservation` definitions mid-migration. Live
  `doctor: clean` re-run above confirms the migration finished cleanly — `flowspec.py`'s diff
  shows the four classes fully removed (not just left as dead code) at the same commit that adds
  them to `observation.py`. Genuinely resolved.
- **AT-089** (checker-sweep-filed, `e362214`): claimed `.goal/goal.json`'s `T-121` row was still
  `pending` despite a tick claiming it closed. Diffed `git show ce1b624 -- .goal/goal.json`
  directly: `"status": "pending"` → `"status": "done"` for `T-121`, and the live file confirms
  `status: done` today. Genuinely resolved, bundled into this commit as the manifest states.
- Both were still marked `"status": "open"` in `qa/issues.jsonl` at check time (the maker never
  flipped them to `fixed`) — moved directly to `verified` below since this check is itself the
  independent re-verification.

## Ledger

- **AT-089** `open` → `verified` (T-121 status flip in `.goal/goal.json`, confirmed in the
  committed diff of `ce1b624` and in the current file).
- **AT-090** `open` → `verified` (`autotester doctor: clean` re-run confirms the duplicate-concept
  violations are gone; `flowspec.py` diff shows a clean move, not a copy).
- No new issues filed — nothing found at >80% confidence beyond the manifest's own claims.

## Source-commit confirmation

`ce1b624` (source) and `0eba245` (manifest) are both present in `git log` on the current branch;
`git status --short` at check time showed only unrelated pre-existing working-tree changes
(`.goal/dashboard.html`, `.goal/goal.json` — the session's own dashboard/tick churn, not part of
this unit) — the maker's actual diff for T-130 is fully committed, nothing left uncommitted.

## Cleanup

No scratch artifacts were created by this check; all verification ran in-container against the
existing test suite and fixtures. `.goal/goal.json` task `T-130` closed via `goal_cli.py done`
below.
