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


def absolute_url(url: str) -> str:
    """Restore the scheme a browser hid, so the host is never read as a path.

    An address bar shows an ABSOLUTE url, and every mainstream browser now hides
    `https://` — so a vision model transcribing one returns `vidysea.com/erp/trainers`,
    not `https://vidysea.com/erp/trainers`. `urlsplit` has no `//` to anchor on
    there, puts the host in `.path`, and `url_template` templates it as a path
    segment: `/vidysea.com/erp/trainers`. That is AT-294, and it is why the same
    screen learned from a video and found by a crawl still did not collapse to
    one row after both producers were switched to `keep_host=False` — the flags
    agreed, the inputs did not.

    This is NOT the host-shape guessing AT-287's first fix tried and failed at
    (`settings.json` and `example.com` are indistinguishable by shape). The
    caller here KNOWS the string is an absolute url, because it came out of an
    address bar; only the scheme is missing. Callers holding a genuine relative
    path must not use this.
    """
    if not url or "//" in url.split("?", 1)[0][:8]:
        return url
    return url if url.startswith("/") else f"https://{url}"


def url_template(url: str, *, keep_host: bool = True) -> str:
    """Normalise `url` to a screen-identity path: strip query/fragment,
    collapse repeated slashes, template id/date-shaped segments, and drop a
    trailing slash (the root `/` is kept as-is).

    **Idempotent for path-shaped input only** — `url_template(p) == p` for any
    `p` this function produced with `keep_host=False`. It is NOT idempotent over
    its own `keep_host=True` output: `urlsplit("demo.test/x")` has no `//`, so
    the host lands in `.path` and re-templating yields `/demo.test/x`.

    That asymmetry is why `Screen.url_pattern` is stored host-LESS by every
    producer (`stages/ingest.py`, `stages/explore_merge.py`,
    `stages/product_map.py`, `stages/screen_identity.py`) — a path pattern, not
    a browsing identity. AT-287: two producers stored it host-ful, coverage
    re-templated it to compare, and the screen became invisible. Inferring
    host-ness back out of a schemeless string is impossible in principle —
    `settings.json` and `example.com` are the same shape — so the fix is one
    canonical stored shape, not a smarter parser."""
    parts = urlsplit(url)
    segments = [seg for seg in parts.path.split("/") if seg != ""]
    templated = "/".join(_template_segment(seg) for seg in segments)
    path = f"/{templated}" if segments else "/"
    if keep_host and parts.netloc:
        return f"{parts.netloc}{path}"
    return path
