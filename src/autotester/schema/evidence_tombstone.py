"""Sidecar tag for a unit's evidence spec whose `kills` node-ids moved out from
under it.

`qa/evidence/<slug>/mutations.json` is a unit's mutation-testing evidence
(`scripts/mutation_check.py`). A LATER unit sometimes splits or renames the test
file its `kills` node-ids name; the spec's bytes never change, but the node-ids
stop resolving. Gate `at516-evidence-spec-splitting-policy` asked whether that
is acceptable history or a defect a check should catch. Umesh answered (c)
(D-048, 2026-09-26): the spec stays byte-intact, and a sidecar file next to it
says where the test actually lives now -- so a check can tell "stale on
purpose" from "stale because a test quietly vanished". This module never edits
`mutations.json`; only `ledger/evidence_specs.py` reads this shape.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EvidenceTombstoneEntry(BaseModel):
    """One `kills` node-id, named by file + bare function name (no parametrize
    suffix -- every parameter id of a moved parametrized test shares one entry),
    that no longer resolves where the spec names it, and where it resolves now.

    Both ids are always `file::function`, never a bare name: a bare `kills`
    entry that genuinely still resolves is resolved against the spec's own
    `tests` scope and never reaches this model at all (`ledger/evidence_specs.py`
    `check_stale_evidence_specs`); requiring the full path here removes the one
    ambiguity (which file?) a bare name would otherwise reopen in the tag itself.
    """

    model_config = ConfigDict(extra="forbid")

    old_nodeid: str = Field(description="file::function as the mutations.json spec names it")
    moved_to: str = Field(description="file::function where the same test lives now")
    moved_by_unit: str = Field(description="the unit slug whose split or rename moved the test")
    note: str = Field(default="stale on purpose, test moved")

    @field_validator("old_nodeid", "moved_to")
    @classmethod
    def _must_be_path_qualified(cls, value: str) -> str:
        if "::" not in value:
            raise ValueError(f"{value!r} must be 'file::function', not a bare name")
        return value


class EvidenceTombstone(BaseModel):
    """`qa/evidence/<slug>/mutations.stale.json` -- absent means untagged."""

    model_config = ConfigDict(extra="forbid")

    entries: list[EvidenceTombstoneEntry] = Field(default_factory=list)
