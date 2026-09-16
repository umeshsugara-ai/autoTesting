"""One property, generated shapes: scrolling must not change WHAT is reported.

AT-423. Five separate defects in `visual_order.js` — AT-373, AT-379, AT-392,
AT-408, AT-416 — were all the same mistake, and all five were found by a checker
driving a browser at a shape the maker had no fixture for. Across three fix
cycles every command the manifests listed stayed green while a real false
negative shipped each time: the suite, ruff, doctor, and the mutation specs.

The five share one property:

    the multiset of glyphs `visual_text` reports must not change when the window
    or ANY scrollable container is scrolled anywhere in its range.

A reader can scroll. Anything a scroll can bring into view is text a reader can
see, so a detector claiming to report what a reader sees cannot report a
different set before and after. Every one of the five was a scroll-invariance
failure; AT-379 was literally filed as `equal_before_after=False`.

Two deliberate choices:

**The scrolls are PERFORMED, not computed.** Computing offsets from
`getBoundingClientRect` is exactly the reasoning that got this wrong five times
in a row. This drives the browser and compares what came back.

**The shapes are GENERATED, not imagined.** `tests/fixtures/bidi_site/
scrolled_panes.html` already *is* the AT-416 shape — `overflow:hidden` wrapping
`overflow:auto` — and cannot exhibit the defect only because the inner box does
not overflow. The shape was on screen and the one parameterisation chosen proved
the opposite property. Enumerating the product removes the need for anyone to
guess which corner is the dangerous one.

**Honest limit: the property is ONE-SIDED.** A detector that reported every node
on the page would be perfectly scroll-invariant. It says nothing about false
positives, so it is a floor beneath the "text a reader cannot see is not
reported" assertions in `test_browser_unreadable.py`, never a replacement.
"""

from __future__ import annotations

import itertools
from collections.abc import Callable
from pathlib import Path

import pytest

from autotester.browser.observe import visual_text

OVERFLOWS = ("auto", "hidden")
DEPTHS = (1, 2, 3)


def _shapes() -> list[tuple[str, ...]]:
    """Every nesting of `overflow` values up to three deep.

    `visible` is left out on purpose: a box that does not clip cannot scroll
    either, so it adds pages without adding a state the detector treats
    differently. `scroll` behaves as `auto` once the content overflows, which it
    always does here by construction.
    """
    return [combo for depth in DEPTHS for combo in itertools.product(OVERFLOWS, repeat=depth)]


def _html(shape: tuple[str, ...], *, clip_path: bool, tall_page: bool) -> str:
    """Nested boxes, innermost holding two lines far enough apart to overflow.

    Every level gets an id so the driver can scroll it by name, and a spacer
    below the child so every level's own content overflows its 40px box — a
    level that cannot scroll cannot contribute the offset this is about.
    """
    body = ('<p>INNER_TOP</p>\n'
            '<p style="margin-top:300px">INNER_BOTTOM</p>')
    for level, overflow in enumerate(reversed(shape)):
        clip = "clip-path:inset(0 0 0 0);" if clip_path and level == len(shape) - 1 else ""
        body = (f'<div id="L{len(shape) - 1 - level}" '
                f'style="height:40px;width:300px;overflow:{overflow};{clip}">\n'
                f"{body}\n"
                '<div style="height:300px"></div>\n'
                "</div>")
    spacer = '<div style="height:2000px"></div>' if tall_page else ""
    return ("<!doctype html>\n<meta charset=\"utf-8\">\n<title>shape</title>\n"
            "<p>CONTROL_QUARTERLY_REPORT</p>\n"
            f"{body}\n{spacer}\n<p>PAGE_FOOT</p>\n")


def _label(shape: tuple[str, ...], clip_path: bool, tall_page: bool) -> str:
    return "-".join(shape) + ("+clip" if clip_path else "") + ("+tall" if tall_page else "")


CORPUS = [
    (_label(shape, clip_path, tall), shape, clip_path, tall)
    for shape in _shapes()
    for clip_path in (False, True)
    for tall in (False, True)
]

KNOWN_RED = {
    'auto+clip',
    'auto+clip+tall',
    'auto-auto+clip',
    'auto-auto+clip+tall',
    'auto-auto-auto+clip',
    'auto-auto-auto+clip+tall',
    'auto-auto-hidden+clip',
    'auto-auto-hidden+clip+tall',
    'auto-hidden+clip',
    'auto-hidden+clip+tall',
    'auto-hidden-auto',
    'auto-hidden-auto+clip',
    'auto-hidden-auto+clip+tall',
    'auto-hidden-auto+tall',
    'auto-hidden-hidden+clip',
    'auto-hidden-hidden+clip+tall',
    'hidden-auto',
    'hidden-auto+clip',
    'hidden-auto+clip+tall',
    'hidden-auto+tall',
    'hidden-auto-auto',
    'hidden-auto-auto+clip',
    'hidden-auto-auto+clip+tall',
    'hidden-auto-auto+tall',
    'hidden-auto-hidden',
    'hidden-auto-hidden+clip',
    'hidden-auto-hidden+clip+tall',
    'hidden-auto-hidden+tall',
    'hidden-hidden-auto',
    'hidden-hidden-auto+clip',
    'hidden-hidden-auto+clip+tall',
    'hidden-hidden-auto+tall',
}
"""The shapes that fail TODAY, recorded from a run rather than predicted.

Predicting which shapes would fail is the reasoning that lost five times in a
row, so this list is a measurement: repeated runs produce the identical set of
32. They split cleanly into two already-open defects, and neither was invented
here — the corpus rediscovered both without anyone imagining the failing shape:

  * **AT-416** (10 shapes, every one with a `hidden` box OUTSIDE an `auto` one) —
    a scrollable pane inside a clipping ancestor drops what is below its fold.
    Exactly the shape a checker found by hand; the generator found it from the
    product instead.
  * **AT-417** (22 shapes, every `+clip` one) — a `clip-path` ancestor that also
    scrolls never contributes its own offset, because the `clipPath` branch in
    `reachOf` returns before the scroll accumulation. Filed as pre-existing and
    uncharged when a checker noticed it by reading; here it is measured.

Each is `xfail(strict=True)`: the suite stays green while the defects are open,
and the moment either is fixed the unexpected PASS fails loudly instead of the
fix landing unnoticed. **These are not accepted behaviour** — they are two open
ledger rows with a running instrument pointed at them."""


@pytest.fixture(scope="module")
def corpus_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    site = tmp_path_factory.mktemp("scroll-invariance-corpus")
    for label, shape, clip_path, tall in CORPUS:
        (site / f"{label}.html").write_text(
            _html(shape, clip_path=clip_path, tall_page=tall), encoding="utf-8")
    return site


@pytest.fixture(scope="module")
def shape_page(corpus_site: Path, serve_dir: Callable[[Path], str]):
    playwright = pytest.importorskip("playwright.sync_api")
    base = serve_dir(corpus_site)
    try:
        runner = playwright.sync_playwright().start()
        browser = runner.chromium.launch(headless=True)
    except Exception as exc:  # browser binary missing on this machine
        pytest.skip(f"chromium unavailable: {type(exc).__name__}")
    page = browser.new_page()

    def visit(label: str):
        page.goto(f"{base}/{label}.html")
        page.wait_for_load_state("domcontentloaded")
        return page

    yield visit
    browser.close()
    runner.stop()


_RESET = """() => {
  document.querySelectorAll('[id^=L]').forEach(el => { el.scrollTop = 0; el.scrollLeft = 0; });
  window.scrollTo(0, 0);
}"""
"""Resetting every box is safe — putting a container back to 0 is the state the
page loaded in, whether or not a reader could have moved it."""

_SCROLLERS = """() => Array.from(document.querySelectorAll('[id^=L]'))
  .filter(el => {
    // A READER's scroll, not a script's. `el.scrollTop = n` moves an
    // overflow:hidden box perfectly well in Chromium, and the first version of
    // this driver did exactly that: it scrolled boxes nobody can scroll, the
    // detector correctly reported different text, and 50 of 56 shapes came back
    // red. The corpus was measuring the driver. Computed overflow decides.
    const s = getComputedStyle(el);
    const y = /^(auto|scroll)$/.test(s.overflowY) && el.scrollHeight > el.clientHeight;
    const x = /^(auto|scroll)$/.test(s.overflowX) && el.scrollWidth > el.clientWidth;
    return y || x;
  })
  .map(el => el.id)"""


def _states(page) -> list[tuple[str, Callable[[], None]]]:
    """Every scroll state worth visiting, named so a failure says which one.

    The containers are enumerated AT RUNTIME rather than from the shape spec:
    whether a box actually scrolls is the browser's answer, not the fixture
    author's, and assuming it was the fixture author's is how an existing
    fixture came to hold the AT-416 shape without exhibiting it.
    """
    out: list[tuple[str, Callable[[], None]]] = []
    for scroller in page.evaluate(_SCROLLERS):
        for where, expr in (("mid", "el.scrollHeight / 2"), ("max", "el.scrollHeight")):
            out.append((
                f"{scroller}:{where}",
                lambda s=scroller, e=expr: page.eval_on_selector(
                    f"#{s}", f"el => {{ el.scrollTop = {e}; el.scrollLeft = el.scrollWidth; }}"),
            ))
    out.append(("window:bottom",
                lambda: page.evaluate("window.scrollTo(0, document.body.scrollHeight)")))
    return out


@pytest.mark.parametrize(
    "label",
    [pytest.param(label, marks=pytest.mark.xfail(
        strict=True, reason="AT-417" if "+clip" in label else "AT-416"))
     if label in KNOWN_RED else label
     for label, _shape, _clip, _tall in CORPUS],
)
def test_what_is_reported_does_not_change_when_anything_is_scrolled(shape_page, label: str) -> None:
    """The floor: a scroll may reorder the result, never change its contents.

    Sorted-character equality is the assertion because scrolling a pane DOES
    legitimately change visual order — two texts can come to share a screen row
    and interleave. What may never change is which glyphs are there at all."""
    page = shape_page(label)
    page.evaluate(_RESET)
    at_rest = sorted(visual_text(page))
    # The positive control, on every generated page: without it a detector that
    # returned nothing would be trivially invariant and pass this whole corpus.
    assert "CONTROL_QUARTERLY_REPORT" in visual_text(page)

    for name, scroll in _states(page):
        page.evaluate(_RESET)
        scroll()
        # Force a layout flush before measuring. Without it this corpus was
        # NON-DETERMINISTIC — 33 failures on one run, 32 on the next — because a
        # scroll is committed asynchronously and `visual_text` measures rects.
        # A flaky instrument is worse than no instrument, and C7 forbids shipping
        # one, so the settle is part of the probe rather than a retry loop.
        page.evaluate("() => { document.body.offsetHeight; }")
        page.wait_for_timeout(30)
        assert sorted(visual_text(page)) == at_rest, f"{label} changed after {name}"
