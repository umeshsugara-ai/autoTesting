"""Filesystem layout. The ONLY place project paths are constructed.

Every artifact lives under `projects/<slug>/` as a human-readable file. Nothing
in the system may build these paths by string concatenation elsewhere.
"""

from __future__ import annotations

import os
from pathlib import Path

ENV_ROOT = "AUTOTESTER_ROOT"


def repo_root() -> Path:
    """Repository root; overridable via `AUTOTESTER_ROOT` (used by tests)."""
    override = os.environ.get(ENV_ROOT)
    if override:
        return Path(override).resolve()
    return Path(__file__).resolve().parents[3]


class ProjectPaths:
    """Resolved paths for one project. Construct with a slug, ask for what you need."""

    def __init__(self, slug: str, root: Path | None = None) -> None:
        self.slug = slug
        self.root = root or repo_root()

    @property
    def dir(self) -> Path:
        return self.root / "projects" / self.slug

    @property
    def config(self) -> Path:
        return self.dir / "project.json"

    @property
    def env_file(self) -> Path:
        """One credential file for the whole repo, at the root (Umesh, 2026-09-03).

        Keys are namespaced per project (`PATHLYNKS_*`) and declared in each
        project's `SecretRef[]`; a project can only resolve the keys it declares.
        """
        return self.root / ".env"

    @property
    def sources_dir(self) -> Path:
        return self.dir / "sources"

    @property
    def sources_index(self) -> Path:
        return self.dir / "sources.jsonl"

    @property
    def flowspec(self) -> Path:
        return self.dir / "flowspec.json"

    @property
    def cases(self) -> Path:
        return self.dir / "cases.jsonl"

    @property
    def rubrics_dir(self) -> Path:
        return self.dir / "rubrics"

    @property
    def scripts_dir(self) -> Path:
        return self.dir / "scripts"

    @property
    def runs_dir(self) -> Path:
        return self.dir / "runs"

    @property
    def requests(self) -> Path:
        return self.dir / "requests.jsonl"

    @property
    def knowledge(self) -> Path:
        return self.dir / "knowledge.md"

    @property
    def bench_dir(self) -> Path:
        return self.dir / "bench"

    def bench_corpus(self, corpus_id: str) -> Path:
        return self.bench_dir / f"{corpus_id}.json"

    def bench_trial(self, trial_id: str) -> Path:
        return self.bench_dir / f"{trial_id}.trial.json"

    @property
    def profile_dir(self) -> Path:
        """Persistent browser profile — gitignored, holds the logged-in session."""
        return self.root / "profiles" / self.slug

    def run_dir(self, run_id: str) -> Path:
        return self.runs_dir / run_id

    def ensure(self) -> None:
        """Create the directories a project needs. Safe to call repeatedly."""
        for path in (
            self.dir,
            self.sources_dir,
            self.rubrics_dir,
            self.scripts_dir,
            self.runs_dir,
            self.profile_dir,
            self.bench_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


def work_dir(root: Path | None = None) -> Path:
    """Scratch space. Nothing here is committed; nothing outside here is scratch."""
    path = (root or repo_root()) / ".work"
    path.mkdir(parents=True, exist_ok=True)
    return path


class RepoDocs:
    """Repo-level documents: the living map, the ledger, the history, the router."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or repo_root()

    @property
    def docs_dir(self) -> Path:
        return self.root / "docs"

    @property
    def architecture(self) -> Path:
        return self.docs_dir / "ARCHITECTURE.md"

    @property
    def snapshot(self) -> Path:
        return self.docs_dir / "SNAPSHOT.md"

    @property
    def map(self) -> Path:
        """Generated directory map + schema summary (kept out of ARCHITECTURE's 150-line budget)."""
        return self.docs_dir / "MAP.md"

    @property
    def features(self) -> Path:
        return self.docs_dir / "FEATURES.jsonl"

    @property
    def decisions(self) -> Path:
        return self.docs_dir / "DECISIONS.md"

    @property
    def router(self) -> Path:
        """`CLAUDE.md` carries the "open X when Y" table."""
        return self.root / "CLAUDE.md"

    @property
    def goal(self) -> Path:
        return self.root / ".goal" / "goal.json"

    @property
    def prompts_dir(self) -> Path:
        return self.root / "src" / "autotester" / "prompts"
