"""The operator-facing recording registry.

This is the UI door to the same content-addressed ``Source`` ledger used by
``autotester ingest register``. It never creates a second upload registry or a
UI-only representation. Planned owner: Track A5.2 in ``plan.md``.
"""

from __future__ import annotations

import shutil
from html import escape
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse

from autotester import providers
from autotester.browser.secrets import SecretStore
from autotester.core.ids import file_sha256
from autotester.core.paths import ProjectPaths, RepoDocs, work_dir
from autotester.providers.base import ProviderError
from autotester.schema.enums import ReviewStatus, SourceKind
from autotester.schema.observation import VisionOptions
from autotester.schema.project import Source
from autotester.stages.analyze_video import DuplicateProviders, NoObservations, analyze
from autotester.stages.ingest import register_source
from autotester.stages.issues import derive_issues, sync_source_issues
from autotester.stages.media_prep import SourceNotPrepared, UnreadableRecording, require_prepared
from autotester.stages.product_map import attach_screenshots, build_screen_map
from autotester.ui import theme
from autotester.ui.helpers import (
    _load_project_or_404,
    _refuse_unsafe_submission,
    _require_safe_id,
    _reserved_temp_path,
)

router = APIRouter()
_UPLOAD_SUFFIXES = frozenset({".avi", ".mkv", ".mov", ".mp4", ".webm"})


def _link(href: str, text: str) -> str:
    return f"<a class='btn' href='{escape(href)}'>{escape(text)}</a>"


def _refusal(slug: str, message: str, *, title: str = "Recording not found") -> HTMLResponse:
    body = theme.card(
        f"<p>{escape(message)}</p><p style='margin-top:14px'>"
        f"{_link(f'/projects/{slug}/sources', 'Try another path')}</p>",
        title=title,
    )
    return HTMLResponse(
        theme.page(title, body, active_slug=slug), status_code=400)


def _source_rows(store, slug: str) -> str:
    return "".join(
        f"<tr><td><code>{escape(source.id)}</code></td>"
        f"<td>{escape(source.label or '—')}</td>"
        f"<td><code>{escape(source.path or '—')}</code></td>"
        f"<td><form method='post' action='/projects/{escape(slug)}/sources/"
        f"{escape(source.id)}/analyze'><button type='submit'>Analyze</button></form></td></tr>"
        for source in store.list_sources()
    ) or "<tr><td colspan='4'>No recordings registered yet.</td></tr>"


@router.get("/projects/{slug}/sources", response_class=HTMLResponse)
def sources_page(slug: str) -> str:
    """List registered sources and offer a server-local path registration form."""
    store, project = _load_project_or_404(slug)
    name = escape(project.name)
    crumbs = theme.breadcrumb(("Projects", "/"), (name, f"/projects/{slug}"),
                              ("Sources", None))
    rows = _source_rows(store, slug)
    form = f"""
      <form method="post" action="/projects/{escape(slug)}/sources">
        <div class="field"><label for="path">Recording path on this machine</label>
          <input id="path" name="path" required placeholder="C:\\Videos\\product-flow.mp4">
          <span class="hint">The file stays where it is; AutoTester records its content hash.</span>
        </div>
        <div class="field"><label for="label">What this recording shows</label>
          <input id="label" name="label" placeholder="Trainer onboarding — happy path">
        </div>
        <button class="btn btn-primary" type="submit">Add recording</button>
      </form>"""
    upload = f"""
      <form method="post" enctype="multipart/form-data"
            action="/projects/{escape(slug)}/sources/upload">
        <div class="field"><label for="recording">Upload a recording</label>
          <input id="recording" type="file" name="recording" required accept="video/*">
        </div>
        <div class="field"><label for="upload-label">What this recording shows</label>
          <input id="upload-label" name="label" placeholder="Trainer onboarding — edge cases">
        </div>
        <button class="btn btn-primary" type="submit">Upload recording</button>
      </form>"""
    body = (crumbs + theme.card(form, title="Register a recording already on this host")
            + theme.card(upload, title="Upload a recording") + theme.card(
        "<table><thead><tr><th>Source</th><th>Label</th><th>Path</th><th></th></tr></thead>"
        f"<tbody>{rows}</tbody></table>",
        title=f"{name} recordings",
    ))
    return theme.page(f"{name} · Sources", body, active_slug=slug)


@router.post("/projects/{slug}/sources")
def add_source(slug: str, path: str = Form(""), label: str = Form("")):
    """Register a real local file through the canonical ingest-stage function."""
    store, project = _load_project_or_404(slug)
    secrets = SecretStore.load(project, ProjectPaths(slug).env_file, strict=False)
    _refuse_unsafe_submission([("recording path", path), ("label", label)], project, secrets)
    try:
        register_source(store, Path(path.strip()), label=label.strip() or None)
    except (FileNotFoundError, OSError):
        return _refusal(slug, "Recording not found")
    return RedirectResponse(f"/projects/{slug}/sources", status_code=303)


@router.post("/projects/{slug}/sources/upload")
def upload_source(slug: str, recording: Annotated[UploadFile, File()], label: str = Form("")):
    """Copy an uploaded recording into its content-addressed project directory."""
    store, project = _load_project_or_404(slug)
    secrets = SecretStore.load(project, ProjectPaths(slug).env_file, strict=False)
    _refuse_unsafe_submission([("label", label)], project, secrets)
    submitted_suffix = Path(recording.filename or "recording").suffix.lower()
    suffix = submitted_suffix if submitted_suffix in _UPLOAD_SUFFIXES else ".video"
    temp = _reserved_temp_path(
        suffix,
        directory=work_dir(store.paths.root),
    )
    target: Path | None = None
    try:
        with temp.open("wb") as handle:
            shutil.copyfileobj(recording.file, handle)
        digest = file_sha256(temp)
        existing = next((source for source in store.list_sources()
                         if source.sha256 == digest), None)
        if existing is not None:
            return RedirectResponse(f"/projects/{slug}/sources", status_code=303)
        draft = Source(project=slug, kind=SourceKind.VIDEO, sha256=digest,
                       label=label.strip() or None)
        target = store.paths.source_dir(draft.id) / f"recording{suffix}"
        target.parent.mkdir(parents=True, exist_ok=True)
        temp.replace(target)
        store.add_source(draft.model_copy(update={"path": str(target.resolve())}))
    except OSError:
        if target is not None:
            target.unlink(missing_ok=True)
        return _refusal(slug, "The uploaded recording could not be stored.",
                        title="Upload failed")
    finally:
        temp.unlink(missing_ok=True)
    return RedirectResponse(f"/projects/{slug}/sources", status_code=303)


def _save_analysis_outputs(store, source, analysis) -> None:
    sync_source_issues(
        store,
        source.id,
        derive_issues(analysis, source, store.paths.slug),
        remove_missing=analysis.is_complete,
    )
    screen_map = build_screen_map(store)
    store.save_screen_map(screen_map)
    spec = store.load_flowspec()
    if spec is not None and spec.review.status is not ReviewStatus.APPROVED:
        store.save_flowspec(attach_screenshots(spec, screen_map))


@router.post("/projects/{slug}/sources/{source_id}/analyze")
def analyze_source(slug: str, source_id: str):
    """Run the configured vision provider, then refresh issues and product map."""
    store, project = _load_project_or_404(slug)
    _require_safe_id(source_id, "source_id")
    source = next((item for item in store.list_sources() if item.id == source_id), None)
    if source is None:
        raise HTTPException(404, "source not found")
    try:
        require_prepared(store, source.id)
    except SourceNotPrepared as exc:
        return _refusal(slug, str(exc), title="Prepare this recording first")
    try:
        provider = providers.get(project.providers.vision)
        if not provider.available():
            raise ProviderError("the configured vision provider has no credential")
        analysis = analyze(store, source, [provider], docs=RepoDocs(), options=VisionOptions())
    except (ProviderError, SourceNotPrepared, UnreadableRecording,
            NoObservations, DuplicateProviders) as exc:
        return _refusal(slug, str(exc), title="Analysis could not finish")
    _save_analysis_outputs(store, source, analysis)
    return RedirectResponse(f"/projects/{slug}/product-map", status_code=303)
