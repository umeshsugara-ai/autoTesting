"""Consent as an artifact, not a habit (D-018).

`write_policy` and the HUMAN_GATE files already reach for this informally. This
makes it a file a human writes once and a runner checks every time: what may be
touched, how much of it, until when, and who said so.

The id is content-addressed over **every bound field**, so `core/consent.py`
recomputes it and refuses a row whose id no longer matches its contents.

**What that does and does not buy (AT-110, found by a checker who did it).**
`core.ids.content_id` is an UNKEYED sha256, so the id is recomputable by anyone
who can write the file — including the agent this gate exists to bound. Deleting
the `id` field is enough: `model_post_init` mints a matching one. So this
detects a **careless or accidental edit**, not a determined forger; a checker
widened a 12-action grant to 9999 with `production` flipped true and ran a
500-action crawl on it. Closing that needs a secret (an HMAC keyed from the
repo-root `.env`, or a signed audit line) and is a HUMAN_GATE for Umesh —
`qa/gates/at110-approval-forgery.md`. Do not read the check below as tamper
*proofing*; it is tamper *evidence*.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import Field

from autotester.core.ids import content_id
from autotester.schema.base import Artifact
from autotester.schema.enums import ApprovalKind


class RunApproval(Artifact):
    """One human's authorisation for one kind of run against one target."""

    id: str = ""
    project: str
    run_kind: ApprovalKind
    target: str = Field(description="the exact base_url or endpoint this authorises")
    scope: str = Field(description="what will be read, clicked or sent — in the human's words")
    max_actions: int = 0
    max_probes: int = 0
    wall_clock_s: float = 0.0
    production: bool = Field(
        default=False,
        description="an adversarial run against production requires this to be explicitly true",
    )
    granted_by: str
    granted_at: str
    expires_at: str = Field(description="ISO date/datetime; consent is never open-ended")
    note: str | None = None

    def _bound_payload(self) -> dict[str, object]:
        """Every field that limits what the run may do. Changing any of them
        changes the id, which is how tampering is detected."""
        return {
            "project": self.project, "run_kind": str(self.run_kind), "target": self.target,
            "scope": self.scope, "max_actions": self.max_actions, "max_probes": self.max_probes,
            "wall_clock_s": self.wall_clock_s, "production": self.production,
            "granted_by": self.granted_by, "granted_at": self.granted_at,
            "expires_at": self.expires_at,
        }

    def model_post_init(self, _context: object) -> None:
        if not self.id:
            object.__setattr__(self, "id", content_id("appr", self._bound_payload()))

    @property
    def computed_id(self) -> str:
        return content_id("appr", self._bound_payload())

    @property
    def is_intact(self) -> bool:
        """False when the row was edited after it was granted — the point of
        content-addressing it. `note` is deliberately outside the payload, so a
        human may annotate an approval without invalidating it."""
        return self.id == self.computed_id

    def is_expired(self, now: datetime) -> bool:
        try:
            expiry = datetime.fromisoformat(self.expires_at)
        except ValueError:
            return True  # an unparseable expiry is an expired one, never an eternal one
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        if now.tzinfo is None:
            now = now.replace(tzinfo=UTC)
        return now.astimezone(UTC) > expiry.astimezone(UTC)
