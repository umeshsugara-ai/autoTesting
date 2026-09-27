"""Live browser probe for T-186/AT-453 -- real headed-capable Chromium,
using the SHIPPING visual_text() (observe.py), not a hand-spliced JS copy."""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

from autotester.browser.observe import visual_text

FIXTURE = (Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "bidi_site" / "cvcontents.html")

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(FIXTURE.as_uri())
    page.wait_for_timeout(300)
    seen = visual_text(page)
    version = browser.version
    browser.close()

result = {
    "chromium": version,
    "A3_reported": "CONTENTS_DETAILSCONTENT_CONTENTS_A3" in seen,
    "A4_reported": "CONTENTS_DETAILSCONTENT_INLINE_A4" in seen,
    "S3_closeddetails_still_hidden": "CONTENTS_CLOSEDDETAILS_S3" not in seen,
    "S4_cvhidden_still_hidden": "CONTENTS_CVHIDDEN_S4" not in seen,
    "S2_opendetails_still_shown": "CONTENTS_OPENDETAILS_S2" in seen,
    "quarterly_report_control": "Quarterly report" in seen,
    "full_text": seen,
}
Path(sys.argv[1]).write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in result.items() if k != "full_text"}, indent=2))
