"""Google Drive folder listing + file fetch, and the OAuth device-flow token
exchange, as plain HTTPS calls (httpx) behind a small seam the tests mock.

qa/contracts/source-adapters.md DRIVE phase-2 row + SA3. The chosen auth
mechanism is OAuth **device flow** (no service-account auth): a one-time
interactive consent yields a refresh token, which the caller stores as a
`SecretRef` -- its KEY and domain scope, never the value. At call time
`HttpDriveClient` resolves that key to a value, exchanges it for a short-lived
access token, and calls Drive REST v3 `files.list`/`files.get`. The token value
is never stored on the instance, logged, put on a `Source`, or returned (SA3);
only the Drive file id travels outward, into `Source.url`.
`sources/drive_register.py` does the registering -- split from this module the
same way `sources/email.py` (parse) stays separate from
`sources/email_register.py` (register), and to keep each file under the doctor's
300-line rule.

No `google-api-python-client` / `google-auth` dependency (the design rule
forbids a heavyweight client): these are hand-written httpx calls behind the
`DriveClient` protocol, which the tests replace wholesale -- a fake client, or
`httpx.MockTransport` over the real one -- so the unit is fully offline, with no
network and no real credentials.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple, Protocol

import httpx

DRIVE_FILES_ENDPOINT = "https://www.googleapis.com/drive/v3/files"
OAUTH_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
OAUTH_DEVICE_CODE_ENDPOINT = "https://oauth2.googleapis.com/device/code"
DRIVE_READONLY_SCOPE = "https://www.googleapis.com/auth/drive.readonly"
DEVICE_GRANT = "urn:ietf:params:oauth:grant-type:device_code"
_HTTP_TIMEOUT = 30.0
_PAGE_SIZE = 1000


class DriveFile(NamedTuple):
    """One file's metadata from `files.list` -- never its bytes, never a token."""

    id: str
    name: str
    mime_type: str


class DriveFetch(NamedTuple):
    """The bytes of one file, or an honest reason they could not be fetched (SA5)."""

    content: bytes | None
    error: str | None


class DriveClient(Protocol):
    """The seam the register layer depends on -- two operations, both mockable.

    The register layer (`drive_register.py`) knows only this shape, so it never
    sees a credential: the token lives entirely inside the implementation (SA3).
    """

    def list_folder(self, folder_id: str) -> list[DriveFile]: ...

    def fetch_file(self, file: DriveFile) -> DriveFetch: ...


class DeviceCode(NamedTuple):
    """A device-flow authorization request the human completes in a browser."""

    device_code: str
    user_code: str
    verification_url: str
    interval: int


def request_device_code(client_id: str, *, http: httpx.Client | None = None) -> DeviceCode:
    """Step 1 of device flow: ask Google for a code the human enters at
    `verification_url` to grant read-only Drive access. No secret is involved --
    only the public client id -- so nothing here needs redaction."""
    client = http or httpx.Client(timeout=_HTTP_TIMEOUT)
    try:
        resp = client.post(
            OAUTH_DEVICE_CODE_ENDPOINT,
            data={"client_id": client_id, "scope": DRIVE_READONLY_SCOPE},
        )
        resp.raise_for_status()
        body = resp.json()
        return DeviceCode(
            device_code=body["device_code"],
            user_code=body["user_code"],
            verification_url=body.get("verification_url") or body.get("verification_uri", ""),
            interval=int(body.get("interval", 5)),
        )
    finally:
        if http is None:
            client.close()


def exchange_device_code(
    client_id: str, client_secret: str, device_code: str, *, http: httpx.Client | None = None
) -> str:
    """Step 2 of device flow: exchange an authorized `device_code` for a refresh
    token, which the CALLER stores as a `SecretRef` in the project `.env`. This
    function neither persists nor logs the returned value (SA3). The
    `authorization_pending` polling loop is deliberately the caller's, kept out
    so this stays one testable HTTPS call."""
    client = http or httpx.Client(timeout=_HTTP_TIMEOUT)
    try:
        resp = client.post(
            OAUTH_TOKEN_ENDPOINT,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "device_code": device_code,
                "grant_type": DEVICE_GRANT,
            },
        )
        resp.raise_for_status()
        return resp.json()["refresh_token"]
    finally:
        if http is None:
            client.close()


class HttpDriveClient:
    """The real `DriveClient`: httpx calls to Google's OAuth token endpoint and
    Drive REST v3.

    Holds the refresh token (and client secret) as a resolver plus a KEY, never
    a value (SA3): `_resolver(key)` returns the value only at call time, it is
    used immediately to mint a short-lived access token, and it is never stored
    on `self`, logged, or placed on any `Source`.
    """

    def __init__(
        self,
        client_id: str,
        client_secret_key: str,
        refresh_token_key: str,
        resolver: Callable[[str], str],
        *,
        http: httpx.Client | None = None,
    ) -> None:
        self._client_id = client_id
        self._client_secret_key = client_secret_key
        self._refresh_token_key = refresh_token_key
        self._resolver = resolver
        self._http = http or httpx.Client(timeout=_HTTP_TIMEOUT)

    def _access_token(self) -> str:
        """Exchange the resolved refresh token for a short-lived bearer token.
        The refresh token and client secret are read from the resolver HERE,
        used at once, and never retained on the instance."""
        resp = self._http.post(
            OAUTH_TOKEN_ENDPOINT,
            data={
                "client_id": self._client_id,
                "client_secret": self._resolver(self._client_secret_key),
                "refresh_token": self._resolver(self._refresh_token_key),
                "grant_type": "refresh_token",
            },
        )
        resp.raise_for_status()
        return resp.json()["access_token"]

    def list_folder(self, folder_id: str) -> list[DriveFile]:
        """Every non-trashed file directly in `folder_id` (paged), via
        `files.list`. A listing failure raises -- a folder that cannot be listed
        is a real error the caller sees, not a silently empty folder."""
        headers = {"Authorization": f"Bearer {self._access_token()}"}
        files: list[DriveFile] = []
        page_token: str | None = None
        while True:
            params = {
                "q": f"'{folder_id}' in parents and trashed = false",
                "fields": "nextPageToken, files(id, name, mimeType)",
                "pageSize": _PAGE_SIZE,
            }
            if page_token:
                params["pageToken"] = page_token
            resp = self._http.get(DRIVE_FILES_ENDPOINT, params=params, headers=headers)
            resp.raise_for_status()
            body = resp.json()
            files.extend(
                DriveFile(f["id"], f.get("name", "file"), f.get("mimeType", ""))
                for f in body.get("files", [])
            )
            page_token = body.get("nextPageToken")
            if not page_token:
                return files

    def fetch_file(self, file: DriveFile) -> DriveFetch:
        """One file's raw bytes via `files.get?alt=media`. A fetch failure
        becomes an honest `DriveFetch(None, error)` (SA5), never a raised
        exception that would drop the whole folder nor a silently empty file."""
        try:
            headers = {"Authorization": f"Bearer {self._access_token()}"}
            resp = self._http.get(
                f"{DRIVE_FILES_ENDPOINT}/{file.id}", params={"alt": "media"}, headers=headers
            )
            resp.raise_for_status()
            return DriveFetch(resp.content, None)
        except Exception as exc:  # honest degradation (SA5), never a dropped file
            return DriveFetch(None, f"{type(exc).__name__}: {exc}")
