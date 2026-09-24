# Verdict — t164-portal-persona

**Date:** 2026-09-24
**Checker:** claude-sonnet-subagent (fresh context, no builder reasoning)
**Cycle checked:** 1
**Bound root:** D:/autoTesting/.worktrees/t164-portal-persona (branch wave/t164-portal-persona,
head df979243b7b833965cc6f64913e740ee6530e211)
**Base for diff scope:** ec82440 (`git merge-base master wave/t164-portal-persona`)

## What I re-ran myself

- `uv run pytest tests/test_portal_persona.py` -> `7 passed in 2.81s` (reproduced; matches manifest).
- `uv run ruff check src tests scripts` -> `All checks passed!` (reproduced; matches manifest).
- `uv run autotester doctor` -> `doctor: clean` (reproduced; matches manifest).
- `uv run pytest` (full suite) -> **`1 failed, 1584 passed, 5 skipped, 32 xfailed, 1 warning in
  2388.66s`** — does **not** reproduce the manifest's pasted `1585 passed ... 0 failed in
  665.01s`. The one failure is `tests/test_flake_probe_real_process.py::test_run_once_kills_a_real_hung_process_and_its_real_grandchild`.
  Investigated before judging (see FAILURES/ISSUES-WRITTEN below) — this file and its supporting
  module are byte-identical between base `ec82440` and head `df97924`
  (`git diff ec82440 df97924 -- tests/test_flake_probe_real_process.py` is empty; last real touch
  was `eb48415`, well before this unit's base). Re-ran it 3 more times in isolation on an
  otherwise-idle machine: failed identically all 3 times (deterministic, not a transient flake).
  Per this repo's own AT-196 precedent (`qa/contracts/core-invariants.md` amendment log,
  2026-09-09) and the same-shaped prior findings `ISS-t162-drive-2b-1` / `ISS-t163-1`: a full-suite
  failure confirmed untouched by the unit's diff is recorded as ledger debt, not charged against
  the unit's own PASS. Filed as `ISS-t164-1` (medium; not a blocker on T-164).
- Diff scope: `git diff ec82440 df97924 --stat` -> 9 files changed, 885 insertions(+), 1
  deletion(-) (the `-1` is `docs/SNAPSHOT.md`'s decisions-list edit, not a deletion of a class,
  function, export, route, test or config key). Exactly the 9 files the manifest's "What changed"
  names: `docs/MAP.md`, `docs/SNAPSHOT.md`, `qa/manifests/t164-portal-persona.md`,
  `src/autotester/core/paths.py`, `src/autotester/schema/portal_persona.py`,
  `src/autotester/stages/portal_persona.py`, `src/autotester/stages/portal_persona_view.py`,
  `src/autotester/store/project_store.py`, `tests/test_portal_persona.py`. No file outside this
  list touched; no existing function/class/export/test/config key deleted or renamed —
  `core/paths.py` and `store/project_store.py` diffs are pure additions.

## Naming deviation (PP contract sketch `run(input, ctx)` vs. `build_portal_persona(store, ...)`)

Judged and accepted. `doctor.py:195` already defines a top-level `run(root)`, so a second
module-level `run` would trip C3's duplicate-definition rule (confirmed: `uv run autotester
doctor` is clean, and a direct grep shows only one `def run(`, at `doctor.py:195`). The repo
already has a precedent for this exact shape — `build_screen_map(store)` in
`stages/product_map.py:66`. The contract's "a `run(input, ctx) -> PortalPersona` stage" language
describes the STAGE SHAPE (a callable taking the store/context and producing the artifact), not a
literal function name, and `build_portal_persona(store, *, crawl_id=None, redactor=None) ->
PortalPersona` satisfies that shape one-for-one (`store` is `ctx`; the FlowSpec + crawl id loaded
from `store` are `input`). No criterion is weakened by this reading.

## Criteria (PP1-PP6)

All six judged MET on evidence I reproduced myself, not on pasted output.

- **PP1** — single JSON store (`portal_persona.json` via `store/filestore.py`'s atomic
  `write_json`/`read_json`, no second store) + `knowledge.md` as a regenerated view. Falsifying
  edit reproduced: GREEN (7 passed) -> RED (`assert False +where False = exists()`, matches
  manifest exactly) -> revert -> GREEN.
- **PP2** — a second run with material omitting "Login" still keeps it, adds "Dashboard". Reproduced:
  GREEN -> RED (`assert 'Login' in {'Dashboard'}`, matches manifest) -> revert -> GREEN.
- **PP3 (delta)** — a real change appends exactly one dated, named revision. Reproduced: GREEN ->
  RED (`assert 1 == 2`, matches manifest) -> revert -> GREEN.
- **PP3 (identical re-run)** — an unchanged re-run appends nothing. Reproduced: GREEN -> RED
  (`assert 2 == 1`, a fabricated `summary='noop change'` revision, matches manifest) -> revert ->
  GREEN.
- **PP4** — `knowledge.md` is a faithful regenerated view; mutating the model and regenerating
  reflects the change. Reproduced: GREEN -> RED (`assert 'Settings Panel' in '...'`, matches
  manifest) -> revert -> GREEN.
- **PP5** — a raw secret in incoming material never reaches the persisted JSON or the page; the
  pre-write `_guard_clean` gate (functionally equivalent to `assert_no_raw_secrets`: raises
  `ValueError` on any known-clean-check failure) refuses to persist when the scrub is bypassed.
  Reproduced: GREEN -> RED (`ValueError: refusing to persist portal persona: raw secret value
  present`, matches manifest) -> revert -> GREEN.
- **PP6** — a taught flow's `run_ref` resolves back to it via `PortalPersona.resolve_run`; a bogus
  ref resolves to `None`. Reproduced: GREEN -> RED (`assert None is TaughtFlow(...)`, matches
  manifest) -> revert -> GREEN.

Explicit no-fire list respected: no finding raised about pipeline-diagram placement, a new
datastore, or `knowledge.md` "duplicating" the JSON.

## Core invariants (core-invariants.md)

- **C1** — `PortalPersona(Artifact)` inherits `extra="forbid"` from `schema/base.py`'s `Artifact`
  (`model_config = ConfigDict(extra="forbid", use_enum_values=False)`); no dict/dataclass/TypedDict
  duplicate found. Met.
- **C2** — all 4 new/changed files well under 300 lines (177, 266, 113, 156); every module carries
  a one-job docstring; `docs/ARCHITECTURE.md` untouched, stays at 150 lines (its declared ceiling),
  consistent with D-038 (no pipeline-diagram prose change). `uv run autotester doctor` clean. Met.
- **C3** — grepped every new class/function name (`PortalPersona`, `PersonaProfile`, `AuthField`,
  `AuthShape`, `PersonaScreen`, `PersonaTransition`, `FlowRunRef`, `TaughtFlow`, `Gotcha`,
  `PersonaRevision`, `save_portal_persona`, `load_portal_persona`, the `portal_persona` property):
  each defined exactly once. No `*_v2.py`/`*_new.py`-shaped filenames. `doctor` clean. Met.
- **C4** — no repo-root clutter introduced; new files live under existing `src/`/`tests/` layout. Met.
- **C5** — auth carried by shape only (`AuthField.secret_key`, never a value); PP5's falsifying
  edit proves the pre-write secret guard is load-bearing, not decorative. Met.
- **C6** — persisted via the shared `filestore.py` atomic JSON primitives (temp file + `os.replace`),
  human-editable, no DB. Met.
- **C7** — this unit adds a new test file, so the mutation duty applies; I performed the mutation
  runs myself (the capability-coverage table above) rather than trusting the pasted rows, each
  anchor asserted to match exactly once before applying, each named failure attributed to the
  correct test, each GREEN baseline in the copy asserted before mutating. The `uv run pytest`
  (whole-project) sub-clause is discussed above (ISS-t164-1) — not treated as a T-164-attributable
  violation per the AT-196 precedent.
- **C8** — no model/provider calls in this stage at all; `grep -rE "^(import|from)
  (anthropic|google)" src/autotester/stages/` returns nothing new here. N/A-clean.
- **C9** — N/A (no criticality/done_check/approved field touched by this unit).
- **C10** — this verdict's own commit will carry only `qa/verdicts/t164-portal-persona.md`,
  `qa/issues.jsonl`, `qa/contracts/portal-persona.md`, `.goal/goal.json`, staged narrowly.

## Capability coverage

7/7 rows reproduced independently in a throwaway copy
(`C:/Users/Lenovo/AppData/Local/Temp/claude/checker-t164/tree`, `.venv` copied alongside so `uv
run pytest` executes for real, not against a bare source extraction). The named check ran GREEN
in the copy before every edit (proving the copy is real), then RED for the exact reason each row
claims, then GREEN again after revert. `grep -rn SABOTAGE` in the copy returns nothing after the
run, and a `diff -rq` of every edited file against the bound tree shows the bound tree was never
touched (edits applied and reverted only in the scratch copy, one row and one pytest process at a
time — the machine's ~2.6 GB free RAM was respected throughout).

## Live browser

Not applicable. Changed paths are schema/stage/store/paths/tests/docs plus a markdown
knowledge-view generator — none render a UI surface. `knowledge.md` is a generated file artifact,
not a page served to a browser; nothing in `ui/` or a templated route was touched.

## Issues addressed

Manifest declares none (new feature) — correct; nothing in the ledger names this feature before
today.

## FAILURES

None at >80% confidence against any PP or core-invariants criterion attributable to this unit.

## Contract status

Per the contract's own instruction ("the checker takes it DRAFT->ACTIVE on T-164's first PASS"),
flipped `qa/contracts/portal-persona.md`'s Status line DRAFT -> ACTIVE, citing this verdict.

---

```
VERDICT: PASS
SCOREBOARD: 6/6 criteria met (PP1-PP6, PP3 counted once; 7/7 falsifying rows reproduced), 10/10 applicable core invariants hold (C8/C9 not applicable to this unit)
FAILURES (if any):
- none
CAPABILITY-COVERAGE: 7/7 rows reproduced
LIVE-BROWSER: not-applicable (schema/stage/store/paths/tests/docs + generated knowledge.md view; no UI surface touched)
ISSUES-WRITTEN: ISS-t164-1 (medium, pre-existing unrelated full-suite pytest failure, not a T-164 blocker)
EXECUTOR: claude-sonnet-subagent (checker: claude-sonnet-subagent)
EXPLANATION: All 6 PP criteria (7 falsifying rows) reproduced green-before/red-for-the-named-reason/revert-green in an independent throwaway copy with its own .venv. The manifest's scoped verify commands (test_portal_persona.py, ruff, doctor) all reproduced exactly as pasted. The manifest's full-suite claim did not reproduce -- one unrelated, deterministic, pre-existing failure in test_flake_probe_real_process.py, confirmed untouched by this unit's diff via git diff/log, filed as ISS-t164-1 per the repo's own AT-196 precedent rather than charged to this unit. Diff scope is exactly the 9 files the manifest names, no deletions of existing symbols. Contract taken DRAFT->ACTIVE per its own instruction.
```
