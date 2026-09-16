import sys
from playwright.sync_api import sync_playwright
html = """<!doctype html><meta charset=utf-8><body style="font:28px sans-serif">
<p>CONTROLPOSITIVE_SEVENTYSEVEN</p>
<div>1: <span style="content-visibility:hidden">SPANX_G</span>VISIBLESIB_H</div>
<div>2: <x-card style="content-visibility:hidden">CUSTOMDIRECT_O</x-card></div>
<div>3: <ruby>KANJI_AD<rt style="content-visibility:hidden">RUBYRT_AE</rt></ruby></div>
<div>4: <div style="display:contents;content-visibility:hidden">DCONTENTS_K</div></div>
<div>5: <span style="display:inline-block;content-visibility:hidden">IBX_I</span>VISIBLESIB_J</div>
</body>"""
js = open("D:/autoTesting/src/autotester/browser/visual_order.js", encoding="utf-8").read()
with sync_playwright() as pw:
    b = pw.chromium.launch(); p = b.new_page(viewport={"width":900,"height":420})
    p.set_content(html); p.wait_for_timeout(300)
    p.screenshot(path=sys.argv[1])
    print(repr(p.evaluate(js)))
    print(p.evaluate("""[...document.querySelectorAll('[style*=content-visibility]')].map(e=>[e.tagName, getComputedStyle(e).display, getComputedStyle(e).contentVisibility, e.checkVisibility()])"""))
    b.close()
