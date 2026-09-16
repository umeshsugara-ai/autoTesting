"""Checker Mode D, at438 cycle 2. Three detector versions on identical pages:
OLD = c687b73^ (pre-AT-438), PROBE = c687b73 (cycle 1), NEW = the bound tree (cycle 2).
Ground truth: full-page screenshot hash before/after REPLACING the sentinel text node with
same-length different glyphs (monospace), never color:transparent. Positive control per page."""
import hashlib, json, sys, subprocess
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("D:/autoTesting")


def at(rev):
    return subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:src/autotester/browser/visual_order.js"],
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout


VERS = {"OLD": at("c687b73^"), "PROBE": at("c687b73"),
        "NEW": (ROOT / "src/autotester/browser/visual_order.js").read_text(encoding="utf-8")}
OUT = Path(sys.argv[1])
POS = '<p style="margin:0 0 30px">POSCTRL_OK</p>'
HEAD = ('<!doctype html><meta charset=utf-8><style>body{margin:8px;font:20px monospace}{css}</style>'
        '<body>' + POS + '{body}</body>')
S = "SENTZQ_KEY"
C = f'<div id="c" style="display:contents">{S}</div>'


def jsbuild(parent_sel, tag="div"):
    return (f"const c=document.createElement('{tag}');c.id='c';c.style.display='contents';c.textContent='{S}';"
            f"document.querySelector('{parent_sel}').appendChild(c)")


def shadow(inner, light=C):
    return (f'<div id="host">{light}</div>',
            f"document.getElementById('host').attachShadow({{mode:'open'}}).innerHTML={json.dumps(inner)}")


CASES = [
    # --- cycle-1 layouts (regression floor) ---
    ("plain contents", "", C, None),
    ("open details", "", f"<details open><summary>s</summary>{C}</details>", None),
    ("closed details", "", f"<details><summary>s</summary>{C}</details>", None),
    ("closed details, contents nested twice", "", f'<details><summary>s</summary><div style="display:contents">{C}</div></details>', None),
    ("cv:hidden block", "", f'<div style="content-visibility:hidden">{C}</div>', None),
    ("display:none", "", f'<div style="display:none">{C}</div>', None),
    ("hidden attribute", "", f"<div hidden>{C}</div>", None),
    ("visibility:hidden ancestor", "", f'<div style="visibility:hidden">{C}</div>', None),
    ("opacity:0 ancestor", "", f'<div style="opacity:0">{C}</div>', None),
    ("closed dialog", "", f"<dialog>{C}</dialog>", None),
    ("contents inside ul", "", f"<ul><li>a</li>{C}</ul>", None),
    ("author span:empty{display:none}", "span:empty{display:none}", C, None),
    ("author *:empty{display:none}", "*:empty{display:none}", C, None),
    # --- point 1 attacks ---
    ("summary itself display:contents, closed details", "", f'<details><summary id="c" style="display:contents">{S}</summary><p>body</p></details>', None),
    ("summary contents > contents span, closed", "", f'<details><summary style="display:contents"><span id="c" style="display:contents">{S}</span></summary></details>', None),
    ("SECOND summary display:contents, closed details", "", f'<details><summary>first</summary><summary id="c" style="display:contents">{S}</summary></details>', None),
    ("contents wrapping a summary, closed details", "", f'<details><div style="display:contents"><summary>{S}</summary></div></details>', None),
    ("hidden=until-found on block box", "", f'<div hidden="until-found">{C}</div>', None),
    ("hidden=until-found on inline span box", "", f'<p><span hidden="until-found">{C}</span></p>', None),
    ("open dialog (non-modal)", "", f"<dialog open>{C}</dialog>", None),
    ("modal dialog (showModal)", "", f'<dialog id="d">{C}</dialog>', "document.getElementById('d').showModal()"),
    ("fieldset > legend display:contents", "", f'<fieldset><legend id="c" style="display:contents">{S}</legend><p>f</p></fieldset>', None),
    ("fieldset > legend > contents", "", f'<fieldset><legend>{C}</legend><p>f</p></fieldset>', None),
    ("fieldset > contents", "", f'<fieldset><legend>L</legend>{C}</fieldset>', None),
    ("table with display:contents tr", "", f'<table><tbody><tr id="c" style="display:contents"><td>{S}</td></tr></tbody></table>', None),
    ("table: contents td text", "", f'<table><tr><td id="c" style="display:contents">{S}</td><td>x</td></tr></table>', None),
    ("table: tbody+tr contents, JS text in tr", "", '<table><tbody style="display:contents"><tr id="tr" style="display:contents"><td>x</td></tr></tbody></table>', jsbuild('#tr')),
    ("slot display:contents: slotted contents child", "", *shadow('<slot style="display:contents"></slot>')),
    ("slot inside visible div: slotted contents child", "", *shadow('<div><slot></slot></div>')),
    ("slot inside CLOSED details in shadow", "", *shadow('<details><summary>s</summary><slot></slot></details>')),
    ("slot inside cv:hidden div in shadow", "", *shadow('<div style="content-visibility:hidden"><slot></slot></div>')),
    ("slot inside display:none in shadow", "", *shadow('<div style="display:none"><slot></slot></div>')),
    ("unslotted light child (no slot)", "", *shadow('<p>shadow</p>')),
    ("flex container contain:paint height:0", "", f'<div style="display:flex;height:0;contain:paint">{C}</div>', None),
    ("grid container contain:paint height:0", "", f'<div style="display:grid;grid-template-rows:0;height:0;contain:paint">{C}</div>', None),
    ("flex container clip-path hides all", "", f'<div style="display:flex;clip-path:inset(0 0 100% 0)">{C}</div>', None),
    ("grid 0-size track overflow visible", "", f'<div style="display:grid;grid-template-columns:0;grid-template-rows:0">{C}</div>', None),
    ("nested closed>closed, contents at L1", "", f'<details><summary>o</summary>{C}<details><summary>i</summary><p>x</p></details></details>', None),
    ("nested closed>closed, contents at L2", "", f'<details><summary>o</summary><details><summary>i</summary>{C}</details></details>', None),
    ("nested closed>closed, contents in inner summary", "", f'<details><summary>o</summary><details><summary>{C}</summary></details></details>', None),
    ("nested closed>open, contents at L2", "", f'<details><summary>o</summary><details open><summary>i</summary>{C}</details></details>', None),
    ("nested open>closed, contents in inner summary", "", f'<details open><summary>o</summary><details><summary>{C}</summary></details></details>', None),
    ("nested open>closed, contents at L2", "", f'<details open><summary>o</summary><details><summary>i</summary>{C}</details></details>', None),
    ("closed details, contents wrapper x3", "", f'<details><summary>o</summary><div style="display:contents"><div style="display:contents">{C}</div></div></details>', None),
    ("closed details with ::details-content visible", "details::details-content{content-visibility:visible}", f"<details><summary>s</summary>{C}</details>", None),
    ("details itself display:contents, closed", "", f'<details style="display:contents"><summary>s</summary>{C}</details>', None),
    ("open details display:contents inside closed details", "", f'<details><summary>o</summary><details open style="display:contents"><summary>i</summary>{C}</details></details>', None),
    # --- point 3: dead-branch deletion ---
    ("video fallback child", "", '<video id="p" width="200" height="50"></video>', jsbuild('#p')),
    ("video controls fallback child", "", '<video id="p" controls width="200" height="50"></video>', jsbuild('#p')),
    ("audio controls fallback child", "", '<audio id="p" controls></audio>', jsbuild('#p')),
    ("audio (no controls) fallback child", "", '<audio id="p"></audio>', jsbuild('#p')),
    ("canvas fallback child", "", '<canvas id="p" width="200" height="50"></canvas>', jsbuild('#p')),
    ("iframe child (JS)", "", '<iframe id="p" width="200" height="50"></iframe>', jsbuild('#p')),
    ("object (no data) fallback child", "", f'<object>{C}</object>', None),
    ("object with svg data fallback child", "", f'<object type="image/svg+xml" width="20" height="20" data="data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%2210%22 height=%2210%22/%3E">{C}</object>', None),
    ("textarea element child (JS)", "", '<textarea id="p"></textarea>', jsbuild('#p')),
    ("select element child (JS)", "", '<select id="p"><option>o</option></select>', jsbuild('#p')),
    ("img element child (JS)", "", '<img id="p" width="20" height="20" alt="">', jsbuild('#p')),
    ("input element child (JS)", "", '<input id="p">', jsbuild('#p')),
    ("slotted child, plain slot (must report)", "", *shadow('<slot></slot>')),
]
GT = ("(s) => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);"
      " let n; while ((n = w.nextNode())) { if (n.nodeValue.includes(s)) {"
      " n.nodeValue = n.nodeValue.replace(s, 'MMMMMMMMMM'); return true; } } return false; }")
MO = ("() => { window.__recs = []; const f = rs => { for (const r of rs) window.__recs.push(r.type + ':' + (r.target.id || r.target.nodeName)); };"
      " new MutationObserver(f).observe(document, {subtree:true, childList:true, attributes:true, characterData:true});"
      " const c = document.getElementById('c'); if (c) new MutationObserver(f).observe(c, {subtree:true, childList:true, attributes:true, characterData:true}); }")
RECS = "() => new Promise(r => setTimeout(() => r(window.__recs), 30))"
CLOCK = "() => document.getAnimations().map(a => Math.round(a.currentTime))"


def shot(page):
    return hashlib.sha1(page.screenshot(full_page=True)).hexdigest()


def new_page(browser):
    page = browser.new_page(viewport={"width": 900, "height": 600})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    return page, errors


def run_case(browser, label, css, body, setup):
    row = {"case": label}
    for tag, js in VERS.items():
        page, errors = new_page(browser)
        page.set_content(HEAD.replace("{css}", css).replace("{body}", body))
        if setup:
            page.evaluate(setup)
        page.wait_for_timeout(150)
        page.evaluate(MO)
        seen = page.evaluate(js)
        row[tag] = {"reported": S in seen, "pos_ctrl": "POSCTRL_OK" in seen, "mutations": page.evaluate(RECS),
                    "console_errors": len(errors)}
        if tag == "NEW":
            page.evaluate("() => window.scrollTo(0,0)")
            b = shot(page)
            row["gt_found"] = page.evaluate(GT, S)
            page.wait_for_timeout(80)
            row["painted"] = b != shot(page)
        page.close()
    for tag in VERS:
        r = row[tag]["reported"]
        row[tag]["verdict"] = "ok" if r == row["painted"] else ("FALSE_POSITIVE" if r else "FALSE_NEGATIVE")
    return row


KF = "@keyframes fin{from{opacity:0}2%{opacity:1}to{opacity:1}}"
SIDE = [
    ("last-child animation", KF + "#c>b:last-child{animation:fin 100s linear}", f'<div id="c" style="display:contents">{S}<b>SIBLING_ANIM</b></div>', "() => {}", "SIBLING_ANIM"),
    ("has(span) animation elsewhere", KF + ".w:not(:has(span)) .t{animation:fin 100s linear}", f'<div class="w"><div id="c" style="display:contents">{S}</div><p class="t">HAS_TARGET</p></div>', "() => {}", "HAS_TARGET"),
    ("has(*) animation elsewhere", KF + "#c:not(:has(*)) + .t{animation:fin 100s linear}", f'<div class="w"><div id="c" style="display:contents">{S}</div><p class="t">HAS_TARGET</p></div>', "() => {}", "HAS_TARGET"),
    (":empty rules + contents", "span:empty{display:none} *:empty{display:none}", C, "() => {}", S),
    ("appendChild/insertBefore throw (instance + prototype)", "", C,
     "() => { document.getElementById('c').appendChild = () => { throw new Error('x'); }; Node.prototype.appendChild = function(){ throw new Error('proto'); }; Node.prototype.insertBefore = function(){ throw new Error('proto'); }; }", S),
    ("remove()/removeChild no-op", "", C,
     "() => { Element.prototype.remove = function () {}; Node.prototype.removeChild = function (n) { return n; }; }", S),
    ("createElement throws", "", C, "() => { Document.prototype.createElement = function(){ throw new Error('ce'); }; }", S),
]


def run_side(browser, label, css, body, pre, must):
    out = {"case": label}
    for tag, js in VERS.items():
        page, errors = new_page(browser)
        page.set_content(HEAD.replace("{css}", css).replace("{body}", body))
        page.wait_for_timeout(2500 if "anim" in label else 100)
        page.evaluate(MO)
        page.evaluate(pre)
        clock0 = page.evaluate(CLOCK)
        html0 = page.evaluate("() => document.documentElement.outerHTML")
        try:
            seen, exc = page.evaluate(js), None
        except Exception as e:  # noqa: BLE001
            seen, exc = "", str(e).splitlines()[0]
        out[tag] = {"must_seen": must in seen, "pos_ctrl": "POSCTRL_OK" in seen, "exception": exc,
                    "clock_before": clock0, "clock_after": page.evaluate(CLOCK),
                    "html_unchanged": page.evaluate("() => document.documentElement.outerHTML") == html0,
                    "mutation_records": page.evaluate(RECS), "console_errors": len(errors)}
        page.close()
    return out


def fixture(browser):
    url = (ROOT / "tests/fixtures/bidi_site/cvcontents.html").as_uri()
    out = {}
    for tag, js in VERS.items():
        page, errors = new_page(browser)
        page.goto(url)
        page.wait_for_timeout(400)
        page.evaluate(MO)
        c0 = page.evaluate(CLOCK)
        seen = page.evaluate(js)
        out[tag] = {"reported_glyphs": len(seen), "seen": seen, "clock_before": c0, "clock_after": page.evaluate(CLOCK),
                    "mutation_records": page.evaluate(RECS), "console_errors": len(errors)}
        page.close()
    return out


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        cases = [run_case(browser, *c) for c in CASES]
        side = [run_side(browser, *s) for s in SIDE]
        fx = fixture(browser)
        version = browser.version
        browser.close()
    rep = {"unit": "at438-display-contents", "cycle_checked": 2, "by": "checker Mode D (own Chromium, own pages)",
           "date": "2026-09-16", "chromium": version,
           "versions": {"OLD": "c687b73^ (pre-AT-438)", "PROBE": "c687b73 (cycle 1)", "NEW": "bound tree == ba30b71 (cycle 2)"},
           "groundtruth": "full-page screenshot hash before/after replacing the sentinel text node (same-length glyphs, monospace)",
           "cases": cases, "side_effects": side, "fixture_cvcontents_before_after": fx}
    OUT.write_text(json.dumps(rep, indent=1), encoding="utf-8")
    for c in cases:
        print(f"{c['case'][:50]:<50} painted={c['painted']!s:<5} OLD={c['OLD']['verdict']:<14} PROBE={c['PROBE']['verdict']:<14} "
              f"NEW={c['NEW']['verdict']:<14} pc={all(c[t]['pos_ctrl'] for t in VERS)} gt={c['gt_found']} "
              f"mut={[len(c[t]['mutations']) for t in VERS]} ce={[c[t]['console_errors'] for t in VERS]}")
    for s in side:
        print(json.dumps(s))
    for t, v in fx.items():
        print("FIXTURE", t, v["reported_glyphs"], v["seen"], v["clock_before"], v["clock_after"], v["mutation_records"], v["console_errors"])


main()
