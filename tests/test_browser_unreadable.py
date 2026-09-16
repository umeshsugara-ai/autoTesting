"""What a reader CANNOT see — the false-positive half of the glyph detector.

Split from `test_browser_visual_order.py` (doctor's 300-line cap) along the seam
the module itself has: that file asks whether the detector sees what the DOM
hides — bidi overrides, zero-width interleaving, form-control values, reading
order. This one asks the opposite question, and it is a different kind of claim:
a box can be painted and show nothing, and reporting it costs the false-positive
rate that is a term in this product's north star.

AT-363 was six such constructs. AT-372 added a closed `<details>` and
`-webkit-text-security`. AT-373, AT-379 and AT-392 are the three occasions when a fix for
these false positives manufactured a false NEGATIVE of the AT-355 shape instead
— text lost above the window's scroll fold, text lost below the fold of a
scrollable pane, and text lost before the offset of a pane already scrolled.
All three are the same mistake: asking whether a reader can SEE something and
forgetting to ask whether they can REACH it.

Every test here that asserts something is not reported is paired with a positive
control on the same page.
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


def test_a_pane_the_reader_already_scrolled_loses_nothing(page_factory) -> None:
    """AT-392 — the other half of AT-379, and the THIRD time this one line has
    been wrong in the same direction.

    A pane scrolled away from its origin pushes its earlier lines to negative
    viewport coordinates, and the document-edge rule dropped them because it
    added only `window.scrollX/scrollY`. The reader scrolls the pane back and
    reads them, so they are reachable. Each of AT-373, AT-379 and AT-392 was a
    fix for false POSITIVES that manufactured a false NEGATIVE of the AT-355
    shape, by asking whether a reader can SEE something and forgetting to ask
    whether they can REACH it.

    It uses its own SHORT page, and that is load-bearing rather than tidiness:
    on the tall `unreadable.html` the window itself scrolls ~1600px, the
    document-edge rule adds `window.scrollY`, and every glyph then tests as
    reachable on the window's offset alone. The mutation that removes the pane's
    contribution SURVIVED twice against that fixture — a test that looked like it
    covered this and did not. The pane's own offset is only isolated when the
    window contributes nothing.

    The assertion is that the same CHARACTERS come back, not the same string.
    When the window scrolls, everything moves together and reading order is
    preserved, so that test asserts equality. When a PANE scrolls, its content
    genuinely moves relative to everything outside it, so the visual order really
    does change and a detector reporting visual order must report the new one.
    Sorting both sides pins the only thing that must not change: nothing dropped,
    nothing invented.
    """
    page, visit = page_factory
    visit("scrolled_panes.html")
    assert page.evaluate("window.scrollY") == 0, "fixture must not scroll the window"

    at_origin = visual_text(page)

    page.eval_on_selector("#pane", "el => { el.scrollTop = el.scrollHeight; }")
    page.eval_on_selector("#hpane", "el => { el.scrollLeft = el.scrollWidth; }")
    assert page.eval_on_selector("#pane", "el => el.scrollTop") > 0, "pane did not scroll"
    assert page.eval_on_selector("#hpane", "el => el.scrollLeft") > 0, "hpane did not scroll"

    # AT-412: the `scrollY == 0` guard above catches a window ALREADY scrolled,
    # and the checker measured that it does NOT catch the other drift — a spacer
    # added above the panes makes the window scroll, the document-edge rule is
    # satisfied by the window's own offset, and the mutation survives in silence.
    # So the precondition is asserted directly: the pane's first line must
    # actually reach a NEGATIVE viewport coordinate, which is the only state in
    # which the accumulated-offset rule is load-bearing at all.
    pane_bottom = page.eval_on_selector("#pane p", "el => el.getBoundingClientRect().bottom")
    assert pane_bottom < 0, f"pane content never went negative ({pane_bottom})"

    scrolled = visual_text(page)
    assert sorted(scrolled) == sorted(at_origin)
    # Named explicitly too, so a failure says WHICH pane lost its text rather
    # than only that two sorted strings differ.
    for sentinel in ("SCROLLED_TOP_SENTINEL_D1", "SCROLLED_BOTTOM_SENTINEL_D2",
                     "SCROLLED_LEFT_SENTINEL_D3", "SCROLLED_RIGHT_SENTINEL_D4"):
        assert sentinel in scrolled, (sentinel, scrolled)


def test_a_scrolled_pane_inside_a_scrolled_pane_loses_nothing(page_factory) -> None:
    """AT-408 — the FOURTH occurrence of the pattern this module now documents
    at the line itself.

    `reachOf` stopped walking at the first ancestor that scrolled on ONE axis,
    which is what an ordinary `overflow:auto` pane is. So a pane inside a
    scrolled pane never saw the outer offset, and everything above the outer
    scroll position silently vanished — in the module about to be wired into a
    crawl that scrolls panes.

    The offsets must ACCUMULATE. A reader scrolls both panes back and reads
    every line of both."""
    page, visit = page_factory
    visit("scrolled_panes.html")

    at_origin = visual_text(page)
    assert "INNER_TOP_SENTINEL_E2" in at_origin, at_origin

    page.eval_on_selector("#outer", "el => { el.scrollTop = el.scrollHeight; }")
    page.eval_on_selector("#inner", "el => { el.scrollTop = el.scrollHeight; }")
    assert page.eval_on_selector("#outer", "el => el.scrollTop") > 0, "outer did not scroll"
    assert page.eval_on_selector("#inner", "el => el.scrollTop") > 0, "inner did not scroll"
    # The precondition, asserted rather than assumed: only a negative viewport
    # coordinate exercises the accumulated-offset rule.
    inner_bottom = page.eval_on_selector("#inner p", "el => el.getBoundingClientRect().bottom")
    assert inner_bottom < 0, f"inner content never went negative ({inner_bottom})"

    scrolled = visual_text(page)

    # Sorted-character equality is the whole assertion here, and a substring
    # check would be WRONG rather than merely weaker. Scrolling the outer pane
    # lands its own first line and the inner pane's on the same screen row, so
    # the detector interleaves them — `OINUNTEERR__TTOOPP...` — which is exactly
    # what a visual-order detector should do with two texts that overlap on
    # screen. Nothing is lost; the reading order genuinely changed. Asserting
    # `"INNER_TOP_SENTINEL_E2" in scrolled` would fail on correct behaviour.
    assert sorted(scrolled) == sorted(at_origin)
    # E3 sits alone on its row, so it survives as a substring and gives the
    # failure message something legible to point at.
    assert "INNER_BOTTOM_SENTINEL_E3" in scrolled, scrolled


def test_a_pane_inside_a_clipping_box_does_not_leak_past_it(page_factory) -> None:
    """AT-393 — the false positive cycle 1 of this unit introduced and then
    misdescribed as pre-existing.

    `reachOf` used to return at the first clipping ancestor, so an inner box's
    bounds were the whole answer and an outer `overflow:hidden` was never
    consulted. The inner box here does not overflow, so nothing can be scrolled
    and the outer 40px band is all a reader will ever see.

    The positive control is the inner box's own first line, on the same page and
    in the same band: without it, a detector that reported nothing would satisfy
    the negative assertion by itself."""
    page, visit = page_factory
    visit("scrolled_panes.html")

    seen = visual_text(page)

    assert "NESTCLIP_TOP_SENTINEL_F1" in seen, seen
    assert "NESTCLIP_BELOW_SENTINEL_F2" not in seen, seen

    # And the other direction, which needs a real INTERSECTION rather than
    # "keep the outermost box": here the OUTER box is 300px tall and would show
    # the line happily, and only the inner 30px box excludes it.
    assert "INNERCLIP_TOP_SENTINEL_G1" in seen, seen
    assert "INNERCLIP_BELOW_SENTINEL_G2" not in seen, seen
