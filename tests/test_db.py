"""Read-only DB assertions. Contract: qa/contracts/db-assert.md D1-D5.

No test here opens a real socket to Mongo (D5) — a fake collection stands in
for pymongo's, same pattern as test_browser.py's FakePage.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

import pytest

from autotester.browser.db import ReadOnlyCollection, assert_document, connect_read_only
from autotester.core.redact import Redactor
from autotester.schema.enums import EvidenceKind

SECRET = "s3cr3t-session-token"


class FakeCollection:
    def __init__(self, docs: list[dict]) -> None:
        self.docs = docs
        self.find_one_calls: list[dict] = []

    def find(self, query: dict, **kwargs) -> list[dict]:
        return [d for d in self.docs if all(d.get(k) == v for k, v in query.items())]

    def find_one(self, query: dict, **kwargs) -> dict | None:
        self.find_one_calls.append(query)
        matches = self.find(query)
        return matches[0] if matches else None

    def count_documents(self, query: dict) -> int:
        return len(self.find(query))


# -- D1 read-only by construction --------------------------------------------

def test_read_only_collection_has_no_mutating_method() -> None:
    banned = ("insert", "update", "delete", "drop", "replace", "remove")
    members = [m for m in dir(ReadOnlyCollection) if not m.startswith("_")]
    assert members == ["count_documents", "find", "find_one"]
    for name in members:
        assert not any(word in name for word in banned)


def test_read_only_collection_delegates_reads() -> None:
    fake = FakeCollection([{"_id": 1, "email": "a@b.com"}, {"_id": 2, "email": "c@d.com"}])
    ro = ReadOnlyCollection(fake)

    assert ro.find_one({"_id": 1}) == {"_id": 1, "email": "a@b.com"}
    assert ro.count_documents({}) == 2
    assert len(ro.find({})) == 2


# -- D3 evidence is redacted before it becomes Evidence ----------------------

def test_assert_document_evidence_is_redacted() -> None:
    fake = FakeCollection([{"_id": "u1", "session_token": SECRET}])
    ro = ReadOnlyCollection(fake)
    redactor = Redactor({"SESSION_TOKEN": SECRET})

    ev = assert_document(ro, {"_id": "u1"}, label="user exists", redactor=redactor, step_order=3)

    assert ev.kind is EvidenceKind.DB
    assert "found" in ev.path
    assert SECRET not in ev.path
    assert ev.step_order == 3 and ev.label == "user exists"


def test_assert_document_not_found_is_evidence_not_an_exception() -> None:
    ro = ReadOnlyCollection(FakeCollection([]))
    redactor = Redactor({})

    ev = assert_document(ro, {"_id": "missing"}, label="user exists", redactor=redactor)

    assert "not found" in ev.path


# -- D2 the connection string is never logged --------------------------------

def test_connect_read_only_source_never_logs_the_uri() -> None:
    src = Path(__file__).resolve().parents[1] / "src" / "autotester" / "browser" / "db.py"
    text = src.read_text(encoding="utf-8")
    assert not re.search(r"print\(.*uri", text, re.IGNORECASE)
    assert "logging" not in text


# -- D5 a live connection is never made by the default suite -----------------

@pytest.mark.skipif(
    not os.environ.get("AUTOTESTER_LIVE_MONGO_TEST"),
    reason="live Mongo connection requires explicit opt-in (AUTOTESTER_LIVE_MONGO_TEST=1) "
    "per this project's standing rule: never aim at Pathlynks without per-use approval",
)
def test_connect_read_only_against_a_real_uri() -> None:
    uri = os.environ["PATHLYNKS_MONGO_URI"]
    ro = connect_read_only(uri, "pathlynks", "users")
    ro.count_documents({})  # only proves the read-only handle can actually read
