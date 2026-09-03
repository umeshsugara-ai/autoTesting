"""Canonical data models. Every shape in the system is defined here, once.

If code anywhere else declares a dict shape, a dataclass, or a TypedDict for a
domain object, that is a bug — import from here instead.
"""

from autotester.schema.base import SCHEMA_VERSION, Artifact, Provenance
from autotester.schema.bench import BenchCorpus, BenchTrial, Finding, SeededBug
from autotester.schema.case import Case, Script
from autotester.schema.coverage import CoverageGap, VideoRequest
from autotester.schema.flowspec import (
    Conflict,
    ExpectedState,
    FieldConstraints,
    Flow,
    FlowSpec,
    InputField,
    Review,
    Screen,
    SourceRef,
    Step,
)
from autotester.schema.ledger import FeatureEvent, RelitigationVerdict
from autotester.schema.project import Project, ProviderConfig, SecretRef, Source
from autotester.schema.run import Evidence, ProviderUsage, RawResult, Run
from autotester.schema.verdict import Criterion, Failure, Rubric, Verdict

__all__ = [
    "SCHEMA_VERSION",
    "Artifact",
    "BenchCorpus",
    "BenchTrial",
    "Case",
    "Conflict",
    "CoverageGap",
    "Criterion",
    "Evidence",
    "ExpectedState",
    "Failure",
    "FeatureEvent",
    "FieldConstraints",
    "Finding",
    "Flow",
    "FlowSpec",
    "InputField",
    "Project",
    "Provenance",
    "ProviderConfig",
    "ProviderUsage",
    "RawResult",
    "RelitigationVerdict",
    "Review",
    "Rubric",
    "Run",
    "Screen",
    "Script",
    "SecretRef",
    "SeededBug",
    "Source",
    "SourceRef",
    "Step",
    "Verdict",
    "VideoRequest",
]
