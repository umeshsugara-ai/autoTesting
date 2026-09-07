"""`core.urls.url_template` — the shared identity input for both Track A's
ingest (`Screen.url_pattern`) and Track B's screen identity (`ScreenNode`).
"""

from __future__ import annotations

from autotester.core.urls import url_template


def test_numeric_segment_is_templated() -> None:
    assert url_template("/students/1/") == "/students/{id}"
    assert url_template("/students/42") == "/students/{id}"


def test_uuid_and_ulid_segments_are_templated() -> None:
    assert url_template("/erp/batch/01J8Z1Q2R3S4T5V6W7X8Y9ZABC/edit") == "/erp/batch/{id}/edit"
    assert url_template("/items/550e8400-e29b-41d4-a716-446655440000") == "/items/{id}"


def test_hex_id_segment_is_templated() -> None:
    assert url_template("/objects/deadbeefcafef00d1234") == "/objects/{id}"


def test_date_segment_is_templated() -> None:
    assert url_template("/erp/reports/2026-09") == "/erp/reports/{date}"
    assert url_template("/erp/reports/2026-09-07") == "/erp/reports/{date}"


def test_non_id_shaped_segment_is_left_alone() -> None:
    assert url_template("/erp/p/me") == "/erp/p/me"


def test_query_and_fragment_are_stripped() -> None:
    assert url_template("/erp/students/123?tab=2#x") == "/erp/students/{id}"


def test_full_url_with_host_kept_by_default() -> None:
    result = url_template("https://www.vidysea.com/erp/students/123?tab=2#x")
    assert result == "www.vidysea.com/erp/students/{id}"


def test_keep_host_false_returns_path_only() -> None:
    result = url_template("https://www.vidysea.com/erp/students/123", keep_host=False)
    assert result == "/erp/students/{id}"


def test_root_path_stays_root() -> None:
    assert url_template("https://app.test/", keep_host=False) == "/"
    assert url_template("https://app.test", keep_host=False) == "/"


def test_repeated_slashes_are_collapsed() -> None:
    assert url_template("/erp//students//1", keep_host=False) == "/erp/students/{id}"


def test_idempotent_on_path_only_output() -> None:
    once = url_template("/students/1/", keep_host=False)
    twice = url_template(once, keep_host=False)
    assert once == twice == "/students/{id}"
