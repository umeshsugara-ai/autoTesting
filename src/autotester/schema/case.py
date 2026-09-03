"""A test case — one falsifiable claim about the product, plus how to check it."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from autotester.core.ids import content_id
from autotester.schema.base import Artifact
from autotester.schema.enums import Action, CaseClass, CaseKind, CaseStatus, Severity
from autotester.schema.flowspec import Step


class Case(Artifact):
    """One generated or hand-written test case.

    Cases are content-addressed: the same flow + class + steps always produces
    the same id, so regenerating a flowspec does not duplicate the suite.
    """

    id: str = ""
    project: str
    flow_id: str
    kind: CaseKind
    case_class: CaseClass
    title: str
    rationale: str | None = Field(default=None, description="why this case is worth running")
    preconditions: list[str] = Field(default_factory=list)
    steps: list[Step] = Field(default_factory=list)
    severity: Severity = Severity.S2
    rubric_ref: str | None = None
    script_ref: str | None = None
    status: CaseStatus = CaseStatus.PROPOSED

    def model_post_init(self, _context: object) -> None:
        if not self.id:
            object.__setattr__(self, "id", self.compute_id())

    def compute_id(self) -> str:
        payload = {
            "project": self.project,
            "flow_id": self.flow_id,
            "case_class": str(self.case_class),
            "steps": [s.model_dump(mode="json") for s in self.steps],
        }
        return content_id("case", payload)

    def with_fixed_step(self, order: int, fix: AgentFix) -> Case:
        """A new `Case` with the step at `order` replaced by `fix`. Content-addressed,
        so the same fix applied twice never produces two rows (`ProjectStore.add_case`)."""
        new_steps = [
            Step(order=order, action=fix.action, target=fix.target, value=fix.value,
                 expected=s.expected, source_ref=s.source_ref, note=f"agent fix: {fix.reasoning}")
            if s.order == order else s
            for s in self.steps
        ]
        return Case(
            project=self.project, flow_id=self.flow_id, kind=self.kind,
            case_class=self.case_class, title=self.title, rationale=self.rationale,
            preconditions=self.preconditions, steps=new_steps, severity=self.severity,
            rubric_ref=self.rubric_ref, script_ref=self.script_ref, status=self.status,
        )


class AgentFix(BaseModel):
    """The agent's proposed correction for one failing step."""

    model_config = ConfigDict(extra="forbid")

    action: Action
    target: str
    value: str | None = None
    reasoning: str = Field(min_length=1, description="why this should fix the observed error")


class Script(Artifact):
    """A durable Playwright script produced once an agent gets a case working.

    The point of the whole execution model: after the first successful agent
    run, a case costs zero tokens to re-run.
    """

    id: str = ""
    case_id: str
    path: str = Field(description="repo-relative path under projects/<slug>/scripts/")
    generated_by: str = Field(description="provider id, or 'human'")
    iterations: int = Field(default=1, description="agent attempts before it worked")
    stable_runs: int = Field(default=0, description="consecutive passes since last edit")

    def model_post_init(self, _context: object) -> None:
        if not self.id:
            payload = {"case": self.case_id, "p": self.path}
            object.__setattr__(self, "id", content_id("scr", payload))
