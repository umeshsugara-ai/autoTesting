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

from autotester.browser.observe import visual_text

SECRET = "ZEBRA_QUILT_APIKEY_31"
CSS_SECRET = "MARIGOLD_LEDGER_KEY_77"
"""A distinct sentinel for the CSS-override field.

It had `SECRET` at first, which made the test VACUOUS: three other
fields on that page also render `SECRET`, so `SECRET in visual_text`
was satisfied whatever the CSS field did. The mutation run caught it --
dropping `unicode-bidi` from the mirror left that test passing and broke
a different one. A per-case sentinel is what makes the assertion about
the case it names."""


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


def test_a_secret_in_a_form_control_value_is_seen(page_factory) -> None:
    """AT-361, filed by a checker while this unit was in flight.

    A form control's value is not a text node, so a `TreeWalker(SHOW_TEXT)`
    detector is structurally blind to it — and a case title renders ONLY inside
    `input[name=title]`, the single field U8 is written about. The detector
    would have returned a clean string for that page whatever the field held."""
    page, visit = page_factory
    visit("inputs.html")

    assert SECRET not in page.inner_text("body")
    assert SECRET in visual_text(page)


def test_a_direction_override_inside_a_form_control_is_seen_in_reading_order(
    page_factory,
) -> None:
    """The reason the value is MIRRORED and measured rather than just read off
    `control.value`. Reading the property would report the STORED order, which
    is the reversed string — the same blindness as `innerText`, one element
    deeper. The mirror reorders exactly as the control does."""
    page, visit = page_factory
    visit("inputs.html")

    stored = page.input_value("input[name=reversed]")
    assert SECRET not in stored, stored  # stored order hides it

    # Twice: once from the plain field, once from the reversed one rendered
    # forwards. Counting pins that the override field really was read, rather
    # than the plain field alone satisfying a substring check.
    seen = visual_text(page)
    # Twice: the plain field and the field reversed by an override CHARACTER.
    # The CSS-reversed field carries its own sentinel, so it cannot stand in
    # for either of these.
    assert seen.count(SECRET) == 2, seen


def test_reversal_forced_by_css_alone_is_seen(page_factory) -> None:
    """`unicode-bidi: bidi-override` reverses rendering with NO override
    character in the value, so nothing in the stored string is suspicious. The
    mirror reproduces it only because it copies the control's computed
    `unicode-bidi`; a mirror that copied only the font would render the value
    forwards and report the reverse."""
    page, visit = page_factory
    visit("inputs.html")

    stored = page.input_value("input[name=cssrev]")
    assert CSS_SECRET not in stored, stored

    assert CSS_SECRET in visual_text(page)


def test_measuring_the_page_leaves_it_exactly_as_it_was(page_factory) -> None:
    """The detector writes to the page — one offscreen span per form control —
    and that is the only place it does. If a span is left behind, the next
    measurement reads it as if it were content, so the page grows every time it
    is observed. Idempotence is the property that catches it."""
    page, visit = page_factory
    visit("inputs.html")

    first = visual_text(page)
    second = visual_text(page)

    assert first == second
    assert page.eval_on_selector_all("body > span", "els => els.length") == 0


def test_the_first_call_on_a_content_visibility_subtree_drops_no_glyph(page_factory) -> None:
    """AT-410: a first-glyph drop in the SHIPPING detector, not a fixture quirk.

    `content-visibility:auto` lets the browser skip rendering an off-screen
    subtree. The first `Range.getBoundingClientRect()` inside it returns all
    zeros, the zero-width guard dropped that glyph, and the query itself forces
    layout. So every LATER measurement is right. That is why the maker who first
    saw this (AT-398) re-measured, found a real rect, and could not see a cause.

    **The assertion must be on the FIRST call of a FRESH page.** Callers call
    once, and a second call passes on the unfixed detector. `visit()` navigates,
    so each test starts from a page on which nothing has been measured.

    The second line and the control are asserted too. Without them, a "fix" that
    dropped the whole subtree would satisfy nothing, but one that reported only
    the control would look fine on a hurried read.
    """
    page, visit = page_factory
    visit("cvauto.html")

    first = visual_text(page)

    assert "CVAUTO_SENTINEL_91" in first, first
    assert "CVAUTO_SECOND_92" in first, first
    assert "Quarterly report" in first, first
