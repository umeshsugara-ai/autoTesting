import json
from pathlib import Path
from playwright.sync_api import sync_playwright
S="C:/Users/Lenovo/AppData/Local/Temp/claude/d--autoTesting/30f63fa7-ff7f-443d-9d54-85867b5557ce/scratchpad"
NEW=Path("D:/autoTesting/src/autotester/browser/visual_order.js").read_text(encoding="utf-8")
OLD=Path(S+"/old_vo.js").read_text(encoding="utf-8")
KF="@keyframes fin{from{opacity:0}2%{opacity:1}to{opacity:1}}"
PAGES={
 "last-child sibling": (KF+"#c>b:last-child{animation:fin 100s linear}", '<p>POSCTRL_OK</p><div id="c" style="display:contents">SENTZQ_KEY<b>SIBLING_ANIM</b></div>'),
 "has() elsewhere": (KF+".w:not(:has(span)) .t{animation:fin 100s linear}", '<p>POSCTRL_OK</p><div class="w"><div id="c" style="display:contents">SENTZQ_KEY</div><p class="t">HAS_TARGET</p></div>'),
 "control: same page, no display:contents": (KF+"#c>b:last-child{animation:fin 100s linear}", '<p>POSCTRL_OK</p><div id="c">SENTZQ_KEY<b>SIBLING_ANIM</b></div>'),
 "clip-path plain div (pre-existing?)": ("", '<p>POSCTRL_OK</p><div style="clip-path:inset(50%)"><div>SENTZQ_KEY</div></div>'),
 "opacity0 on contents (old)": ("", '<p>POSCTRL_OK</p><div style="display:contents;opacity:0">SENTZQ_KEY</div>'),
}
res={}
with sync_playwright() as pw:
    b=pw.chromium.launch()
    for name,(css,body) in PAGES.items():
        for tag,js in (("old",OLD),("new",NEW)):
            p=b.new_page(); p.set_content(f"<!doctype html><style>{css}</style><body>{body}")
            p.wait_for_timeout(3000)
            before=p.evaluate("()=>document.getAnimations().map(a=>Math.round(a.currentTime))")
            p.screenshot(path=f"{S}/{tag}-{name[:10].replace(' ','_').replace(':','')}-before.png")
            seen=p.evaluate(js)
            after=p.evaluate("()=>document.getAnimations().map(a=>Math.round(a.currentTime))")
            p.screenshot(path=f"{S}/{tag}-{name[:10].replace(' ','_').replace(':','')}-after.png")
            res[f"{name} [{tag}]"]={"seen":seen,"anim_time_before":before,"anim_time_after":after}
            p.close()
    b.close()
print(json.dumps(res,indent=1))
