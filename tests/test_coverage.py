"""COVERAGE stage. Contract: qa/contracts/coverage.md V1-V4."""

from __future__ import annotations

from pathlib import Path

from autotester.schema.enums import EvidenceKind, Outcome
from autotester.schema.flowspec import FlowSpec, Screen
from autotester.schema.run import Evidence, RawResult
from autotester.stages.coverage import diff_coverage, request_for
from autotester.store.project_store import ProjectStore


def make_spec(*url_patterns: str) -> FlowSpec:
    screens = [Screen(id=f"scr_{i}", name=f"screen {i}", url_pattern=p)
               for i, p in enumerate(url_patterns)]
    return FlowSpec(project="pathlynks", screens=screens)


def make_result(case_id: str, *urls: str) -> RawResult:
    evidence = [Evidence(kind=EvidenceKind.URL, path=u) for u in urls]
    return RawResult(case_id=case_id, outcome=Outcome.COMPLETED, evidence=evidence)


# -- V1 a known route produces no gap ----------------------------------------

def test_known_route_produces_no_gap() -> None:
    spec = make_spec("https://app.test/signin", "https://app.test/dashboard")
    results = [make_result("case_1", "https://app.test/dashboard")]

    gaps = diff_coverage(spec, results)

    assert gaps == []


# -- V2 an unseen route produces exactly one gap -----------------------------

def test_unseen_route_produces_exactly_one_gap() -> None:
    spec = make_spec("https://app.test/signin")
    results = [make_result("case_1", "https://app.test/reports/new")]

    gaps = diff_coverage(spec, results)

    assert len(gaps) == 1
    assert gaps[0].subject == "/reports/new"
    assert gaps[0].project == "pathlynks"


def test_the_same_unseen_route_seen_by_two_cases_dedupes_to_one_gap() -> None:
    spec = make_spec("https://app.test/signin")
    results = [
        make_result("case_1", "https://app.test/reports/new"),
        make_result("case_2", "https://app.test/reports/new"),
    ]

    gaps = diff_coverage(spec, results)

    assert len(gaps) == 1


# -- redacted evidence is never mistaken for a route -------------------------

def test_redacted_evidence_string_is_not_treated_as_a_route() -> None:
    spec = make_spec("https://app.test/signin")
    results = [make_result("case_1", "[REDACTED]:PATHLYNKS_USER_LOGIN_URL")]

    gaps = diff_coverage(spec, results)

    assert gaps == []


# -- V3 exactly one VideoRequest per gap, deduped on re-diff -----------------

def test_request_for_names_the_gap(tmp_path: Path) -> None:
    spec = make_spec("https://app.test/signin")
    results = [make_result("case_1", "https://app.test/reports/new")]
    gap = diff_coverage(spec, results)[0]

    request = request_for(gap)

    assert request.gap_id == gap.id
    assert "/reports/new" in request.prompt


def test_add_request_is_idempotent(tmp_path: Path) -> None:
    store = ProjectStore("pathlynks", tmp_path)
    spec = make_spec("https://app.test/signin")
    results = [make_result("case_1", "https://app.test/reports/new")]
    gap = diff_coverage(spec, results)[0]
    request = request_for(gap)

    store.add_request(request)
    store.add_request(request)  # same gap, re-diffed later -> must not duplicate

    assert len(store.list_requests()) == 1
