import json, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from autotester.browser.observe import visual_text

fixture = Path(sys.argv[1]).resolve()
url = fixture.as_uri()

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(400)
    seen = visual_text(page)
    result = {
        "chromium": browser.version,
        "A3_reported": "CONTENTS_DETAILSCONTENT_CONTENTS_A3" in seen,
        "A4_reported": "CONTENTS_DETAILSCONTENT_INLINE_A4" in seen,
        "S3_closeddetails_still_hidden": "CONTENTS_CLOSEDDETAILS_S3" not in seen,
        "S4_cvhidden_still_hidden": "CONTENTS_CVHIDDEN_S4" not in seen,
        "S2_opendetails_still_shown": "CONTENTS_OPENDETAILS_S2" in seen,
        "S12_detailscontents_still_hidden": "CONTENTS_DETAILSCONTENTS_S12" not in seen,
        "quarterly_report_control": "Quarterly report for the trainers list" in seen,
        "raw_seen": seen,
    }
    browser.close()
Path(sys.argv[2]).write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
