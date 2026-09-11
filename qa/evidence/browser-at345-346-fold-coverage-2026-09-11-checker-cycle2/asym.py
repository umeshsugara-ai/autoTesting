import sys, unicodedata, re
sys.path.insert(0, "D:/autoTesting/src")
from autotester.core import redact
from autotester.core.redact import Redactor, ASCII_CONFUSABLES, _FOLD_STRIP, _is_invisible

STORED = "CAF\u00c9_QUILT_APIKEY_31"           # precomposed U+00C9
SPELLED = STORED.replace("\u00c9", "E\u200b\u0301")  # E + ZWSP + combining acute

def fold_invisible(t):
    s = "".join(c for c in t if not _is_invisible(c))
    return _FOLD_STRIP.sub("", unicodedata.normalize("NFKC", s).translate(ASCII_CONFUSABLES)).casefold()

def fold_all_mn(t):
    s = "".join(c for c in t if _is_invisible(c) is False and unicodedata.category(c) != "Mn")
    return _FOLD_STRIP.sub("", unicodedata.normalize("NFKC", s).translate(ASCII_CONFUSABLES)).casefold()

for name, f in (("keying on invisibility", fold_invisible), ("stripping ALL Mn", fold_all_mn)):
    fs, fi = f(STORED), f(SPELLED)
    print(f"{name:24s} stored={fs!r}")
    print(f"{'':24s} input ={fi!r}")
    print(f"{'':24s} -> {'MATCH (leak closed)' if fs in fi or fi in fs else 'MISS  (LEAK)'}\n")
