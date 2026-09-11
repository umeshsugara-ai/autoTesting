"""Independent audit of redact._DEFAULT_IGNORABLE against Unicode 14 DI.

Authoritative inputs:
  - Other_Default_Ignorable_Code_Point: fetched verbatim from
    unicode.org/Public/14.0.0/ucd/PropList.txt this session.
  - Variation_Selector: FE00..FE0F, 180B..180D, 180F, E0100..E01EF (Unicode 14).
  - Cf: read from THIS MACHINE's unicodedata (unidata_version 14.0.0).
  - Exclusions per DerivedCoreProperties definition: White_Space,
    FFF9..FFFB, prepended concatenation marks, 13430..1343F.
"""
import unicodedata, sys
sys.path.insert(0, "D:/autoTesting/src")
from autotester.core import redact

MAX = 0x110000

OTHER_DI = [(0x034F,0x034F),(0x115F,0x1160),(0x17B4,0x17B5),(0x2065,0x2065),
            (0x3164,0x3164),(0xFFA0,0xFFA0),(0xFFF0,0xFFF8),(0xE0000,0xE0000),
            (0xE0002,0xE001F),(0xE0080,0xE00FF),(0xE01F0,0xE0FFF)]
VS = [(0x180B,0x180D),(0x180F,0x180F),(0xFE00,0xFE0F),(0xE0100,0xE01EF)]
EXCLUDE = [(0xFFF9,0xFFFB),(0x0600,0x0605),(0x06DD,0x06DD),(0x070F,0x070F),
           (0x0890,0x0891),(0x08E2,0x08E2),(0x110BD,0x110BD),(0x110CD,0x110CD),
           (0x13430,0x1343F)]

def expand(rs): return {c for lo,hi in rs for c in range(lo,hi+1)}

cf = {c for c in range(MAX) if unicodedata.category(chr(c)) == "Cf"}
di = (expand(OTHER_DI) | expand(VS) | cf) - expand(EXCLUDE)
di = {c for c in di if not chr(c).isspace()}

declared = expand(redact._DEFAULT_IGNORABLE)
stripped_by_code = {c for c in range(MAX) if redact._is_invisible(chr(c))}

def fmt(s):
    s = sorted(s); out=[]; i=0
    while i < len(s):
        j=i
        while j+1 < len(s) and s[j+1]==s[j]+1: j+=1
        out.append(f"U+{s[i]:04X}" if i==j else f"U+{s[i]:04X}..U+{s[j]:04X}")
        i=j+1
    return ", ".join(out) or "(none)"

print("unidata_version :", unicodedata.unidata_version)
print("DI code points  :", len(di))
print("guard strips    :", len(stripped_by_code))
print()
print("DI NOT stripped by the guard (UNDER-inclusion == leak risk):")
print("  ", fmt(di - stripped_by_code))
print()
print("Stripped but NOT DI (OVER-inclusion == false-positive risk):")
print("  ", fmt(stripped_by_code - di))
print()
non_cf = sorted(c for c in declared if unicodedata.category(chr(c)) != "Cf")
print("declared-range entries that are NOT Cf (the part the category test misses):")
print("  ", fmt(set(non_cf)))
