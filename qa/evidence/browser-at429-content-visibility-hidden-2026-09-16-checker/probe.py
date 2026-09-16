"""Checker Mode D probe for at429: independent pages, ground truth by screenshot diff."""
import json, subprocess, sys, pathlib
from playwright.sync_api import sync_playwright

REPO = pathlib.Path("D:/autoTesting")
NEW = (REPO / "src/autotester/browser/visual_order.js").read_text(encoding="utf-8")
OLD = subprocess.run(["git", "-C", str(REPO), "show", "dbe6185^:src/autotester/browser/visual_order.js"],
                     capture_output=True, text=True, encoding="utf-8", check=True).stdout
FIX = (REPO / "tests/fixtures/bidi_site/cvhidden.html").read_text(encoding="utf-8")
CTRL = '<p id="ctl">CONTROLPOSITIVE_SEVENTYSEVEN</p>'

def page(body, head=""):
    return f"<!doctype html><meta charset=utf-8>{head}<body>{CTRL}{body}</body>"

# (name, html, sentinels, script-before-measure)
CASES = [
 ("auto_onscreen", page('<div style="content-visibility:auto">AUTOONSCREEN_A</div>'), ["AUTOONSCREEN_A"], None),
 ("auto_offscreen_cis", page('<div style="height:3000px"></div><div style="content-visibility:auto;contain-intrinsic-size:auto 40px">AUTOOFFSCREEN_B</div>'), ["AUTOOFFSCREEN_B"], None),
 ("auto_offscreen_cis_px", page('<div style="height:3000px"></div><div style="content-visibility:auto;contain-intrinsic-size:300px 40px"><p>AUTOOFFNESTED_C</p></div>'), ["AUTOOFFNESTED_C"], None),
 ("hidden_then_visible_by_script", page('<div id="t" style="content-visibility:hidden">TOGGLED_D</div><p>AFTERLINE_E</p>'), ["TOGGLED_D", "AFTERLINE_E"],
  "document.getElementById('t').style.contentVisibility='visible'"),
 ("hidden_then_auto_by_script", page('<div id="t" style="content-visibility:hidden"><p>TOGGLEDNEST_F</p></div>'), ["TOGGLEDNEST_F"],
  "document.getElementById('t').style.contentVisibility='auto'"),
 ("inline_span_hidden_with_sibling", page('<div><span style="content-visibility:hidden">SPANX_G</span>VISIBLESIB_H</div>'), ["SPANX_G", "VISIBLESIB_H"], None),
 ("inline_block_span_hidden_with_sibling", page('<div><span style="display:inline-block;content-visibility:hidden">IBX_I</span>VISIBLESIB_J</div>'), ["IBX_I", "VISIBLESIB_J"], None),
 ("display_contents_hidden", page('<div style="display:contents;content-visibility:hidden">DCONTENTS_K</div>'), ["DCONTENTS_K"], None),
 ("td_hidden", page('<table><tr><td style="content-visibility:hidden">TDCELL_L</td><td>TDOTHER_M</td></tr></table>'), ["TDCELL_L", "TDOTHER_M"], None),
 ("tr_hidden", page('<table><tr style="content-visibility:hidden"><td>TRCELL_N</td></tr></table>'), ["TRCELL_N"], None),
 ("custom_el_inline_hidden_direct", page('<x-card style="content-visibility:hidden">CUSTOMDIRECT_O</x-card>'), ["CUSTOMDIRECT_O"], None),
 ("custom_el_inline_hidden_nested", page('<x-card style="content-visibility:hidden"><b>CUSTOMNEST_P</b></x-card>'), ["CUSTOMNEST_P"], None),
 ("custom_el_block_hidden_nested", page('<x-card style="display:block;content-visibility:hidden"><p>CUSTOMBLOCKNEST_Q</p></x-card>'), ["CUSTOMBLOCKNEST_Q"], None),
 ("nested_3_levels", page('<div style="content-visibility:hidden"><div><section><article><p>DEEP3_R</p></article></section></div></div>'), ["DEEP3_R"], None),
 ("hidden_ancestor_auto_between", page('<div style="content-visibility:hidden"><div style="content-visibility:auto"><p>HIDAUTO_S</p></div></div>'), ["HIDAUTO_S"], None),
 ("hidden_ancestor_auto_direct_text", page('<div style="content-visibility:hidden"><div style="content-visibility:auto">HIDAUTODIRECT_T</div></div>'), ["HIDAUTODIRECT_T"], None),
 ("hidden_ancestor_inline_span", page('<div style="content-visibility:hidden"><span>HIDSPAN_U</span></div>'), ["HIDSPAN_U"], None),
 ("hidden_until_found", page('<div hidden="until-found">UNTILFOUND_V</div>'), ["UNTILFOUND_V"], None),
 ("input_hidden", page('<p><input id="i1" style="content-visibility:hidden" value="INPUTVAL_W"></p><p><input id="i2" value="INPUTOK_X"></p>'), ["INPUTVAL_W", "INPUTOK_X"], None),
 ("textarea_hidden", page('<textarea style="content-visibility:hidden">TEXTAREAVAL_Y</textarea>'), ["TEXTAREAVAL_Y"], None),
 ("input_in_hidden_block", page('<div style="content-visibility:hidden"><input value="INPUTINHID_Z"></div>'), ["INPUTINHID_Z"], None),
 ("body_hidden", "<!doctype html><meta charset=utf-8><body style=\"content-visibility:hidden\">" + CTRL + "<p>BODYP_AA</p>BODYTEXT_AB</body>", ["CONTROLPOSITIVE_SEVENTYSEVEN", "BODYP_AA", "BODYTEXT_AB"], None),
 ("html_hidden", "<!doctype html><html style=\"content-visibility:hidden\"><meta charset=utf-8><body>" + CTRL + "BODYTEXT_AC</body></html>", ["CONTROLPOSITIVE_SEVENTYSEVEN", "BODYTEXT_AC"], None),
 ("ruby_rt_hidden", page('<ruby>KANJI_AD<rt style="content-visibility:hidden">RUBYRT_AE</rt></ruby>'), ["KANJI_AD", "RUBYRT_AE"], None),
 ("li_marker_hidden_item", page('<ul><li style="content-visibility:hidden">LIITEM_AF</li><li>LIOK_AG</li></ul>'), ["LIITEM_AF", "LIOK_AG"], None),
 ("button_hidden", page('<button style="content-visibility:hidden">BUTTONTXT_AH</button>'), ["BUTTONTXT_AH"], None),
 # interleave layouts (manifest's b / e) + committed fixture
 ("layout_hidden_first", page('<div style="content-visibility:hidden">HIDDEN_S2</div><div style="content-visibility:auto">AUTO_S1</div>'), ["HIDDEN_S2", "AUTO_S1"], None),
 ("layout_auto_first", page('<div style="content-visibility:auto">AUTO_S1</div><div style="content-visibility:hidden">HIDDEN_S2</div>'), ["HIDDEN_S2", "AUTO_S1"], None),
 ("layout_hidden_plain_after", page('<div style="content-visibility:hidden">HIDDEN_S2</div><div>PLAIN_S3</div>'), ["HIDDEN_S2", "PLAIN_S3"], None),
 ("committed_fixture", FIX.replace("<p>Quarterly", CTRL + "<p>Quarterly"), ["CVHIDDEN_DIRECT_SENTINEL_61", "CVHIDDEN_NESTED_SENTINEL_62", "CVAUTO_ONSCREEN_SENTINEL_63"], None),
]

BLANK = """(s) => {
  const w = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
  let n; let c = 0;
  while ((n = w.nextNode())) { if (n.nodeValue.includes(s)) { n.nodeValue = n.nodeValue.split(s).join('\\u00a0'.repeat(s.length)); c++; } }
  for (const el of document.querySelectorAll('input,textarea')) { if (el.value.includes(s)) { el.value = el.value.split(s).join(' '.repeat(s.length)); c++; } }
  return c;
}"""
LOCATE = """(s) => {
  const w = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
  let n;
  while ((n = w.nextNode())) { if (n.nodeValue.includes(s)) { const el = n.parentElement; el.scrollIntoView({block:'center'}); return true; } }
  for (const el of document.querySelectorAll('input,textarea')) { if (el.value.includes(s)) { el.scrollIntoView({block:'center'}); return true; } }
  return false;
}"""


def ground_truth(ctx, html, sentinel, script):
    p = ctx.new_page()
    p.set_content(html); p.wait_for_timeout(150)
    if script: p.evaluate(script); p.wait_for_timeout(100)
    p.evaluate(LOCATE, sentinel); p.wait_for_timeout(250)
    a = p.screenshot()
    n = p.evaluate(BLANK, sentinel); p.wait_for_timeout(250)
    b = p.screenshot()
    p.close()
    return a != b, n


def main():
    out = {"unit": "at429-content-visibility-hidden", "cycle": 1, "cases": []}
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=True)
        out["chromium"] = br.version
        ctx = br.new_context(viewport={"width": 1000, "height": 700})
        for name, html, sentinels, script in CASES:
            rec = {"case": name, "sentinels": {}}
            for label, js in (("old", OLD), ("new", NEW)):
                p = ctx.new_page(); errs = []
                p.on("console", lambda m, e=errs: e.append(m.text) if m.type == "error" else None)
                p.on("pageerror", lambda x, e=errs: e.append(str(x)))
                p.set_content(html); p.wait_for_timeout(150)
                if script: p.evaluate(script); p.wait_for_timeout(100)
                rec[f"{label}_text"] = p.evaluate(js)
                rec[f"{label}_console_errors"] = len(errs)
                p.close()
            for s in sentinels:
                painted, blanked = ground_truth(ctx, html, s, script)
                rec["sentinels"][s] = {"painted_ground_truth": painted, "blanked_nodes": blanked,
                                        "old_reported": s in rec["old_text"], "new_reported": s in rec["new_text"]}
            rec["control_new"] = "CONTROLPOSITIVE_SEVENTYSEVEN" in rec["new_text"]
            out["cases"].append(rec)
        br.close()
    for c in out["cases"]:
        for s, v in c["sentinels"].items():
            v["new_false_negative"] = v["painted_ground_truth"] and not v["new_reported"]
            v["new_false_positive"] = (not v["painted_ground_truth"]) and v["new_reported"]
    json.dump(out, open(sys.argv[1], "w", encoding="utf-8"), indent=2)
    for c in out["cases"]:
        flags = []
        for s, v in c["sentinels"].items():
            flags.append(f"{s}: ink={int(v['painted_ground_truth'])} old={int(v['old_reported'])} new={int(v['new_reported'])}{' FN!' if v['new_false_negative'] else ''}{' FP!' if v['new_false_positive'] else ''}")
        print(f"{c['case']:40s} ctl={int(c['control_new'])} err={c['old_console_errors']}/{c['new_console_errors']} | " + " ; ".join(flags))
        print(f"   old={c['old_text']!r}\n   new={c['new_text']!r}")

main()
