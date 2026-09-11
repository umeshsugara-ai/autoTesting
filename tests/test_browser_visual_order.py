"""One question: can this codebase see text a reader sees but the DOM hides?

AT-358. Every instrument in `browser/observe.py` read DOCUMENT order —
`innerText`, element names, the enumerated controls. A bidi override makes
document order and reading order disagree, and AT-355 exploited exactly that:
a credential stored backwards behind `U+202E` renders forwards, so every
DOM-order check called the page clean while a human could read the secret off
it in plain type. Three checker cycles missed it; a per-glyph measurement
caught it.

The detector is in `browser/`, not in a test helper, because reading other
people's rendered pages is what this product does.

**Every test here that asserts something is NOT visible is paired with a
planted positive control**, because a detector that always returns nothing
would pass every clean-page assertion in this file. That is the technique the
checkers used on this repo and it is the reason to trust a negative at all.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from autotester.browser.observe import visual_text

SITE = Path(__file__).resolve().parent / "fixtures" / "bidi_site"
SECRET = "ZEBRA_QUILT_APIKEY_31"


@pytest.fixture(scope="module")
def page_factory(serve_dir: Callable[[Path], str]):
    """A real Chromium page, per module — this file makes several visits."""
    playwright = pytest.importorskip("playwright.sync_api")
    base = serve_dir(SITE)
    try:
        runner = playwright.sync_playwright().start()
        browser = runner.chromium.launch(headless=True)
    except Exception as exc:  # browser binary missing on this machine
        pytest.skip(f"chromium unavailable: {type(exc).__name__}")
    page = browser.new_page()

    def visit(name: str) -> str:
        page.goto(f"{base}/{name}")
        page.wait_for_load_state("domcontentloaded")
        return name

    yield page, visit
    browser.close()
    runner.stop()


def test_the_detector_sees_a_plainly_rendered_secret(page_factory) -> None:
    """THE POSITIVE CONTROL. Run first and read first: every "not visible"
    assertion below is worthless unless this one passes."""
    page, visit = page_factory
    visit("plain.html")

    assert SECRET in visual_text(page)


def test_the_detector_reports_nothing_on_a_clean_page(page_factory) -> None:
    """The negative control: it does not simply find the secret everywhere."""
    page, visit = page_factory
    visit("clean.html")

    seen = visual_text(page)
    assert SECRET not in seen
    assert "Quarterly report" in seen, seen


def test_the_dom_calls_the_bidi_page_clean(page_factory) -> None:
    """The defect being instrumented, stated as a fact about the OLD tools.

    This is the assertion that makes the next one mean something: the page
    genuinely does hide the secret from `innerText`, so a DOM-order check has
    no way to see it."""
    page, visit = page_factory
    visit("hidden.html")

    assert SECRET not in page.inner_text("body")


def test_the_detector_sees_what_the_dom_hides(page_factory) -> None:
    """AT-355, caught by measurement instead of by reading the DOM."""
    page, visit = page_factory
    visit("hidden.html")

    assert SECRET in visual_text(page)


def test_a_zero_width_interleaved_secret_is_seen_as_it_renders(page_factory) -> None:
    """AT-345's shape, and the reason unpainted characters are dropped rather
    than kept.

    U+200B between every character paints nothing, so the page looks identical
    to `plain.html` — and `innerText` returns a string that no substring search
    for the secret will match. Keeping the zero-width characters in the result
    would reproduce exactly that blindness in the new instrument."""
    page, visit = page_factory
    visit("zerowidth.html")

    assert SECRET not in page.inner_text("body")
    assert SECRET in visual_text(page)


def test_text_that_occupies_layout_but_is_invisible_is_not_reported(page_factory) -> None:
    """The one filter that is NOT redundant with the width test, and finding
    that out took a measurement rather than an intuition.

    `display:none` text, `<script>` text and `<style>` text all report
    zero-width rects, so the width filter already drops them — a tag deny-list
    was dead code and is gone. `visibility:hidden` preserves layout, so its
    glyphs report a real width, and without this check the detector would
    report text nobody can see as text a reader saw. That is the same class of
    error as the DOM-order tools it replaces, pointed the other way."""
    page, visit = page_factory
    visit("invisible.html")

    seen = visual_text(page)
    assert SECRET not in seen, seen
    assert "Quarterly report" in seen, seen

