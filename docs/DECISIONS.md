# DECISIONS — d:/autoTesting (append-only history)

**Purpose:** the reasoned history of every design decision, experiment, and rejected approach in
AutoTester, so a later session cannot relitigate old ground without seeing why it was settled.
**Open me when:** you are about to change an approach, revive something, or need to know *why* the
system is shaped as it is. Never edit — append only via `scripts/append_decision.ps1`.
Schema: `D:/ai_os/templates/lab-protocol/DECISIONS.schema.md` (Lab Protocol v1.1: write-time status
∈ {ACTIVE, REJECTED}; SUPERSEDED is computed from later entries' `Supersedes:` fields).

## D-000 | 2026-09-03 | type: decision | status: ACTIVE
**What:** Adopted the Lab Protocol for this repo (append-only DECISIONS, computed-status injection,
authorized state edits) on top of the maker-checker pair installed the same day.
**Why:** Umesh's explicit requirement (goal.md, 2026-09-03): the previous product (`d:/erp`) lost
human control because schema, structure, and reasoning were never written down and drifted; this
project must stay readable to a human engineer and cheap for an agent to hold in context.
**Result:** `docs/DECISIONS.md` (this file) + `docs/archive/INDEX.md` + repo-committed hooks
(`.claude/hooks/lab-*.ps1`, `decisions-append-guard.ps1`) + `scripts/append_decision.ps1` +
`.claude/settings.json` hooks merged with the maker-checker hooks. `ARCHITECTURE.md` lives at
`docs/ARCHITECTURE.md` (plan §6 layout); the repo copy of the session-start hook falls back to it.
`qa/contracts/` + `autotester doctor` + `uv run pytest` are the validators — no separate
`contracts/verify_contracts.py` (spec'd project, not research-first data pipeline).
**Changes-authorized:** `.claude/settings.json` (hooks merge); `.claude/hooks/*` (lab + mc hooks);
`scripts/append_decision.ps1`; `qa/hooks/mc-*.ps1`; `CLAUDE.md` lab + maker-checker blocks —
enforcement wiring that lets the protocol and the pair travel with the repo.
**Approved-by:** Umesh — plan v2 (§7 Enforcement, §14 Living ledger) approved via `ExitPlanMode`
2026-09-03; maker-checker init authorized by "proceed ahead with /maker /checker" (2026-09-03).
**Links:** goal T-000, T-005; commits a5ffcec, 458304a; plan
`C:/Users/Lenovo/.claude/plans/great-when-you-really-iridescent-ocean.md`

## D-001 | 2026-09-03 | type: decision | status: ACTIVE
**What:** Design-first build: every domain shape is a Pydantic model in `src/autotester/schema/`
(`extra="forbid"`), one concept in one place, file ≤ 300 lines / function ≤ 50, clean repo root,
all model calls through `providers.base.Provider`, prompts as files. Enforced by `autotester doctor`.
**Why:** `d:/erp` reached 232 root entries, 977 source files, duplicated concepts, and a 291-line
landmine CLAUDE.md — unreadable to humans and expensive for agents. Cheap rules now, unaffordable later.
**Result:** `qa/contracts/core-invariants.md` C1–C8; doctor + ruff + pytest green at P0 (26 tests).
**Links:** goal T-000; commit a5ffcec; contract `qa/contracts/core-invariants.md`

## D-002 | 2026-09-03 | type: decision | status: ACTIVE
**What:** Stack and scope: Python; Gemini (key in hand) for vision/video + Anthropic SDK behind a
pluggable provider layer; first target Pathlynks; auth via `.env` credentials + persistent browser
profile with OTP as a human pause; file-based storage (JSON/JSONL per project, SQLite index later,
no Mongo for AutoTester's own state); Playwright headed by default; no LangGraph in v1.
**Why:** Umesh's answers 2026-09-03 (AskUserQuestion): Gemini key exists, Anthropic SDK preferred,
both wanted; Pathlynks is the real regression target; human-editable artifacts are the point.
File checkpoints give resumability with zero framework context cost; stage interface stays
LangGraph-node-shaped for a mechanical migration if headless-days autonomy is ever needed.
**Result:** plan v2 §1, §4, §6; provider seam + mock provider built at P0.
**Links:** goal T-000; plan §1 Decisions

## D-003 | 2026-09-03 | type: decision | status: ACTIVE
**What:** One credential file for the whole repo at the repo root (`d:/autoTesting/.env`), keys
namespaced per project (`PATHLYNKS_*`) and declared per project via `SecretRef[]` with domain
scope; undeclared values are masked but never resolvable. Replaces the per-project
`projects/<slug>/.env` in the first draft.
**Why:** Umesh, mid-cycle 2026-09-03: "place .env too in the root directory". Security is unchanged
(scoping comes from per-project `SecretRef.domains`; gitignore `**/.env` already covers root), and one
file is simpler to hand to a human.
**Result:** `core/paths.py::env_file` → root; contracts B1 + C5 amended by /checker (cycle 2); `.env.example` at root.
**Links:** goal T-011; verdict `qa/verdicts/t011-secret-store.md`; commit 06c614d

## D-004 | 2026-09-03 | type: decision | status: ACTIVE
**What:** Project-wide principle: **rules answer only where they are confident; everywhere else,
spend tokens on AI judgement.** A deterministic check may decide a case only when it can be certain
(exact id, explicit link); an absent keyword hit is never treated as confidence of "no match".
First application: the feature-ledger relitigation gate reads descriptions via the LLM.
**Why:** Umesh, grill 2026-09-03 Q6: "simplistic rule-based systems fail on edge cases and give a
confident wrong answer… it is better to lose the tokens instead of betting in the wrong direction."
**Result:** encoded in `qa/contracts/living-ledger.md` L4; to be cited by later contracts
(grader, coverage diff, case expander) wherever a threshold or match is decided.
**Links:** goal T-005; grill capture `.work/grill-living-ledger.md`
