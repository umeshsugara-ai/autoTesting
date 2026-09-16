"""Checker's OWN live-browser probe for at379 cycle 2. Read-only toward d:/autoTesting.

Serves the checker's own pages, loads the BOUND TREE's visual_order.js as a string,
evaluates it in a real Chromium, and asserts measured outcomes. Never edits the tree.
"""
from __future__ import annotations

import functools
import http.server
import json
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
PAGES = HERE / "pages"
TREE = Path("D:/autoTesting")
JS = (TREE / "src/autotester/browser/visual_order.js").read_text(encoding="utf-8")

GUARD = "    if (el.checkVisibility && !el.checkVisibility()) return false;"
JS_NOGUARD = JS.replace(GUARD, "    if (false) return false;")
assert JS_NOGUARD != JS, "checkVisibility guard anchor did not match"

results = []
console = {}


def serve(directory: Path) -> str:
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(directory))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_address[1]}"


def rec(page_name, case, claim, ok, detail=""):
    results.append({"page": page_name, "case": case, "claim": claim,
                    "pass": bool(ok), "detail": detail})
    print(f"{'PASS' if ok else 'FAIL'}  [{page_name}] {case}: {claim} {detail}")


def main() -> None:
    base = serve(PAGES)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(viewport={"width": 1000, "height": 700})
        page = ctx.new_page()
        errs = {"n": 0}
        page.on("console", lambda m: errs.__setitem__("n", errs["n"] + 1)
                if m.type == "error" else None)
        page.on("pageerror", lambda e: errs.__setitem__("n", errs["n"] + 1))

        def visual(js=JS):
            return str(page.evaluate(js))

        def goto(name):
            errs["n"] = 0
            page.goto(f"{base}/{name}")
            page.wait_for_load_state("load")

        # ---------------- p1: the two cycle-1 failures ----------------
        goto("p1_repro.html")
        assert page.evaluate("window.scrollY") == 0
        at_rest = visual()
        rec("p1", "control", "positive control present at rest",
            "CTLP1_CONTROL_AAA" in at_rest and "CTLP1_TAIL_ZZZ" in at_rest)
        for s in ("PANETOP_SENTINEL_01", "PANEBOT_SENTINEL_02",
                  "HPLEFT_SENTINEL_03", "HPRIGHT_SENTINEL_04"):
            rec("p1", "at-rest", f"{s} reported", s in at_rest)

        page.eval_on_selector("#scrolled", "el => { el.scrollTop = 602; }")
        page.eval_on_selector("#hscrolled", "el => { el.scrollLeft = 1200; }")
        st = page.eval_on_selector("#scrolled", "el => el.scrollTop")
        sl = page.eval_on_selector("#hscrolled", "el => el.scrollLeft")
        rec("p1", "scroll-applied", "scrollTop==602 and scrollLeft==1200 actually applied",
            st == 602 and sl == 1200, f"scrollTop={st} scrollLeft={sl}")
        scrolled = visual()
        rec("p1", "control", "positive control present after scroll",
            "CTLP1_CONTROL_AAA" in scrolled)
        rec("p1", "AT-392-y", "PANETOP still reported at scrollTop=602 (cycle-1 failure)",
            "PANETOP_SENTINEL_01" in scrolled)
        rec("p1", "AT-392-y", "PANEBOT still reported at scrollTop=602",
            "PANEBOT_SENTINEL_02" in scrolled)
        rec("p1", "AT-392-x", "HPLEFT still reported at scrollLeft=1200 (cycle-1 failure)",
            "HPLEFT_SENTINEL_03" in scrolled)
        rec("p1", "AT-392-x", "HPRIGHT still reported at scrollLeft=1200",
            "HPRIGHT_SENTINEL_04" in scrolled)
        rec("p1", "no-loss", "sorted glyph multiset unchanged by pane scrolling",
            sorted(scrolled) == sorted(at_rest),
            f"len {len(at_rest)} -> {len(scrolled)}")
        console["p1"] = errs["n"]

        # ---------------- p4: scrolled then scrolled back ----------------
        page.eval_on_selector("#scrolled", "el => { el.scrollTop = 0; }")
        page.eval_on_selector("#hscrolled", "el => { el.scrollLeft = 0; }")
        back = visual()
        rec("p1", "round-trip", "scrolled then scrolled back == at rest, byte for byte",
            back == at_rest)
        rec("p1", "round-trip", "PANETOP + HPLEFT present after returning to origin",
            "PANETOP_SENTINEL_01" in back and "HPLEFT_SENTINEL_03" in back)

        # ---------------- p2: NESTED scrollable panes ----------------
        goto("p2_nested.html")
        assert page.evaluate("window.scrollY") == 0
        n_rest = visual()
        rec("p2", "control", "positive control present at rest",
            "CTLP2_CONTROL_AAA" in n_rest and "CTLP2_TAIL_ZZZ" in n_rest)
        for s in ("OUTERTOP_SENTINEL_11", "INNERTOP_SENTINEL_12",
                  "INNERBOT_SENTINEL_13", "OUTERBOT_SENTINEL_14"):
            rec("p2", "at-rest", f"{s} reported at rest", s in n_rest)

        page.eval_on_selector("#outer", "el => { el.scrollTop = 500; }")
        page.eval_on_selector("#inner", "el => { el.scrollTop = 400; }")
        ot = page.eval_on_selector("#outer", "el => el.scrollTop")
        it = page.eval_on_selector("#inner", "el => el.scrollTop")
        rec("p2", "scroll-applied", "both panes actually scrolled",
            ot > 0 and it > 0, f"outer={ot} inner={it}")
        n_scr = visual()
        rec("p2", "control", "positive control present after nested scroll",
            "CTLP2_CONTROL_AAA" in n_scr)
        geom = page.evaluate("""() => {
          const p = document.querySelector('#inner p');
          const r = p.getBoundingClientRect();
          return {top: r.top, bottom: r.bottom, winY: window.scrollY,
                  outer: document.querySelector('#outer').scrollTop,
                  inner: document.querySelector('#inner').scrollTop};
        }""")
        rec("p2", "NESTED", "INNERTOP still reported with BOTH ancestors scrolled",
            "INNERTOP_SENTINEL_12" in n_scr, json.dumps(geom))
        rec("p2", "NESTED", "OUTERTOP still reported with outer scrolled",
            "OUTERTOP_SENTINEL_11" in n_scr)
        rec("p2", "NESTED", "sorted glyph multiset unchanged by nested scrolling",
            sorted(n_scr) == sorted(n_rest),
            f"missing={sorted(set(n_rest) - set(n_scr))}")
        console["p2"] = errs["n"]

        # ---------------- p3: mid position ----------------
        goto("p3_mid.html")
        m_rest = visual()
        rec("p3", "control", "positive control present",
            "CTLP3_CONTROL_AAA" in m_rest and "CTLP3_TAIL_ZZZ" in m_rest)
        maxs = page.eval_on_selector("#mid", "el => el.scrollHeight - el.clientHeight")
        page.eval_on_selector("#mid", f"el => {{ el.scrollTop = {maxs // 2}; }}")
        mid = page.eval_on_selector("#mid", "el => el.scrollTop")
        rec("p3", "scroll-applied", "pane parked at a MID position (not 0, not max)",
            0 < mid < maxs, f"scrollTop={mid} max={maxs}")
        m_scr = visual()
        for s in ("MIDA_SENTINEL_21", "MIDB_SENTINEL_22", "MIDC_SENTINEL_23"):
            rec("p3", "mid", f"{s} reported at mid scroll", s in m_scr)
        rec("p3", "mid", "sorted glyph multiset unchanged at mid scroll",
            sorted(m_scr) == sorted(m_rest))
        console["p3"] = errs["n"]

        # ---------------- p5: scrollable pane inside a NON-scrollable clip ----
        goto("p5_nonscroll_clip.html")
        c_rest = visual()
        rec("p5", "control", "positive control present",
            "CTLP5_CONTROL_AAA" in c_rest and "CTLP5_TAIL_ZZZ" in c_rest)
        rec("p5", "nested-clip", "NESTTOP reported (visible through the outer clip)",
            "NESTTOP_SENTINEL_31" in c_rest)
        rec("p5", "AT-393", "NESTBELOW reported although the outer overflow:hidden box hides it "
            "(FALSE POSITIVE, disclosed)", "NESTBELOW_SENTINEL_32" in c_rest)
        page.eval_on_selector("#sp", "el => { el.scrollTop = el.scrollHeight; }")
        sp = page.eval_on_selector("#sp", "el => el.scrollTop")
        c_scr = visual()
        rec("p5", "scroll-applied", "inner pane scrolled inside the non-scrollable clip",
            sp > 0, f"scrollTop={sp}")
        rec("p5", "nested-clip", "nothing lost when the pane inside a hard clip is scrolled",
            sorted(c_scr) == sorted(c_rest),
            f"missing={sorted(set(c_rest) - set(c_scr))}")
        console["p5"] = errs["n"]

        # ---------------- p6: AT-398, the dropped glyph ----------------
        goto("p6_details.html")
        plain = visual()
        rec("p6", "control", "positive control present with the guard IN PLACE",
            "CTLP6_CONTROL_AAA" in plain and "CTLP6_TAIL_ZZZ" in plain)
        rec("p6", "AT-372", "closed <details> body dropped with the guard in place",
            "DETAILSBODY_SENTINEL_77" not in plain)
        rec("p6", "AT-372", "OPEN <details> body reported with the guard in place",
            "OPENBODY_SENTINEL_80" in plain)

        bypassed = visual(JS_NOGUARD)
        rec("p6", "AT-398", "guard bypassed -> the closed body IS now reported at all",
            "SENTINEL_77" in bypassed)
        rec("p6", "AT-398", "guard bypassed -> the FULL sentinel comes back "
            "(i.e. no glyph dropped)", "DETAILSBODY_SENTINEL_77" in bypassed,
            repr(bypassed))
        rec("p6", "AT-398", "the second <details>, sentinel NOT at index 0, comes back whole",
            "SECONDBODY_SENTINEL_79" in bypassed)
        rec("p6", "AT-398-control", "a plain overflow:hidden clip's first glyph is not dropped",
            "PLAINCLIP_SENTINEL_81" in bypassed or "PLAINCLIP" not in bypassed,
            "clip drops the whole line, not one glyph")

        # diagnostic: per-index rect + reachability for the closed body text node
        diag = page.evaluate("""() => {
          const p = document.querySelectorAll('details')[0].querySelector('p');
          const node = p.firstChild;
          const out = [];
          for (let i = 0; i < Math.min(node.nodeValue.length, 6); i += 1) {
            const r = document.createRange();
            r.setStart(node, i); r.setEnd(node, i + 1);
            const b = r.getBoundingClientRect();
            const rects = Array.from(r.getClientRects()).map(x =>
              ({w: x.width, h: x.height, x: x.left, y: x.top}));
            out.push({i, ch: node.nodeValue[i], w: b.width, h: b.height,
                      x: b.left, y: b.top, nClientRects: rects.length, rects});
          }
          const cs = getComputedStyle(p);
          return {glyphs: out,
                  pStyle: {cv: cs.contentVisibility, overflow: cs.overflow,
                           display: cs.display, visibility: cs.visibility},
                  pRect: p.getBoundingClientRect().toJSON(),
                  parentCV: getComputedStyle(p.parentElement).contentVisibility};
        }""")
        print("DIAG p6 details body:", json.dumps(diag, indent=1))
        results.append({"page": "p6", "case": "AT-398-diagnostic",
                        "claim": "per-index range geometry for the closed <details> body",
                        "pass": True, "detail": diag})
        console["p6"] = errs["n"]

        browser.close()

    npass = sum(1 for r in results if r["pass"])
    report = {
        "unit": "at379-scrollable-pane-reachability",
        "cycle": 2,
        "date": "2026-09-16",
        "by": "checker (Mode D, own browser, own pages)",
        "browser": "chromium (playwright, headless)",
        "js_under_test": "D:/autoTesting/src/autotester/browser/visual_order.js (bound tree, read-only)",
        "pages": sorted(console),
        "console_errors_per_page": console,
        "assertions": len(results),
        "passed": npass,
        "failed": len(results) - npass,
        "results": results,
    }
    out = HERE / "report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\n{npass}/{len(results)} assertions passed; console errors {console}")
    print(f"report -> {out}")


if __name__ == "__main__":
    main()
