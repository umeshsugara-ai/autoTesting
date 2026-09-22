"""The crawl's consent pre-flight (D-018 gate 2) — split from `explore.py`
for the 300-line cap (AT-507/AT-460: the stage was at its line budget).

One job: answer "may this crawl start" BEFORE a browser opens, and raise
`ApprovalRequired` naming exactly what is missing. `run_crawl` and both
production pre-flights (CLI, UI) call `require_consent`; nothing else decides
consent. X10-b condition 3 (AT-535) lives here too: a synthetic-typing run
against an approval that says `production: true` is refused before the
browser opens — D-029's four conditions are enforced where the run begins,
not discovered mid-crawl.
"""

from __future__ import annotations

from autotester.core.consent import require_approval
from autotester.schema.crawl import CrawlBounds, SafetyPolicy
from autotester.schema.enums import ApprovalKind
from autotester.schema.project import Project
from autotester.store.project_store import ProjectStore


def covering_approval(project: Project, store: ProjectStore, bounds: CrawlBounds):
    """The RunApproval covering this crawl, or `ApprovalRequired`."""
    return require_approval(
        store.list_approvals(), project=project.slug, kind=ApprovalKind.CRAWL,
        target=project.base_url, actions=bounds.max_actions,
        wall_clock_s=bounds.wall_clock_s,
    )


def require_consent(project: Project, store: ProjectStore, bounds: CrawlBounds,
                    policy: SafetyPolicy | None = None) -> None:
    """D-018 gate 2, plus X10-b condition 3 (AT-535): a synthetic-typing crawl
    must be covered by an approval whose target is NOT production — typing on
    a production system is the one thing D-029's four conditions exist to
    prevent. Raises `ApprovalRequired` naming the approval's id.

    `policy` is optional so every existing caller stays valid; `run_crawl`
    always passes the run's policy, so the runtime seam holds even when a
    pre-flight caller forgets to."""
    approval = covering_approval(project, store, bounds)
    if policy is not None and policy.synthetic_typing and approval.production:
        from autotester.core.consent import ApprovalRequired

        raise ApprovalRequired(
            f"{approval.id}: synthetic typing (X10-b) is refused against a "
            "production target — grant a dev-environment approval "
            "(production: false) instead"
        )