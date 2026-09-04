"""Shared request-validation and lookup helpers used by every UI route module.

One place for slug/id validation so `ui/app.py`, `ui/routes_runs.py` and
`ui/routes_credentials.py` never each grow their own copy (AT-035's
attribute-injection hole started exactly there).
"""

from __future__ import annotations

import re

from fastapi import HTTPException

from autotester.core.paths import repo_root
from autotester.schema.project import Project
from autotester.store.project_store import ProjectStore

# Same shape as schema.project.Project.slug's own field pattern -- a slug is a
# single safe path segment, never `..`, `/`, `\`, or a null byte, before it is
# ever handed to ProjectPaths/ProjectStore as a directory name.
_SLUG_RE = re.compile(r"^[a-z][a-z0-9-]*$")
# run/case ids are ulid- or content_id-shaped: alnum plus `_`/`-` only.
_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _require_slug(slug: str) -> str:
    if not _SLUG_RE.fullmatch(slug):
        raise HTTPException(400, "invalid project slug")
    return slug


def _require_safe_id(value: str, label: str) -> str:
    if not _SAFE_ID_RE.fullmatch(value):
        raise HTTPException(400, f"invalid {label}")
    return value


def _project_slugs() -> list[str]:
    projects_dir = repo_root() / "projects"
    if not projects_dir.exists():
        return []
    return sorted(p.name for p in projects_dir.iterdir() if (p / "project.json").exists())


def _load_project_or_404(slug: str) -> tuple[ProjectStore, Project]:
    _require_slug(slug)
    store = ProjectStore(slug)
    project = store.load_project()
    if project is None:
        raise HTTPException(404, f"no project '{slug}'")
    return store, project
