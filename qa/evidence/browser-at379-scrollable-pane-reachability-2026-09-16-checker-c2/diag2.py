"""AT-398 cause hunt + nested-pane quantification. Read-only toward d:/autoTesting."""
from __future__ import annotations

import functools
import http.server
import json
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"
JS = Path("D:/autoTesting/src/autotester/browser/visual_order.js").read_text(encoding="utf-8")
GUARD = "    if (el.checkVisibility && !el.checkVisibility()) return false;"
JS_NOGUARD = JS.replace(GUARD, "    if (false) return false;")


def serve(directory: Path) -> str:
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{s.server_address[1]}"


FIRST_TOUCH = """() => {
  // FIRST geometry query ever made inside this closed <details> subtree.
  const p = document.querySelectorAll('details')[0].querySelector('p');
  const node = p.firstChild;
  const measure = (i) => {
    const r = document.createRange();
    r.setStart(node, i); r.setEnd(node, i + 1);
    const b = r.getBoundingClientRect();
    return {ch: node.nodeValue[i], w: b.width, h: b.height, x: b.left, y: b.top,
            n: r.getClientRects().length};
  };
  const first0 = measure(0);          // first query in the subtree, ever
  const first1 = measure(1);
  const second0 = measure(0);         // same index, queried again
  const third0 = measure(0);
  return {first0, first1, second0, third0};
}"""


def main() -> None:
    base = serve(PAGES)
    out = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_context(viewport={"width": 1000, "height": 700}).new_page()

        page.goto(f"{base}/p6_details.html")
        page.wait_for_load_state("load")
        out["first_touch"] = page.evaluate(FIRST_TOUCH)

        # control: same experiment on an OPEN details (no content-visibility)
        page.goto(f"{base}/p6_details.html")
        page.wait_for_load_state("load")
        out["open_details_first_touch"] = page.evaluate("""() => {
          const p = document.querySelectorAll('details')[2].querySelector('p');
          const node = p.firstChild;
          const m = (i) => { const r = document.createRange();
            r.setStart(node, i); r.setEnd(node, i+1);
            const x = r.getBoundingClientRect();
            return {ch: node.nodeValue[i], w: x.width, x: x.left, y: x.top}; };
          return {first0: m(0), second0: m(0)};
        }""")

        # run the real detector twice on a fresh load: does the drop persist?
        page.goto(f"{base}/p6_details.html")
        page.wait_for_load_state("load")
        out["run1"] = str(page.evaluate(JS_NOGUARD))
        out["run2"] = str(page.evaluate(JS_NOGUARD))
        out["run3"] = str(page.evaluate(JS_NOGUARD))

        # nested panes: exact multiset delta
        page.goto(f"{base}/p2_nested.html")
        page.wait_for_load_state("load")
        rest = str(page.evaluate(JS))
        page.eval_on_selector("#outer", "el => { el.scrollTop = 500; }")
        page.eval_on_selector("#inner", "el => { el.scrollTop = 400; }")
        scr = str(page.evaluate(JS))
        out["nested"] = {
            "at_rest_len": len(rest), "scrolled_len": len(scr),
            "at_rest": rest, "scrolled": scr,
            "INNERTOP_at_rest": "INNERTOP_SENTINEL_12" in rest,
            "INNERTOP_scrolled": "INNERTOP_SENTINEL_12" in scr,
            "INNERBOT_scrolled": "INNERBOT_SENTINEL_13" in scr,
        }
        # what reachOf actually returns for the inner pane's first <p>
        out["nested_reach"] = page.evaluate("""() => {
          const SCROLLS = /^(auto|scroll)$/;
          const p = document.querySelector('#inner p');
          const trace = [];
          let sx = window.scrollX, sy = window.scrollY, stopped = null;
          for (let n = p; n && n !== document.documentElement; n = n.parentElement) {
            const st = getComputedStyle(n);
            const box = n.getBoundingClientRect();
            const sY = SCROLLS.test(st.overflowY) && n.scrollHeight > n.clientHeight;
            const sX = SCROLLS.test(st.overflowX) && n.scrollWidth > n.clientWidth;
            trace.push({tag: n.tagName, id: n.id, overflow: st.overflow,
                        overflowX: st.overflowX, overflowY: st.overflowY,
                        scrollsX: sX, scrollsY: sY,
                        scrollTop: n.scrollTop, scrollLeft: n.scrollLeft});
            if (st.overflow === 'visible') continue;
            if (sX) sx += n.scrollLeft;
            if (sY) sy += n.scrollTop;
            if (sX && sY) continue;
            stopped = n.id || n.tagName;
            break;
          }
          const r = p.getBoundingClientRect();
          return {trace, accumulatedScrollY: sy, accumulatedScrollX: sx,
                  stoppedAt: stopped, rectTop: r.top, rectBottom: r.bottom,
                  documentEdgeTest: r.bottom + sy,
                  neededToPass: '> 0'};
        }""")
        b.close()

    (HERE / "diag2.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2)[:6000])


if __name__ == "__main__":
    main()
