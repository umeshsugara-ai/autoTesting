"""SOURCE ADAPTERS -- DRIVE (T-162 phase-2b). Contract:
qa/contracts/source-adapters.md DRIVE row + SA1-SA6. Split out of
test_source_adapters.py (doctor's file-length rule); TEXT/DOC stay there,
AUDIO/EMAIL in their own files.

DRIVE is the one adapter that touches the credential boundary: an OAuth
device-flow refresh token, held as a `SecretRef`, is resolved only at call time
and exchanged for a short-lived access token INSIDE the `DriveClient` seam --
the register layer never sees a token (SA3). Covers: SA1 (DRIVE shares the one
store + enum; files reuse the EXISTING DOC/VIDEO/AUDIO adapters), SA2 (dedupe by
sha256 of fetched bytes -- same bytes twice is ONE Source), SA3 (no token value
reaches a stored Source / the sources.jsonl on disk), SA4 (each child cites its
Drive folder via `Source.provenance`), and SA5 (a file that cannot be fetched
registers with an `extraction_error` note, never dropped).

Every HTTP/OAuth call is mocked: the register-layer tests use a `FakeDriveClient`
(no HTTP at all), and the SA3 test drives the REAL `HttpDriveClient` over
`httpx.MockTransport` -- fully offline, no network, no real credentials.
"""

from __future__ import annotations

import httpx

from autotester.core.redact import Redactor, assert_no_raw_secrets
from autotester.schema.enums import SourceKind
from autotester.sources import register_drive
from autotester.sources.drive import DriveClient, DriveFetch, DriveFile, HttpDriveClient
from autotester.store.project_store import ProjectStore


def _store(tmp_path) -> ProjectStore:
    return ProjectStore("pathlynks", tmp_path)


class FakeDriveClient:
    """A `DriveClient` with no HTTP: files declared up front, bytes served from a
    dict, and per-file fetch errors to exercise SA5."""

    def __init__(
        self,
        files: list[DriveFile],
        contents: dict[str, bytes],
        errors: dict[str, str] | None = None,
    ) -> None:
        self._files = files
        self._contents = contents
        self._errors = errors or {}

    def list_folder(self, folder_id: str) -> list[DriveFile]:
        return list(self._files)

    def fetch_file(self, file: DriveFile) -> DriveFetch:
        if file.id in self._errors:
            return DriveFetch(None, self._errors[file.id])
        return DriveFetch(self._contents[file.id], None)


# -- SA1: folder + files land in the one store, files reuse existing adapters ---
def test_drive_files_become_child_sources_with_kind_and_drive_id(tmp_path) -> None:
    store = _store(tmp_path)
    files = [
        DriveFile("doc-1", "notes.md", "text/markdown"),
        DriveFile("vid-1", "lecture.mp4", "video/mp4"),
    ]
    client: DriveClient = FakeDriveClient(
        files, {"doc-1": b"# heading\nbody", "vid-1": b"fake video bytes"}
    )

    results = register_drive(store, "folder-XYZ", client)

    folder = results[0]
    assert folder.source.kind is SourceKind.DRIVE
    assert folder.source.url == "folder-XYZ"
    children = {r.source.kind: r.source for r in results[1:]}
    assert children[SourceKind.DOC].url == "doc-1"  # Drive file id in Source.url
    assert children[SourceKind.VIDEO].url == "vid-1"
    assert children[SourceKind.DOC].text == "# heading\nbody"  # extracted, not empty
    assert len(store.list_sources()) == 3  # all in the ONE sources.jsonl (SA1)


# -- SA2: content-addressed dedupe (same bytes -> ONE Source) ------------------
def test_drive_dedupes_same_bytes_into_one_source(tmp_path) -> None:
    store = _store(tmp_path)
    same = b"identical drive bytes"
    files = [DriveFile("a", "one.md", "text/markdown"), DriveFile("b", "two.md", "text/markdown")]
    client = FakeDriveClient(files, {"a": same, "b": same})

    results = register_drive(store, "folder-1", client)

    child_results = results[1:]
    assert child_results[0].created is True
    assert child_results[1].created is False  # "already registered", not a new row
    assert child_results[0].source.id == child_results[1].source.id
    doc_sources = [s for s in store.list_sources() if s.kind is SourceKind.DOC]
    assert len(doc_sources) == 1  # ONE Source for the two identical files (SA2)


# -- SA5: honest degradation (unfetchable file -> extraction_error, not empty) --
def test_drive_unfetchable_file_registers_extraction_error(tmp_path) -> None:
    store = _store(tmp_path)
    files = [DriveFile("gone", "secret.md", "text/markdown")]
    client = FakeDriveClient(files, {}, errors={"gone": "HTTPStatusError: 403 Forbidden"})

    results = register_drive(store, "folder-1", client)

    child = results[1]
    assert child.created is True  # it IS registered -- a Source exists (never dropped)
    assert child.source.notes is not None
    assert child.source.notes.startswith("extraction_error")
    assert child.source.url == "gone"  # still traceable to the Drive file


# -- SA4: each child cites its Drive folder via provenance ---------------------
def test_drive_child_provenance_links_to_the_folder(tmp_path) -> None:
    store = _store(tmp_path)
    files = [DriveFile("doc-1", "notes.md", "text/markdown")]
    client = FakeDriveClient(files, {"doc-1": b"content"})

    results = register_drive(store, "folder-XYZ", client)

    folder, child = results[0], results[1]
    assert child.source.provenance is not None
    assert child.source.provenance.produced_by == "sources.drive"
    assert child.source.provenance.inputs == [folder.source.id]  # SA4


# -- SA3: no token value reaches a stored Source / the sources.jsonl on disk ----
def test_drive_credential_never_reaches_stored_sources(tmp_path) -> None:
    store = _store(tmp_path)
    refresh_token = "REFRESH_SECRET_TOKEN_XYZ"
    client_secret = "CLIENT_SECRET_ABC_9090"
    access_token = "ACCESS_BEARER_TOKEN_QWER"

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/token":
            return httpx.Response(200, json={"access_token": access_token})
        if request.url.path == "/drive/v3/files":
            return httpx.Response(
                200, json={"files": [{"id": "f1", "name": "notes.md", "mimeType": "text/markdown"}]}
            )
        if request.url.path.startswith("/drive/v3/files/"):
            return httpx.Response(200, content=b"# real drive content")
        return httpx.Response(404)

    def resolver(key: str) -> str:
        return {"GDRIVE_REFRESH_TOKEN": refresh_token, "GDRIVE_CLIENT_SECRET": client_secret}[key]

    http = httpx.Client(transport=httpx.MockTransport(handler))
    client = HttpDriveClient("client-id", "GDRIVE_CLIENT_SECRET", "GDRIVE_REFRESH_TOKEN", resolver,
                             http=http)

    register_drive(store, "folder-1", client)

    stored = store.paths.sources_index.read_text(encoding="utf-8")
    secrets = [refresh_token, client_secret, access_token]
    for secret in secrets:
        assert secret not in stored  # no token value written to disk
    assert_no_raw_secrets(stored, secrets)  # does not raise: the hard gate is clean
    assert Redactor({f"K{i}": s for i, s in enumerate(secrets)}).is_clean(stored)
    # the fetched CONTENT still landed -- absence of tokens is not absence of data
    assert any(s.kind is SourceKind.DOC and s.url == "f1" for s in store.list_sources())


# -- device-flow token exchange is a real HTTPS call, not a stub (SA3 mechanism) -
def test_device_code_exchange_returns_refresh_token_offline() -> None:
    from autotester.sources.drive import exchange_device_code, request_device_code

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/device/code":
            return httpx.Response(
                200,
                json={
                    "device_code": "DC-123",
                    "user_code": "WXYZ-1234",
                    "verification_url": "https://www.google.com/device",
                    "interval": 5,
                },
            )
        if request.url.path == "/token":
            return httpx.Response(200, json={"refresh_token": "NEW_REFRESH_TOKEN"})
        return httpx.Response(404)

    http = httpx.Client(transport=httpx.MockTransport(handler))
    device = request_device_code("client-id", http=http)
    assert device.user_code == "WXYZ-1234"
    token = exchange_device_code("client-id", "secret", device.device_code, http=http)
    assert token == "NEW_REFRESH_TOKEN"  # the caller stores THIS as a SecretRef, never inline
