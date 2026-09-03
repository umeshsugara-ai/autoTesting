# AutoTester — map (generated sections; do not edit between markers)

**Purpose:** the directory map (every module's one job, from its docstring) and the schema summary (every model, from its docstring), derived from code by `autotester map`.
**Open me when:** you need to find which module owns a job or which model holds a shape. `autotester doctor` fails when this file is stale.

## Directory map

<!-- generated:map -->
| Module | One job |
|---|---|
| `browser/secrets.py` | The credential boundary. Secret values live here and nowhere else. |
| `browser/session.py` | One real, visible browser session per project. Contract: browser-and-secrets.md B5-B9. |
| `cli.py` | Command line. Every action the UI offers is available here first. |
| `core/ids.py` | Identifier generation. The ONLY place ids are minted. |
| `core/paths.py` | Filesystem layout. The ONLY place project paths are constructed. |
| `core/redact.py` | Secret redaction. Every log line and stored artifact passes through here. |
| `doctor.py` | Design enforcement. Runs the rules that keep this repo readable. |
| `ledger/relitigation.py` | The cyclic-rebuild gate: is this new unit a retired feature coming back? |
| `ledger/render.py` | Derive the living docs from code and the ledger. Nothing here is hand-typed. |
| `ledger/store.py` | Read and append `docs/FEATURES.jsonl`. The only write path to the ledger. |
| `providers/base.py` | The provider seam. Every model call in the system goes through this interface. |
| `providers/mock.py` | Deterministic provider for tests and dry runs. Never calls a network. |
| `schema/base.py` | Base model every artifact inherits. Defines the shared envelope. |
| `schema/bench.py` | The north star, made measurable: human expert tester vs AutoTester. |
| `schema/case.py` | A test case — one falsifiable claim about the product, plus how to check it. |
| `schema/coverage.py` | Coverage gaps and the video requests that close them. |
| `schema/enums.py` | Every closed vocabulary in the system. Nothing else defines these strings. |
| `schema/flowspec.py` | The FlowSpec — the system's understanding of the product under test. |
| `schema/ledger.py` | The feature ledger row and the relitigation verdict. Contract: qa/contracts/living-ledger.md. |
| `schema/project.py` | Project configuration and the secret contract. One directory per project. |
| `schema/run.py` | What EXECUTE observed. Deliberately contains no judgement — see verdict.py. |
| `schema/verdict.py` | Grading. An independent, stateless judge reads evidence against a rubric. |
| `stages/execute.py` | EXECUTE: run one case's steps in a real browser, producing a RawResult. |
| `stages/grade.py` | GRADE: an independent, stateless judge reads a Rubric + a RawResult's evidence. |
| `store/filestore.py` | The one place any artifact is read from or written to disk. Contract: core-invariants.md C6. |
| `store/project_store.py` | Typed convenience over `filestore` for one project's directory. |
<!-- /generated:map -->

## Schema summary

<!-- generated:schema -->
| Model | Meaning |
|---|---|
| `Provenance` (`schema/base.py`) | Who or what produced this artifact, and from what. |
| `Artifact` (`schema/base.py`) | Common envelope: versioned, timestamped, attributable. |
| `SeededBug` (`schema/bench.py`) | A deliberately introduced defect with known ground truth. |
| `Finding` (`schema/bench.py`) | One reported defect from a participant, matched against ground truth. |
| `BenchCorpus` (`schema/bench.py`) | A build with known seeded defects and the material pack given to testers. |
| `BenchTrial` (`schema/bench.py`) | One participant's attempt on one corpus. |
| `Case` (`schema/case.py`) | One generated or hand-written test case. |
| `Script` (`schema/case.py`) | A durable Playwright script produced once an agent gets a case working. |
| `CoverageGap` (`schema/coverage.py`) | A screen or route observed in a run but absent from the FlowSpec. |
| `VideoRequest` (`schema/coverage.py`) | What the system asks a human to record, and why. |
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
| `FeatureEvent` (`schema/ledger.py`) | One dated event in the life of a feature: planned, live, updated, or retired. |
| `RelitigationVerdict` (`schema/ledger.py`) | The judge's answer to "is this new unit a retired feature coming back?". |
| `SecretRef` (`schema/project.py`) | A declared credential. Holds the KEY and its scope — never the value. |
| `ProviderConfig` (`schema/project.py`) | Which provider serves each role. Roles are swappable per project. |
| `Source` (`schema/project.py`) | An immutable input the system learned from. |
| `Project` (`schema/project.py`) | Everything the system needs to test one product. |
| `Evidence` (`schema/run.py`) | A file or value the grader may cite. Already redacted and masked. |
| `ProviderUsage` (`schema/run.py`) | Token and call accounting per provider role — the cost story per run. |
| `RawResult` (`schema/run.py`) | One case's execution record. |
| `Run` (`schema/run.py`) | One regression run over a set of cases. |
| `Criterion` (`schema/verdict.py`) | One checkable bar. If it can be argued about, it is not a criterion. |
| `Rubric` (`schema/verdict.py`) | The grading contract for a case. More specific than the case itself. |
| `Failure` (`schema/verdict.py`) | One unmet criterion, with the evidence that shows it. |
| `Judgment` (`schema/verdict.py`) | Raw judge output for one grading call — the stage fills in run_id, case_id, |
| `Verdict` (`schema/verdict.py`) | The judge's output for one case in one run. |
<!-- /generated:schema -->
