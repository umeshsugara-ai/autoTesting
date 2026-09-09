"""Presentation-only noVNC page for watching the container's real browser."""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from autotester.ui import theme

router = APIRouter()


@router.get("/live", response_class=HTMLResponse)
def live_view() -> str:
    body = (
        theme.breadcrumb(("Projects", "/"), ("Live view", None))
        + "<h1>Live view</h1>"
        "<p class='subtitle'>Watch the real browser as a run happens.</p>"
        "<div class='live-tip'><strong>A black screen below is normal.</strong> It is the "
        "container's real display, empty whenever no run is in progress. Open a project and "
        "press <em>▶ Run tests</em> with this page open in a second tab.</div>"
        "<div class='live-tip live-tip-muted'>To slow a run down, set "
        "<code>AUTOTESTER_SLOW_MO_MS=1500</code> before "
        "<code>docker compose up -d</code>.</div>"
        "<div class='live-shell'><iframe src='http://localhost:6080/"
        "vnc.html?autoconnect=true&resize=scale'></iframe></div>"
    )
    return theme.page("Live view", body)
