# d:/autoTesting — AutoTester

An AI system that does the automated-tester job end to end: ingest a product's videos and docs,
derive a reviewed FlowSpec, generate best/worst/edge-case evals, run them as regression in a real
visible browser, and ask for new videos when it meets a screen it does not know.

**North star:** an expert human tester and AutoTester get the same material and the same build;
AutoTester wins on bugs found, false-positive rate, and time.

## Read first, always

1. **`docs/ARCHITECTURE.md`** — the concept→file map. Read before touching any code.
2. **`src/autotester/schema/`** — every data shape in the system. Nothing else defines one.
3. **`qa/contracts/core-invariants.md`** — the rules every unit is judged against.
4. `.goal/goal.json` — the task backlog; `.goal/dashboard.html` for the view.

Plan of record: `C:/Users/Lenovo/.claude/plans/great-when-you-really-iridescent-ocean.md`.

## Design rules (enforced by `uv run autotester doctor`, not by memory)

These exist because `d:/erp` shipped without an upfront schema and became unreadable to humans and
expensive for agents to hold in context. The rules are cheap now and unaffordable later.

- File ≤ 300 lines · function ≤ 50 lines · module docstring states its one job.
- Every domain shape is a Pydantic model in `schema/`, with `extra="forbid"`.
- One concept, one place — a class or function defined in two modules is a bug.
- No `*_v2.py` / `*_new.py` — edit in place.
- Scratch, logs, and evidence go to `.work/`, never the repo root.
- All model calls go through `providers.base.Provider`; prompts are files, not inline strings.

## Credentials (hard boundary)

- Values live only in `projects/<slug>/.env` (gitignored). `SecretRef` holds the **key** and its
  domain scope — never a value.
- Prompts carry `{{SECRET:KEY}}`; substitution happens at `page.fill()` time only, scoped to the
  project's `allowed_domains`. `core.redact.assert_no_raw_secrets` is the gate before any model call.
- Screenshots mask secret inputs before capture; logs pass `Redactor.scrub`.
- `write_policy` defaults to `read_only`. Testing against a real product requires a **test account**
  and explicit per-run approval — never a live user's credentials.

## Maker-checker discipline (installed 2026-09-03)

This project runs dev work through the maker-checker pair:

- **Substantive dev work** (feature, module, schema change, multi-file edit) → route through
  `/maker`. Announce in one line; the user can say "normal" to opt out.
- **Trivial work** (typo, single command, read-only) → normal mode, no ceremony.
- Ground truth lives in `qa/contracts/` — **maker never edits it**; feedback goes verbatim into
  `qa/feedback-inbox.md`; `/checker` folds it in.
- Only `/checker` can PASS a unit. "Done" claims without a checker verdict are invalid.
- Open issues: `qa/issues.jsonl` (canonical). Adapter: `qa/adapter.json` (coding; verify =
  `uv run pytest -q`, `uv run ruff check src tests`, `uv run autotester doctor`).
- **The maker↔checker handshake is files, never memory:** maker's request = manifest at
  `Status: ready-for-check` (with `Fix cycle: N`); checker's reply = `qa/verdicts/<same-slug>.md`
  (with `Cycle checked: N`); maker's close-out = manifest flip to `checked-PASS`.
- **AUTO-CONTINUE (no human hand-crank):** on session start, if the hook line or `qa/` shows
  pending state (unchecked manifest · PASS not closed out · open issues · stale `.last-tick`), run
  `/maker continue "d:/autoTesting"` **before anything else**. The maker self-continues via
  `ScheduleWakeup` and dispatches its own checker subagents and sweeps; the only human actions are
  `/maker init` (once) and answering HUMAN_GATE decisions.
- Manual overrides (never required): `/checker sweep` · `/loop /maker continue "d:/autoTesting"`.

## Commands

```bash
uv run pytest -q                # tests
uv run ruff check src tests     # lint
uv run autotester doctor        # design rules
uv run autotester providers     # which model providers have credentials
```
