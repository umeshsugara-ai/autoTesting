"""Checker's own probe of AT-358 visual_text. Independent of the repo's tests."""
from __future__ import annotations

import functools
import http.server
import json
import socketserver
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

from autotester.browser.observe import visual_text

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"
SHOTS = HERE / "shots"
SHOTS.mkdir(exist_ok=True)

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(PAGES))
httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
port = httpd.server_address[1]
threading.Thread(target=httpd.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{port}"

out: dict = {}
errors: list[str] = []


def run() -> None:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 900, "height": 700})
        console: list[str] = []
        page.on("console", lambda m: console.append(f"{m.type}:{m.text}"))

        def visit(name: str) -> str:
            page.goto(f"{BASE}/{name}")
            page.wait_for_load_state("networkidle")
            return visual_text(page)

        for name in ["p01_control.html", "p02_scalex.html", "p03_rotate.html",
                     "p04_pseudo.html", "p05_shadow.html", "p06_canvas_svg.html",
                     "p07_iframe.html", "p08_order.html", "p09_vertical.html",
                     "p10_hiddenish.html", "p11_controls.html"]:
            seen = visit(name)
            page.screenshot(path=str(SHOTS / (name + ".png")), full_page=True)
            out[name] = seen

        # --- page-left-alone checks ---
        page.goto(f"{BASE}/p12_state.html")
        page.wait_for_load_state("networkidle")
        page.evaluate("window.scrollTo(0, 500)")
        page.focus("#f1")
        page.evaluate("""() => {
            const r = document.createRange();
            const t = document.getElementById('para').firstChild;
            r.setStart(t, 0); r.setEnd(t, 10);
            const s = window.getSelection(); s.removeAllRanges(); s.addRange(r);
        }""")
        before = page.evaluate("""() => ({
            scrollY: window.scrollY,
            active: document.activeElement ? document.activeElement.id : null,
            selection: String(window.getSelection()),
            f1: document.getElementById('f1').value,
            t1: document.getElementById('t1').value,
            spans: document.querySelectorAll('body > span').length,
            bodyChildren: document.body.children.length,
            html: document.body.innerHTML.length,
        })""")
        seen = visual_text(page)
        after = page.evaluate("""() => ({
            scrollY: window.scrollY,
            active: document.activeElement ? document.activeElement.id : null,
            selection: String(window.getSelection()),
            f1: document.getElementById('f1').value,
            t1: document.getElementById('t1').value,
            spans: document.querySelectorAll('body > span').length,
            bodyChildren: document.body.children.length,
            html: document.body.innerHTML.length,
        })""")
        out["state_before"] = before
        out["state_after"] = after
        out["state_seen_len"] = len(seen)
        # idempotence
        out["state_idempotent"] = visual_text(page) == seen

        # --- glyphsOf throws inside mirrorGlyphs: does the span survive? ---
        page.goto(f"{BASE}/p13_throw.html")
        page.wait_for_load_state("networkidle")
        page.evaluate("""() => { document.createRange = () => { throw new Error('boom'); }; }""")
        threw = None
        try:
            visual_text(page)
            threw = "no-exception"
        except Exception as exc:  # noqa: BLE001
            threw = type(exc).__name__ + ": " + str(exc).splitlines()[0][:120]
        out["throw_result"] = threw
        out["throw_spans_left"] = page.evaluate(
            "() => document.querySelectorAll('body > span').length")
        out["throw_body_html"] = page.evaluate("() => document.body.innerHTML")[:300]

        out["console"] = console
        browser.close()


run()
httpd.shutdown()
print(json.dumps(out, indent=2, ensure_ascii=False))
