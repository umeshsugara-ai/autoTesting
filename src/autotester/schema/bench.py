"""The north star, made measurable: human expert tester vs AutoTester.

Both participants get the same material pack and the same seeded build. The
scorecard is computed from these records — never written by hand.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from autotester.schema.base import Artifact
from autotester.schema.enums import Participant, Severity


class SeededBug(BaseModel):
    """A deliberately introduced defect with known ground truth."""

    model_config = ConfigDict(extra="forbid")

    id: str
    description: str
    severity: Severity = Severity.S2
    location: str = Field(description="route/screen where it manifests")
    detect_hint: str = Field(description="what a correct finding must state")


class Finding(BaseModel):
    """One reported defect from a participant, matched against ground truth."""

    model_config = ConfigDict(extra="forbid")

    text: str
    matched_bug_id: str | None = Field(default=None, description="None means false positive")
    evidence_refs: list[str] = Field(default_factory=list)
    reported_at_s: float | None = None


class BenchCorpus(Artifact):
    """A build with known seeded defects and the material pack given to testers."""

    id: str
    app: str
    build_ref: str
    seeded_bugs: list[SeededBug] = Field(default_factory=list)
    material_refs: list[str] = Field(default_factory=list, description="videos/docs handed over")


class BenchTrial(Artifact):
    """One participant's attempt on one corpus."""

    id: str
    corpus_id: str
    participant: Participant
    participant_label: str = ""
    findings: list[Finding] = Field(default_factory=list)
    duration_s: float = 0.0

    def score(self, corpus: BenchCorpus) -> dict[str, float]:
        """Detection rate, false-positive rate, and severity-weighted recall."""
        seeded = {b.id: b for b in corpus.seeded_bugs}
        matched = {f.matched_bug_id for f in self.findings if f.matched_bug_id in seeded}
        false_positives = [f for f in self.findings if f.matched_bug_id is None]
        weights = {Severity.S1: 3.0, Severity.S2: 2.0, Severity.S3: 1.0}
        total_weight = sum(weights[b.severity] for b in corpus.seeded_bugs) or 1.0
        found_weight = sum(weights[seeded[b].severity] for b in matched)
        reported = len(self.findings) or 1
        return {
            "detected": len(matched),
            "seeded": len(seeded),
            "detection_rate": len(matched) / (len(seeded) or 1),
            "false_positives": len(false_positives),
            "false_positive_rate": len(false_positives) / reported,
            "severity_weighted_recall": found_weight / total_weight,
            "duration_s": self.duration_s,
        }
