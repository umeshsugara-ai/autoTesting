"""Typed convenience over `filestore` for one project's directory.

A thin wrapper — the read/write logic lives once in `filestore`. A new
artifact kind adds a method here, not a new file format (C1/C3).
"""

from __future__ import annotations

from pathlib import Path

from autotester.core.paths import ProjectPaths
from autotester.schema.bench import BenchCorpus, BenchTrial
from autotester.schema.case import Case
from autotester.schema.coverage import VideoRequest
from autotester.schema.flowspec import FlowSpec
from autotester.schema.project import Project, Source
from autotester.schema.run import RawResult, Run
from autotester.schema.verdict import Verdict
from autotester.store.filestore import append_jsonl, read_json, read_jsonl, write_json


class ProjectStore:
    """Load and save one project's artifacts as human-editable files (C6)."""

    def __init__(self, slug: str, root: Path | None = None) -> None:
        self.paths = ProjectPaths(slug, root)

    # -- project --------------------------------------------------------------
    def save_project(self, project: Project) -> None:
        write_json(self.paths.config, project)

    def load_project(self) -> Project | None:
        return read_json(self.paths.config, Project)

    # -- sources (immutable, content-addressed) --------------------------------
    def add_source(self, source: Source) -> Source:
        """Idempotent: re-adding an identical source is a no-op, not a duplicate."""
        if any(s.id == source.id for s in self.list_sources()):
            return source
        append_jsonl(self.paths.sources_index, source)
        return source

    def list_sources(self) -> list[Source]:
        return read_jsonl(self.paths.sources_index, Source)

    # -- flowspec (single, human-reviewed) -------------------------------------
    def save_flowspec(self, spec: FlowSpec) -> None:
        write_json(self.paths.flowspec, spec)

    def load_flowspec(self) -> FlowSpec | None:
        return read_json(self.paths.flowspec, FlowSpec)

    # -- cases (content-addressed; status can change) ---------------------------
    def add_case(self, case: Case) -> Case:
        """Idempotent on id: regenerating a flowspec never duplicates a case."""
        if any(c.id == case.id for c in self.list_cases()):
            return case
        append_jsonl(self.paths.cases, case)
        return case

    def list_cases(self) -> list[Case]:
        return read_jsonl(self.paths.cases, Case)

    # -- runs (one Run envelope + one RawResult file per case) -------------------
    def save_run(self, run: Run) -> None:
        write_json(self.paths.run_dir(run.id) / "run.json", run)

    def load_run(self, run_id: str) -> Run | None:
        return read_json(self.paths.run_dir(run_id) / "run.json", Run)

    def save_result(self, run_id: str, result: RawResult) -> None:
        write_json(self.paths.run_dir(run_id) / f"{result.case_id}.json", result)

    def load_results(self, run_id: str) -> list[RawResult]:
        run_dir = self.paths.run_dir(run_id)
        if not run_dir.exists():
            return []
        return [
            model
            for path in sorted(run_dir.glob("*.json"))
            if path.name != "run.json" and not path.name.endswith(".verdict.json")
            for model in [read_json(path, RawResult)]
            if model is not None
        ]

    # -- verdicts (one file per case, alongside its RawResult) -------------------
    def save_verdict(self, run_id: str, verdict: Verdict) -> None:
        write_json(self.paths.run_dir(run_id) / f"{verdict.case_id}.verdict.json", verdict)

    def load_verdicts(self, run_id: str) -> list[Verdict]:
        run_dir = self.paths.run_dir(run_id)
        if not run_dir.exists():
            return []
        return [
            model
            for path in sorted(run_dir.glob("*.verdict.json"))
            for model in [read_json(path, Verdict)]
            if model is not None
        ]

    # -- video requests (the self-extension queue) -------------------------------
    def add_request(self, request: VideoRequest) -> VideoRequest:
        """Idempotent: the same gap never queues a second request."""
        if any(r.id == request.id for r in self.list_requests()):
            return request
        append_jsonl(self.paths.requests, request)
        return request

    def list_requests(self) -> list[VideoRequest]:
        return read_jsonl(self.paths.requests, VideoRequest)

    # -- bench (seeded corpus + trial scorecards) --------------------------------
    def save_bench_corpus(self, corpus: BenchCorpus) -> None:
        write_json(self.paths.bench_corpus(corpus.id), corpus)

    def load_bench_corpus(self, corpus_id: str) -> BenchCorpus | None:
        return read_json(self.paths.bench_corpus(corpus_id), BenchCorpus)

    def save_bench_trial(self, trial: BenchTrial) -> None:
        write_json(self.paths.bench_trial(trial.id), trial)

    def list_bench_trials(self, corpus_id: str) -> list[BenchTrial]:
        bench_dir = self.paths.bench_dir
        if not bench_dir.exists():
            return []
        trials = [
            model
            for path in sorted(bench_dir.glob("*.trial.json"))
            for model in [read_json(path, BenchTrial)]
            if model is not None
        ]
        return [t for t in trials if t.corpus_id == corpus_id]
