"""The durable Portal Persona — what AutoTester knows about one product, kept
across runs instead of scoped to a single crawl (T-164, contract portal-persona.md).

One `PortalPersona` model, persisted at `projects/<slug>/portal_persona.json`
via the filestore; `knowledge.md` is a regenerated VIEW of it, never a second
source of truth. Auth is described by field/domain SHAPE only — a `SecretRef`
key, never a value (PP5). `history` is a dated, append-only trail of what each
update changed (PP3).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator

from autotester.schema.base import Artifact


class PersonaProfile(BaseModel):
    """What the product is, at a glance — the durable header of the persona."""

    model_config = ConfigDict(extra="forbid")

    name: str = ""
    base_url: str = ""
    overview: str | None = Field(
        default=None, description="the product's own summary, from a reviewed FlowSpec"
    )


class AuthField(BaseModel):
    """One credential input the login SHAPE has. Carries the SecretRef KEY, never
    a value (PP5) — the value lives only in the repo-root `.env` (C5)."""

    model_config = ConfigDict(extra="forbid")

    name: str
    type: str = "text"
    secret_key: str | None = Field(
        default=None, description="the declared SecretRef key (e.g. DEMO_PASSWORD), never a value"
    )


class AuthShape(BaseModel):
    """How the product authenticates, described by shape alone (PP5): which
    screen, which fields, which domains a credential is scoped to. No values."""

    model_config = ConfigDict(extra="forbid")

    required: bool = False
    login_screen: str | None = None
    fields: list[AuthField] = Field(default_factory=list)
    domains: list[str] = Field(
        default_factory=list, description="hosts a credential is scoped to (from SecretRef.domains)"
    )


class PersonaScreen(BaseModel):
    """One distinct screen the product has. Accumulated across runs (PP2)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    url_template: str | None = None
    signature: str | None = Field(
        default=None, description="structural signature when a crawl supplied one"
    )
    purpose: str | None = None
    controls: list[str] = Field(default_factory=list, description="named interactive controls")
    screenshot_ref: str | None = Field(
        default=None, description="a MASKED screenshot (PP5); secret inputs are masked at capture"
    )

    def key(self) -> str:
        """Cross-run identity: the templated URL when known, else the folded name.
        Two runs naming the same screen must land on one entry (PP2)."""
        return self.url_template or " ".join(self.name.casefold().split())


class PersonaTransition(BaseModel):
    """One learned move between screens — what control takes you where."""

    model_config = ConfigDict(extra="forbid")

    from_screen: str
    to_screen: str | None = None
    action: str = "click"
    control: str = ""

    def key(self) -> str:
        return f"{self.from_screen}|{self.action}|{self.control}|{self.to_screen or ''}"


class FlowRunRef(BaseModel):
    """A stable, runnable reference a Quick Re-Run resolves to re-exercise a
    taught flow without re-teaching it (PP6): the project, the flow id, and the
    screen the flow enters at."""

    model_config = ConfigDict(extra="forbid")

    project: str
    flow_id: str
    entry_screen: str


class TaughtFlow(BaseModel):
    """An end-to-end journey the product supports, carried durably with a stable
    runnable reference (PP6)."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    entry_screen: str
    exit_screen: str | None = None
    requires_auth: bool = False
    run_ref: FlowRunRef


class Gotcha(BaseModel):
    """One thing that bit us — a quirk of this product worth remembering."""

    model_config = ConfigDict(extra="forbid")

    note: str
    screen: str | None = None

    def key(self) -> str:
        return f"{self.screen or ''}|{self.note}"


class PersonaRevision(BaseModel):
    """One dated entry in the persona's history: when it was updated and a
    non-empty summary naming what changed (PP3)."""

    model_config = ConfigDict(extra="forbid")

    at: str = Field(description="ISO-8601 UTC timestamp of the update")
    summary: str = Field(description="what this update changed — never blank (PP3)")

    @field_validator("summary")
    @classmethod
    def _reject_blank_summary(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a revision must name what changed; summary may not be blank")
        return value


class PortalPersona(Artifact):
    """The durable, cross-run model of one product under test (PP1). A single
    artifact — `knowledge.md` is a regenerated view of it, not a second store."""

    project: str
    profile: PersonaProfile = Field(default_factory=PersonaProfile)
    auth: AuthShape = Field(default_factory=AuthShape)
    screens: list[PersonaScreen] = Field(default_factory=list)
    transitions: list[PersonaTransition] = Field(default_factory=list)
    taught_flows: list[TaughtFlow] = Field(default_factory=list)
    gotchas: list[Gotcha] = Field(default_factory=list)
    screenshot_refs: list[str] = Field(default_factory=list)
    history: list[PersonaRevision] = Field(default_factory=list)

    def screen(self, screen_id: str) -> PersonaScreen | None:
        return next((s for s in self.screens if s.id == screen_id), None)

    def taught_flow(self, flow_id: str) -> TaughtFlow | None:
        return next((f for f in self.taught_flows if f.id == flow_id), None)

    def resolve_run(self, ref: FlowRunRef) -> TaughtFlow | None:
        """Resolve a Quick Re-Run reference back to the flow it names (PP6).
        A reference the persona cannot resolve is not runnable, and returns None."""
        if ref.project != self.project:
            return None
        flow = self.taught_flow(ref.flow_id)
        if flow is None or flow.entry_screen != ref.entry_screen:
            return None
        return flow
