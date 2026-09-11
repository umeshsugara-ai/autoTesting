"""Enumerate EVERY code point that defeats fold_credential when interleaved."""
import sys, json, unicodedata
sys.path.insert(0, "d:/autoTesting/src")
from autotester.core.redact import fold_credential

CRED = "ZEBRA_QUILT_APIKEY_31"
target = fold_credential(CRED)
print("folded target:", target)

survivors = []
for cp in range(0x110000):
    if 0xD800 <= cp <= 0xDFFF:
        continue  # handled separately
    ch = chr(cp)
    spelled = ch.join(CRED)
    if target not in fold_credential(spelled):
        survivors.append(cp)

print("total code points that DEFEAT the fold when interleaved:", len(survivors))
from collections import Counter
cats = Counter(unicodedata.category(chr(cp)) for cp in survivors)
print("by category:", dict(sorted(cats.items(), key=lambda kv: -kv[1])))

# Narrow to the classes the dispatch names: invisible-capable ones.
INTEREST = {"Cn","Co","Mn","Me","Zs","Zl","Zp","So","Lo","Sk"}
cand = [cp for cp in survivors if unicodedata.category(chr(cp)) in INTEREST]
print("candidates in invisible-capable categories:", len(cand))
json.dump(survivors, open("d:/autoTesting/qa/evidence/browser-at345-346-fold-coverage-2026-09-11-checker/survivors.json","w"))

# named probes from the dispatch
named = {
 "U+2800 BRAILLE BLANK": 0x2800, "U+E000 PUA": 0xE000, "U+F8FF PUA-end": 0xF8FF,
 "U+100000 PUA-B": 0x100000, "U+0378 unassigned Cn": 0x0378, "U+05EB unassigned": 0x05EB,
 "U+2065 unassigned(DI)": 0x2065, "U+3164 hangul filler": 0x3164, "U+115F hangul choseong filler": 0x115F,
 "U+FFA0 halfwidth hangul filler": 0xFFA0, "U+202E RLO": 0x202E, "U+200F RLM": 0x200F,
 "U+2028 line sep": 0x2028, "U+2029 para sep": 0x2029, "U+180E mongolian vowel sep": 0x180E,
 "U+00A0 NBSP": 0x00A0, "U+1D159 musical null note head": 0x1D159, "U+FFF9 interlinear": 0xFFF9,
 "U+0001 SOH": 0x0001, "U+007F DEL": 0x007F, "U+0000 NUL": 0x0000,
 "U+17B4 khmer inherent": 0x17B4, "U+A4A0 unassigned?": 0xA4A0, "U+2061 function app": 0x2061,
 "U+13430 egyptian format": 0x13430, "U+1CF00 unassigned": 0x1CF00, "U+FE0F VS16": 0xFE0F,
 "U+0335 combining short stroke": 0x0335, "U+0300 combining grave": 0x0300,
}
print()
for label, cp in named.items():
    ch = chr(cp)
    bypass = target not in fold_credential(ch.join(CRED))
    print(f"{'BYPASS ' if bypass else 'caught  '} {label:38s} cat={unicodedata.category(ch)}")
