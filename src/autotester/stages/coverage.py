"""COVERAGE: diff what a run actually saw against what the FlowSpec knows.

Contract: qa/contracts/coverage.md V1-V4. "When it meets a screen it does not
know, it asks the human for a video instead of guessing" — this stage is that
mechanism: any URL a run's evidence reached that matches no known screen's
`url_pattern` becomes a `CoverageGap`, and exactly one `VideoRequest` per gap
(both content-addressed, so re-running the diff never duplicates either).
"""

from __future__ import annotations

from urllib.parse import urlsplit

from autotester.schema.coverage import CoverageGap, VideoRequest
from autotester.schema.enums import EvidenceKind
from autotester.schema.flowspec import FlowSpec
from autotester.schema.run import RawResult


def _path_of(url: str) -> str:
    return urlsplit(url).path or "/"


def _known_paths(spec: FlowSpec) -> set[str]:
    return {_path_of(s.url_pattern) for s in spec.screens if s.url_pattern}


def _seen_urls(results: list[RawResult]) -> list[tuple[str, str]]:
    """(url, case_id) pairs actually observed — only real http(s) URLs; a
    redacted evidence string (e.g. `[REDACTED]:KEY`) never matches this and is
    silently skipped, not mistaken for a route."""
    return [
        (ev.path, result.case_id)
        for result in results
        for ev in result.evidence
        if ev.kind is EvidenceKind.URL and ev.path.startswith(("http://", "https://"))
    ]


def diff_coverage(spec: FlowSpec, results: list[RawResult]) -> list[CoverageGap]:
    """Every URL a run actually reached whose path matches no known screen."""
    known = _known_paths(spec)
    gaps: dict[str, CoverageGap] = {}
    for url, case_id in _seen_urls(results):
        path = _path_of(url)
        if path in known:
            continue
        gap = CoverageGap(
            project=spec.project, kind="route", subject=path, seen_in_run=case_id,
            reason=f"observed '{path}' but no screen in the FlowSpec has this url_pattern",
        )
        gaps.setdefault(gap.id, gap)  # content-addressed on (project, kind, subject): deduped
    return list(gaps.values())


def request_for(gap: CoverageGap) -> VideoRequest:
    """Exactly one `VideoRequest` per gap — content-addressed on (project, gap_id),
    so asking twice for the same gap never produces a second request."""
    return VideoRequest(
        project=gap.project,
        gap_id=gap.id,
        prompt=f"Record a short video showing the screen/flow at '{gap.subject}' — {gap.reason}",
    )
