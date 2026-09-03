"""A test case — one falsifiable claim about the product, plus how to check it."""

from __future__ import annotations

from pydantic import Field

from autotester.core.ids import content_id
from autotester.schema.base import Artifact
from autotester.schema.enums import CaseClass, CaseKind, CaseStatus, Severity
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
