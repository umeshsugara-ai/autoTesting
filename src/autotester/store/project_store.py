"""Typed convenience over `filestore` for one project's directory.

A thin wrapper — the read/write logic lives once in `filestore`. A new
artifact kind adds a method here, not a new file format (C1/C3).
"""

from __future__ import annotations

from pathlib import Path

from autotester.core.paths import ProjectPaths
from autotester.schema.case import Case
from autotester.schema.flowspec import FlowSpec
from autotester.schema.project import Project, Source
from autotester.schema.run import RawResult, Run
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
            if path.name != "run.json"
            for model in [read_json(path, RawResult)]
            if model is not None
        ]
