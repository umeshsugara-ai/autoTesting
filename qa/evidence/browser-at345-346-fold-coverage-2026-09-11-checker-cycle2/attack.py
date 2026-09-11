import sys
sys.path.insert(0, "D:/autoTesting/src")
from autotester.core.redact import Redactor, fold_credential

CRED = "ZEBRA_QUILT_APIKEY_31"
r = Redactor({"DEMO_PASSWORD": CRED})

named = {
 "U+034F CGJ":0x034F,"U+FE00 VS1":0xFE00,"U+FE0F VS16":0xFE0F,
 "U+180B MFVS1":0x180B,"U+180C":0x180C,"U+180D":0x180D,"U+180E MVS":0x180E,"U+180F MFVS4":0x180F,
 "U+115F HANGUL CHOSEONG FILLER":0x115F,"U+1160 JUNGSEONG FILLER":0x1160,
 "U+3164 HANGUL FILLER":0x3164,"U+FFA0 HALFWIDTH HANGUL FILLER":0xFFA0,
 "U+17B4 KHMER AQ":0x17B4,"U+17B5 KHMER AA":0x17B5,
 "U+E0001 LANGUAGE TAG":0xE0001,"U+E0041 TAG A":0xE0041,"U+E0100 VS17":0xE0100,"U+E0FFF":0xE0FFF,
 "U+1D173 MUSICAL BEGIN BEAM":0x1D173,"U+1D17A MUSICAL END PHRASE":0x1D17A,
 "U+2065 reserved DI":0x2065,"U+FFF0 reserved DI":0xFFF0,"U+1BCA0 SHORTHAND":0x1BCA0,
 "U+00AD SOFT HYPHEN":0x00AD,"U+061C ARABIC LETTER MARK":0x061C,"U+200B ZWSP":0x200B,
 "U+200C ZWNJ":0x200C,"U+200D ZWJ":0x200D,"U+2060 WORD JOINER":0x2060,"U+FEFF BOM":0xFEFF,
 "U+202E RLO":0x202E,
 # invisible-but-NOT-default-ignorable controls
 "U+2800 BRAILLE BLANK":0x2800,"U+3000 IDEOGRAPHIC SPACE":0x3000,"U+2000 EN QUAD":0x2000,
 "U+00A0 NBSP":0x00A0,"U+0000 NUL":0x0000,"U+0009 TAB":0x0009,
 "U+0600 ARABIC NUMBER SIGN":0x0600,"U+110BD KAITHI NUMBER SIGN":0x110BD,
}
print("== interleaved-spelling attack (True = guard catches it) ==")
bad=[]
for label, cp in sorted(named.items(), key=lambda kv: kv[1]):
    spelled = chr(cp).join(CRED)
    ok = r.contains_folded(spelled) or not r.is_clean(spelled)
    if not ok: bad.append(label)
    print(f"  {'CAUGHT ' if ok else 'ESCAPED'}  {label}")
print("\nESCAPED:", bad or "none")

print("\n== brute-force hunt: any code point 0..0x110000 that, interleaved, escapes AND is not a visible glyph ==")
import unicodedata
esc=[]
for cp in range(0x110000):
    ch=chr(cp)
    cat=unicodedata.category(ch)
    if cat not in ("Cf","Cc","Cn","Co","Cs","Mn","Me","Zs","Zl","Zp"): continue
    if cat in ("Cs","Co"): continue
    if fold_credential(ch.join(CRED)) == fold_credential(CRED): continue
    esc.append((cp,cat))
print("  candidates that change the fold:", len(esc))
from collections import Counter
print("  by category:", Counter(c for _,c in esc))
