"""AT-408 and AT-416 — both in `reachOf`/`isReachable` (visual_order_reach.js).

**AT-408** (`reachOf` stopped walking at the first one-axis scroller, so an
outer pane's offset was lost) already has dedicated coverage:
`test_browser_unreadable.py::test_a_scrolled_pane_inside_a_scrolled_pane_loses_nothing`
uses `#outer`/`#inner`, both `overflow:auto`, both scrolled — the exact shape
this unit was asked to reproduce. Duplicating it here would be the same
concept in two places (a design-rule violation); it is re-run as part of this
unit's verification instead of copied. `test_browser_scroll_invariance.py`'s
generated corpus also covers every `auto`-only nesting up to depth 3.

**AT-416** is new here. `reachOf`'s running clip intersection (added to close
AT-408/AT-393 together) tested the glyph's CURRENT, scroll-dependent rect
against a clip contributed by an ancestor OUTSIDE the scroller — so the
verdict flipped with the pane's own scroll position instead of asking whether
a reader can reach it AT ALL. `qa/contracts/ui.md` U14(a) charges exactly this
as the scroll-invariance floor: the SET of glyphs `visual_text` reports must
not depend on where anything scrollable currently sits. `at416_card.html`
reproduces the checker's own P6/P7 probes — an `overflow:hidden` card (the
"ordinary shape every real UI has", per the checker's own note) wrapping a
genuinely overflowing `overflow:auto` body — and every assertion below is
checked BOTH before and after actually scrolling the body, which is the one
axis AT-408's existing tests do not exercise for this shape.
"""

from __future__ import annotations

from autotester.browser.observe import visual_text

CONTROL = "CONTROL_AT416_ALWAYS_VISIBLE"


def _scroll_to_end(page, selector: str) -> None:
    page.eval_on_selector(selector, "el => { el.scrollTop = el.scrollHeight; }")
    moved = page.eval_on_selector(selector, "el => el.scrollTop")
    assert moved > 0, f"{selector} did not scroll"


def test_at416_below_the_fold_is_reported_before_any_scroll(page_factory) -> None:
    """The false-negative half of AT-416: AT REST (`scrollTop` still 0), a line
    below the card's visible band must already be reported reachable — a
    reader scrolling the pane is what makes it reachable, not what makes the
    DETECTOR say so. Failing this is exactly the bug: the pre-fix code only
    reported it once actually scrolled."""
    page, visit = page_factory
    visit("at416_card.html")

    assert page.eval_on_selector("#at416_body", "el => el.scrollTop") == 0
    assert page.eval_on_selector("#at416_body2", "el => el.scrollTop") == 0

    seen = visual_text(page)
    assert CONTROL in seen, seen
    assert "CARD_TOP_SENTINEL" in seen, seen
    assert "CARD_BELOW_FOLD_SENTINEL" in seen, seen
    assert "CARD2_TOP_SENTINEL" in seen, seen
    assert "CARD2_BELOW_FOLD_SENTINEL" in seen, seen
    # Negative control, same page: a card wrapping a pane that does NOT
    # overflow (AT-393's shape, not AT-416's) is still a real boundary.
    assert "CARD3_TOP_SENTINEL" in seen, seen
    assert "CARD3_HIDDEN_SENTINEL" not in seen, seen


def test_at416_below_the_fold_is_still_reported_after_scrolling_the_pane(page_factory) -> None:
    """The scroll-invariance half: scroll the body panes to their end (the
    checker's own probe state) and assert the SAME set is reported — U14(a).
    A detector that only passes one of these two tests, never both, is the
    exact scroll-dependent bug AT-416 filed."""
    page, visit = page_factory
    visit("at416_card.html")

    before = visual_text(page)

    _scroll_to_end(page, "#at416_body")
    _scroll_to_end(page, "#at416_body2")
    page.evaluate("() => { document.body.offsetHeight; }")
    page.wait_for_timeout(30)

    seen = visual_text(page)
    assert sorted(seen) == sorted(before), "the reported glyph set changed when scrolled"
    assert CONTROL in seen, seen
    assert "CARD_TOP_SENTINEL" in seen, seen
    assert "CARD_BELOW_FOLD_SENTINEL" in seen, seen
    assert "CARD2_TOP_SENTINEL" in seen, seen
    assert "CARD2_BELOW_FOLD_SENTINEL" in seen, seen
    assert "CARD3_HIDDEN_SENTINEL" not in seen, seen
