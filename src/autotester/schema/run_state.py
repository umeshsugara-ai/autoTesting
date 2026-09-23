"""RunState: the durable per-run ledger over the filestore's stage artifacts.

One job — record which entry path a run chose (learn vs explore) and how far
each stage got, so `stages/orchestrate.py::run_or_resume` can re-enter the first
non-done stage after an interruption without redoing completed work. The stage
outputs themselves live in the filestore (T-020); this is a thin
pointer-and-status ledger over them, not a second copy of their data.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from autotester.schema.base import utc_now


class StageName(StrEnum):
    """The pipeline stages a run drives, in canonical order.

    INGEST and DISCOVER are the two mutually-exclusive ENTRY stages — learn from
    teaching material, or bootstrap a bounded-BFS crawl from credentials. Every
    run then converges on MODEL (FlowSpec assembly) and continues down one line.
    """

    INGEST = "ingest"
    DISCOVER = "discover"
    MODEL = "model"
    EXPAND = "expand"
    EXECUTE = "execute"
    GRADE = "grade"
    REPORT = "report"


StageStatus = Literal["pending", "running", "done", "failed", "skipped"]
"""A checkpoint's lifecycle. `done`/`skipped` are terminal-good (never re-run);
`failed` is terminal-bad but re-enterable; `pending`/`running` are in-flight."""


class StageCheckpoint(BaseModel):
    """One stage's durable record within a run.

    `artifact_ref` points at the stage's persisted output — the proof it
    completed. A `failed` checkpoint always carries a non-empty `error` and
    never an `artifact_ref`: a stage is never marked done without its artifact.
    """

    model_config = ConfigDict(extra="forbid")

    stage: StageName
    status: StageStatus = "pending"
    artifact_ref: str | None = None
    error: str | None = None
    started: datetime | None = None
    finished: datetime | None = None


class RunState(BaseModel):
    """The ledger for one run, keyed by `run_id` (`OR5`: one run_id, one lineage).

    Persisted to `projects/<slug>/runs/<run_id>/state.json`. `mode` is chosen
    once and recorded with `mode_reason` (`OR1`); it is never re-decided on
    resume. The resume pointer is `next_pending()` — the first stage whose
    status is not `done`/`skipped`.
    """

    model_config = ConfigDict(extra="forbid")

    run_id: str
    project_slug: str
    mode: Literal["learn", "explore"]
    mode_reason: str
    stages: list[StageCheckpoint] = Field(default_factory=list)
    created: datetime = Field(default_factory=utc_now)
    updated: datetime = Field(default_factory=utc_now)

    def next_pending(self) -> StageCheckpoint | None:
        """The resume pointer: the first stage not yet `done`/`skipped`, or None
        when every stage is terminal-good."""
        return next(
            (c for c in self.stages if c.status not in ("done", "skipped")), None
        )

    def checkpoint(self, stage: StageName) -> StageCheckpoint | None:
        """The checkpoint for `stage`, or None if this run has no such stage
        (e.g. INGEST on an explore run)."""
        return next((c for c in self.stages if c.stage is stage), None)
