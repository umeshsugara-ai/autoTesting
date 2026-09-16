"""Checker Mode D, at438 cycle 3 -- point 2: attacks on the NEW mechanisms (::details-content,
first-summary exemption, check-before-skip, flatParent). Reuses moded3.py's machinery verbatim
(same four versions, same screenshot ground truth, same positive control, same observers)."""
import json, re, sys
from pathlib import Path

HERE = Path(__file__).parent
_src = (HERE / "moded3.py").read_text(encoding="utf-8")
exec(_src[: _src.rindex("main()")])  # everything except the trailing call

ROOTS = "window.__roots = window.__roots || [];"


def sh(host_id, mode, inner):
    return (f"{ROOTS} {{ const r = document.getElementById('{host_id}').attachShadow({{mode:'{mode}'}});"
            f" r.innerHTML = {json.dumps(inner)}; window.__roots.push(r); }}")


NESTED = (ROOTS + " const r = document.getElementById('host').attachShadow({mode:'open'});"
          " r.innerHTML = '<div id=\"ih\"><slot></slot></div>'; window.__roots.push(r);"
          " const r2 = r.getElementById('ih').attachShadow({mode:'@M@'}); r2.innerHTML = @INNER@; window.__roots.push(r2);")


def nested(mode, inner):
    return f'<div id="host">{C}</div>', NESTED.replace("@M@", mode).replace("@INNER@", json.dumps(inner))


ATTACKS = [
    # --- ::details-content support / pseudo display ---
    ("A1 closed details, NO author override", "", f"<details><summary>s</summary>{C}</details>", None),
    ("A2 open details, NO author override", "", f"<details open><summary>s</summary>{C}</details>", None),
    ("A3 closed, ::details-content{display:contents}", "details::details-content{display:contents}", f"<details><summary>s</summary>{C}</details>", None),
    ("A4 closed, ::details-content{display:inline}", "details::details-content{display:inline}", f"<details><summary>s</summary>{C}</details>", None),
    ("A5 open, ::details-content{display:none}", "details::details-content{display:none}", f"<details open><summary>s</summary>{C}</details>", None),
    ("A6 closed, ::details-content{content-visibility:auto}", "details::details-content{content-visibility:auto}", f"<details><summary>s</summary>{C}</details>", None),
    ("A7 open, [open]::details-content{content-visibility:hidden}", "details[open]::details-content{content-visibility:hidden}", f"<details open><summary>s</summary>{C}</details>", None),
    # --- first summary added / removed by script, nested summary ---
    ("B1 closed: FIRST summary removed by script, contents summary becomes first", "",
     f'<details id="d"><summary id="s1">first</summary><summary style="display:contents"><span id="c" style="display:contents">{S}</span></summary></details>',
     "document.getElementById('s1').remove()"),
    ("B2 closed: summary inserted before a body contents element", "",
     f'<details id="d">{C}</details>',
     "const s=document.createElement('summary');s.textContent='late';document.getElementById('d').prepend(s)"),
    ("B3 closed: new summary prepended before the contents summary", "",
     f'<details id="d"><summary style="display:contents"><span id="c" style="display:contents">{S}</span></summary></details>',
     "const s=document.createElement('summary');s.textContent='late';document.getElementById('d').prepend(s)"),
    ("B4 closed: summary nested in a div wrapper", "",
     f'<details><div><summary><span id="c" style="display:contents">{S}</span></summary></div></details>', None),
    ("B5 closed: summary nested in a display:contents wrapper", "",
     f'<details><div style="display:contents"><summary><span id="c" style="display:contents">{S}</span></summary></div></details>', None),
    ("B6 closed: contents element BEFORE the first summary", "",
     f'<details>{C}<summary>s</summary></details>', None),
    # --- name-grouped exclusive accordions ---
    ("C1 name=x: A open, then B opened by script (A closes), contents in A", "",
     f'<details name="x" id="a" open><summary>a</summary>{C}</details><details name="x" id="b"><summary>b</summary><p>bb</p></details>',
     "document.getElementById('b').open = true"),
    ("C2 name=x: B open, then A opened by script, contents in A", "",
     f'<details name="x" id="a"><summary>a</summary>{C}</details><details name="x" id="b" open><summary>b</summary><p>bb</p></details>',
     "document.getElementById('a').open = true"),
    # --- flat tree: nested shadow, slot into slot, closed shadow ---
    ("D1 slot->slot, inner shadow slot inside CLOSED details", "", *nested("open", "<details><summary>s</summary><slot></slot></details>")),
    ("D2 slot->slot, inner shadow slot inside OPEN details", "", *nested("open", "<details open><summary>s</summary><slot></slot></details>")),
    ("D3 slot->slot, inner shadow visible div", "", *nested("open", "<div><slot></slot></div>")),
    ("D4 slot->slot, inner CLOSED-mode shadow, slot in closed details", "", *nested("closed", "<details><summary>s</summary><slot></slot></details>")),
    ("D5 closed-mode shadow, slot inside CLOSED details", "", f'<div id="host">{C}</div>', sh("host", "closed", "<details><summary>s</summary><slot></slot></details>")),
    ("D6 closed-mode shadow, slot inside visible div", "", f'<div id="host">{C}</div>', sh("host", "closed", "<div><slot></slot></div>")),
    ("D7 closed-mode shadow, slot inside cv:hidden div", "", f'<div id="host">{C}</div>', sh("host", "closed", '<div style="content-visibility:hidden"><slot></slot></div>')),
    ("D8 open shadow: host inside CLOSED details, slot at shadow-root top", "", f'<details><summary>s</summary><div id="host">{C}</div></details>', sh("host", "open", "<slot></slot>")),
    ("D9 open shadow: slot as FIRST summary's child", "", f'<div id="host">{C}</div>', sh("host", "open", "<details><summary><slot></slot></summary><p>b</p></details>")),
    # --- hidden=until-found / cv:hidden on the details element itself ---
    ("E1 details hidden=until-found (open), contents in body", "", f'<details open hidden="until-found"><summary>s</summary>{C}</details>', None),
    ("E2 details hidden=until-found (open), contents in summary", "", f'<details open hidden="until-found"><summary><span id="c" style="display:contents">{S}</span></summary></details>', None),
    ("E3 details content-visibility:hidden (open), contents in body", "", f'<details open style="content-visibility:hidden"><summary>s</summary>{C}</details>', None),
    ("E4 details content-visibility:hidden (open), contents in summary", "", f'<details open style="content-visibility:hidden"><summary><span id="c" style="display:contents">{S}</span></summary></details>', None),
    ("E5 details content-visibility:hidden (closed), contents in summary", "", f'<details style="content-visibility:hidden"><summary><span id="c" style="display:contents">{S}</span></summary></details>', None),
]

PSEUDO = ("() => { const all = [document, ...(window.__roots || [])].flatMap(r => [...r.querySelectorAll('details')]);"
          " return { supports: CSS.supports('selector(::details-content)'),"
          " details: all.map(x => ({open: x.open, dc_cv: getComputedStyle(x, '::details-content').contentVisibility,"
          " dc_display: getComputedStyle(x, '::details-content').display, own_cv: getComputedStyle(x).contentVisibility})),"
          " bogus_pseudo_cv: all.length ? getComputedStyle(all[0], '::no-such-pseudo').contentVisibility : null,"
          " body_dc_cv: getComputedStyle(document.body, '::details-content').contentVisibility }; }")
OPENS = "() => [document, ...(window.__roots || [])].flatMap(r => [...r.querySelectorAll('details')]).map(x => x.open)"


def flat_parent_src():
    m = re.search(r"function flatParent\(node\) \{.*?\n  \}", VERS["NEW"], re.S)
    return m.group(0)


TERM = ("() => { @FP@ const roots = [document, ...(window.__roots || [])]; let maxSteps = 0, walked = 0, threw = null;"
        " for (const r of roots) { const w = document.createTreeWalker(r, NodeFilter.SHOW_ALL); let n;"
        " while ((n = w.nextNode())) { walked++; let steps = 0; try { for (let x = n; x; x = flatParent(x)) { if (++steps > 1000) break; } }"
        " catch (e) { threw = String(e); } maxSteps = Math.max(maxSteps, steps); } }"
        " return {walked, maxSteps, threw}; }")


def run_attack(browser, label, css, body, setup, shots):
    row = run_case(browser, label, css, body, setup)
    page, errors = new_page(browser)
    page.set_content(HEAD.replace("{css}", css).replace("{body}", body))
    if setup:
        page.evaluate(setup)
    page.wait_for_timeout(150)
    row["pseudo"] = page.evaluate(PSEUDO)
    row["termination"] = page.evaluate(TERM.replace("@FP@", flat_parent_src()))
    o0 = page.evaluate(OPENS)
    page.evaluate(VERS["NEW"])
    row["details_open_unchanged_by_NEW"] = page.evaluate(OPENS) == o0
    tag = label.split()[0]
    if tag in shots:
        page.screenshot(path=str(HERE / f"{tag}.png"), full_page=True)
        row["screenshot"] = f"{tag}.png"
    row["console_errors_extra_page"] = len(errors)
    page.close()
    return row


def main2():
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        rows = [run_attack(browser, *a, shots={"A1", "A2", "A3", "A4", "D5", "B1"}) for a in ATTACKS]
        version = browser.version
        browser.close()
    Path(sys.argv[1]).write_text(json.dumps({"chromium": version, "attacks": rows}, indent=1), encoding="utf-8")
    for c in rows:
        print(f"{c['case'][:62]:<62} painted={c['painted']!s:<5} OLD={c['OLD']['verdict']:<14} PROBE={c['PROBE']['verdict']:<14} "
              f"C2={c['C2']['verdict']:<14} NEW={c['NEW']['verdict']:<14} pc={all(c[t]['pos_ctrl'] for t in VERS)} gt={c['gt_found']} "
              f"mutNEW={len(c['NEW']['mutations'])} ce={[c[t]['console_errors'] for t in VERS]}+{c['console_errors_extra_page']} "
              f"term={c['termination']} openSame={c['details_open_unchanged_by_NEW']}")
        print("    pseudo:", json.dumps(c["pseudo"]))


main2()
