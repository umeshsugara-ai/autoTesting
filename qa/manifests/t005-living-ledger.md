# Manifest — t005-living-ledger

**Contract:** qa/contracts/living-ledger.md (L1–L7) + qa/contracts/core-invariants.md
**Goal task:** T-005 (`user_value: high`)
**Date:** 2026-09-03
**Fix cycle:** 2 of max 3
**Issues addressed:** AT-019 (S2, C2), AT-020, AT-021, AT-022 (S3) — this cycle. Design source: `.work/grill-living-ledger.md` (9 Qs, pre-mortem) and plan §14, approved by Umesh.

## Cycle 2 — fixes for verdict `qa/verdicts/t005-living-ledger.md` (Cycle checked: 1)

- **AT-019 (S2)** "ARCHITECTURE.md is 200 lines > the 150 cap, and doctor has no rule for the cap" →
  the two generated sections moved to a new routed sibling **`docs/MAP.md`** (self-describing header;
  `RepoDocs.map`; `autotester map` writes it; L1 freshness check now targets MAP.md).
  `docs/ARCHITECTURE.md` keeps a one-paragraph pointer and is **135 lines**. New doctor rule
  `check_architecture_budget` (`architecture-too-long` at > 150, cap in `render.ARCHITECTURE_MAX_LINES`).
  Router row added for MAP.md. **The cap itself was not touched** (raising it is Umesh's call).
  Contract note: L1 still says the sections live in ARCHITECTURE.md — the checker said it would fold
  the MAP.md relocation as a routine, non-weakening amendment at this check.
  Tests: `test_architecture_over_budget_is_a_doctor_violation`, map tests re-pointed at `docs.map`.
- **AT-020 (S3)** "hand-pasted duplicate id passes doctor silently" → `store.load_events` rejects a
  duplicate `id` with its line number (`duplicate id F-001 (rows are append-only)`).
  Test: `test_duplicate_id_pasted_by_hand_is_rejected_at_load`.
- **AT-021 (S3)** "doctor tracebacks instead of reporting `ledger-invalid`" → `check_ledger` catches
  any exception from the loader and reports it as a violation with the exception type.
  Test: `test_doctor_reports_a_broken_ledger_instead_of_raising`.
- **AT-022 (S3)** "no roll-up for high features" → snapshot shows at most 8 high features, then
  `+N more high-value features → docs/FEATURES.jsonl`. Test: `test_snapshot_rolls_up_high_features_past_the_cap`.

## What changed

- `src/autotester/schema/enums.py` — `FeatureEventKind` (planned/live/updated/retired), `UserValue` (high/normal/low).
- `src/autotester/schema/ledger.py` (new) — `FeatureEvent` (the FEATURES row; retirement refuses the auto-reason `update`; `ask_required` = high value + auto reason) and `RelitigationVerdict`. Exported from `schema/__init__.py`.
- `src/autotester/core/paths.py` — `RepoDocs` (ledger, snapshot, architecture, decisions, router, goal, prompts paths). One place for repo-level doc paths, as `ProjectPaths` is for project paths.
- `src/autotester/ledger/store.py` (new) — `load_events` (line-numbered errors), `append_event` (the only write path, never rewrites), `latest_by_feature`, `retired`, `live`, `new_event`, `raise_weight` (S2 amendment: raising to high asks once), `check_rows_on_pass` (L3), `load_goal_tasks`.
- `src/autotester/ledger/render.py` (new) — `render_map` (directory map from module docstrings + schema summary from model docstrings), `replace_generated`/`apply_map` (marker-delimited sections), `decision_index` (computed SUPERSEDED status from `Supersedes:` fields), `render_snapshot` (≤60 lines, deterministic — the 30-day window anchors on the latest ledger date, not today, so doctor does not drift daily), `doc_header_missing`, `router_paths`.
- `src/autotester/ledger/relitigation.py` (new) — D-004 confidence-gated gate: certain only on an explicit `F-NNN` id; otherwise the judge provider reads the *latest* retired rows (descriptions + reasons) via `prompts/relitigation_v1.md`; `gate_message` renders the HUMAN_GATE with date, reason, and the three choices. No retired rows → no model call.
- `src/autotester/prompts/relitigation_v1.md` (new) — the judge prompt file (C8: prompts are files).
- `src/autotester/cli.py` — `map`, `snapshot [--print]`, `ledger add|weight|check|relitigation`.
- `src/autotester/doctor.py` — `check_generated_fresh` (L1: ARCHITECTURE generated sections + SNAPSHOT must equal regeneration), `check_ledger` (L2/L3), `check_docs_routed` (L6: every `docs/*.md` self-describes and is in the CLAUDE.md router; router names only existing docs). `scripts` added to the root allowlist.
- `pyproject.toml` — ruff per-file ignore `B008` for `cli.py` (typer's option-default idiom).
- `docs/ARCHITECTURE.md` — Purpose/Open-me-when header; concept→file rows for the ledger modules; commands; pointer to `docs/MAP.md` (cycle 2: generated sections moved out to respect the 150-line cap).
- `docs/MAP.md` (new, cycle 2) — the two generated sections (directory map, schema summary) with markers, filled by `autotester map`.
- `docs/SNAPSHOT.md` (generated, 29 lines) · `docs/FEATURES.jsonl` (F-001 design-lock normal, F-002 credential-boundary high with reason + verdict ref) · `docs/DECISIONS.md` (D-000..D-004, via /init-lab) · `docs/archive/INDEX.md` · headers on both research docs.
- `CLAUDE.md` — router table "Open | When" for every `docs/` file (L6); maker rule: ledger row on PASS for `high` tasks with prefilled reason, relitigation check before picking a unit; Lab Protocol block (L7).
- `qa/hooks/mc-sessionstart.ps1` — regenerates and **prints** `docs/SNAPSHOT.md` (UTF-8) at session start (L5). Lab hooks + `scripts/append_decision.ps1` + settings merge (L7).
- Memory: `~/.claude/projects/d--autoTesting/memory/autotesting-router.md` + one `MEMORY.md` line (pointer only).
- `tests/test_ledger.py` (new, 15 tests) — one per criterion incl. the negative paths.

## How to verify (commands + expected)

- `uv run pytest tests/test_ledger.py -q` → exit 0, 19 passed
- `uv run pytest -q` → exit 0 (69 tests)
- `uv run ruff check src tests` → "All checks passed!"
- `uv run autotester doctor` → "doctor: clean" (this now includes L1/L2/L3/L6 checks)
- **L1 rot test:** change any module docstring's first line → `uv run autotester doctor` exits 1 with `stale-generated: docs/MAP.md`; `uv run autotester map` → clean again
- **C2 budget:** `wc -l docs/ARCHITECTURE.md` → 135 (≤ 150); doctor rule `architecture-too-long` exists (`doctor.check_architecture_budget`)
- **L1 snapshot:** `uv run autotester snapshot --print | wc -l` ≤ 60
- **L3:** `uv run autotester ledger check` → exit 0
- **L4:** `uv run autotester ledger relitigation "browser session with persistent profile"` → "no gate — no retired features (rule)"; the paraphrase-gates-via-judge path is `test_paraphrased_unit_goes_to_the_judge_with_descriptions_and_gates`
- **L5/L6:** `powershell -File qa/hooks/mc-sessionstart.ps1` prints the snapshot after the status line; remove any row from the CLAUDE.md router → doctor fails `doc-unrouted`
- **L7:** `docs/DECISIONS.md` has D-000..D-004; `.claude/hooks/decisions-append-guard.ps1` wired in `.claude/settings.json` (PreToolUse Write|Edit)

## Actual outputs (from maker's own run, cycle 2)

```
$ uv run pytest -q
.....................................................................    [100%]
$ wc -l docs/ARCHITECTURE.md docs/MAP.md docs/SNAPSHOT.md
  135 docs/ARCHITECTURE.md
   73 docs/MAP.md
   29 docs/SNAPSHOT.md
$ uv run ruff check src tests
All checks passed!
$ uv run autotester doctor
doctor: clean
$ uv run autotester snapshot
snapshot: 29 lines written
$ uv run autotester ledger check
ledger: every closed high-value task has a row
$ uv run autotester ledger relitigation "browser session with persistent profile"
no gate — no retired features (rule)
```

## Sweep findings folded into this unit (sweep commit 2aadf21)

- **AT-009** (doctor.py root-allowlist edit landed in the lab-protocol commit `5f83bdb` without a manifest): acknowledged — that one-token change (`scripts` allowed at root) is now claimed by **this** manifest ("What changed" → doctor.py). The pattern is exactly what the pair exists to stop; recorded here rather than argued away.
- **Enforcement path authorization:** `qa/hooks/mc-sessionstart.ps1` (snapshot injection, L5) and the `.claude/settings.json` hooks merge are enforcement paths; both are covered by **D-000 `Changes-authorized` + `Approved-by: Umesh`** (`docs/DECISIONS.md`).
- **AT-012** (tick stamped in UTC): the tick line written at the end of this cycle uses local time; earlier UTC line left as-is (append-only).
- **AT-013** (living-ledger.md L7 backfill list off by one — D-000 is genesis, D-001 design-first): checker-owned amendment; please fold during this check. Code/docs already reflect reality.
- **AT-010** (D-005 never appended): appended this cycle via `scripts/append_decision.ps1` — see `docs/DECISIONS.md` D-005.
- **AT-017 / AT-018**: goal tasks **T-065** (FlowSpec review gate, `high`) and **T-045** (read-only DB assertions) added; T-070 now depends on T-065. **AT-016**: stale STALLED notification acked.
- **Encoding defect found while appending D-005:** `scripts/append_decision.ps1` read the UTF-8 entry as ANSI, so `·`/`—` in D-005 are mojibake in `docs/DECISIONS.md` (append-only, left as-is; D-006 `session` entry records it). Script fixed to UTF-8 in/out under D-000 `Changes-authorized`; logged in `qa/feedback-inbox.md`.
- **AT-011** (`qa/loop.md`), **AT-014** (`.goal/rubrics/` for rubric_ref tasks), **AT-015** (lab hook injects only ARCHITECTURE's H1 — its numbered-section filter does not match our headings): left in `qa/QUEUE.md`; AT-015 is an enforcement-path edit I will make under D-000 in the next unit, not silently here.

## Scope notes for the checker

- The relitigation judge is exercised with the mock provider only; a real-provider run is T-080's concern (C8 holds: no vendor SDK imported anywhere in `ledger/`).
- "Ask on PASS" is a maker-process rule (CLAUDE.md) surfaced by `ask_required` + the CLI's `ASK:` line; there is no UI yet (T-100).
- `docs/FEATURES.jsonl` rows carry `created_at` with microseconds — cosmetic, not a criterion.
- The T-011 unit's code (`browser/secrets.py` etc.) is still uncommitted by the user's commit-style preference; this unit builds on it in the working tree.

## Status: checked-PASS

Verdict: `qa/verdicts/t005-living-ledger.md` (Cycle checked: 2, PASS, 7/7 + 8/8; commit 6d697ab). Goal task T-005 closed by the checker. AT-021 (S3) carried to T-010.
