"""Checker Mode D for at438: display:contents in hiding contexts + probe side effects.
Ground truth: full-page screenshot before/after replacing the sentinel text node with a
same-length string of different glyphs in a monospace font (no layout shift, no colour trick)."""
import hashlib, json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

JS = Path("D:/autoTesting/src/autotester/browser/visual_order.js").read_text(encoding="utf-8")
OUT = Path(sys.argv[1])
POS = '<p style="margin:0 0 30px">POSCTRL_OK</p>'
HEAD = ('<!doctype html><meta charset=utf-8><style>body{margin:8px;font:20px monospace}{css}</style>'
        '<body>' + POS + '{body}</body>')
S = "SENTZQ_KEY"
C = f'<div id="c" style="display:contents">{S}</div>'

CASES = [  # (label, want_reported per author intent or None=let ground truth decide, css, body, setup_js)
    ("plain contents", "", C, None),
    ("open details", "", f"<details open><summary>s</summary>{C}</details>", None),
    ("closed details", "", f"<details><summary>s</summary>{C}</details>", None),
    ("closed details, contents nested twice", "", f'<details><summary>s</summary><div style="display:contents">{C}</div></details>', None),
    ("cv:hidden block", "", f'<div style="content-visibility:hidden">{C}</div>', None),
    ("display:none", "", f'<div style="display:none">{C}</div>', None),
    ("hidden attribute", "", f"<div hidden>{C}</div>", None),
    ("hidden=until-found", "", f'<div hidden="until-found">{C}</div>', None),
    ("visibility:hidden ancestor", "", f'<div style="visibility:hidden">{C}</div>', None),
    ("contents itself visibility:hidden", "", f'<div id="c" style="display:contents;visibility:hidden">{S}</div>', None),
    ("opacity:0 ancestor", "", f'<div style="opacity:0">{C}</div>', None),
    ("zero-alpha colour ancestor", "", f'<div style="color:rgba(0,0,0,0)">{C}</div>', None),
    ("contents itself zero-alpha", "", f'<div id="c" style="display:contents;color:rgba(0,0,0,0)">{S}</div>', None),
    ("overflow:hidden clip", "", f'<div style="overflow:hidden;height:30px;width:400px"><div style="height:200px">top</div>{C}</div>', None),
    ("off-screen absolute", "", f'<div style="position:absolute;left:-9999px;top:0">{C}</div>', None),
    ("text-indent -9999", "", f'<div style="text-indent:-9999px">{C}</div>', None),
    ("clip-path inset 100%", "", f'<div style="clip-path:inset(50%)">{C}</div>', None),
    ("closed dialog", "", f"<dialog>{C}</dialog>", None),
    ("unslotted light child of shadow host", "", f'<div id="host">{C}</div>',
     "document.getElementById('host').attachShadow({mode:'open'}).innerHTML='<p>shadow</p>'"),
    ("slotted light child of shadow host", "", f'<div id="host">{C}</div>',
     "document.getElementById('host').attachShadow({mode:'open'}).innerHTML='<slot></slot>'"),
    ("cv:auto far below (scrollable)", "", f'<div style="height:3000px"></div><div style="content-visibility:auto">{C}</div>', None),
    ("contents inside ul", "", f"<ul><li>a</li>{C}</ul>", None),
    ("contents inside tr (JS-built)", "", '<table><tr id="tr"><td>cell</td></tr></table>',
     f"const c=document.createElement('div');c.id='c';c.style.display='contents';c.textContent='{S}';document.getElementById('tr').appendChild(c)"),
    ("contents inside select (JS-built)", "", '<select id="sel"><option>opt</option></select>',
     f"const c=document.createElement('div');c.id='c';c.style.display='contents';c.textContent='{S}';document.getElementById('sel').appendChild(c)"),
    # author CSS that targets the PROBE, not the text
    ("author span:empty{display:none}", "span:empty{display:none}", C, None),
    ("author #c>span{display:none}", "#c>span{display:none}", C, None),
    ("author :empty{display:none} universal", "*:empty{display:none}", C, None),
    ("contents itself opacity:0 (opacity n/a on contents)", "", f'<div id="c" style="display:contents;opacity:0">{S}</div>', None),
]

GT = ("(s) => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);"
      " let n; while ((n = w.nextNode())) { if (n.nodeValue.includes(s)) {"
      " n.nodeValue = n.nodeValue.replace(s, 'MMMMMMMMMM'); return true; } } return false; }")


def shot(page):
    return hashlib.sha1(page.screenshot(full_page=True)).hexdigest()


def run_case(browser, label, css, body, setup):
    page = browser.new_page(viewport={"width": 900, "height": 600})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.set_content(HEAD.replace("{css}", css).replace("{body}", body))
    if setup:
        page.evaluate(setup)
    page.wait_for_timeout(150)
    html_before = page.evaluate("() => document.documentElement.outerHTML")
    seen = page.evaluate(JS)
    html_after = page.evaluate("() => document.documentElement.outerHTML")
    reported = S in seen
    page.evaluate("() => window.scrollTo(0,0)")
    b = shot(page)
    found = page.evaluate(GT, S)
    page.wait_for_timeout(80)
    a = shot(page)
    painted = b != a
    page.close()
    return {"case": label, "reported": reported, "painted_groundtruth": painted,
            "correct": reported == painted,
            "error": None if reported == painted else ("FALSE_POSITIVE" if reported else "FALSE_NEGATIVE"),
            "positive_control_seen": "POSCTRL_OK" in seen, "sentinel_found_for_gt": found,
            "dom_unchanged": html_before == html_after, "console_errors": len(errors)}


SIDE = [
    ("MutationObserver on contents element",
     "", f'<div id="c" style="display:contents">{S}</div>',
     """() => { window.__recs = []; new MutationObserver(rs => { for (const r of rs) window.__recs.push(
        {type: r.type, target: r.target.id, added: [...r.addedNodes].map(n => n.nodeName), removed: [...r.removedNodes].map(n => n.nodeName)}); })
        .observe(document.body, {subtree: true, childList: true, attributes: true, characterData: true}); }""",
     "() => new Promise(r => setTimeout(() => r(window.__recs), 50))"),
    ("animation on :last-child sibling restarts?",
     "@keyframes fin{from{opacity:0}2%{opacity:1}to{opacity:1}} #c>b:last-child{animation:fin 100s linear}",
     f'<div id="c" style="display:contents">{S}<b>SIBLING_ANIM</b></div>',
     "() => { window.__a0 = document.getAnimations().map(a => [a.animationName, a.currentTime]); }",
     "() => ({before: window.__a0, after: document.getAnimations().map(a => [a.animationName, a.currentTime]), op: getComputedStyle(document.querySelector('#c>b')).opacity})"),
    ("transition on :last-child sibling",
     "#c>b{transition:opacity 20s linear} #c>b:not(:last-child){opacity:0}",
     f'<div id="c" style="display:contents">{S}<b>SIBLING_TRANS</b></div>',
     "() => {}",
     "() => ({anims: document.getAnimations().map(a => [a.constructor.name, a.transitionProperty, a.currentTime, a.playState]), op: getComputedStyle(document.querySelector('#c>b')).opacity})"),
    (":has(span) on ancestor with animation",
     "@keyframes fin{from{opacity:0}2%{opacity:1}to{opacity:1}} .w:not(:has(span)) .t{animation:fin 100s linear}",
     f'<div class="w"><div id="c" style="display:contents">{S}</div><p class="t">HAS_TARGET</p></div>',
     "() => { window.__a0 = document.getAnimations().map(a => [a.animationName, a.currentTime]); }",
     "() => ({before: window.__a0, after: document.getAnimations().map(a => [a.animationName, a.currentTime]), op: getComputedStyle(document.querySelector('.t')).opacity})"),
    ("appendChild throws (instance override)",
     "", f'<div id="c" style="display:contents">{S}</div>',
     "() => { document.getElementById('c').appendChild = () => { throw new Error('restricted children'); }; }",
     "() => document.body.innerHTML"),
    ("remove() is a no-op (prototype patch)",
     "", f'<div id="c" style="display:contents">{S}</div>',
     "() => { Element.prototype.remove = function () {}; }",
     "() => document.getElementById('c').innerHTML"),
]


def run_side(browser, label, css, body, pre, post):
    page = browser.new_page(viewport={"width": 900, "height": 600})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.set_content(HEAD.replace("{css}", css).replace("{body}", body))
    page.wait_for_timeout(3000 if "anim" in label or "has" in label or "transition" in label else 100)
    page.evaluate(pre)
    inner_before = page.evaluate("() => document.body.innerHTML")
    try:
        seen = page.evaluate(JS)
        exc = None
    except Exception as e:  # noqa: BLE001
        seen, exc = "", str(e).splitlines()[0]
    res = {"case": label, "visual_text": seen, "exception": exc,
           "innerHTML_unchanged": page.evaluate("() => document.body.innerHTML") == inner_before,
           "post": page.evaluate(post), "positive_control_seen": "POSCTRL_OK" in seen,
           "console_errors": len(errors)}
    page.close()
    return res


def main():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        cases = [run_case(browser, *c) for c in CASES]
        side = [run_side(browser, *s) for s in SIDE]
        version = browser.version
        browser.close()
    report = {"unit": "at438-display-contents", "by": "checker (Mode D, own Chromium, own probe pages)",
              "date": "2026-09-16", "chromium": version,
              "groundtruth": "full-page screenshot hash before/after replacing the sentinel text node with same-length different glyphs in monospace",
              "hiding_and_visible_contexts": cases, "probe_side_effects": side}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    for c in cases:
        print(f"{c['case']:<52} reported={c['reported']!s:<5} painted={c['painted_groundtruth']!s:<5} {c['error'] or 'ok'} pc={c['positive_control_seen']} gt={c['sentinel_found_for_gt']} dom={c['dom_unchanged']} ce={c['console_errors']}")
    for s in side:
        print(json.dumps(s))


main()
