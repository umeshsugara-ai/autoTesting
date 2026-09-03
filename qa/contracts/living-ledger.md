# Contract — living project map + feature ledger

**Covers:** goal task T-005. **Owner:** /checker.
**Source of truth for intent:** grill capture `.work/grill-living-ledger.md` (2026-09-03, 9 Qs, pre-mortem)
and plan §14 — approved by Umesh 2026-09-03. **Depends on:** `core-invariants.md` (all criteria).

## Purpose

One derived snapshot Claude reads at session start for whole-project context, plus a date-wise
feature ledger carrying the *reasoning* for every live / updated / retired event — so tokens go to
the part being worked on, and a re-proposal of something retired is caught and confirmed with the
human instead of silently rebuilt. It is the product's **overview, not a logger**.

## Criteria

### L1 — Derived, never typed (rot defence)
- `docs/MAP.md` (routed, self-describing) carries two generated sections (directory map from module
  docstrings; schema summary from the Pydantic models) delimited by markers; `autotester map` regenerates
  them. `docs/ARCHITECTURE.md` keeps a pointer to MAP.md and stays ≤ 150 lines, enforced by the doctor
  rule `architecture-too-long` (C2 cap unchanged).
- `docs/SNAPSHOT.md` is produced only by `autotester snapshot`; it has a "generated — do not edit" header.
- `autotester doctor` **fails** when `docs/MAP.md` or `docs/SNAPSHOT.md` differs from a fresh regeneration.
- **Verify:** `uv run autotester map && uv run autotester snapshot && git diff --exit-code docs/MAP.md docs/SNAPSHOT.md`; then change one module docstring → `uv run autotester doctor` exits non-zero (`stale-generated: docs/MAP.md`) until `map` is re-run; `wc -l docs/ARCHITECTURE.md` ≤ 150.

### L2 — Every change gets a row; the ask is gated by user value (fatigue defence)
- `docs/FEATURES.jsonl` rows validate against `schema/ledger.py::FeatureEvent`
  (`id`, `feature`, `event ∈ {planned, live, updated, retired}`, `date`, `unit`, `verdict_ref`,
  `reason`, `user_value ∈ {high, normal, low}`, `description`, `supersedes?`).
- The only write path is `autotester ledger add` (and the maker close-out that calls it). No hand edits.
- A `retired` row **refuses** an empty reason. A `live`/`updated` row for a `user_value: high`
  feature is written with a **prefilled** reason (goal task note + originating instruction) that the
  maker shows for confirm-or-edit; `normal`/`low` rows auto-stamp `reason: "update"` with no question.
- `user_value` is a default, not a fixture: `autotester ledger weight <feature> high` raises it later
  and triggers the reasoning ask once.
- **Verify:** `uv run pytest tests/test_ledger.py -q` covers: schema validation, refused empty retire
  reason, auto-`update` for normal, prefilled reason surfaced for high, weight raise → ask flag.

### L3 — Row on PASS
- A goal task closed on a checker PASS whose `user_value` is `high` has a matching `live` or
  `updated` row citing the verdict file. The `/checker sweep` flags a PASSed `high` unit without one.
- **Verify:** `uv run autotester ledger check` exits 0 (every closed `high` task has a row).

### L4 — Relitigation gate, confidence-gated (project principle S4)
- When the maker picks a unit, `autotester ledger relitigation "<unit title + description>"` is run.
  Deterministic match only on feature id / explicit `supersedes`; **every other case** the LLM (via
  `providers.base.Provider`, prompt file `prompts/relitigation_v1.md`) reads the *latest* row per
  retired/superseded feature (descriptions + reasons) and answers `same_behaviour: bool` with a
  one-line justification. A keyword miss is **not** treated as "no match".
- A hit is a `HUMAN_GATE` quoting feature, date, and reason, with choices rebuild-as-is / build
  differently (reason required) / cancel; the answer becomes a new ledger row + DECISIONS entry.
- **Verify:** test with the mock provider: a retired row "OTP via email link" and a new unit
  "2FA handling for login" → gate fires with the retired reason quoted; an unrelated unit → no gate.

### L5 — Lean snapshot, injected (ignored-it defence)
- `docs/SNAPSHOT.md` ≤ 60 lines: product + north star · live features (`high` with reason, `normal`
  one line, overflow rolled up with a count) · updated/retired in last 30 days with reason · next 5
  open goal tasks · last 5 decisions (computed status). No schema summary, no directory map.
- `qa/hooks/mc-sessionstart.ps1` regenerates and **prints** the snapshot and the DECISIONS index
  (all headers, computed status) — injected, not linked.
- **Verify:** `powershell -File qa/hooks/mc-sessionstart.ps1` output contains the snapshot; `wc -l docs/SNAPSHOT.md` ≤ 60.

### L6 — Every doc self-describes; CLAUDE.md is the router
- Each file in `docs/` opens with a 2-line header: **Purpose** and **Open me when**.
- `CLAUDE.md` carries a table "open X when Y" listing every `docs/` file; `autotester doctor` fails
  when a `docs/` file is missing from the router or a routed file does not exist.
- `MEMORY.md` (Claude's memory dir) gets one pointer line to the router, nothing more.
- **Verify:** `uv run autotester doctor` exits 0; remove a doc from the router → doctor fails.

### L7 — History is append-only with authorization (lab protocol)
- `docs/DECISIONS.md` exists (via `/init-lab`), append-only through `scripts/append_decision.ps1`
  (PreToolUse deny on direct Edit/Write); supersession by `Supersedes: D-NNN -- <why>` in the new entry.
- Backfilled: D-000 genesis (Lab Protocol adoption) · D-001 design-first rules · D-002 the
  2026-09-03 stack/target/auth decisions · D-003 `.env` at repo root · D-004 principle S4
  (confidence-gated rules → AI).
- **Verify:** `git log -p docs/DECISIONS.md` shows additions only; a direct Edit is denied by the hook.

## Out of scope
The UI view of the ledger (T-100); auto-inferring `user_value` from run data (suggestion source
only, later); Google-Sheet sync.

## No-fire list
- Snapshot prose wording; choice of markers; line counts under the caps.
- Absence of retired rows today (nothing has been retired yet).
- The relitigation LLM's judgement quality beyond the mock-provider test.

## Amendment log (append-only; git history is the version)

- 2026-09-03 · routine · L7: backfill list corrected to D-000 genesis/adoption, D-001 design-first, D-002 stack, D-003 root `.env`, D-004 S4 · why: AT-013 (sweep 2aadf21) — the list was off by one against `docs/DECISIONS.md`; tightening only, applied at the T-005 cycle-1 check.
- 2026-09-03 · routine · L1: generated sections live in `docs/MAP.md` (routed sibling), not in `docs/ARCHITECTURE.md`; doctor fails when MAP.md or SNAPSHOT.md differ from regeneration; ARCHITECTURE.md ≤ 150 is doctor-enforced (`architecture-too-long`) · why: AT-019 — the generated sections pushed ARCHITECTURE.md to 200 lines against the C2 cap; relocation keeps every derived-not-typed guarantee and adds enforcement of the cap; the cap itself is untouched. Pre-declared at the T-005 cycle-1 check, folded at cycle 2.
