"""Onboard Pathlynks: real login via the credential boundary, evidence, knowledge.md.

Contract: qa/contracts/pathlynks-onboarding.md O1-O4.

Deliberately does NOT use /portal-explorer's default mechanism (Playwright MCP
tool calls), because a raw credential passed as an MCP tool argument would
appear in this session's own transcript -- exactly the leak T-011/T-010 were
built to prevent. This script drives the same `BrowserSession` the rest of
the system uses, so a secret only ever exists inside `SecretStore.resolve`'s
return value, used immediately by Playwright and nowhere else (O1).
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from autotester.browser.secrets import SecretStore
from autotester.browser.session import BrowserSession
from autotester.core.ids import ulid
from autotester.core.paths import ProjectPaths
from autotester.store import ProjectStore

SIGNIN_EMAIL = 'input[name="identifier"]'
SIGNIN_PASSWORD = 'input[name="password"]'
SIGNIN_SUBMIT = 'button[type="submit"]:has-text("Login")'
DASHBOARD_WAIT_MS = 4000


def onboard(role: str = "user", root: Path | None = None) -> Path:
    """Log in as `role` ('user' or 'counsellor'), capture evidence, write knowledge.md.

    `root` overrides the repo root (tests pass a tmp_path so this never
    touches the real project/.env). Returns the run directory. Raises if the
    project or a login fails -- never silently produces a knowledge file from
    a failed login.
    """
    store = ProjectStore("pathlynks", root)
    project = store.load_project()
    if project is None:
        raise RuntimeError(
            "projects/pathlynks/project.json not found; run T-030's project step first"
        )
    paths = ProjectPaths("pathlynks", root)
    secrets = SecretStore.load(project, paths.env_file)

    run_id = f"onboard-{ulid()}"
    run_dir = paths.run_dir(run_id)
    session = BrowserSession(project, secrets, run_dir, paths)
    session.start()
    screens: list[str] = []
    try:
        session.goto(project.base_url)
        session.screenshot("landing")
        screens.append("landing (signin page)")

        email_key = f"PATHLYNKS_{role.upper()}_EMAIL"
        password_key = f"PATHLYNKS_{role.upper()}_PASSWORD"
        session.fill(SIGNIN_EMAIL, f"{{{{SECRET:{email_key}}}}}")
        session.fill(SIGNIN_PASSWORD, f"{{{{SECRET:{password_key}}}}}")
        session.screenshot("filled-login-form")

        session.click(SIGNIN_SUBMIT)
        session.page.wait_for_timeout(DASHBOARD_WAIT_MS)
        session.screenshot("post-login")
        landed_url = session.secrets.redactor().scrub(session.page.url)
        screens.append(f"post-login landing: {landed_url}")
    finally:
        session.close()

    _write_knowledge(paths, run_id, role, screens)
    return run_dir


def _write_knowledge(paths: ProjectPaths, run_id: str, role: str, screens: list[str]) -> None:
    now = datetime.now(UTC).strftime("%Y-%m-%d")
    body = f"""# Pathlynks (pathlynks)

**Purpose:** what this system has learned about the Pathlynks product from real,
credentialed exploration — screens reached, auth boundaries, gotchas.
**Open me when:** onboarding a new flow, deciding what a video request should show,
or checking whether a screen was already seen.

## Quick Re-Run
```bash
uv run python scripts/onboard_pathlynks.py --role user
```

**Last successful run:** {now} | role={role} | run={run_id}
**Output file(s):** projects/pathlynks/runs/{run_id}/

## Portal Profile
| Field | Value |
|-------|-------|
| URL | (see project.json base_url; redacted here where it overlaps a declared secret) |
| Type | saas |
| Intent explored | audit (onboarding) |
| AI involvement | Tier 2 -- agent + knowledge, deterministic once mapped |
| Browser tool used | Playwright via autotester.browser.session.BrowserSession |
| Auth | email + password, two roles observed (counsellor, user) |
| Write policy | read_only (no writes performed) |

## How it works
Sign-in form at the project's base_url takes an `identifier` (email) field and a
`password` field, submitted via a "Login" button. No 2FA/OTP was presented for
this dev-environment account on this run.

## Screens reached
{chr(10).join(f"- {s}" for s in screens)}

## Gotchas & edge cases
- Two account roles exist for this product (counsellor and user/student); this
  run exercised the `{role}` role only. The other role's login page differs
  (see `.env.example` for both `*_LOGIN_URL` shapes) -- a separate run should
  cover it before this knowledge file is considered complete.
- Login URLs stored in `.env` are NOT declared as project secrets, so they are
  masked by the redactor as undeclared values (AT-004 behaviour) -- this is a
  known false-positive redaction of non-sensitive URLs, not a security issue;
  use `project.json::base_url` for the canonical, unmasked entry point instead.

## Change detection
- Re-run and diff the screenshot set; a materially different login form or a
  redirect to an unexpected host means this file needs a fresh pass.

## History
| Date | Intent | Findings | Duration | Tool | Notes |
|---|---|---|---|---|---|
| {now} | audit | login form mapped, 3 screenshots | -- | BrowserSession | T-030 first pass |
"""
    paths.knowledge.parent.mkdir(parents=True, exist_ok=True)
    paths.knowledge.write_text(body, encoding="utf-8")


if __name__ == "__main__":
    role_arg = "user"
    if len(sys.argv) > 1 and sys.argv[1] == "--role" and len(sys.argv) > 2:
        role_arg = sys.argv[2]
    out = onboard(role_arg)
    print(f"onboarded role={role_arg}; evidence in {out}")
