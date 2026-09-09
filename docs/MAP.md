# AutoTester — map (generated sections; do not edit between markers)

**Purpose:** the directory map (every module's one job, from its docstring) and the schema summary (every model, from its docstring), derived from code by `autotester map`.
**Open me when:** you need to find which module owns a job or which model holds a shape. `autotester doctor` fails when this file is stale.

## Directory map

<!-- generated:map -->
| Module | One job |
|---|---|
| `browser/db.py` | Read-only backend assertions against MongoDB. Contract: qa/contracts/db-assert.md. |
| `browser/launch.py` | Playwright launch options for one project's persistent browser context. |
| `browser/observe.py` | Passive observation: enumerate a page's controls, capture console/network |
| `browser/secrets.py` | The credential boundary. Secret values live here and nowhere else. |
| `browser/session.py` | One real, visible browser session per project. Contract: browser-and-secrets.md B5-B9. |
| `cli.py` | Command line. Every action the UI offers is available here first. |
| `cli_crawl.py` | Crawl commands — `autotester explore` and `autotester report crawl`. |
| `cli_issues.py` | `autotester issues` — turn an analysis into the sheet a human tester reads. |
| `cli_video.py` | `autotester ingest` — register a recording and learn a FlowSpec from it. |
| `core/consent.py` | The consent gate (D-018): nothing outward-facing starts without a human's |
| `core/env.py` | Load the repo-root `.env` — one definition, used by every entry point. |
| `core/excel.py` | Workbook presentation helpers shared by every Excel exporter. |
| `core/ids.py` | Identifier generation. The ONLY place ids are minted. |
| `core/paths.py` | Filesystem layout. The ONLY place project paths are constructed. |
| `core/redact.py` | Secret redaction. Every log line and stored artifact passes through here. |
| `core/urls.py` | URL templating: the identity input a crawled screen shares with the |
| `doctor.py` | Design enforcement. Runs the rules that keep this repo readable. |
| `ledger/relitigation.py` | The cyclic-rebuild gate: is this new unit a retired feature coming back? |
| `ledger/render.py` | Derive the living docs from code and the ledger. Nothing here is hand-typed. |
| `ledger/store.py` | Read and append `docs/FEATURES.jsonl`. The only write path to the ledger. |
| `media/chunks.py` | Split a recording into overlapping chunks a vision model can actually read. |
| `media/frames.py` | Pull a single still out of a recording, at a second the model named. |
| `media/probe.py` | Ask ffmpeg what a recording actually is, and whether ffmpeg is here at all. |
| `media/transcribe.py` | Get a recording's narration — reusing a sidecar first, transcribing last. |
| `providers/anthropic.py` | Anthropic provider: the `agent` and `judge` roles via the Messages API. |
| `providers/base.py` | The provider seam. Every model call in the system goes through this interface. |
| `providers/gemini.py` | Gemini provider: the `vision` role (video understanding), plus `agent`/`judge` |
| `providers/gemini_files.py` | Upload a video to the Files API and wait until the service can actually read it. |
| `providers/gemini_schema.py` | Turn a Pydantic model into a schema Gemini's `response_schema` will accept. |
| `providers/langchain_fallback.py` | LangChain-backed provider with automatic fallback across configured vendors. |
| `providers/mock.py` | Deterministic provider for tests and dry runs. Never calls a network. |
| `schema/analysis.py` | The adjudicated result of running an ensemble over one video's chunks. |
| `schema/approval.py` | Consent as an artifact, not a habit (D-018). |
| `schema/base.py` | Base model every artifact inherits. Defines the shared envelope. |
| `schema/bench.py` | The north star, made measurable: human expert tester vs AutoTester. |
| `schema/case.py` | A test case — one falsifiable claim about the product, plus how to check it. |
| `schema/coverage.py` | Coverage gaps and the video requests that close them. |
| `schema/crawl.py` | Crawl-safety and crawl-envelope primitives (Track B). |
| `schema/enums.py` | Every closed vocabulary in the system. Nothing else defines these strings. |
| `schema/flowspec.py` | The FlowSpec — the system's understanding of the product under test. |
| `schema/issue.py` | A video-derived issue — its own artifact, deliberately NOT a `CaseClass`. |
| `schema/ledger.py` | The feature ledger row and the relitigation verdict. Contract: qa/contracts/living-ledger.md. |
| `schema/media.py` | Host-side media preparation artifacts: transcripts and chunk manifests. |
| `schema/observation.py` | A vision model's raw reading of one video — INGEST's input material. |
| `schema/project.py` | Project configuration and the secret contract. One directory per project. |
| `schema/run.py` | What EXECUTE observed. Deliberately contains no judgement — see verdict.py. |
| `schema/screen_graph.py` | What one page-visit observed: its interactive elements and identity inputs. |
| `schema/screenmap.py` | The product map — every screen the system has learned across all a |
| `schema/verdict.py` | Grading. An independent, stateless judge reads evidence against a rubric. |
| `stages/adjudicate.py` | ADJUDICATE: merge every model's chunked observations into one reading. |
| `stages/agent_loop.py` | Agent fallback: when a case's steps break, ask the agent for a fix and retry. |
| `stages/analyze_video.py` | ANALYZE: run the ensemble over a prepared recording, then adjudicate. |
| `stages/bench.py` | BENCH: the north star made measurable. Contract: qa/contracts/bench.md K1-K5. |
| `stages/coverage.py` | COVERAGE: diff what a run actually saw against what the FlowSpec knows. |
| `stages/crawl_report.py` | The crawl, as something a human can read: an Excel workbook and the |
| `stages/execute.py` | EXECUTE: run one case's steps in a real browser, producing a RawResult. |
| `stages/expand.py` | EXPAND: FlowSpec -> Case[], covering every applicable CaseClass per flow. |
| `stages/explore.py` | EXPLORE: a bounded, safety-gated BFS crawl of a (usually logged-in) app. |
| `stages/explore_merge.py` | Fold a crawl's screen graph into the reviewed FlowSpec (Track B5). |
| `stages/explore_node.py` | One node's worth of exploring: try each safe candidate action, record what |
| `stages/explore_safety.py` | The explorer's inner safety guard (Track B4, D-016). |
| `stages/grade.py` | GRADE: an independent, stateless judge reads a Rubric + a RawResult's evidence. |
| `stages/ingest.py` | INGEST: turn a video Source into a FlowSpec, provenance-tracked to the second. |
| `stages/issues.py` | ISSUES: turn an adjudicated analysis into rows a human tester can read. |
| `stages/manual_login.py` | Manual one-time login. Contract: qa/contracts/manual-login.md ML1-ML5. |
| `stages/media_prep.py` | MEDIA PREP: make a recording readable — probe it, cut it, transcribe it. |
| `stages/report_export.py` | Tester-style run reports: an Excel summary and a screen-by-screen HTML |
| `stages/review.py` | FlowSpec review gate: nothing generates cases from an unreviewed understanding |
| `stages/run_case_pipeline.py` | RUN_CASE_PIPELINE: the one function that runs a case and grades it. |
| `stages/score.py` | SCORE: compare AutoTester's issues against a human tester's own sheet. |
| `stages/screen_identity.py` | Screen identity: turn one `PageObservation` into a `ScreenNode`. |
| `stages/similarity_score.py` | How two bug reports are compared for `stages/score.py`'s T-136 scorer. |
| `store/crawl_store.py` | Crawl artifact persistence — split from `project_store.py` at the |
| `store/filestore.py` | The one place any artifact is read from or written to disk. Contract: core-invariants.md C6. |
| `store/project_store.py` | Typed convenience over `filestore` for one project's directory. |
| `ui/app.py` | Thin FastAPI viewer/editor over project files. Design principle 8: never a |
| `ui/case_form.py` | Rendering the add-a-case form. Contract: qa/contracts/ui.md. |
| `ui/crawl_view.py` | HTML fragments for the crawl pages — split from `routes_crawls.py` to keep |
| `ui/env_editor.py` | The one legitimate WRITE path to the repo-root `.env` (every other module |
| `ui/helpers.py` | Shared request-validation and lookup helpers used by every UI route module. |
| `ui/project_view.py` | The project page's action card — the operator's control panel for one product. |
| `ui/routes_cases.py` | Create, list, rename and delete a project's test cases from the UI. |
| `ui/routes_crawls.py` | The explorer, on screen: crawl history, one crawl's screen graph, its |
| `ui/routes_credentials.py` | The masked .env editor. Contract: qa/contracts/ui.md U3 — a real value is |
| `ui/routes_flow_diagram.py` | The BFS-style companion to `routes_report.py`'s DFS per-run step flow: |
| `ui/routes_learn.py` | The learning loop on screen — review the FlowSpec, generate cases, see the asks. |
| `ui/routes_project_edit.py` | Edit a project's own settings after onboarding. Contract: qa/contracts/ui.md. |
| `ui/routes_report.py` | Run history, per-case screenshots, and portable downloads. Contract: |
| `ui/routes_runs.py` | Trigger a real run. Contract: qa/contracts/ui-run.md RU1-RU4. Run-history |
| `ui/routes_settings.py` | Global AI/API provider keys. Contract: qa/contracts/ui-settings.md US1-US4. |
| `ui/theme.py` | Shared visual system for every UI route. Contract: qa/contracts/docker.md D5. |
| `ui/theme_style.py` | The raw CSS/font-link template for every page. Split out of `theme.py` |
<!-- /generated:map -->

## Schema summary

<!-- generated:schema -->
| Model | Meaning |
|---|---|
| `AnalysedScreen` (`schema/analysis.py`) | An `ObservedScreen` two or more models agreed on (or the one model that |
| `AnalysedIssue` (`schema/analysis.py`) | An `ObservedIssue` after cross-model merge — `id` is stamped by |
| `JourneyStop` (`schema/analysis.py`) | One stop in a recording's end-to-end journey — reuses `ObservedScreen`'s |
| `VideoAnalysis` (`schema/analysis.py`) | One source's adjudicated understanding — screens, flows, the ordered |
| `RunApproval` (`schema/approval.py`) | One human's authorisation for one kind of run against one target. |
| `Provenance` (`schema/base.py`) | Who or what produced this artifact, and from what. |
| `Artifact` (`schema/base.py`) | Common envelope: versioned, timestamped, attributable. |
| `SeededBug` (`schema/bench.py`) | A deliberately introduced defect with known ground truth. |
| `Finding` (`schema/bench.py`) | One reported defect from a participant, matched against ground truth. |
| `BenchCorpus` (`schema/bench.py`) | A build with known seeded defects and the material pack given to testers. |
| `BenchTrial` (`schema/bench.py`) | One participant's attempt on one corpus. |
| `Case` (`schema/case.py`) | One generated or hand-written test case. |
| `AgentFix` (`schema/case.py`) | The agent's proposed correction for one failing step. |
| `ExpandedSteps` (`schema/case.py`) | One taxonomy class's proposed steps for a flow — `stages/expand.py`'s raw |
| `Script` (`schema/case.py`) | A durable Playwright script produced once an agent gets a case working. |
| `CoverageGap` (`schema/coverage.py`) | A screen or route observed in a run but absent from the FlowSpec. |
| `VideoRequest` (`schema/coverage.py`) | What the system asks a human to record, and why. |
| `DialogEvent` (`schema/crawl.py`) | One JS dialog (`alert`/`confirm`/`prompt`/`beforeunload`) the observer saw. |
| `CrawlBounds` (`schema/crawl.py`) | Bounds the BFS actually stops on — every field must be able to end |
| `SafetyPolicy` (`schema/crawl.py`) | What the explorer will and won't click, given a project's `write_policy`. |
| `CrawlIssue` (`schema/crawl.py`) | One problem the crawl noticed — console error, failed first-party |
| `NoiseCount` (`schema/crawl.py`) | One third-party host's dropped-request tally (never an issue, X9). |
| `Crawl` (`schema/crawl.py`) | The envelope for one bounded BFS run — `stages/explore.py`'s output. |
| `SourceRef` (`schema/flowspec.py`) | Where a piece of understanding came from — a video second, a doc line. |
| `FieldConstraints` (`schema/flowspec.py`) | What the UI says a field accepts. Drives boundary/edge case generation. |
| `InputField` (`schema/flowspec.py`) | One input on a screen. |
| `ExpectedState` (`schema/flowspec.py`) | What must be true for a step to have succeeded. |
| `Step` (`schema/flowspec.py`) | One browser action plus what it should produce. |
| `Screen` (`schema/flowspec.py`) | A distinguishable page/state of the product. |
| `Flow` (`schema/flowspec.py`) | An end-to-end journey through screens. |
| `Review` (`schema/flowspec.py`) | The human gate. A flowspec drives nothing until a person approves it. |
| `Conflict` (`schema/flowspec.py`) | Sources disagreed. Flagged for a human — never silently merged. |
| `FlowSpec` (`schema/flowspec.py`) | The reviewed understanding of one project's UI. |
| `Issue` (`schema/issue.py`) | One row of "what's wrong", derived from a video and (optionally) matched |
| `FeatureEvent` (`schema/ledger.py`) | One dated event in the life of a feature: planned, live, updated, or retired. |
| `RelitigationVerdict` (`schema/ledger.py`) | The judge's answer to "is this new unit a retired feature coming back?". |
| `TranscriptSegment` (`schema/media.py`) | One spoken utterance, absolute seconds into the source video. |
| `Transcript` (`schema/media.py`) | A video's narration. `from_sidecar` loads the exact shape the existing |
| `MediaChunk` (`schema/media.py`) | One re-encoded chunk of a longer video. |
| `MediaPrep` (`schema/media.py`) | Probe + chunk manifest for one `Source`. Degrades gracefully (VL1): |
| `ObservedStep` (`schema/observation.py`) | One action a vision model saw in a video. Raw material for a `Step` — |
| `ObservedFlow` (`schema/observation.py`) | One journey a vision model saw across screens. |
| `ObservedScreen` (`schema/observation.py`) | One distinguishable screen a vision model saw. |
| `ObservedIssue` (`schema/observation.py`) | A problem the vision model itself noticed — spoken, on-screen, or both. |
| `VisionOptions` (`schema/observation.py`) | Generation config for a vision call — the settings the proven external |
| `VideoObservation` (`schema/observation.py`) | A vision provider's raw reading of one video (or chunk) — turned into a |
| `ModelObservation` (`schema/observation.py`) | One model's raw answer for one chunk — cached on disk so re-running the |
| `SecretRef` (`schema/project.py`) | A declared credential. Holds the KEY and its scope — never the value. |
| `ProviderConfig` (`schema/project.py`) | Which provider serves each role. Roles are swappable per project. |
| `Source` (`schema/project.py`) | An immutable input the system learned from. |
| `Project` (`schema/project.py`) | Everything the system needs to test one product. |
| `Evidence` (`schema/run.py`) | A file or value the grader may cite. Already redacted and masked. |
| `ProviderUsage` (`schema/run.py`) | Token and call accounting per provider role — the cost story per run. |
| `RawResult` (`schema/run.py`) | One case's execution record. |
| `Run` (`schema/run.py`) | One regression run over a set of cases. |
| `ElementRef` (`schema/screen_graph.py`) | One interactive element found by `browser/enumerate.js`. |
| `PageObservation` (`schema/screen_graph.py`) | One page-visit's raw material: its url/title and interactive elements. |
| `ScreenNode` (`schema/screen_graph.py`) | One distinct screen the crawl found. Identity is structural |
| `ScreenEdge` (`schema/screen_graph.py`) | One candidate action the crawl tried from one screen. |
| `CrawlFrontier` (`schema/screen_graph.py`) | The BFS queue state — persisted so a crash mid-crawl leaves a resumable |
| `ScreenVisit` (`schema/screenmap.py`) | One recording that showed this screen. |
| `MappedScreen` (`schema/screenmap.py`) | One screen folded across every recording that showed it. |
| `Journey` (`schema/screenmap.py`) | One recording's ordered path through screens. |
| `ScreenMap` (`schema/screenmap.py`) | The product map: every learned screen plus the journeys that visited them. |
| `Criterion` (`schema/verdict.py`) | One checkable bar. If it can be argued about, it is not a criterion. |
| `Rubric` (`schema/verdict.py`) | The grading contract for a case. More specific than the case itself. |
| `Failure` (`schema/verdict.py`) | One unmet criterion, with the evidence that shows it. |
| `Judgment` (`schema/verdict.py`) | Raw judge output for one grading call — the stage fills in run_id, case_id, |
| `Verdict` (`schema/verdict.py`) | The judge's output for one case in one run. |
<!-- /generated:schema -->
