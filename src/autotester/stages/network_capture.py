"""First-party network capture as evidence (T-170, NA1/NA2/NA4/NA5/NA6).

Turns `PageObserver`-buffered `(method, url, status)` responses into
`EvidenceKind.NETWORK` evidence -- one item per FIRST-PARTY response,
independent of status (NA1). Third-party/noise hosts are excluded by
reusing `explore_safety.classify_request` (X9, C3) rather than a second
classifier. Every URL passes through the caller's `Redactor` before it
becomes evidence (NA5, core-invariants C5). Pure data transform: no
browser, no provider (NA4), and nothing here assigns a verdict (NA2, C7) --
`stages/execute.py` (a run) and `stages/explore.py` (a crawl) both call
this, so the ONE capture mechanism (NA6) has ONE conversion too (C3).
"""

from __future__ import annotations

from autotester.core.redact import Redactor
from autotester.schema.crawl import SafetyPolicy
from autotester.schema.enums import EvidenceKind
from autotester.schema.project import Project
from autotester.schema.run import Evidence
from autotester.stages.explore_safety import classify_request


def first_party_evidence(
    responses: list[tuple[str, str, int]],
    project: Project,
    policy: SafetyPolicy,
    redactor: Redactor,
    *,
    step_order: int | None = None,
) -> list[Evidence]:
    """One `EvidenceKind.NETWORK` item per first-party `(method, url,
    status)` response in `responses`; third-party/noise hosts produce none."""
    items: list[Evidence] = []
    for method, url, status in responses:
        if classify_request(url, project, policy) != "first_party":
            continue
        items.append(Evidence(
            kind=EvidenceKind.NETWORK,
            path=redactor.scrub(f"{method} {url} -> {status}"),
            step_order=step_order,
            label="network",
        ))
    return items
