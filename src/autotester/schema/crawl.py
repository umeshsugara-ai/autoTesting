"""Crawl-safety and crawl-envelope primitives (Track B).

`DialogEvent` shipped at B1. B2 adds the schema the crawl stage itself
(B3) and the safety layer (B4) need: bounds that actually stop a BFS,
a policy the explorer consults before every action, and the envelope
artifact persisted per crawl.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from autotester.core.ids import content_id, run_id
from autotester.schema.base import Artifact
from autotester.schema.enums import CrawlStatus, IssueKind, WritePolicy


class DialogEvent(BaseModel):
    """One JS dialog (`alert`/`confirm`/`prompt`/`beforeunload`) the observer saw."""

    model_config = ConfigDict(extra="forbid")

    dialog_type: str
    message: str = ""
    accepted: bool = False


# D-016's default deny-list: destructive-name patterns a READ_ONLY/TEST_ACCOUNT
# crawl never clicks. Word-bounded so "Deliverables" doesn't match "deliver".
DEFAULT_DENY_PATTERNS = (
    r"\bdelete\b", r"\bremove\b", r"\bdeactivate\b", r"\bdisable\b", r"\barchive\b",
    r"\bpurge\b", r"\bdrop\b", r"\breset\b", r"\brevoke\b", r"\bterminate\b",
    r"\bcancel subscription\b", r"\bpay\b", r"\bcheckout\b", r"\bsend\b", r"\bsubmit\b",
    r"\bapprove\b", r"\breject\b", r"\bpublish\b", r"\bunsubscribe\b",
)

# Never clicked at ANY write_policy, including ALLOW_WRITES. The [\s\w]{0,10}
# gap tolerates "Log me out"/"Sign yourself out" without over-matching an
# unrelated sentence (bounded width, not `.*`).
DEFAULT_NEVER_CLICK_PATTERNS = (
    r"\blog ?out\b", r"\blog\b[\s\w]{0,10}\bout\b",
    r"\bsign ?out\b", r"\bsignout\b", r"\bsign\b[\s\w]{0,10}\bout\b",
)

# Third-party hosts whose failed requests are noise, never an issue.
DEFAULT_THIRD_PARTY_IGNORE = (
    "google-analytics.com", "googletagmanager.com", "doubleclick.net",
    "facebook.net", "connect.facebook.net", "hotjar.com", "clarity.ms",
    "sentry.io", "segment.io", "intercom.io", "fonts.gstatic.com", "fonts.googleapis.com",
)


class CrawlBounds(BaseModel):
    """Bounds the BFS actually stops on — every field must be able to end
    the crawl and name itself as `Crawl.stop_reason` (X4)."""

    model_config = ConfigDict(extra="forbid")

    max_screens: int = 30
    max_actions: int = 200
    wall_clock_s: float = 600.0
    max_depth: int = 6
    per_node_action_cap: int = 25
    dialog_repeat_limit: int = 3
    settle_ms: int = Field(
        default=2500,
        description="per-action settle ceiling. Deliberately far below the 8s a graded "
        "test case waits: a crawl performs hundreds of actions, and a page whose "
        "third-party requests never resolve would otherwise cost the full ceiling every "
        "single time (measured: a 60-action crawl of the fixture site took >5 minutes at "
        "8s, because one page fetches unreachable analytics hosts)",
    )


class SafetyPolicy(BaseModel):
    """What the explorer will and won't click, given a project's `write_policy`."""

    model_config = ConfigDict(extra="forbid")

    write_policy: WritePolicy = WritePolicy.READ_ONLY
    deny_patterns: list[str] = Field(default_factory=lambda: list(DEFAULT_DENY_PATTERNS))
    never_click_patterns: list[str] = Field(
        default_factory=lambda: list(DEFAULT_NEVER_CLICK_PATTERNS)
    )
    third_party_ignore: list[str] = Field(
        default_factory=lambda: list(DEFAULT_THIRD_PARTY_IGNORE)
    )
    click_unnamed: bool = False


class CrawlIssue(Artifact):
    """One problem the crawl noticed — console error, failed first-party
    request, an off-domain navigation attempt, or a dialog storm."""

    id: str = ""
    crawl_id: str
    project: str
    kind: IssueKind
    node_id: str
    detail: str
    first_party: bool = True

    def model_post_init(self, _context: object) -> None:
        if not self.id:
            payload = {"crawl_id": self.crawl_id, "node_id": self.node_id,
                       "kind": str(self.kind), "detail": self.detail}
            object.__setattr__(self, "id", content_id("cissue", payload))


class CoverageHole(BaseModel):
    """One control the crawl discovered and did not perform, with the ONE reason why (V7b)."""

    model_config = ConfigDict(extra="forbid")

    node_id: str
    url_template: str
    selector: str
    name: str = ""
    reason: str = Field(description="bound:<name> | policy:<rule> | unnamed | off_domain | "
                                    "error | login_wall | not_visited")


class CrawlCoverage(BaseModel):
    """What a crawl covered, stated by the crawl itself (coverage.md V7). The books balance:
    `controls_exercised + len(holes) == controls_discovered`."""

    model_config = ConfigDict(extra="forbid")

    controls_discovered: int = 0
    controls_exercised: int = 0
    screens_reached: int = 0
    screens_queued_unvisited: int = 0
    percent: int = Field(default=0, description="floor(exercised / discovered * 100); never "
                                                "100 for a crawl that did not complete (V7d)")
    holes: list[CoverageHole] = Field(default_factory=list)
    screens_not_entered: list[CoverageHole] = Field(
        default_factory=list, description="screens a link led to that a bound kept the crawl "
                                          "from entering (max_depth / max_screens) — AT-470")
    spec_screens_reached: int | None = None
    spec_screens_total: int | None = None
    spec_error: str | None = Field(default=None, description="why the FlowSpec could not be "
                                                             "read for the spec counts (AT-472)")
    error: str | None = Field(default=None, description="why coverage could not be computed; "
                                                        "the crawl record is kept regardless")

    def by_reason(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for hole in self.holes:
            counts[hole.reason] = counts.get(hole.reason, 0) + 1
        return dict(sorted(counts.items()))


class NoiseCount(BaseModel):
    """One third-party host's dropped-request tally (never an issue, X9)."""

    model_config = ConfigDict(extra="forbid")

    host: str
    count: int = 0


class Crawl(Artifact):
    """The envelope for one bounded BFS run — `stages/explore.py`'s output."""

    id: str = Field(default_factory=lambda: run_id("crawl"))
    project: str
    status: CrawlStatus = CrawlStatus.RUNNING
    bounds: CrawlBounds = Field(default_factory=CrawlBounds)
    policy: SafetyPolicy = Field(default_factory=SafetyPolicy)
    login_case_id: str | None = None
    provider: str = "mock"
    started_at: str | None = None
    finished_at: str | None = None
    stop_reason: str | None = None
    screens: int = 0
    edges: int = 0
    actions: int = 0
    denied: int = 0
    issues: int = 0
    """Problems found in the PRODUCT under test. `IssueKind.EVIDENCE` is
    deliberately excluded — see `tool_failures` (AT-120)."""
    tool_failures: int = 0
    """Times the crawler itself failed to record something. Counted apart for
    the same reason `noise_counts` is: a number a human reads as "bugs in my
    product" must not silently include the tool's own failures. Kept as a
    count rather than dropped so "we did not report it" stays auditable."""
    noise_counts: list[NoiseCount] = Field(default_factory=list)
    coverage: CrawlCoverage | None = Field(
        default=None, description="V7; None on a crawl recorded before coverage existed")
