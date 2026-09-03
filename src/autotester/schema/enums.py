"""Every closed vocabulary in the system. Nothing else defines these strings."""

from __future__ import annotations

from enum import StrEnum


class SourceKind(StrEnum):
    VIDEO = "video"
    DOC = "doc"
    TEXT = "text"
    URL = "url"


class Action(StrEnum):
    """What a step does to the browser."""

    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    SELECT = "select"
    UPLOAD = "upload"
    WAIT = "wait"
    ASSERT = "assert"


class CaseKind(StrEnum):
    """Coarse bucket a case belongs to."""

    BEST = "best"
    WORST = "worst"
    EDGE = "edge"
    ANCHOR = "anchor"


class CaseClass(StrEnum):
    """The edge-case taxonomy — the product's differentiator.

    Expansion guarantees at least one case per applicable class per flow, so the
    agent cannot drift to the happy path alone.
    """

    HAPPY = "happy"
    AUTH_WRONG_CREDS = "auth_wrong_creds"
    AUTH_EXPIRED_SESSION = "auth_expired_session"
    SERVER_ERROR = "server_error"
    NETWORK_OFFLINE_SLOW = "network_offline_slow"
    INPUT_EMPTY = "input_empty"
    INPUT_BOUNDARY = "input_boundary"
    INPUT_UNICODE_OVERSIZE = "input_unicode_oversize"
    DOUBLE_SUBMIT = "double_submit"
    BACK_REFRESH_MIDFLOW = "back_refresh_midflow"
    DEEPLINK_UNAUTH = "deeplink_unauth"
    CONCURRENT_TAB = "concurrent_tab"
    LOCALE_I18N = "locale_i18n"
    VIEWPORT_MOBILE = "viewport_mobile"
    REGRESSION_ANCHOR = "regression_anchor"


KIND_BY_CLASS: dict[CaseClass, CaseKind] = {
    CaseClass.HAPPY: CaseKind.BEST,
    CaseClass.AUTH_WRONG_CREDS: CaseKind.WORST,
    CaseClass.AUTH_EXPIRED_SESSION: CaseKind.WORST,
    CaseClass.SERVER_ERROR: CaseKind.WORST,
    CaseClass.NETWORK_OFFLINE_SLOW: CaseKind.WORST,
    CaseClass.INPUT_EMPTY: CaseKind.EDGE,
    CaseClass.INPUT_BOUNDARY: CaseKind.EDGE,
    CaseClass.INPUT_UNICODE_OVERSIZE: CaseKind.EDGE,
    CaseClass.DOUBLE_SUBMIT: CaseKind.EDGE,
    CaseClass.BACK_REFRESH_MIDFLOW: CaseKind.EDGE,
    CaseClass.DEEPLINK_UNAUTH: CaseKind.EDGE,
    CaseClass.CONCURRENT_TAB: CaseKind.EDGE,
    CaseClass.LOCALE_I18N: CaseKind.EDGE,
    CaseClass.VIEWPORT_MOBILE: CaseKind.EDGE,
    CaseClass.REGRESSION_ANCHOR: CaseKind.ANCHOR,
}


class Severity(StrEnum):
    S1 = "S1"  # blocks a core flow
    S2 = "S2"  # degrades a flow, workaround exists
    S3 = "S3"  # cosmetic or minor


class CaseStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    RETIRED = "retired"


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    NEEDS_EDIT = "needs_edit"


class Outcome(StrEnum):
    """What the executor observed — NOT a judgement. Grading is separate."""

    COMPLETED = "completed"
    ERRORED = "errored"
    BLOCKED_HITL = "blocked_hitl"


class Result(StrEnum):
    """The grader's verdict. Only the grader writes this."""

    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"
    INCONCLUSIVE = "INCONCLUSIVE"


class EvidenceKind(StrEnum):
    SCREENSHOT = "screenshot"
    DOM = "dom"
    URL = "url"
    NETWORK = "network"
    TRACE = "trace"
    CONSOLE = "console"


class Trigger(StrEnum):
    MANUAL = "manual"
    CI = "ci"
    SCHEDULE = "schedule"


class WritePolicy(StrEnum):
    """How much the tester is allowed to mutate in the target app."""

    READ_ONLY = "read_only"
    TEST_ACCOUNT = "test_account"
    ALLOW_WRITES = "allow_writes"


class ProviderRole(StrEnum):
    VISION = "vision"
    AGENT = "agent"
    JUDGE = "judge"


class RequestStatus(StrEnum):
    OPEN = "open"
    FULFILLED = "fulfilled"
    DISMISSED = "dismissed"


class Participant(StrEnum):
    HUMAN = "human"
    AUTOTESTER = "autotester"


class FeatureEventKind(StrEnum):
    """What happened to a feature, as recorded in `docs/FEATURES.jsonl`."""

    PLANNED = "planned"
    LIVE = "live"
    UPDATED = "updated"
    RETIRED = "retired"


class UserValue(StrEnum):
    """How much the product's user depends on a feature. Gates the reasoning ask."""

    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"
