"""Checker follow-up: (a) is the flex/grid contain:paint FP pre-existing on a PLAIN div (no display:contents)?
(b) does the ::details-content pseudo's computed content-visibility answer the closed-details question
the walk enumerates by tag, including the author override and details{display:contents}? Read-only measurements."""
import hashlib, json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path("D:/autoTesting")
NEW = (ROOT / "src/autotester/browser/visual_order.js").read_text(encoding="utf-8")
S = "SENTZQ_KEY"
HEAD = '<!doctype html><meta charset=utf-8><style>body{margin:8px;font:20px monospace}%s</style><body><p>POSCTRL_OK</p>%s'
GT = ("(s) => { const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);"
      " let n; while ((n = w.nextNode())) { if (n.nodeValue.includes(s)) { n.nodeValue = n.nodeValue.replace(s, 'MMMMMMMMMM'); return true; } } return false; }")
PLAIN = [
    ("plain div in flex contain:paint height:0", "", f'<div style="display:flex;height:0;contain:paint"><div>{S}</div></div>'),
    ("plain div in grid contain:paint height:0", "", f'<div style="display:grid;grid-template-rows:0;height:0;contain:paint"><div>{S}</div></div>'),
    ("plain div in flex clip-path", "", f'<div style="display:flex;clip-path:inset(0 0 100% 0)"><div>{S}</div></div>'),
]
PSEUDO = [
    ("closed", "", f'<details id="d"><summary>s</summary><div>{S}</div></details>'),
    ("open", "", f'<details id="d" open><summary>s</summary><div>{S}</div></details>'),
    ("closed + author ::details-content visible", "details::details-content{content-visibility:visible}", f'<details id="d"><summary>s</summary><div>{S}</div></details>'),
    ("closed, details display:contents", "", f'<details id="d" style="display:contents"><summary>s</summary><div>{S}</div></details>'),
]
out = {"plain_div_classification": [], "details_content_pseudo": []}
with sync_playwright() as pw:
    b = pw.chromium.launch()
    for label, css, body in PLAIN:
        p = b.new_page(viewport={"width": 900, "height": 600}); p.set_content(HEAD % (css, body)); p.wait_for_timeout(100)
        seen = p.evaluate(NEW); h0 = hashlib.sha1(p.screenshot(full_page=True)).hexdigest(); p.evaluate(GT, S)
        painted = h0 != hashlib.sha1(p.screenshot(full_page=True)).hexdigest()
        out["plain_div_classification"].append({"case": label, "reported": S in seen, "painted": painted, "pos_ctrl": "POSCTRL_OK" in seen})
        p.close()
    for label, css, body in PSEUDO:
        p = b.new_page(viewport={"width": 900, "height": 600}); p.set_content(HEAD % (css, body)); p.wait_for_timeout(100)
        cv = p.evaluate("() => getComputedStyle(document.getElementById('d'), '::details-content').contentVisibility")
        h0 = hashlib.sha1(p.screenshot(full_page=True)).hexdigest(); p.evaluate(GT, S)
        painted = h0 != hashlib.sha1(p.screenshot(full_page=True)).hexdigest()
        out["details_content_pseudo"].append({"case": label, "pseudo_content_visibility": cv, "body_painted": painted})
        p.close()
    b.close()
Path(ROOT / "qa/evidence/browser-at438-display-contents-2026-09-16-checker-c2/classify.json").write_text(json.dumps(out, indent=1))
print(json.dumps(out, indent=1))
