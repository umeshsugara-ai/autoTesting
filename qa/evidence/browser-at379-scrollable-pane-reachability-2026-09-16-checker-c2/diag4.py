import functools, http.server, json, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
HERE = Path(__file__).resolve().parent
JS = Path("D:/autoTesting/src/autotester/browser/visual_order.js").read_text(encoding="utf-8")
def serve(d):
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(d))
    s = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{s.server_address[1]}"
base = serve(HERE / "pages")
out = {}
with sync_playwright() as pw:
    b = pw.chromium.launch(); page = b.new_context(viewport={"width":1000,"height":700}).new_page()
    errs = []
    page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errs.append(str(e)))
    page.goto(f"{base}/p7_cvauto.html"); page.wait_for_load_state("load")
    out["run1_UNMUTATED_shipping_detector"] = str(page.evaluate(JS))
    out["run2"] = str(page.evaluate(JS))
    page.goto(f"{base}/p7_cvauto.html"); page.wait_for_load_state("load")
    page.evaluate("window.scrollTo(0, 2000)")
    out["run1_after_scrolling_into_view"] = str(page.evaluate(JS))
    out["console_errors"] = errs
    b.close()
print(json.dumps(out, indent=2))
(HERE/"diag4.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
