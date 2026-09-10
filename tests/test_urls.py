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


# -- AT-287: one canonical stored shape, because no parser can infer host-ness --

def test_a_path_shaped_pattern_survives_re_templating_unchanged() -> None:
    """The invariant coverage actually relies on. `Screen.url_pattern` is stored
    host-LESS by every producer, and re-templating such a value is a no-op — so
    a stored pattern and a freshly observed URL reduce to the same identity."""
    for url in ("https://demo.test/students/42", "https://demo.test/", "/reports/new",
                "http://localhost/students/1"):
        stored = url_template(url, keep_host=False)
        assert url_template(stored, keep_host=False) == stored, url
        assert stored.startswith("/"), stored


def test_a_video_pattern_and_a_fresh_url_agree_on_the_path() -> None:
    """What ingest stores and what a run observes must reduce to the same thing,
    or the screen is invisible to coverage (AT-287)."""
    stored = url_template("https://demo.test/students/42", keep_host=False)
    observed = url_template("https://demo.test/students/99", keep_host=False)

    assert stored == observed == "/students/{id}"


def test_host_ful_output_is_documented_as_NOT_re_templatable() -> None:
    """Pinned deliberately, because this asymmetry is the whole reason
    url_pattern is stored host-less. `urlsplit("demo.test/x")` has no "//", so
    the host becomes a path segment. A test that hid this would let a future
    producer store host-ful again and re-introduce AT-287."""
    host_ful = url_template("https://demo.test/students/42")

    assert host_ful == "demo.test/students/{id}"
    assert url_template(host_ful, keep_host=False) == "/demo.test/students/{id}"


def test_no_path_segment_is_ever_swallowed() -> None:
    """The first fix for AT-287 guessed host-ness from the string, which silently
    DELETED a dotted first segment: "settings.json" became "/" and "v1.2/foo"
    became "/foo". `settings.json` and `example.com` are the same shape, so the
    guess is unwinnable in principle — hence one canonical shape instead."""
    assert url_template("settings.json", keep_host=False) == "/settings.json"
    assert url_template("sitemap.xml", keep_host=False) == "/sitemap.xml"
    assert url_template("v1.2/foo", keep_host=False) == "/v1.2/foo"
    assert url_template("reports/new", keep_host=False) == "/reports/new"
