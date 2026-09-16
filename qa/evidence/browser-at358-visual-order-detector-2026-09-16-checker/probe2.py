from __future__ import annotations
import functools, http.server, json, socketserver, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
from autotester.browser.observe import visual_text
HERE = Path(__file__).resolve().parent; PAGES = HERE / "pages"
h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(PAGES))
class Q(socketserver.TCPServer): allow_reuse_address = True
srv = Q(("127.0.0.1", 0), h); port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
with sync_playwright() as pw:
    b = pw.chromium.launch(headless=True); p = b.new_page(viewport={"width":1000,"height":800})
    p.goto(f"http://127.0.0.1:{port}/extras.html"); p.wait_for_load_state("networkidle")
    out = {}
    out["visual_text"] = visual_text(p)
    out["details_body_checkVisibility"] = p.evaluate(
        "document.querySelector('details p').checkVisibility({checkVisibilityCSS:true,contentVisibilityAuto:true,opacityProperty:true})")
    out["details_body_rect"] = p.evaluate("JSON.stringify(document.querySelector('details p').getBoundingClientRect())")
    out["details_open"] = p.evaluate("document.querySelector('details').open")
    out["details_body_display"] = p.evaluate("getComputedStyle(document.querySelector('details p')).display")
    out["details_parent_content_visibility"] = p.evaluate(
        "getComputedStyle(document.querySelector('details')).contentVisibility")
    out["marker_rendered_text"] = p.evaluate(
        "getComputedStyle(document.querySelector('ol.m li'),'::marker').content")
    out["css_content_el"] = p.evaluate("getComputedStyle(document.getElementById('cs')).content")
    out["ol_marker_numbers_in_visual"] = ("1." in out["visual_text"], "2." in out["visual_text"])
    p.screenshot(path=str(HERE/"extras-probe2.png"), full_page=True)
    b.close()
srv.shutdown()
print(json.dumps(out, indent=2, ensure_ascii=False))
