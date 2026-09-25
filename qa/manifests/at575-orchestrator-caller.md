# Manifest — at575-orchestrator-caller

**Status:** ready-for-check
**Fix cycle:** 1 of 3
**Dual check:** no
**Issues addressed:** AT-575
**Branch:** `wave/at575-orchestrator-caller` (from master `76dfbde`)
**Commit:** `26d7d93` feat(orchestrate): live CLI caller for run_or_resume (AT-575)
**Contract:** `qa/contracts/orchestrator.md` (OR1-OR6, D-036)

## The gap this closes

T-163's resumable orchestrator (`src/autotester/stages/orchestrate.py::run_or_resume`, D-036) had
no caller outside `tests/test_orchestrate*.py` — `grep -rn run_or_resume src/autotester` (excluding
`stages/orchestrate*`) returned no hits on master `ef1b043` (AT-575's own evidence). `at562-564`
wired the UI Run route to build its own `StageContext` directly (trace + secrets) and run cases,
not through `run_or_resume`, so learn/explore resume-after-interruption stayed reachable only from
pytest. `docs/FEATURES.jsonl` F-053 carries a caveat naming exactly this gap.

## What changed

- **`src/autotester/cli_orchestrate.py`** (new, 186 lines) — `orchestrate_cmd` (line 145), a new
  `autotester orchestrate <project>` command. It:
  - loads the project (`ProjectStore.load_project`, line 166-169) and its `SecretStore`
    (`SecretStore.load(proj, paths.env_file, strict=False)`, line 174), same as `explore_cmd`
    (`cli_crawl.py:86`);
  - decides the entry path via the SAME `choose_mode` the driver uses (line 172), then
    `_build_runners` (line 94-114) wires **exactly** `{INGEST|DISCOVER, MODEL}` through the
    existing stage adapters `stages/orchestrate_runners.py::make_ingest_runner` /
    `make_discover_runner` / `make_model_runner` — no new stage logic, no new approval mechanism
    (matches `orchestrate.py`'s own "a stage with no registered runner is a STOP point" contract,
    the driver halts at the review gate exactly as it does under test);
  - for the `explore` path, calls `_require_crawl_consent` (line 51-65) — the same D-018 gate-2
    check (`stages/explore_consent.py::require_consent`) `explore_cmd`'s own preflight
    (`cli_crawl.py::_preflight_consent`) runs, BEFORE any directory or browser opens (AT-111's
    invariant: a refused run leaves no trace);
  - constructs `StageContext(store=store_, run_id=run_id or mint_run_id("run"), runners=runners,
    secrets=secrets)` (line 181-182) — `secrets=` is the AT-561 fix: without it `StageContext`
    silently falls back to an unredacted `Redactor({})` and the RT6 trace gate goes dark;
  - `--run-id` (line 146-149) lets the same run be re-invoked to resume it — omitted, a fresh id is
    minted; the printed summary (`_echo_state`, line 117-141) always echoes the run id back so an
    operator can resume it.
- **`src/autotester/cli.py`** — `cli.py:10` adds `cli_orchestrate` to the import line (was at its
  line budget, 294/300, so the command lives in a sibling module exactly like `cli_crawl.py` /
  `cli_video.py`); `cli.py:291` mounts `app.command("orchestrate")(cli_orchestrate.orchestrate_cmd)`.
- **`tests/test_cli_orchestrate.py`** (new, 197 lines) — drives the real CLI via
  `typer.testing.CliRunner`, never `run_or_resume` directly. Temp `AUTOTESTER_ROOT`
  (`monkeypatch.setenv`, no real `.env`/`projects/` touched), `MockProvider` for the model call.
- **`docs/MAP.md`** regenerated (`uv run autotester map`) — the only way `doctor`'s
  `stale-generated` check passes after a new module.

### The wiring itself (`cli_orchestrate.py:94-114`)

```python
def _build_runners(...) -> dict[StageName, Callable]:
    if mode == "learn":
        source = _entry_source(sources)
        model = providers.get(provider_id)
        return {
            StageName.INGEST: make_ingest_runner(source, project, model, RepoDocs()),
            StageName.MODEL: make_model_runner(source_id=source.id),
        }
    _require_crawl_consent(proj, store_, bounds)
    crawl_fn = _make_crawl_fn(proj, store_, paths, secrets, bounds, login_case_id)
    return {
        StageName.DISCOVER: make_discover_runner(proj, crawl_fn),
        StageName.MODEL: make_model_runner(),
    }
```

```python
ctx = StageContext(store=store_, run_id=run_id or mint_run_id("run"), runners=runners,
                   secrets=secrets)
state = run_or_resume(proj, ctx)
```

## Tests (red-first; TDD, all through the CLI entry point)

`tests/test_cli_orchestrate.py`, 4 tests, all against a temp `AUTOTESTER_ROOT`:

1. `test_fresh_learn_run_checkpoints_ingest_and_model_through_the_cli` — (a) a fresh run: INGEST +
   MODEL land `done` in `state.json`, and the flowspec on disk actually gained the ingested screen
   (DRAFT, never auto-approved).
2. `test_resume_after_interruption_never_redoes_the_done_stage` — (b) MODEL is made to raise once
   (`merge_flowspec` monkeypatched flaky); first invocation: INGEST `done`, MODEL `failed`, exit 1.
   Second invocation with the SAME `--run-id`: `ingest_video` call count stays at 1 (proven via a
   counting wrapper), INGEST's `artifact_ref` is byte-identical, MODEL re-enters and this time
   succeeds, exit 0.
3. `test_secrets_reach_stagecontext_so_the_trace_gate_never_falls_back` — (c) a declared secret in a
   temp `.env`; asserts NO `RuntimeWarning` about `StageContext` falling back to an unredacted
   `Redactor({})` fires during a real invocation (the AT-561 defect, proven live rather than
   inferred).
4. `test_explore_mode_without_an_approval_refuses_before_the_crawl_starts` — (d) a credentials-only
   project (no approval granted) on the `explore`/DISCOVER path: exit 2, "approv" in the message,
   no run directory left on disk.

Run: `uv run pytest tests/test_cli_orchestrate.py -q` → `4 passed`.

## Capability-coverage table

Each row: committed code is green; a single-hunk falsifying edit (via `git checkout -- <file>`
revert afterward, never left in the worktree) reproduces red **for the named reason**; reverted →
green again. All four done directly in the worktree via edit → run → `git checkout --` revert
(code was committed first specifically so this revert is exact and clean — no throwaway copy
needed for a same-repo git-tracked revert).

| # | Capability | Falsifying edit | Red — named reason | Revert | Result |
|---|---|---|---|---|---|
| 1 | The CLI actually exposes a command that drives `run_or_resume` (acceptance bar item 1) | Commented out `cli.py:291` (`app.command("orchestrate")(...)`) | `No such command 'orchestrate'` — typer refuses the invocation outright | `git checkout -- src/autotester/cli.py` | green (4 passed) |
| 2 | `--run-id` enables a real resume, not a relabelled fresh run | `cli_orchestrate.py:181` — dropped `run_id or` so a fresh id is minted every invocation | `test_resume_after_interruption_never_redoes_the_done_stage` fails: `state.json` never lands at the requested run dir (`assert None is not None`) | `git checkout -- src/autotester/cli_orchestrate.py` | green (4 passed) |
| 3 | Secrets reach `StageContext` (RT6 gate live, acceptance bar item 2) | `cli_orchestrate.py:181-182` — dropped `secrets=secrets` | `test_secrets_reach_stagecontext_so_the_trace_gate_never_falls_back` fails: the AT-561 `RuntimeWarning` fires | `git checkout -- src/autotester/cli_orchestrate.py` | green (4 passed) |
| 4 | DISCOVER honours the same D-018 consent gate `explore` does, before anything starts | `cli_orchestrate.py:109` — commented out `_require_crawl_consent(...)` | `test_explore_mode...` fails: exit code drops from 2 to 1 — the crawl now reaches `run_crawl`'s own deeper gate and dies as a **failed checkpoint with a run directory left on disk**, instead of the clean AT-111 "no trace" refusal; proves the CLI-level preflight is what delivers the correct, trace-free refusal, not merely defense in depth | `git checkout -- src/autotester/cli_orchestrate.py` | green (4 passed) |

Row 4 finding: even with the preflight removed, `stages/explore.py::run_crawl`'s own consent check
still refuses the crawl (defense in depth, D-018 gate 2 is checked at two seams by design) — but
without the CLI's own preflight the refusal shows up as a failed `RunState` checkpoint (a run
directory on disk, exit 1) rather than AT-111's "a refused run leaves no trace" (exit 2, nothing
written). The preflight is load-bearing for that invariant even though the deeper gate cannot
actually be bypassed.

## Verify

```
uv run pytest tests/test_cli_orchestrate.py tests/test_orchestrate.py tests/test_orchestrate_runners.py \
  tests/test_cli_surface.py tests/test_expand_cli.py tests/test_ingest_real_cli.py \
  tests/test_crawl_real_cli.py tests/test_approve_cli.py -q
  -> all green (no `-q` stacking beyond pyproject's own addopts, AT-503)
uv run ruff check src tests scripts   -> All checks passed!
uv run autotester doctor              -> doctor: clean (after `uv run autotester map` regenerated docs/MAP.md)
```

**Full non-browser suite:** gated per the RAM rule — free RAM measured 2.94-2.95 GB across the
build (below the 3.5 GB floor) with 7 `python.exe` processes already present on the machine.
Polled every 5 minutes for 20 minutes via a background monitor; if it clears the floor before this
manifest is checked, its result supersedes this note — otherwise this is a **gap**: the full suite
was not run this cycle, and the targeted modules above (85+ tests spanning orchestrate, orchestrate
runners, ingest, crawl, expand, approve, and the CLI surface) stand in as the closest available
substitute. No `d:/autoTesting` pytest process was independently confirmed idle beyond the
`python.exe` count above.

**Pre-existing state:** `docs/DECISIONS.md` / Lab Protocol are not active in this repo (no
`docs/DECISIONS.md` at the root — `qa/` maker-checker discipline applies instead, per
`d:/autoTesting/CLAUDE.md`).

## Browser / Mode D

**Not UI-touching.** Changed files: `src/autotester/cli_orchestrate.py` (new CLI command),
`src/autotester/cli.py` (2-line mount + import), `tests/test_cli_orchestrate.py` (new test file),
`docs/MAP.md` (regenerated). No file under `src/autotester/ui/` was read or modified, and no
route was added or changed. Mode D: **SKIP**.

## Gaps / follow-ups for the checker

1. Full non-browser suite RAM-gated this cycle (see Verify section) — worth a re-run when the
   machine is quieter.
2. This unit deliberately stops at MODEL (the review gate) per `orchestrate.py`'s own contract — it
   does **not** wire EXPAND/EXECUTE/GRADE/REPORT into the orchestrator; those stay reached through
   their existing standalone commands (`expand`, etc.) exactly as today. If F-053's caveat should
   only drop once the ENTIRE pipeline is orchestrator-driven rather than "resume through the review
   gate is live", that is a scope question for the checker/ledger, not something this unit silently
   assumed either way.
3. `--run-id` is a new, minimal convention (no prior "latest run" helper existed anywhere in the
   codebase to build on) — an operator must copy the printed run id to resume. A future unit could
   add a `--resume-latest` convenience; out of scope here (no issue currently open for it).
