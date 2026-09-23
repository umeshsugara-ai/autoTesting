# Contract — portal-persona (durable cross-run product model)

**Status:** DRAFT (authorized by D-038; the checker takes it DRAFT->ACTIVE on T-164's first PASS).
**Feature:** the durable Portal Persona — per-crawl portal-explorer knowledge promoted to a durable,
versioned cross-run artifact (`projects/<slug>/portal_persona.json`) plus a regenerated human-readable
knowledge page (`projects/<slug>/knowledge.md`), so what AutoTester learns about a product accumulates
across runs instead of being scoped to one crawl.
**Covers:** goal task T-164. **Deps:** T-163 (done). **Grounding:** target.md M9; reuses the T-020
filestore-as-durable-store pattern (D-036) and the existing screen_graph.py/screenmap.py crawl output.

## What the persona is

`schema/portal_persona.py` (Pydantic, `extra="forbid"`): a `PortalPersona` model holding the product's
durable profile — auth shape, screens, transitions, taught flows, gotchas, screenshot refs — plus a
dated `history: list[PersonaRevision]`, each revision recording when it was updated and a change
summary. Persisted at `projects/<slug>/portal_persona.json` via the filestore.

`stages/portal_persona.py`: a `run(input, ctx) -> PortalPersona` stage that builds or updates the
persona from a crawl's screen graph + the reviewed FlowSpec, then regenerates `knowledge.md` from it.

## Criteria (PP1-PP6) — each judged on re-runnable evidence

- **PP1 — Durable, one model, one store.** The persona is a single `PortalPersona` model persisted as
  `projects/<slug>/portal_persona.json` (no second store); `knowledge.md` is a regenerated VIEW of it,
  never an independent source of truth.
- **PP2 — Cross-run accumulation, never silent loss.** A second run MERGES into the existing persona:
  new screens/transitions/flows are added; a screen/flow already known is not dropped or blanked. (Falsifiable:
  build a persona, run again with partial new material, assert prior entries all survive + new ones appear.)
- **PP3 — Dated history with change detection.** Every update that changes the persona appends a
  `PersonaRevision` with a timestamp and a non-empty change summary naming what changed; a run that
  changes nothing does not fabricate a revision. (Falsifiable: two runs with a real delta -> a dated
  revision naming the delta; an identical re-run -> no new revision.)
- **PP4 — Knowledge page is a faithful regenerated view.** `knowledge.md` is regenerated from the
  persona JSON on every update and reflects the current screens/flows/gotchas/history; it is never
  hand-authored content the JSON lacks. (Falsifiable: mutate the JSON, regenerate, assert the page reflects it.)
- **PP5 — Credentials never leak into the persona or page.** Auth is described by SHAPE only (which
  fields, which domain), never a secret value; `assert_no_raw_secrets` gates any model call on persona
  content; screenshots referenced are the masked ones. (Falsifiable: a persona built from material that
  contains a secret token -> the token never appears in portal_persona.json or knowledge.md.)
- **PP6 — Quick Re-Run pointer.** The persona records enough to re-exercise a taught flow (a stable
  reference to the flow + its entry), so a "Quick Re-Run" can target a known flow without re-teaching.
  (Falsifiable: assert a taught flow in the persona carries a runnable reference the re-run can resolve.)

## Explicit no-fire list (do not raise these as findings)

- The persona is NOT a new canonical pipeline stage (D-038) — it is a durable artifact + a stage; raising
  "add it to the ARCHITECTURE pipeline diagram" is out of scope.
- No new datastore/DB — the filestore JSON is the store by design (reuses D-036's precedent).
- knowledge.md is a generated view; raising "it duplicates the JSON" is wrong — that is the intended
  human-readable projection, regenerated, not a second source of truth.

## How a unit is verified (adapter slot 1)

`uv run pytest tests/test_portal_persona.py` (bare, no CLI -q, AT-503) + `uv run ruff check src tests
scripts` + `uv run autotester doctor`, all exit 0; each PP criterion carries a capability-coverage row
with a single-hunk falsifying edit reproduced green->red-for-the-named-reason->revert->green.
