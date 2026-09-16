"""Checker's own Mode D probe for at410. Unfixed (77cba2d^) vs fixed (bound tree) detector."""
import functools, http.server, json, statistics, subprocess, sys, threading, time
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).parent
PAGES = HERE / "pages"; PAGES.mkdir(exist_ok=True)
FIXED = Path("D:/autoTesting/src/autotester/browser/visual_order.js").read_text(encoding="utf-8")
UNFIXED = subprocess.run(["git", "-C", "D:/autoTesting", "show", "77cba2d^:src/autotester/browser/visual_order.js"],
                         capture_output=True, text=True, encoding="utf-8", check=True).stdout
assert "warm.getBoundingClientRect" in FIXED and "warm" not in UNFIXED
BYPASS_OLD = "    if (el.checkVisibility && !el.checkVisibility()) return false;"
def bypass(js):
    assert js.count(BYPASS_OLD) == 1
    return js.replace(BYPASS_OLD, "    if (false) return false;")

CTRL = '<p>POSCONTROL_ONSCREEN_01</p>'
SPACER = '<div style="height:2000px"></div>'
CV = 'content-visibility:auto;contain-intrinsic-size:auto 500px'
pages = {
 "p1_cvauto_fixture": Path("D:/autoTesting/tests/fixtures/bidi_site/cvauto.html").read_text(encoding="utf-8"),
 "p2_several_nodes": f'<!doctype html><meta charset=utf-8>{CTRL}{SPACER}<div style="{CV}"><p>ALPHA_SIB_11</p><p>BRAVO_SIB_12</p><p>CHARLIE_SIB_13</p><p>DELTA_A<b>ECHO_B</b>FOXTROT_C</p></div>'
                     f'{SPACER}<div style="{CV}"><p>GOLF_BLOCK2_14</p><p>HOTEL_BLOCK2_15</p></div>',
 "p3_zwsp_first": f'<!doctype html><meta charset=utf-8>{CTRL}{SPACER}<div style="{CV}"><p>\u200bZWSP_SENTINEL_33</p><p>\u200bKILO_AFTER_34</p></div>',
 "p4_nested_cvauto": f'<!doctype html><meta charset=utf-8>{CTRL}{SPACER}<div style="{CV}"><div style="{CV}"><p>NESTED_INNER_41</p></div><p>NESTED_OUTER_42</p></div>',
 "p5_details_in_cvauto": f'<!doctype html><meta charset=utf-8>{CTRL}{SPACER}<div style="{CV}"><details><summary>SUMMARY_SEEN_51</summary><p>DETAILS_HIDDEN_52</p></details><p>LIMA_AFTER_53</p></div>',
 "p6_cvhidden_at429": f'<!doctype html><meta charset=utf-8>{CTRL}<div style="content-visibility:hidden">CVHIDDEN_SENTINEL_92</div><p>AFTER_HIDDEN_93</p>',
 "p7_unreadable_fixture": Path("D:/autoTesting/tests/fixtures/bidi_site/unreadable.html").read_text(encoding="utf-8"),
 "p8_many_nodes": '<!doctype html><meta charset=utf-8>' + CTRL + "".join(
     f'<div style="{CV}">' + "".join(f"<p>row {b}-{i} lorem ipsum dolor sit amet consect</p>" for i in range(40)) + "</div>"
     for b in range(25)),
 "p9_many_nodes_onscreen": '<!doctype html><meta charset=utf-8>' + CTRL + "".join(
     f"<p>row {i} lorem ipsum dolor sit amet consect</p>" for i in range(1000)),
}
for name, html in pages.items():
    (PAGES / f"{name}.html").write_text(html, encoding="utf-8")

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Q, directory=str(PAGES)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"

report = {"unit": "at410-first-glyph-content-visibility", "date": "2026-09-16", "browser": None, "pages": {}}
STATE_JS = """() => ({scrollX: scrollX, scrollY: scrollY,
  cv: [...document.querySelectorAll('[style*="content-visibility"]')].map(e => e.checkVisibility({contentVisibilityAuto: true})),
  events: window.__cvEvents ? window.__cvEvents.slice() : null,
  bodyChildren: document.body.children.length})"""
LISTEN_JS = """() => { window.__cvEvents = [];
  for (const e of document.querySelectorAll('[style*="content-visibility"]'))
    e.addEventListener('contentvisibilityautostatechange', ev => window.__cvEvents.push(ev.skipped)); }"""

with sync_playwright() as pw:
    br = pw.chromium.launch(headless=True)
    report["browser"] = br.version
    def fresh(name):
        page = br.new_page(); errs = []
        page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.append(str(e)))
        page.goto(f"{BASE}/{name}.html"); page.wait_for_load_state("load")
        return page, errs
    for name in pages:
        if name.startswith("p8") or name.startswith("p9"): continue
        entry = {}
        for label, js in (("unfixed", UNFIXED), ("fixed", FIXED), ("unfixed_bypass", bypass(UNFIXED)), ("fixed_bypass", bypass(FIXED))):
            if "bypass" in label and name not in ("p7_unreadable_fixture", "p5_details_in_cvauto"): continue
            trials = []
            for t in range(3):
                page, errs = fresh(name)
                page.evaluate(LISTEN_JS); page.wait_for_timeout(100)
                before = page.evaluate(STATE_JS)
                first = page.evaluate(js); page.wait_for_timeout(150)
                mid = page.evaluate(STATE_JS)
                second = page.evaluate(js)
                after = page.evaluate(STATE_JS)
                trials.append({"first": first, "second": second, "first_eq_second": first == second,
                               "state_before": before, "state_after_first": mid, "state_after_second": after,
                               "console_errors": len(errs), "errors": errs})
                page.close()
            entry[label] = trials
        report["pages"][name] = entry
    # timing
    timing = {}
    for name in ("p8_many_nodes", "p9_many_nodes_onscreen"):
        timing[name] = {}
        for label, js in (("unfixed", UNFIXED), ("fixed", FIXED)) * 1:
            ms = []; outs = set(); errc = 0
            for t in range(7):
                page, errs = fresh(name)
                t0 = time.perf_counter(); out = page.evaluate(js); ms.append((time.perf_counter() - t0) * 1000)
                outs.add(len(out)); errc += len(errs); page.close()
            timing[name][label] = {"ms": [round(x, 1) for x in ms], "median_ms": round(statistics.median(ms), 1),
                                   "out_lengths": sorted(outs), "console_errors": errc,
                                   "has_control": "POSCONTROL_ONSCREEN_01" in out}
    report["timing"] = timing
    br.close()
srv.shutdown()
out = Path(sys.argv[1]); out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
print("written", out)
