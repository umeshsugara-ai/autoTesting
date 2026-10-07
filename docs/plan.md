# Plan — AutoTester, remaining units

**Purpose:** the 26 remaining work units (refreshed 2026-10-07 from `.goal/goal.json`: 59 of 90 tasks done, 31 pending) in dependency order — files touched, how each is tested, criticality, persona walk — and the tasks held on a human gate.
**Open me when:** picking the next unit or wave, or asking what is deliberately not being built right now.

<!-- PLAN phase step 4, BACKFILL. Covers only what is NOT yet shipped; M0–M6 units are already
     checker-PASSed and live in docs/FEATURES.jsonl. Rows become qa/QUEUE.md TODO rows.
     2026-10-07 refresh (AT-744..756 drift): the 2026-09-27 list said "26 units"; nine of them have
     since closed (T-195, T-185, AT-335, T-186, T-189, T-191, T-192, T-150, T-171) and group 10 + the
     D-071 tasks were added. The count happens to be 26 again, but it is a different 26. -->

**Spec:** docs/spec.md (backfill, 2026-09-27) · **Status:** draft — awaiting approval

**Scope decisions (Umesh, 2026-09-27):** build order = everything, max parallel, bounded only by
measured RAM. Track C is built through C3 only; T-154 (adversarial pass) and T-155 (its report)
are **held for a separate approval** — no probe traffic in this push.

**What D-070 (Umesh, 2026-10-07) changed in this plan:**
- **T-125 and T-165 are unblocked.** The native-egress sandbox precondition is dropped: AutoTester
  runs a local visible browser and the full suite directly on whatever machine it is installed on,
  against any product given by URL plus supplied credentials (not Pathlynks-specific). The gate files
  carry `Answered: 2026-10-07`. T-125 cycle 4 and AT-113 cycle 4 (T-165) are the next runs. T-165 is
  **not done**: AT-113 cycle 3 FAILed/STALLED and cycle 4 is pending.
- **The FlowSpec review gate no longer blocks.** Video flows are reconciled by the system (each video's
  own knowledge graph is re-mapped onto the crawl's product KG; every flow kept, differences
  highlighted for developers). The DRAFT status stays as a label only and never blocks case
  generation from reconciled flows. This lands inside T-166; contract text comes through the
  checker's inbox fold-in, not this file.
- **Group 10 "Team loop" (T-197..T-201) is the top priority**, ahead of groups 5-9. Its scope widens
  to an in-product developer portal (T-198, grill in progress).
- **The tracker loop (T-199) is a parked must-have:** an in-product tracker with auto-validation and a
  Test button anyone can press. It is parked, not dropped, and not allowed to fall off the plan.
- **Push on checker PASS** (D-007 restated): everything built and validated is committed and pushed.

## Units (in dependency order; independent rows run in the same wave)

Group 10 first (top priority). Every group-10 unit goes through the maker PLAN gate first
(`docs/intent.md` → `/grill` → spec → plan → `qa/gates/plan-approved.md`); slugs here are proposed.

| # | unit slug | task | requirements | files it touches | how it is tested | criticality | persona walk | depends on |
|---|---|---|---|---|---|---|---|---|
| 1 | `t197-video-ingest-pointers` | T-197 | group 10 (TL-1) | `stages/ingest.py`, `cli_video.py` (`ingest run --pointers <file>`) | oracle `.work/pathlynks-dev-videos-oracle-2026-10-07.md` over the three Navnit sources; flow summary + 4-5 point confirm-list | high | required (dev) | — |
| 2 | `t198-developer-video-intake` | T-198 | group 10 (TL-2) | `sources/drive.py`, `cli_video.py`, `ui/routes_sources.py`; developer-portal scope per the live grill | safe zip expansion, one source per video; `ingest fetch-drive <fileId>` (gws writes only under CWD, register does not copy) | high | required (dev) | — |
| 3 | `t200-scheduled-autotest` | T-200 | group 10 (TL-4) | `schema/project.py` (frequency field), trigger over `stages/parallel_run.py` | per-project frequency honoured; must respect `RunApproval` (D-018) | high | skip (scheduler) | — |
| 4 | `t199-bug-loop-tracker` | T-199 | group 10 (TL-3) | tracker module + per-project column mapping | stable bug key dedupes; re-test updates, pass closes; mapping proposed then user-confirmed; first live write shown and confirmed (HUMAN_GATE) | high | required (tester) | 1 |
| 5 | `t201-team-test-button` | T-201 | group 10 (TL-5) | `ui/routes_runs.py::trigger_run` | report goes to whoever clicked; prerequisite AT-570 (trigger_run checks no `RunApproval` today) closed first | high | required (dev, tester) | 3 |
| 6 | `t125-catalog` | T-125 | R8 | catalog module + schema | cycle 4 under D-051; pytest; blocked entries name their one unblocking action; CT6 amended to tier ordering + reporting (D-071) | low | skip (backend) | — |
| 7 | `t165-crawl-completion-c4` | T-165 | R3, R6 | `stages/explore.py` + crawl schema (`at113-crawl-completion`) | cycle 4: frontier exhaustion proven on a live crawl; every bound names what it left unreached | critical | skip (crawl engine) | — |
| 8 | `t151-track-c1-discovery` | T-151 | R30 | Track C discovery module | one narrow extra cycle (D-071: one scan-path deadline test, repair checker B only); every Signal cites a real `file:line`; no model chooses which checks run | high | skip (read-only discovery) | — |
| 9 | `t196-l10-citation-subject` | T-196 | governance | doctor rule L10 | a citing line's subject must match the cited entry's `What:`; still BUILDING | critical | skip (governance) | — |
| 10 | `at518-grandchild-pid-flake` | AT-518 | infra | probe process teardown | probe kill proven, not argued | medium | skip (infra) | — |
| 11 | `t190-persona-ux-advisory` | T-190 | R28 | `schema/user_persona.py`, grade/report surfaces | pytest: a UX finding can never change a PASS/FAIL; severity scored | high | required (lead, tester) | mini-grill first |
| 12 | `t202-any-model-provider` | T-202 | D-071 | LiteLLM-backed `Provider` behind `providers.base.Provider` | Gemini / Claude / OpenAI / Ollama / OpenAI-compatible chosen by config; `litellm` authorized in this unit only | high | skip (provider) | — |
| 13 | `t204-team-login` | T-204 | D-071 (go-live blocker) | hosted UI auth | every page and API route requires an authenticated team member; mechanism is a HUMAN_GATE | high | required (dev) | — |
| 14 | `t174-cli-mcp` | T-174 | R25 | CLI modules + new MCP entry point | documented exit codes asserted; `--dry-run` sends nothing; MCP tools answer; `mcp` SDK authorized (D-071) | high | skip (CLI/MCP) | 6 |
| 15 | `t178-failure-bundle` | T-178 | R24 | `schema/` bundle model, report surfaces | bundle is atomic and replayable; pruning happens before LLM spend | high | required (dev) | 6 |
| 16 | `t179-deep-agents-lead` | T-179 | R26 | new `agents/` package wrapping existing stages as tools | guards proven to live in the tools, not the model; skills loaded via `skills=` | high | skip (agent layer) | — |
| 17 | `t176-script-replay` | T-176 | R23 | `Script` / `case.script_ref`, locator layer | a replayed script reproduces the run; semantic locators preferred over CSS | high | skip (engine) | 7 |
| 18 | `t166-eval-compiler-kg` | T-166 | R7 | `stages/expand.py`, new KG artifact; video KG reconciled onto the product KG (D-070) | every generated eval traces to its source; component PASS cannot hide workflow failure; every flow kept, differences highlighted | high | skip (engine) | 6, 7 |
| 19 | `t180-subagents` | T-180 | R26 | `agents/` | the grader subagent holds no action tools (C7); judge vendor named, warned when it matches | high | skip (agent layer) | 16 |
| 20 | `t152-track-c2-registry` | T-152 | R30 | check registry reusing T-125's Catalog | kind→checks is a literal table a checker can re-derive | low | skip | 6, 8 |
| 21 | `t177-browser-use-fallback` | T-177 | R23 | actuator + revived `agent_loop.run_with_fallback` | an unknown screen is driven with typed outputs; AT-253 dead code is alive | high | skip (actuator) | 17 |
| 22 | `t167-langgraph-regression` | T-167 | R21 | `stages/orchestrate.py` → LangGraph 1.x | a release trigger runs the approved suite; consent via `interrupt()`; resumes after a crash | critical | required (release-manager) | 18 |
| 23 | `t181-agent-gain-measured` | T-181 | R26 | `agents/` + bench | measured gain vs the plain pipeline on a fixture; per-run token/cost budget enforced | high | skip (measurement) | 19 |
| 24 | `t153-track-c3-behavioural` | T-153 | R30 | behavioural checks over a captured run | the capturer never grades (C7); every capture scrubbed before a judge sees it | high | skip | 20 |
| 25 | `t168-damage-control-report` | T-168 | R22 | report layer | blocked/unvisited never renders as pass; one operator-readable report | high | required (lead) | 7, 22 |
| 26 | `t203-hosted-website` | T-203 | D-071 | Docker image, service, HTTPS, persistent project store, `AUTOTESTER_ALLOWED_ORIGINS` | UI runs on a Linux/Ubuntu server for the Vidysea dev + product teams; server/host choice and DNS are a HUMAN_GATE before first deploy | critical | required (dev) | 13 |

Closed since the 2026-09-27 list (no longer in this plan): T-195, T-185, AT-335, T-186, T-189,
T-191, T-192, T-150, T-171 (all checker-PASS or fixed; see `docs/FEATURES.jsonl`).

## Held / blocked (not in this plan's waves)

| task | why |
|---|---|
| T-154, T-155 | Umesh 2026-09-27: build C1–C3, hold the adversarial pass for a separate approval; firing it needs a per-run approval naming target and consent scope |
| T-122, T-145 | needs TEST-account **ERP** credentials. Corrected 2026-09-27: a gitignored **repo-root** `.env` does exist and holds `PATHLYNKS_USER_*` / `PATHLYNKS_COUNSELLOR_*` key names, so Pathlynks-targeted live work is credential-capable — but `ERP_EMAIL`/`ERP_PASSWORD` are absent from every store and no `projects/*/.env` exists, which is what T-122's gate (D-048) names as its unblock condition. T-145 additionally needs a fresh D-018 RunApproval per run |
| T-136 | `ERP_Issues_Trainers.xlsx` truth sheet is not on disk (AT-752, 2026-10-07: restore it or amend the criterion) |
| T-169 | depends on all three above |

No longer held (D-070, 2026-10-07): T-125 and T-165 (runtime egress gate answered), and the FlowSpec
review gate (status label only). Still owed a human answer: the T-204 login mechanism, the T-203
host and DNS, and the first live write of T-199.

## Persona walk rule

Required when a unit adds or changes a screen, a navigation path or a user-facing flow, or touches
onboarding/sign-in/payment. High criticality alone does not trigger one — the unit must also touch
a UI surface. Audience is `internal-tool`, so a required walk covers 1–2 user types, not all five.

## Release slices

- **S0** — units 1–5: group 10 "Team loop", top priority (video ingest with pointers, developer
  intake, scheduled auto-test, the parked-must-have tracker loop, the team Test button). Unit 4 waits
  on unit 1; unit 5 on unit 3 and on AT-570.
- **S1** — units 6–10: the unblocked spine (T-125 cycle 4, AT-113 cycle 4 for T-165), T-151's narrow
  extra cycle, T-196, AT-518. These run beside S0, not after it.
- **S2** — units 11–16: UX advisory, any-model provider, team login, the CLI/MCP surface, the failure
  bundle, the agent-layer skeleton.
- **S3** — units 17–21: script replay, the eval compiler + KG (with video-KG reconciliation),
  subagents, Track C2, the browser-use fallback.
- **S4** — units 22–26: LangGraph regression, the measured agent gain, Track C3, the unified
  damage-control report, and the hosted website go-live.

## Risks

1. **RAM is the binding parallelism ceiling** (3.9 GB free of 23.7 measured 2026-09-27) — waves get
   trimmed to what fits, so "max parallel" is bounded by the machine, not by the plan. Noticed in
   each tick's `concurrent peak=` line.
2. **T-165 is still the spine, and it is not done** — units 17, 18 and (through them) 22 and 25 sit
   behind it, and AT-113 has already FAILed three cycles. A stall there stalls S3 and S4. Noticed as a
   STALLED stamp with a `qa/debug/` report; AT-745 records that cycle 3 has no diagnosis file.
3. **The buildable queue can spin without closing a unit** (AT-755: three sweeps ended EXHAUSTED with
   the same top three). Group 10 as top priority is the answer; if no S0 unit closes in two sweeps,
   that is a HUMAN_GATE, not another tick.
4. **The agent layer may not earn its place** — T-181 measures it against the plain pipeline, and a
   negative result means it is removed, not patched. Noticed in T-181's own bench numbers.
5. **The tracker loop (T-199) writes to a team sheet** — outward-facing; first live write is confirmed
   by a human. Parked must-have means it is not dropped, not that it ships unreviewed.

## T-190 concrete PLAN proposal — 2026-10-06

Status: proposed, not implementation-approved or shipped. This supplements unit10/R28;
it does not replace the canonical goal dependencies or turn an advisory finding into a
functional verdict. Product direction is already answered A in
`qa/gates/meeting-user-persona-ux-judging.md`; do not ask that question again.
The implementation/count preview and review receipts live in the existing
`qa/manifests/t190-plan-preparation.md`.

The contract's five required plan choices are:

1. Use the project's configured functional judge through the existing Provider registry,
   with a separate UX prompt/output schema. Preserve vendor/model/fallback order; the UI's
   currently hardcoded provider is not evidence of correct configuration resolution.
2. Proposed opt-in default:20 physical call attempts per run, serial across eligible cases,
   failed attempts and retries spent. This is not a money/token ceiling. Enforce the shared
   budget below retry/redirect/fallback dispatch; unsupported transport/output-limit
   capabilities refuse before a call with a typed reason. Record exhausted remaining cases
   as advisory skipped_budget; functional results remain unchanged. The numeric limit,
   payload/output limits and complete installed-adapter wiring still need plan approval.
3. Persist one typed `projects/<slug>/runs/<run_id>/ux_report.json`, separately from result
   and verdict files. Include per-case findings, exact evidence path/step, severity, effective
   conditions and safe error/skip status. Absent, malformed and incomplete are distinct;
   exports must never turn a failed UX load into a completed empty report.
4. Store typed personas in `projects/<slug>/user_personas.jsonl`; attach optional refs on
   both Project and Case, case override first. Validate project-local ids, guard complete
   snapshot values before persistence, and preserve refs during fixed-step construction.
5. `ux_enabled=False` by default. Explicit opt-in snapshots run inputs, then performs one
   read-only UX pass after functional results/verdicts persist, in stable case order. No
   rerun of product actions; advisory failure must not abort functional reporting.

Condition claims are evidence-local:measure each successful screenshot's capture interval,
not merely equal start/end samples for the case. Unknown/unsupported locale or device
conditions cannot support persona findings. Keep Verdict/Judgment and functional rubric
construction untouched; require byte-identical functional verdicts with and without UX.

Exact creation approval was requested once for the six proposed schema/stage/store/prompt/test
paths listed in the manifest. It remains pending; no file is created by this proposal.
The remaining implementation gate is a complete independently approved candidate patch/count
proof plus installed-provider budget fidelity. These engineering obligations, full-suite,
falsification, export/browser checks and final independent acceptance remain mandatory.
No paid run, live write, contract change, architecture change or product PASS is authorized here.
