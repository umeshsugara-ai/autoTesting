"""Video-request persistence — split from `project_store.py` at the 300-line
cap (C2), the same reason `crawl_store.py` exists. `ProjectStore` inherits
`RequestStoreMixin`, so its public API is unchanged; this is not a second
store (C3).

The self-extension queue: COVERAGE queues one ask per gap it cannot name, and
`stages/merge_flowspec.py` closes the ones a later recording answered.
"""

from __future__ import annotations

from autotester.core.paths import ProjectPaths
from autotester.schema.coverage import VideoRequest
from autotester.store.filestore import append_jsonl, read_jsonl, upsert_jsonl


class RequestStoreMixin:
    """Requires `self.paths: ProjectPaths` and `self._request_ids: set[str] | None`
    from `ProjectStore.__init__` — mixed in there, never instantiated alone."""

    paths: ProjectPaths
    _request_ids: set[str] | None

    # -- video requests (the self-extension queue) -------------------------------
    def add_request(self, request: VideoRequest) -> VideoRequest:
        """Idempotent: the same gap never queues a second request."""
        if self._request_ids is None:
            self._request_ids = {r.id for r in self.list_requests()}
        if request.id in self._request_ids:
            return request
        append_jsonl(self.paths.requests, request)
        self._request_ids.add(request.id)
        return request

    def list_requests(self) -> list[VideoRequest]:
        return read_jsonl(self.paths.requests, VideoRequest)

    def update_request(self, request: VideoRequest) -> None:
        """A status transition on an existing ask (open -> fulfilled/dismissed),
        the same upsert pattern as `update_issue`. `add_request` stays
        append-only and idempotent; this is the one way a queued request ever
        changes after it is asked."""
        upsert_jsonl(self.paths.requests, request, VideoRequest)
        if self._request_ids is not None:
            self._request_ids.add(request.id)
