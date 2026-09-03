# Contract — core invariants (project-wide)

**Applies to:** every work unit in `d:/autoTesting`. A unit that violates any criterion here
fails its check regardless of what its own feature contract says.
**Owner:** /checker (maker reads only; feedback → `qa/feedback-inbox.md`).
**Source:** approved plan `C:/Users/Lenovo/.claude/plans/great-when-you-really-iridescent-ocean.md`
§3 Design principles, §7 Enforcement, §8 Security.

## Why these exist

The prior project (`d:/erp`) shipped without an upfront schema or system design. It reached 232
top-level entries, 977 source files, duplicated concepts across modules, and a 291-line landmine
document — at which point neither a human engineer nor an agent could hold it in context or take
control of it. Every criterion below is a cheap rule now that was unaffordable there.

## Criteria

### C1 — Schema-first, single source of truth
- Every domain data shape is a Pydantic model under `src/autotester/schema/`, one model family per file.
- No dict-shaped domain object, dataclass, or TypedDict duplicating a schema model exists elsewhere.
- Every artifact model inherits `schema.base.Artifact` (carries `schema_version`, `created_at`, `provenance`).
- Models use `extra="forbid"`, so an unknown key raises at load instead of being silently dropped.
- **Verify:** `uv run pytest tests/test_schema.py -q` exits 0.

### C2 — Readable by a human and an agent
- No file in `src/` or `tests/` exceeds 300 lines; no function exceeds 50 lines.
- Every module has a docstring stating its one job.
- `docs/ARCHITECTURE.md` stays ≤ 150 lines and its concept→file table matches reality.
- **Verify:** `uv run autotester doctor` exits 0.

### C3 — One concept, one place (anti-drift)
- No class or public top-level function name is defined in two modules.
- No file named `*_v2.py`, `*_new.py`, `*_old.py`, `*_copy.py`, `*_final.py`, `*_temp.py`.
- Changes edit existing files in place; a new module requires a stated reason in the manifest.
- **Verify:** `uv run autotester doctor` exits 0 (duplicate-concept + drift-filename rules).

### C4 — Repo root stays clean
- Top-level entries are limited to the declared layout (`src`, `tests`, `docs`, `projects`,
  `profiles`, `qa`, `.goal`, `.work`, config files).
- Scratch, logs, and in-progress evidence live in `.work/` (gitignored), never the repo root.
- **Verify:** `uv run autotester doctor` exits 0 (root-clutter rule).

### C5 — Secrets never reach a model, a log, or an artifact
- `SecretRef` carries a key and its domain scope. No schema model has a field holding a secret value.
- Prompts and stored steps carry `{{SECRET:KEY}}` placeholders; substitution happens only at the
  moment of typing into the browser, scoped to the project's `allowed_domains`.
- Every log line and stored artifact passes `core.redact.Redactor.scrub`.
- `**/.env`, `profiles/`, `.work/`, and `projects/*/runs/` are gitignored.
- **Verify:** `uv run pytest tests/test_core.py -q` exits 0; `git ls-files | grep -E "\.env$"` returns nothing.

### C6 — Artifacts are human-editable files
- Every stage output is JSON, JSONL, or Markdown on disk under `projects/<slug>/`, valid against its model.
- A human can open, edit, or delete any artifact and the system still loads.
- The UI is a view over these files, never a second source of truth.
- **Verify:** artifact roundtrip tests pass; no database is the primary store.

### C7 — Verification is independent
- A unit is complete only when a check that someone else can re-run passes.
- The executor never grades itself: `RawResult` records observation, `Verdict` records judgement,
  and they are produced by different components.
- **Verify:** `uv run pytest -q` exits 0 and the manifest pastes real output, not a summary.

### C8 — Provider-agnostic
- All model calls go through `providers.base.Provider`. No stage imports a vendor SDK directly.
- Prompts live in `src/autotester/prompts/*.md` as versioned files, never inline string literals.
- **Verify:** `grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/` returns nothing.

## No-fire list (do not raise these as findings)

- Style/formatting preferences already satisfied by `ruff`.
- Missing features that are scheduled in a later phase of the plan and not claimed by this unit.
- Absence of tests for code the unit did not touch.
- Suggestions for future work that no criterion requires.
- The `src/` layout differing from the plan's prose `autotester/` — this was a deliberate,
  recorded choice (standard Python packaging); it is not a finding.
