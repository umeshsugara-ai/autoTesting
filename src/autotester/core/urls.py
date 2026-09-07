"""URL templating: the identity input a crawled screen shares with the
ingest pipeline (`core.urls.url_template` is the ONLY place a URL is
normalised into a screen-identity path — `stages/ingest.py` A2 and
`stages/screen_identity.py` B2 both call this instead of reimplementing it).

A numeric/uuid/ULID/hex/date-shaped path segment is templated to `{id}` or
`{date}` so `/students/1` and `/students/2` collapse to the same identity,
while `/students/me` (not id-shaped) is left alone.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

_NUMERIC = re.compile(r"^\d+$")
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.IGNORECASE
)
_ULID = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")  # Crockford base32, no I/L/O/U
_HEX = re.compile(r"^[0-9a-f]{16,}$", re.IGNORECASE)
_DATE = re.compile(r"^\d{4}-\d{2}(-\d{2})?$")


def _template_segment(segment: str) -> str:
    if not segment:
        return segment
    if _DATE.match(segment):
        return "{date}"
    if _NUMERIC.match(segment) or _UUID.match(segment) or _ULID.match(segment) or _HEX.match(
        segment
    ):
        return "{id}"
    return segment


def url_template(url: str, *, keep_host: bool = True) -> str:
    """Normalise `url` to a screen-identity path: strip query/fragment,
    collapse repeated slashes, template id/date-shaped segments, and drop a
    trailing slash (the root `/` is kept as-is). Idempotent —
    `url_template(url_template(u)) == url_template(u)`."""
    parts = urlsplit(url)
    segments = [seg for seg in parts.path.split("/") if seg != ""]
    templated = "/".join(_template_segment(seg) for seg in segments)
    path = f"/{templated}" if segments else "/"
    if keep_host and parts.netloc:
        return f"{parts.netloc}{path}"
    return path
