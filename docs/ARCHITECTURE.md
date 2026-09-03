# AutoTester — architecture

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
| Every project path on disk | `core/paths.py::ProjectPaths` |
| Model calls (vision / agent / judge) | `providers/base.py::Provider` + registry in `providers/__init__.py` |
| Design enforcement | `doctor.py` |
| Commands | `cli.py` |

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

1. Values live only in `projects/<slug>/.env` (gitignored). `SecretRef` holds the **key**, never the value.
2. Prompts carry `{{SECRET:KEY}}`. Substitution happens at `page.fill()` time only, scoped to the
   project's `allowed_domains`. `core/redact.assert_no_raw_secrets` is the hard gate before any call.
3. Screenshots mask secret inputs; every log and artifact passes `Redactor.scrub`.
4. `write_policy` defaults to `read_only`; writing to a target app is an explicit, per-run decision.

## Storage

Artifacts are plain files a human can open, edit, or delete:

```
projects/<slug>/  project.json · .env (ignored) · sources/ · sources.jsonl · flowspec.json
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

## Commands

```bash
uv run autotester doctor       # design rules
uv run autotester providers    # which model providers have credentials
uv run pytest                  # test suite
uv run ruff check src tests    # lint
```

## Status

**Built:** schema, core (ids/redaction/paths), provider seam + mock, doctor, CLI, tests.
**Next:** `browser/` (Playwright session + secret injection), then `stages/execute.py` and
`stages/grade.py` against Pathlynks — see the plan for phases P1–P5.
