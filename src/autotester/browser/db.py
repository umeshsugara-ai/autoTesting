"""Read-only backend assertions against MongoDB. Contract: qa/contracts/db-assert.md.

Production Mongo is read-only **by construction**, not by convention:
`ReadOnlyCollection` exposes only `find`/`find_one`/`count_documents` — it has
no `insert_one`, `update_one`, `delete_one`, or `drop` method, so a caller
cannot mutate production data even by a typo. `PATHLYNKS_MONGO_URI` is a
`SecretRef` like any other credential; a document's contents pass through the
project's `Redactor` before becoming `Evidence`, exactly like a screenshot or
a DOM string.
"""

from __future__ import annotations

from typing import Any

from autotester.core.redact import Redactor
from autotester.schema.enums import EvidenceKind
from autotester.schema.run import Evidence


class ReadOnlyCollection:
    """Wraps a pymongo `Collection`, exposing only read operations."""

    def __init__(self, collection: Any) -> None:
        self._collection = collection

    def find(self, query: dict[str, Any] | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        return list(self._collection.find(query or {}, **kwargs))

    def find_one(self, query: dict[str, Any] | None = None, **kwargs: Any) -> dict[str, Any] | None:
        return self._collection.find_one(query or {}, **kwargs)

    def count_documents(self, query: dict[str, Any] | None = None) -> int:
        return self._collection.count_documents(query or {})


def connect_read_only(uri: str, db_name: str, collection_name: str) -> ReadOnlyCollection:
    """Open a read-only handle. `uri` carries credentials — never log or store it."""
    from pymongo import MongoClient

    client: Any = MongoClient(uri)
    return ReadOnlyCollection(client[db_name][collection_name])


def assert_document(
    collection: ReadOnlyCollection,
    query: dict[str, Any],
    *,
    label: str,
    redactor: Redactor,
    step_order: int | None = None,
) -> Evidence:
    """Read-only `find_one`, recorded as redacted `EvidenceKind.DB` — an observation,
    not a judgement (grade.py decides whether the document being present/absent
    satisfies a case's rubric)."""
    doc = collection.find_one(query)
    summary = f"{label}: {'found' if doc is not None else 'not found'} for {query!r}"
    return Evidence(
        kind=EvidenceKind.DB, path=redactor.scrub(summary), step_order=step_order, label=label
    )
