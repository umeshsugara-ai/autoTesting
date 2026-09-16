"""Checker's OWN Mode D driver for at358 cycle 2. Reads no maker evidence."""
from __future__ import annotations
import functools, http.server, json, socketserver, threading, sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from autotester.browser.observe import visual_text

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"
OUT = Path(sys.argv[1])
OUT.mkdir(parents=True, exist_ok=True)

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(PAGES))
class Q(socketserver.TCPServer):
    allow_reuse_address = True
srv = Q(("127.0.0.1", 0), handler)
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{port}"

SENTINELS = {
 "disclosed.html": ["PSEUDOBEFORE_01","PSEUDOAFTER_02","SHADOWTEXT_03","SHADOWINPUT_04",
                    "SELECTOPT_05","CANVASTEXT_06","SVGTEXT_07","ALTTEXT_08","TITLETIP_09",
                    "IFRAMEBODY_10"],
 "extras.html": ["MARKERTEXT_11","SUBMITVAL_12","BUTTONVAL_13","BUTTONTEXT_14","SUMMARYTEXT_15",
                 "DETAILSBODY_16","DATALISTOPT_17","MATHMI_18","CSSCONTENT_19","LISTBOXOPT_20",
                 "LISTBOXOPT_20B","OPTGROUPLABEL_22","TEXTAREACHILD_21","TEXTAREAPH_23",
                 "SRCDOCTEXT_24","CAPTIONTEXT_25","OUTPUTTEXT_26","LEGENDTEXT_27","RUBYTEXT_28",
                 "ARIALABEL_29","PSEUDOPASSWORD_30"],
 "falsepos.html": ["FPOPACITY_31","FPTRANSPARENT_32","FPRGBAZERO_33","FPINDENT_34","FPOFFSCREEN_35",
                   "FPCLIPPED_36_LONGTAIL","FPNESTED_37","FPVISHIDDEN_38","FPDISPLAYNONE_39",
                   "FPFONTZERO_40","FPHIDDENINPUT_41","FPPASSWORD_42","FPUNDERNEATH_43",
                   "FPNEARZERO_44"],
 "scroll.html": ["ABOVEFOLD_60","BELOWFOLD_61","PANELVISIBLE_62","PANELSCROLLED_63"],
}
CONTROL = "CONTROL_CHECKER_77"
report = {"unit": "at358-visual-order-detector", "cycle": 2, "checker_run": True, "pages": {}}

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    page = browser.new_page(viewport={"width": 1000, "height": 800})
    errors = []
    page.on("console", lambda m: errors.append(f"{m.type}:{m.text}") if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(f"pageerror:{e}"))

    for name, sents in SENTINELS.items():
        errors.clear()
        page.goto(f"{BASE}/{name}")
        page.wait_for_load_state("networkidle")
        seen = visual_text(page)
        page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
        report["pages"][name] = {
            "console_errors": len(errors), "console_error_detail": list(errors),
            "positive_control_reported": CONTROL in seen,
            "reported": {s: (s in seen) for s in sents},
            "visual_text_len": len(seen),
            "visual_text": seen,
        }

    # scroll behaviour: same page, after scrolling to the bottom
    page.goto(f"{BASE}/scroll.html"); page.wait_for_load_state("networkidle")
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(200)
    seen_bottom = visual_text(page)
    page.evaluate("document.getElementById('panel').scrollTop = 500")
    page.wait_for_timeout(200)
    seen_panel = visual_text(page)
    report["scroll_probe"] = {
        "after_scroll_to_bottom": {s: (s in seen_bottom) for s in
                                   ["CONTROL_CHECKER_77","ABOVEFOLD_60","BELOWFOLD_61"]},
        "after_panel_scrolled": {s: (s in seen_panel) for s in
                                 ["PANELVISIBLE_62","PANELSCROLLED_63"]},
    }

    # INTERACTION probe: type a value, click a button, re-measure each time
    errors.clear()
    page.goto(f"{BASE}/interact.html"); page.wait_for_load_state("networkidle")
    before = visual_text(page)
    page.fill("#typed", "TYPEDSECRET_52")
    after_type = visual_text(page)
    page.click("#reveal")
    page.wait_for_timeout(100)
    after_click = visual_text(page)
    again = visual_text(page)
    leftover = page.eval_on_selector_all("body > span", "e => e.length")
    page.screenshot(path=str(OUT / "interact.png"), full_page=True)
    report["pages"]["interact.html"] = {
        "console_errors": len(errors), "console_error_detail": list(errors),
        "positive_control_reported": CONTROL in before,
        "placeholder_before_typing": "PLACEHOLDERGONE_50" in before,
        "typed_value_seen_after_fill": "TYPEDSECRET_52" in after_type,
        "placeholder_gone_after_fill": "PLACEHOLDERGONE_50" not in after_type,
        "click_revealed_text_seen": "REVEALED_51" in after_click,
        "idempotent_second_call": after_click == again,
        "leftover_mirror_spans": leftover,
        "visual_text_after_click": after_click,
    }
    browser.close()
srv.shutdown()
(OUT / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "visual_text"} for k, v in report["pages"].items()}, indent=2, ensure_ascii=False))
print(json.dumps(report["scroll_probe"], indent=2))
