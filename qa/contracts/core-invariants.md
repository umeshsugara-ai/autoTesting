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
- Secret values live only in the **repo-root `.env`** (one file for the whole repo, keys namespaced
  per project and declared in each project's `SecretRef[]`); a project can resolve only the keys it
  declares. Everything in that file is masked from logs, prompts, and artifacts, declared or not.
- Prompts and stored steps carry `{{SECRET:KEY}}` placeholders; substitution happens only at the
  moment of typing into the browser, scoped to that `SecretRef`'s `domains` (which lie within the
  project's `allowed_domains`).
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
- **A sabotage must assert that it was applied.** Where a manifest's evidence is "I broke X and N
  tests failed", the harness must establish, before believing any result, that its **anchor
  matched exactly once** and that the **file on disk actually changed**. A patch whose anchor did
  not match applies nothing and reports a green suite — which reads as *"the guard test is
  vacuous"*, the precise opposite of the truth. A sabotage needs its own assertion, not just its
  own patch.
- **A zero-failure sabotage is evidence about the SABOTAGE, not about the tests.** "Anchor matched
  once" + "file changed" are necessary but not sufficient: an anchor can match once inside a
  comment, a docstring, or a line no test exercises, so the patch applies, the file changes, and
  nothing semantically moves. When a sabotage yields 0 failures the harness must report it as
  **INCONCLUSIVE — mutation not shown to change behaviour**, and either strengthen the mutation
  (revert the actual fix hunk, not a nearby string) or state the null result as unproven. It must
  never be reported as "the guard test is vacuous" on that evidence alone.
- **Verify:** `uv run pytest -q` exits 0 and the manifest pastes real output, not a summary; a
  sabotage claim in a manifest is re-run by the checker in its own harness, never read.

### C8 — Provider-agnostic
- All model calls go through `providers.base.Provider`. No stage imports a vendor SDK directly.
- Prompts live in `src/autotester/prompts/*.md` as versioned files, never inline string literals.
- **Verify:** `grep -rE "^(import|from) (anthropic|google)" src/autotester/stages/` returns nothing.

### C9 — A declared control value is honoured or rejected, never silently ignored
- A field that exists to change the system's behaviour (a criticality floor, a `done_check`, an
  approval flag, a gate) must either take effect or fail loudly. A reader that does not recognise
  a value must not substitute a default that is *weaker* than the value written.
- Where the reader is outside this repo and cannot be changed here, this repo pins its own data
  against the reader's actual vocabulary in a test, and files the upstream defect in the ledger.
- Applies to `.goal/goal.json` control fields (`base_criticality`, `done_check`, `approved`) as
  well as to `projects/<slug>/` artifacts.
- **Verify:** `uv run pytest tests/test_goal_criticality_vocabulary.py -q` exits 0.

## No-fire list (do not raise these as findings)

- Style/formatting preferences already satisfied by `ruff`.
- Missing features that are scheduled in a later phase of the plan and not claimed by this unit.
- Absence of tests for code the unit did not touch.
- Suggestions for future work that no criterion requires.
- The `src/` layout differing from the plan's prose `autotester/` — this was a deliberate,
  recorded choice (standard Python packaging); it is not a finding.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · routine · C5: credential file is the repo-root `.env`, keys namespaced + declared per
  project; undeclared values still masked; substitution scoped to the `SecretRef`'s `domains` ·
  why: user instruction 2026-09-03 folded from `qa/feedback-inbox.md` (mirrors browser-and-secrets
  B1 amendment); non-safety-weakening — the gitignore rule `**/.env` already covers the root file,
  and per-project declaration + domain scoping are unchanged.
- 2026-09-08 · routine · added C9: a declared control value is honoured or rejected, never silently
  ignored · why: third occurrence of one shape — AT-100 (a `done_check` of `true` that cannot fail),
  AT-115, and AT-116 (an uppercase criticality vocabulary the shared classifier silently downgraded
  to `low`, disarming every declared floor since the file was created). C1's `extra="forbid"` already
  makes an *unknown key* raise; nothing covered an unknown *value* being quietly replaced by a weaker
  default. Tightening only — it adds a criterion and weakens none, so it applies under the routine
  gate. Ruling on the at116-criticality-vocabulary manifest's open question: `.goal/goal.json` does
  NOT need its own feature contract — one file's vocabulary is too narrow a thing to govern
  separately, and the real invariant is project-wide, so it belongs here.
- 2026-09-08 · routine · added to **C7** the sabotage-assertion clause (an anchor must match
  exactly once and the file must actually change before a sabotage result is believed) · why:
  **five occurrences in two days across three independent agents.** (1) AT-140 cycle 1 — the
  maker's no-op sabotage read as "my test is vacuous" and it nearly rewrote a correct test;
  (2) the `at140` checker hit it from its own side (`max_actions=max_actions` matched twice in the
  file); (3) `at149-at150-path-containment` sabotage T — heredoc quoting mangled the anchor, patch
  applied nothing, suite green; (4) and (5) the checker of that same unit, twice, whose harness
  assertion caught it both times and printed "ANCHOR NOT PRESENT -- harness is lying". Without the
  assertion, (4) would have been reported as "sabotage T: 0 failures, the maker's test is vacuous"
  and a correct fix would have been FAILed. Ruling on the maker's request for a home: **not**
  `consent.md` — a feature contract judges the artifact, not how the maker held the tools, which
  is why AT-131 was correctly refused a home in `ingest.md`; **not** `qa/loop.md` — that file is
  the maker's own, and a rule the maker writes for itself is not a gate. C7 is already the
  criterion about how verification is done ("the executor never grades itself", "the manifest
  pastes real output"), and a sabotage that silently applied nothing is a manifest pasting real
  output from an experiment that never happened. Tightening only — it adds a clause and weakens
  none, so it applies under the routine gate. Verdict:
  `qa/verdicts/at149-at150-path-containment.md`.
- 2026-09-08 · routine · added to **C7** the zero-failure clause (a sabotage that produces no
  failures is INCONCLUSIVE about the tests until the mutation is shown to change behaviour) · why:
  measured during `at151-at152-both-arms` cycle 1, the FIRST unit judged against the clause added
  the day before. The checker's own sabotage U matched its anchor exactly once and changed the
  file on disk — satisfying the clause as written — and produced 0 failures, because the mutated
  string (`"already in the past"` → `"already in the past XXX"`) is on a line no assertion reads.
  Under the previous wording that is a clean "sabotage applied, suite green", which is exactly the
  "the guard test is vacuous" misreading the clause exists to prevent. Re-running with the real
  AT-151 hunk reverted produced the expected failure. The clause I wrote had a hole; this closes
  it. Tightening only — adds a reporting duty, weakens nothing, routine gate. Verdict:
  `qa/verdicts/at151-at152-both-arms.md`.
