"""AT-398: which guard drops the glyph, on the FIRST evaluation only."""
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
JS_NG = JS.replace("    if (el.checkVisibility && !el.checkVisibility()) return false;",
                   "    if (false) return false;")
# instrument glyphsOf: record every rejection reason, first run only
INSTR = JS_NG.replace(
    "      if (rect.width === 0) continue;\n"
    "      if (checkReachable && !isReachable(rect, reach)) continue;",
    "      window.__trace = window.__trace || [];\n"
    "      if (text.includes('SENTINEL_77') || text.includes('SENTINEL_79')) {\n"
    "        window.__trace.push({i, ch: text[i], w: rect.width, h: rect.height,\n"
    "          x: rect.left, y: rect.top,\n"
    "          widthDrop: rect.width === 0,\n"
    "          reachDrop: rect.width !== 0 && checkReachable && !isReachable(rect, reach),\n"
    "          reach: {clip: reach.clip, sx: reach.scrollX, sy: reach.scrollY}});\n"
    "      }\n"
    "      if (rect.width === 0) continue;\n"
    "      if (checkReachable && !isReachable(rect, reach)) continue;")
assert INSTR != JS_NG, "instrumentation anchor did not match"


def serve(directory: Path) -> str:
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{s.server_address[1]}"


def main() -> None:
    base = serve(PAGES)
    out = {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        page = b.new_context(viewport={"width": 1000, "height": 700}).new_page()
        page.goto(f"{base}/p6_details.html")
        page.wait_for_load_state("load")
        out["run1"] = str(page.evaluate(INSTR))
        out["trace_run1"] = page.evaluate("window.__trace")
        page.evaluate("window.__trace = []")
        out["run2"] = str(page.evaluate(INSTR))
        out["trace_run2"] = page.evaluate("window.__trace")
        b.close()

    def brief(tr):
        return [t for t in tr if t["i"] < 3]

    print("run1:", out["run1"][:120])
    print("run2:", out["run2"][:120])
    print("run1 first-3-glyph decisions:", json.dumps(brief(out["trace_run1"]), indent=1))
    print("run2 first-3-glyph decisions:", json.dumps(brief(out["trace_run2"]), indent=1))
    print("run1 dropped:", [(t["ch"], t["i"], "width" if t["widthDrop"] else "reach")
                            for t in out["trace_run1"] if t["widthDrop"] or t["reachDrop"]])
    print("run2 dropped:", [(t["ch"], t["i"], "width" if t["widthDrop"] else "reach")
                            for t in out["trace_run2"] if t["widthDrop"] or t["reachDrop"]])
    (HERE / "diag3.json").write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
