"""Verify the maker's corrected C7 claim: `+` is caught by unquote_plus composition,
NOT by the widened separator class."""
import re, sys, unicodedata
from urllib.parse import unquote_plus
sys.path.insert(0,"D:/autoTesting/src")
import autotester.core.redact as R

CRED="ZEBRA_QUILT_APIKEY_31"
NARROW = re.compile(r"[\s\-_.]+")   # AT-339's original class
WIDE   = R._FOLD_STRIP

def fold(text, strip_re):
    s="".join(c for c in text if unicodedata.category(c)!="Cf")
    n=unicodedata.normalize("NFKC",s).translate(R.ASCII_CONFUSABLES)
    return strip_re.sub("",n).casefold()

target = fold(CRED, WIDE)
def variants(t): 
    d=unquote_plus(t); return [t,d,"".join(t.split()),"".join(d.split())]

for label, payload in (("plus", CRED.replace("_","+")), ("tilde", CRED.replace("_","~")),
                       ("slash", CRED.replace("_","/")), ("colon", CRED.replace("_",":"))):
    narrow_hit = any(target in fold(v, NARROW) for v in variants(payload))
    wide_hit   = any(target in fold(v, WIDE)   for v in variants(payload))
    narrow_raw = target in fold(payload, NARROW)   # no variant composition
    print(f"{label:6s}  caught-with-NARROW-class+variants={narrow_hit}  "
          f"caught-with-NARROW-class-raw-only={narrow_raw}  caught-with-WIDE={wide_hit}")
