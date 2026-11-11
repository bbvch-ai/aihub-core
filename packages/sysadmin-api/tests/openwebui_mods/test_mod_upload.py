import hashlib
import json
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from zipfile import ZipFile

import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException, Request
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModHost, OpenWebuiModPackage, OpenWebuiModStore
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModPublicationEntity, OpenWebuiModRevisionEntity
from swiss_ai_hub.core.testing.auth_utils import TestAuthHandler
from swiss_ai_hub.core.testing.auth_utils.test_identity import fake_user

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_controller import OpenWebuiModController
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService
from swiss_ai_hub.sysadmin_api.sysadmin_runner import SysadminApiRunner

BASE = "/api/v1/admin/openwebui-mods/revisions"
MODS = "/api/v1/admin/openwebui-mods"


class ModTestAuth(TestAuthHandler):
    is_admin = True
    authenticated = True

    async def authenticate_token(self, token_str: str, request: Request | None = None) -> UserIdentity:
        if not self.authenticated:
            raise HTTPException(status_code=401, detail="Authentication required")
        return fake_user(is_sys_admin=self.is_admin)


@pytest.fixture
def storage() -> MagicMock:
    client = MagicMock()
    objects: dict[str, bytes] = {}

    def put_object(**kwargs: Any) -> None:
        objects[str(kwargs["Key"])] = bytes(kwargs["Body"])

    def get_object(**kwargs: Any) -> dict[str, BytesIO]:
        return {"Body": BytesIO(objects[str(kwargs["Key"])])}

    client.put_object.side_effect = put_object
    client.get_object.side_effect = get_object
    return client


@pytest.fixture
def auth() -> ModTestAuth:
    return ModTestAuth()


@pytest.fixture
def host() -> OpenWebuiModHost:
    compatibility = Path(__file__).resolve().parents[4] / "infra/deployment/docker/open-webui/mods/compatibility.json"
    return OpenWebuiModHost(compatibility=json.loads(compatibility.read_text()), components={"src/lib/Menu.svelte"})


@pytest.fixture
def client(
    storage: MagicMock, auth: ModTestAuth, host: OpenWebuiModHost, publication: bytes, monkeypatch: pytest.MonkeyPatch
) -> Generator[TestClient]:
    connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    OpenWebuiModRevisionEntity.drop_collection()
    OpenWebuiModPublicationEntity.drop_collection()
    monkeypatch.setattr(OpenWebuiModService, "get_host", AsyncMock(return_value=host))
    monkeypatch.setattr(OpenWebuiModService, "_compile", AsyncMock(return_value=publication))
    runner = SysadminApiRunner()
    runner.mount(
        OpenWebuiModController(auth=auth).get_host().catalog().upload().list_revisions().get_revision().download()
        .publish().list_publications().get_publication().download_publication()
        .get_configuration().replace_configuration().get_builtins().initialize().global_configuration()
    )
    runner._api_app.state.s3_client = storage
    yield TestClient(runner.create_app())
    OpenWebuiModRevisionEntity.drop_collection()
    OpenWebuiModPublicationEntity.drop_collection()
    disconnect()


@pytest.fixture
def archive() -> bytes:
    manifest = {
        "format": 1,
        "id": "chat-tools",
        "name": "Chat tools",
        "version": "1.0.0",
        "replacements": {"src/lib/Menu.svelte": "frontend/Menu.svelte"},
        "backend": "backend/mod.py",
    }
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zipped:
        zipped.writestr("mod.json", json.dumps(manifest))
        zipped.writestr("frontend/Menu.svelte", "<button>Settings</button>")
        zipped.writestr("backend/mod.py", "raise RuntimeError('Upload must never execute source')")
    return buffer.getvalue()


@pytest.fixture
def publication(archive: bytes, host: OpenWebuiModHost) -> bytes:
    metadata = {
        "format": 1,
        "source_revision": hashlib.sha256(archive).hexdigest(),
        "compatibility": host.compatibility.model_dump(),
        "replacements": {"src/lib/Menu.svelte": "frontend/frontend/Menu.svelte.mjs"},
    }
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zipped:
        zipped.writestr("publication.json", json.dumps(metadata))
        zipped.writestr("files/frontend/frontend/Menu.svelte.mjs", "export default function Menu() {}")
    return buffer.getvalue()


def test_archive_round_trip_and_duplicate_upload(
    client: TestClient, archive: bytes, storage: MagicMock
) -> None:
    first = client.post(BASE, content=archive, headers={"content-type": "application/zip"})
    assert first.status_code == 200, first.text
    record = first.json()
    revision = hashlib.sha256(archive).hexdigest()
    assert record["revision"] == revision
    assert record["manifest"]["replacements"] == {"src/lib/Menu.svelte": "frontend/Menu.svelte"}
    assert record["archive_bytes"] == len(archive)
    assert record["uploaded_by"] == fake_user().id
    assert client.get(f"{BASE}/{revision}").json() == record
    assert client.get(BASE, params={"mod_id": "chat-tools"}).json() == [record]
    assert client.get(BASE, params={"mod_id": "another-mod"}).json() == []
    assert client.get(BASE, params={"mod_id": "chat-tools", "offset": 1}).json() == []
    downloaded = client.get(f"{BASE}/{revision}/source")
    assert downloaded.content == archive
    assert downloaded.headers["cache-control"] == "no-store"
    assert downloaded.headers["x-content-type-options"] == "nosniff"
    again = client.post(BASE, content=archive, headers={"content-type": "application/zip"})
    assert again.json() == record
    assert OpenWebuiModRevisionEntity.objects(mod_id="chat-tools").count() == 1
    assert storage.put_object.call_args.kwargs["Bucket"] == "openwebui-mods"


@pytest.mark.parametrize("is_admin, authenticated, status", [(False, True, 403), (True, False, 401)])
@pytest.mark.parametrize(
    "method, path",
    [("GET", BASE), ("POST", BASE), ("GET", BASE + "/" + "0" * 64),
     ("GET", BASE + "/" + "0" * 64 + "/source"), ("GET", MODS + "/host"),
     ("POST", BASE + "/" + "0" * 64 + "/publications"), ("GET", BASE + "/" + "0" * 64 + "/publications"),
     ("GET", MODS + "/publications/" + "0" * 64), ("GET", MODS + "/publications/" + "0" * 64 + "/bundle"),
     ("GET", MODS + "/tenants/one"), ("PUT", MODS + "/tenants/one"),
     ("GET", MODS + "/builtins"), ("POST", MODS + "/initialize"), ("GET", MODS + "/catalog")],
)
def test_all_endpoints_require_sysadmin(
    client: TestClient,
    auth: ModTestAuth,
    storage: MagicMock,
    is_admin: bool,
    authenticated: bool,
    status: int,
    method: str,
    path: str,
) -> None:
    auth.is_admin = is_admin
    auth.authenticated = authenticated
    response = client.request(method, path, content=b"invalid source")
    assert response.status_code == status
    assert storage.mock_calls == []


@pytest.mark.parametrize(
    "content, content_type, status",
    [(b"invalid zip", "application/zip", 422), (b"", "application/zip", 422), (b"invalid zip", "text/plain", 415)],
)
def test_rejects_before_storage(
    client: TestClient, storage: MagicMock, content: bytes, content_type: str, status: int,
) -> None:
    response = client.post(BASE, content=content, headers={"content-type": content_type})
    assert response.status_code == status
    assert storage.mock_calls == []
    assert OpenWebuiModRevisionEntity.objects.count() == 0


@pytest.mark.parametrize("declared_length", [None, "1", "1000"])
def test_upload_limit_also_applies_without_reliable_content_length(
    client: TestClient, storage: MagicMock, monkeypatch: pytest.MonkeyPatch, declared_length: str | None,
) -> None:
    monkeypatch.setattr(OpenWebuiModPackage, "MAX_ARCHIVE_BYTES", 256)
    headers = {"content-type": "application/zip"}
    if declared_length:
        headers["content-length"] = declared_length
    response = client.post(BASE, content=iter([b"x" * 200, b"x" * 200]), headers=headers)
    assert response.status_code == 413
    assert storage.mock_calls == []


def test_object_failure_leaves_no_catalog_record(
    client: TestClient, archive: bytes, storage: MagicMock,
) -> None:
    storage.put_object.side_effect = RuntimeError("storage unavailable")
    with pytest.raises(RuntimeError, match="storage unavailable"):
        client.post(BASE, content=archive, headers={"content-type": "application/zip"})
    assert OpenWebuiModRevisionEntity.objects.count() == 0


def test_metadata_failure_is_repairable_by_reupload(
    client: TestClient, archive: bytes, monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(OpenWebuiModRevisionEntity, "record_upload", MagicMock(side_effect=RuntimeError("db unavailable")))
        with pytest.raises(RuntimeError, match="db unavailable"):
            client.post(BASE, content=archive, headers={"content-type": "application/zip"})
    assert client.get(BASE, params={"mod_id": "chat-tools"}).json() == []
    response = client.post(BASE, content=archive, headers={"content-type": "application/zip"})
    assert response.status_code == 200
    assert client.get(f'{BASE}/{response.json()["revision"]}/source').content == archive


def test_supplied_packages_are_available_without_uploading_or_activating_them(
    client: TestClient, storage: MagicMock,
) -> None:
    response = client.get(MODS + "/builtins")
    assert response.status_code == 200
    records = response.json()
    assert {record["manifest"]["id"] for record in records} == {"builtin-default", "builtin-optional"}
    writes = storage.put_object.call_count
    assert client.get(MODS + "/builtins").json() == records
    assert storage.put_object.call_count == writes == 2
    assert OpenWebuiModPublicationEntity.objects.count() == 0
    for record in records:
        downloaded = client.get(f'{BASE}/{record["revision"]}/source')
        assert downloaded.status_code == 200
        assert OpenWebuiModPackage.from_zip(downloaded.content).manifest.id == record["manifest"]["id"]


def test_download_checks_integrity(client: TestClient, archive: bytes, storage: MagicMock) -> None:
    response = client.post(BASE, content=archive, headers={"content-type": "application/zip"})
    body = BytesIO(b"changed in storage")
    storage.get_object.side_effect = None
    storage.get_object.return_value = {"Body": body}
    with pytest.raises(RuntimeError, match="integrity check"):
        client.get(f'{BASE}/{response.json()["revision"]}/source')
    assert body.closed


@pytest.mark.parametrize("suffix", ["", "/source"])
def test_unknown_revision_is_not_found(client: TestClient, storage: MagicMock, suffix: str) -> None:
    assert client.get(f'{BASE}/{"0" * 64}{suffix}').status_code == 404
    assert storage.mock_calls == []


def test_concurrent_identical_uploads_are_one_revision(client: TestClient, archive: bytes) -> None:
    def upload(_: int) -> dict[str, Any]:
        response = client.post(BASE, content=archive, headers={"content-type": "application/zip"})
        assert response.status_code == 200, response.text
        return response.json()

    with ThreadPoolExecutor(max_workers=8) as executor:
        records = list(executor.map(upload, range(8)))
    assert all(record == records[0] for record in records)
    assert OpenWebuiModRevisionEntity.objects.count() == 1


def test_new_bucket_has_no_public_policy(client: TestClient, archive: bytes, storage: MagicMock) -> None:
    storage.head_bucket.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadBucket")
    storage.create_bucket.side_effect = ClientError({"Error": {"Code": "BucketAlreadyOwnedByYou"}}, "CreateBucket")
    assert client.post(BASE, content=archive, headers={"content-type": "application/zip"}).status_code == 200
    storage.create_bucket.assert_called_once_with(Bucket=OpenWebuiModStore.BUCKET)
    storage.put_bucket_policy.assert_not_called()
    storage.put_bucket_cors.assert_not_called()
    assert "ACL" not in storage.put_object.call_args.kwargs


def test_publication_round_trip_binds_original_source_and_host(
    client: TestClient, archive: bytes, publication: bytes, host: OpenWebuiModHost,
) -> None:
    source = client.post(BASE, content=archive, headers={"content-type": "application/zip"}).json()
    route = f'{BASE}/{source["revision"]}/publications'
    assert client.get(route).json() == []
    response = client.post(route)
    assert response.status_code == 200, response.text
    record = response.json()
    assert record["revision"] == hashlib.sha256(publication).hexdigest()
    OpenWebuiModService._compile.assert_awaited_once_with(archive)
    assert record["manifest"]["source_revision"] == source["revision"]
    assert record["manifest"]["compatibility"] == host.compatibility.model_dump()
    assert client.get(MODS + "/host").json()["compatibility"] == host.compatibility.model_dump()
    assert client.get(f'{MODS}/publications/{record["revision"]}').json() == record
    assert client.get(f'{MODS}/publications/{record["revision"]}/bundle').content == publication
    assert client.get(route).json() == [record]
    again = client.post(route)
    assert again.json() == record
    assert OpenWebuiModPublicationEntity.objects.count() == 1
    assert client.get(f'{BASE}/{source["revision"]}/source').content == archive


def test_upgraded_host_refuses_stale_compilation_but_retains_previous_publication(
    client: TestClient, archive: bytes, publication: bytes, host: OpenWebuiModHost,
) -> None:
    source = client.post(BASE, content=archive, headers={"content-type": "application/zip"}).json()
    route = f'{BASE}/{source["revision"]}/publications'
    previous = client.post(route).json()
    host.compatibility = host.compatibility.model_copy(update={"source_commit": "b" * 40})
    rejected = client.post(route)
    assert rejected.status_code == 422
    assert "recompile" in rejected.json()["detail"]
    assert client.get(route).json() == [previous]
    assert client.get(f'{MODS}/publications/{previous["revision"]}/bundle').content == publication


def test_publication_storage_failure_does_not_create_a_record(
    client: TestClient, archive: bytes, publication: bytes, storage: MagicMock,
) -> None:
    source = client.post(BASE, content=archive, headers={"content-type": "application/zip"}).json()
    storage.put_object.side_effect = RuntimeError("publication storage unavailable")
    with pytest.raises(RuntimeError, match="publication storage unavailable"):
        client.post(f'{BASE}/{source["revision"]}/publications')
    assert OpenWebuiModPublicationEntity.objects.count() == 0
    assert OpenWebuiModRevisionEntity.objects.count() == 1


def test_publication_metadata_failure_can_be_retried(
    client: TestClient, archive: bytes, publication: bytes, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = client.post(BASE, content=archive, headers={"content-type": "application/zip"}).json()
    route = f'{BASE}/{source["revision"]}/publications'
    with monkeypatch.context() as patch:
        patch.setattr(OpenWebuiModPublicationEntity, "record_publication", MagicMock(side_effect=RuntimeError("db failed")))
        with pytest.raises(RuntimeError, match="db failed"):
            client.post(route)
    assert client.get(route).json() == []
    assert client.post(route).status_code == 200
    assert OpenWebuiModPublicationEntity.objects.count() == 1


def test_publications_cannot_reference_missing_source(client: TestClient, publication: bytes) -> None:
    response = client.post(f'{BASE}/{"0" * 64}/publications')
    assert response.status_code == 404
    assert OpenWebuiModPublicationEntity.objects.count() == 0


def test_unavailable_host_keeps_source_without_publishing(
    client: TestClient, archive: bytes, publication: bytes, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = client.post(BASE, content=archive, headers={"content-type": "application/zip"}).json()
    monkeypatch.setattr(OpenWebuiModService, "get_host", AsyncMock(side_effect=HTTPException(503, "Host unavailable")))
    response = client.post(f'{BASE}/{source["revision"]}/publications')
    assert response.status_code == 503
    assert OpenWebuiModPublicationEntity.objects.count() == 0
    assert OpenWebuiModRevisionEntity.objects.count() == 1
