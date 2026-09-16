"""Ground truth for AT-437: does `content-visibility:hidden` actually HIDE text?

Computed style says `hidden` on every box it is set on, including boxes where the
browser ignores it and paints the text anyway. So the question is answered by
the only instrument that cannot be fooled by computed style: a screenshot.

For each display type, one isolated page: screenshot a fixed frame, set the
element's text transparent, screenshot again. Identical -> the text was never
painted (content-visibility took effect). Different -> it was painted, and a
detector that drops it has manufactured a false negative.

Run:  uv run python qa/evidence/at429-content-visibility-hidden/groundtruth.py
"""
import hashlib
import json

from playwright.sync_api import sync_playwright

CASES = [
    ("block", '<div id="t" style="content-visibility:hidden">SENT_X</div>'),
    ("inline", '<span id="t" style="content-visibility:hidden">SENT_X</span>'),
    ("inline-block", '<span id="t" style="display:inline-block;content-visibility:hidden">SENT_X</span>'),
    ("flex", '<div id="t" style="display:flex;content-visibility:hidden">SENT_X</div>'),
    ("inline-flex", '<span id="t" style="display:inline-flex;content-visibility:hidden">SENT_X</span>'),
    ("grid", '<div id="t" style="display:grid;content-visibility:hidden">SENT_X</div>'),
    ("inline-grid", '<span id="t" style="display:inline-grid;content-visibility:hidden">SENT_X</span>'),
    ("flow-root", '<div id="t" style="display:flow-root;content-visibility:hidden">SENT_X</div>'),
    ("list-item", '<ul><li id="t" style="content-visibility:hidden">SENT_X</li></ul>'),
    ("table-cell", '<table><tr><td id="t" style="content-visibility:hidden">SENT_X</td></tr></table>'),
    ("table-caption", '<table><caption id="t" style="content-visibility:hidden">SENT_X</caption><tr><td>c</td></tr></table>'),
    ("table", '<table id="t" style="content-visibility:hidden"><tr><td>SENT_X</td></tr></table>'),
    ("inline-table", '<table id="t" style="display:inline-table;content-visibility:hidden"><tr><td>SENT_X</td></tr></table>'),
    ("table-row", '<table><tr id="t" style="content-visibility:hidden"><td>SENT_X</td></tr></table>'),
    ("table-row-group", '<table><tbody id="t" style="content-visibility:hidden"><tr><td>SENT_X</td></tr></tbody></table>'),
    ("table-header-group", '<table><thead id="t" style="content-visibility:hidden"><tr><td>SENT_X</td></tr></thead></table>'),
    ("table-footer-group", '<table><tfoot id="t" style="content-visibility:hidden"><tr><td>SENT_X</td></tr></tfoot></table>'),
    ("contents", '<div id="t" style="display:contents;content-visibility:hidden">SENT_X</div>'),
    ("ruby", '<ruby id="t" style="content-visibility:hidden">SENT_X<rt>r</rt></ruby>'),
    ("ruby-text", '<ruby>BASE<rt id="t" style="content-visibility:hidden">SENT_X</rt></ruby>'),
]
PAGE = ('<!doctype html><meta charset=utf-8><body style="margin:0;font:28px sans-serif">'
        '<div id="frame" style="width:700px;height:90px;padding:10px">{}</div></body>')
BLANK = ("() => { const t = document.getElementById('t'); t.style.color = 'transparent';"
         " t.querySelectorAll('*').forEach(e => e.style.color = 'transparent'); }")


def main() -> None:
    out = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        for label, inner in CASES:
            page = browser.new_page(viewport={"width": 900, "height": 300})
            page.set_content(PAGE.format(inner))
            page.wait_for_timeout(150)
            before = hashlib.sha1(page.locator("#frame").screenshot()).hexdigest()
            page.evaluate(BLANK)
            page.wait_for_timeout(80)
            after = hashlib.sha1(page.locator("#frame").screenshot()).hexdigest()
            display = page.evaluate("() => getComputedStyle(document.getElementById('t')).display")
            out.append({"case": label, "display": display, "painted": before != after})
            page.close()
        browser.close()
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
