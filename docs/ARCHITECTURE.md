# AutoTester — architecture

**Purpose:** the current state of the system — pipeline, concept→file map, data model, execution and security model, generated directory map and schema summary.
**Open me when:** you need to find where a concept lives or how the stages fit together. Prose changes only under a `docs/DECISIONS.md` entry; the generated sections come from `autotester map`.

Read this file, then `src/autotester/schema/`. That is the whole system.

## What it does

Onboard a web product once (details + demo videos + docs + text). AutoTester learns its flows
screen-by-screen, generates test cases covering **best / worst / edge**, and re-runs them in a
**real visible browser** after every dev cycle — so a new feature cannot silently break an old one.
When it meets a screen it does not know, it asks the human for a video instead of guessing.

North star: an expert human tester and AutoTester get the same material and the same build;
AutoTester wins on bugs found, false positives, and time (`schema/bench.py` computes that scorecard).

## Pipeline

```
INGEST ──► EXPAND ──► EXECUTE ──► GRADE ──► REPORT + COVERAGE ──► BENCH
sources    FlowSpec    Case         RawResult   Verdict    gaps/requests   scorecard
  │          │            │            │           │            │
  │        Case[]    RawResult      Verdict     report      VideoRequest
  └──────────────────────── new material ◄──────────────────────┘
```

Each stage is a pure typed function `run(input, ctx) -> output`, one file in `stages/`, reading only
the previous stage's artifact. A stage never reaches into another stage's internals.

## Concept → file (one concept, one place)

| Concept | Lives in |
|---|---|
| All data shapes | `schema/` (one model per file) |
| Closed vocabularies (actions, case classes, results, policies) | `schema/enums.py` |
| The edge-case taxonomy | `schema/enums.py::CaseClass` + `KIND_BY_CLASS` |
| Artifact envelope (schema_version, created_at, provenance) | `schema/base.py::Artifact` |
| Id minting, content hashing, file sha256 | `core/ids.py` |
| Secret redaction + `{{SECRET:KEY}}` placeholders | `core/redact.py` |
| The credential boundary (load `.env`, resolve per host, mask) | `browser/secrets.py::SecretStore` |
| The visible browser (persistent profile, bounded navigation, masked capture, HITL) | `browser/session.py::BrowserSession` |
| Persistence: atomic JSON/JSONL primitives + the per-project artifact facade | `store/filestore.py`, `store/project_store.py::ProjectStore` |
| Pathlynks: onboarding (login + knowledge.md) and the first real best/worst/edge run | `scripts/onboard_pathlynks.py`, `scripts/run_pathlynks_first_cases.py` |
| Model calls (vision / agent / judge) | `providers/base.py::Provider` + registry in `providers/__init__.py` |
| Design enforcement (incl. generated-doc freshness, ledger validity, router) | `doctor.py` |
| Commands | `cli.py` |
| Feature ledger rows (`docs/FEATURES.jsonl`) — the only write path | `ledger/store.py` |
| Derived docs: generated sections of this file, `docs/SNAPSHOT.md`, decision index | `ledger/render.py` |
| Relitigation gate (retired feature coming back?) — D-004 confidence-gated | `ledger/relitigation.py` + `prompts/relitigation_v1.md` |
| Every path on disk: per-project (`ProjectPaths`) and repo-level docs (`RepoDocs`) | `core/paths.py` |
| Running a case's steps in a browser, no judgement (that's grade.py) | `stages/execute.py::run_case` |
| Judging a case's evidence against its rubric — stateless, evidence-only | `stages/grade.py::grade` |
| Read-only backend assertions (Mongo) + manual one-time login (no secret, human logs in, session persists) + tester report export (Excel + self-contained HTML with embedded screenshots) | `browser/db.py::ReadOnlyCollection`, `stages/manual_login.py::manual_login`, `stages/report_export.py` |
| Agent fallback: fix one broken step, persist the corrected case | `stages/agent_loop.py::run_with_fallback` |
| Multi-vendor fallback (Anthropic→Gemini→Ollama→ChatGPT; no single-provider dependency) — default agent/judge (standalone `AnthropicProvider` also registered) | `providers/langchain_fallback.py::LangChainFallbackProvider` |
| Gemini provider (vision role — video understanding) | `providers/gemini.py::GeminiProvider` |
| Video → FlowSpec (screens/flows, provenance to the second) | `stages/ingest.py::ingest_video` |
| FlowSpec review gate (draft → approved; blocks case generation until reviewed) | `stages/review.py::require_reviewed` |
| FlowSpec → Case[] covering every applicable taxonomy class | `stages/expand.py::expand` |
| Self-extension: unseen route → CoverageGap → deduped VideoRequest | `stages/coverage.py::diff_coverage` |
| Web UI: onboarding, masked .env editor, run/report views, shared visual theme (thin, no second store) | `ui/app.py` + `ui/env_editor.py` + `ui/theme.py::page` |
| Docker: containerized app + virtual display + noVNC live-watch view (local dev only) | `Dockerfile`, `docker/entrypoint.sh`, `docker-compose.yml` |
| Regression proof (break a fixture, confirm exactly that case FAILs) + bench (north star scorecard: seeded corpus, real trial vs human-oracle baseline) | `scripts/regression_proof.py`, `stages/bench.py::scorecard` |

Duplicating any of these is a bug — `autotester doctor` fails on a class or function defined twice.

## Data model (the core five)

- **`Project`** — slug, base URL, `allowed_domains`, `write_policy`, declared `SecretRef[]` (keys and
  their scope, never values), which provider serves each role.
- **`FlowSpec`** — the system's understanding: `Screen[]` (with `InputField[]` and their constraints)
  and `Flow[]` (ordered `Step[]`). Every `Step` carries `expected: ExpectedState` and a `SourceRef`
  back to the video second it was learned from. Conflicts between sources are **flagged, not merged**.
  A `Review` gate means a flowspec drives nothing until a human approves it.
- **`Case`** — one falsifiable claim, tagged with a `CaseClass` from the taxonomy. Content-addressed,
  so regenerating a flowspec does not duplicate the suite.
- **`RawResult`** — what the executor observed (outcome, evidence, iterations). **No judgement.**
- **`Verdict`** — what an independent grader concluded from evidence against a `Rubric`. Only the
  grader writes this; a PASS requires cited evidence.

`Script` records a durable Playwright script for a case; `CoverageGap`/`VideoRequest` drive the
self-extension loop; `BenchCorpus`/`BenchTrial` run the human-vs-AI comparison.

## Execution model

Per case: **script-first** (run the durable Playwright script if one exists) → **agent fallback**
(provider `act` loop: write → run → read failure → edit, capped iterations) → on success the agent
emits a script. So a stable suite costs ~zero tokens to re-run; the agent only pays for new or
broken cases.

Browser is **headed by default** (`Project.headed`), driven against a persistent profile in
`profiles/<slug>/` so login happens once. OTP/2FA puts the run in `blocked_hitl` and asks the human.

## Security (non-negotiable)

1. Values live only in the **repo-root `.env`** (gitignored; one file, keys namespaced per project and
   declared in each project's `SecretRef[]`). `SecretRef` holds the **key** and its domain scope, never the value.
2. Prompts carry `{{SECRET:KEY}}`. Substitution happens at `page.fill()` time only, scoped to the
   `SecretRef`'s `domains`; parser-ambiguous destinations fail closed. `core/redact.assert_no_raw_secrets`
   is the hard gate before any call; undeclared `.env` values are masked too, never usable.
3. Screenshots mask secret inputs; every log and artifact passes `Redactor.scrub`.
4. `write_policy` defaults to `read_only`; writing to a target app is an explicit, per-run decision.

## Storage

Artifacts are plain files a human can open, edit, or delete:

```
.env              all credentials, repo root (ignored) — see `.env.example`
projects/<slug>/  project.json · sources/ · sources.jsonl · flowspec.json
                  cases.jsonl · rubrics/ · scripts/ · runs/<run_id>/ · requests.jsonl · knowledge.md
profiles/<slug>/  persistent browser profile (ignored)
.work/            scratch, logs, evidence in progress (ignored)
```

The UI is a viewer/editor over these files, not a second source of truth.

## Design rules (enforced by `autotester doctor`)

- File ≤ 300 lines · function ≤ 50 lines · module docstring states its one job.
- No `*_v2.py` / `*_new.py` — edit in place.
- No new top-level entries outside the layout; scratch goes to `.work/`.
- No concept defined twice.
- `pydantic` models use `extra="forbid"`, so a typo'd key fails loudly instead of vanishing.

These exist because the previous project lost human control when files, duplicated concepts, and
root-level scratch grew unchecked. The rules are cheap now and unaffordable later.

## Directory map and schema summary

Generated from module and model docstrings into `docs/MAP.md` by `autotester map`; not kept here so this file stays inside its 150-line budget.

## Commands

```bash
uv run autotester doctor       # design rules
uv run autotester providers    # which model providers have credentials
uv run pytest                  # test suite
uv run ruff check src tests    # lint
uv run autotester map          # regenerate docs/MAP.md
uv run autotester snapshot     # regenerate docs/SNAPSHOT.md
uv run autotester ledger add … # append a feature event (see docs/FEATURES.jsonl)
```

## Status

**Built:** schema, core, provider seam (mock/anthropic/gemini/langchain-fallback), doctor, CLI (incl. `flowspec status/approve/request-edit`), `browser/` (secrets, session, db), the living map (`ledger/`, `docs/MAP.md`, `docs/SNAPSHOT.md`, `docs/FEATURES.jsonl`), `store/` (filestore + ProjectStore), `projects/pathlynks/` (onboarded, 3 real cases run+graded), `stages/` execute + grade + agent_loop + ingest + review + expand + coverage + bench, `ui/`, a real regression proof and a real bench trial (`scripts/regression_proof.py`, `scripts/bench_trial.py`) — the north star's scorecard is now real, computed, and cited, not just designed.
**Next:** the P0–P5 goal backlog is closed. Open for later: a real Pathlynks demo video for
`stages/ingest.py`'s golden test; a live, timed human trial (`bench.py` uses an oracle baseline).
