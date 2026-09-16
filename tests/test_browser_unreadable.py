"""What a reader CANNOT see — the false-positive half of the glyph detector.

Split from `test_browser_visual_order.py` (doctor's 300-line cap) along the seam
the module itself has: that file asks whether the detector sees what the DOM
hides — bidi overrides, zero-width interleaving, form-control values, reading
order. This one asks the opposite question, and it is a different kind of claim:
a box can be painted and show nothing, and reporting it costs the false-positive
rate that is a term in this product's north star.

AT-363 was six such constructs. AT-372 added a closed `<details>` and
`-webkit-text-security`. AT-373 and AT-379 are the two occasions when a fix for
these false positives manufactured a false NEGATIVE of the AT-355 shape instead
— text lost above the scroll fold, and text lost below the fold of a scrollable
pane. Every test here that asserts something is not reported is paired with a
positive control on the same page.
"""

from __future__ import annotations

import pytest

from autotester.browser.observe import visual_text

SECRET = "ZEBRA_QUILT_APIKEY_31"


# -- AT-363: a box painted is not a thing seen --------------------------------

UNREADABLE = {
    "opacity-zero": "OPACITY_SENTINEL_11",
    "transparent-colour": "TRANSPARENT_SENTINEL_22",
    "text-indent-offscreen": "INDENT_SENTINEL_33",
    "absolute-offscreen": "OFFSCREEN_SENTINEL_44",
    "overflow-clipped": "CLIPPED_SENTINEL_55",
    "opacity-zero-ancestor": "NESTED_SENTINEL_66",
    "closed-details": "DETAILSBODY_SENTINEL_77",
}
"""One sentinel per case, deliberately. A shared constant is what made an
earlier test in this file vacuous — every case could be satisfied by a
different one."""


@pytest.mark.parametrize("label", sorted(UNREADABLE))
def test_text_a_reader_cannot_see_is_not_reported(page_factory, label: str) -> None:
    """AT-363. Reporting these would be the DOM-order error pointed the other
    way: the module claims to return what a reader sees, and each of these
    paints a box while showing nothing. False-positive rate is a term in this
    product's north star, so a detector that cries leak on invisible text costs
    the metric it exists to protect."""
    page, visit = page_factory
    visit("unreadable.html")

    seen = visual_text(page)
    assert UNREADABLE[label] not in seen, seen
    # The positive control lives on the same page: if this is missing, the
    # assertion above passed because the detector saw nothing at all.
    assert "Quarterly report" in seen, seen


def test_a_placeholder_is_reported_because_it_renders(page_factory) -> None:
    """AT-362: an empty control shows its placeholder, and a reader reads it."""
    page, visit = page_factory
    visit("controls.html")

    assert "PLACEHOLDER_SENTINEL_88" in visual_text(page)


def test_a_password_field_is_reported_as_the_bullets_it_shows(page_factory) -> None:
    """AT-363, and the sharpest case in this file. The screen shows bullets, so
    bullets are what a reader sees. Reporting the value would put a credential
    in CLEARTEXT into an observation string — inside the instrument built to
    catch credentials rendering in plain type."""
    page, visit = page_factory
    visit("controls.html")

    seen = visual_text(page)
    assert SECRET not in seen, seen
    assert "•" * len(SECRET) in seen, seen


def test_a_masked_run_is_reported_as_the_bullets_it_shows(page_factory) -> None:
    """AT-372, and the password defect one CSS property to the left.

    `-webkit-text-security: disc` turns a run into bullets with no
    `type=password` anywhere — on a plain `<span>` as readily as on an input.
    The cycle-2 detector masked the one and returned the other in cleartext,
    which is the same class of error the password branch exists to prevent."""
    page, visit = page_factory
    visit("controls.html")

    seen = visual_text(page)
    assert "MASKEDSPAN_SENTINEL_99" not in seen, seen
    assert SECRET not in seen, seen  # the masked INPUT, same page
    # The positive control: the placeholder on this page is not masked, so a
    # detector that simply saw nothing cannot satisfy the two assertions above.
    assert "PLACEHOLDER_SENTINEL_88" in seen, seen


def test_the_result_does_not_depend_on_where_the_page_is_scrolled(page_factory) -> None:
    """AT-373 — a false NEGATIVE manufactured by the fix for the false positives.

    A client rect is viewport-relative. The first version of the off-left rule
    tested `rect.right <= 0` against the viewport, so on a scrolled page
    everything above the fold tested as unreachable and silently vanished: a
    credential rendering in plain type while this returns a clean string, which
    is the AT-355 shape the whole module exists to catch. The next unit wires
    this into a crawl that scrolls, so it would have shipped straight into the
    one caller that triggers it.

    Equality is the assertion, not a substring: it pins that NOTHING moves in
    or out of the result as the page scrolls."""
    page, visit = page_factory
    visit("unreadable.html")

    at_top = visual_text(page)
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    assert page.evaluate("window.scrollY") > 0, "fixture is not taller than the viewport"
    at_bottom = visual_text(page)

    assert at_top == at_bottom
    assert "Quarterly report" in at_bottom, at_bottom


def test_text_below_the_fold_of_a_scrollable_pane_is_reported(page_factory) -> None:
    """AT-379, and the SECOND time in this module that a fix for false positives
    manufactured a false negative of the AT-355 shape.

    The module's rule is reachability — "further down or right can be scrolled
    to, so those stay" — and a reader can scroll an `overflow:auto` pane and
    read every line of it. Treating the pane's box as a hard clip meant a
    credential below the fold of a scrollable pane returned a clean string.

    The boundary is asserted on the same page and in the same breath, because a
    fix that reports everything would satisfy the first assertion alone:
    `overflow:hidden` with no scroll mechanism really does hide its second line,
    and it must stay dropped."""
    page, visit = page_factory
    visit("unreadable.html")

    seen = visual_text(page)

    assert "SCROLLPANE_TOP_SENTINEL_A1" in seen, seen
    assert "SCROLLPANE_BELOW_SENTINEL_A2" in seen, seen
    assert "HIDDENPANE_TOP_SENTINEL_B1" in seen, seen
    assert "HIDDENPANE_BELOW_SENTINEL_B2" not in seen, seen
