import asyncio
import hashlib
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from botocore.exceptions import ClientError
from fastapi import HTTPException
from fastapi.testclient import TestClient
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModHost, OpenWebuiModPackage, OpenWebuiModStore
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModEntity

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService
from tests.openwebui_mods.helpers import BASE, ModTestAuth, install_mod

ZIP = {"content-type": "application/zip"}


def test_inspection_is_ephemeral_and_install_has_one_record(client: TestClient, archive: bytes, storage: MagicMock) -> None:
    preview = client.post(BASE + "/inspect", content=archive, headers=ZIP)
    assert preview.status_code == 200, preview.text
    assert preview.json()["installed_version"] is None
    assert client.get(BASE + "/catalog").json() == []
    storage.put_object.assert_not_called()
    installed = client.post(BASE + "/install", content=archive, headers=ZIP)
    assert installed.status_code == 200, installed.text
    assert installed.json()["source_revision"] == hashlib.sha256(archive).hexdigest()
    assert client.get(BASE + "/catalog").json() == [installed.json()]
    assert client.post(BASE + "/inspect", content=archive, headers=ZIP).json()["installed_version"] == "1.0.0"
    assert client.post(BASE + "/install", content=archive, headers=ZIP).status_code == 409
    assert client.post(BASE + "/install?replace=true", content=archive, headers=ZIP).status_code == 200
    assert OpenWebuiModEntity.objects.count() == 1


@pytest.mark.parametrize("is_admin, authenticated, status", [(False, True, 403), (True, False, 401)])
@pytest.mark.parametrize("method, path", [
    ("GET", "/catalog"), ("GET", "/host"), ("GET", "/builtins"),
    ("POST", "/builtins/builtin-default/install"), ("POST", "/inspect"), ("POST", "/install"),
    ("GET", "/tenants/one"), ("PUT", "/tenants/one"), ("GET", "/global"), ("PUT", "/global"),
    ("POST", "/global/reconcile"), ("POST", "/global/restart?version=0"),
])
def test_all_endpoints_require_sysadmin(client: TestClient, auth: ModTestAuth, storage: MagicMock, control: list[httpx.Request], is_admin: bool, authenticated: bool, status: int, method: str, path: str) -> None:
    auth.is_admin, auth.authenticated = is_admin, authenticated
    assert client.request(method, BASE + path, content=b"invalid source").status_code == status
    assert storage.mock_calls == []
    assert control == []


@pytest.mark.parametrize("suffix", ["inspect", "install"])
@pytest.mark.parametrize("content, content_type, status", [
    (b"invalid zip", "application/zip", 422), (b"", "application/zip", 422), (b"invalid", "text/plain", 415),
])
def test_invalid_upload_has_no_catalog_entry(client: TestClient, storage: MagicMock, content: bytes, content_type: str, status: int, suffix: str) -> None:
    assert client.post(BASE + "/" + suffix, content=content, headers={"content-type": content_type}).status_code == status
    assert storage.mock_calls == []
    assert OpenWebuiModEntity.objects.count() == 0


@pytest.mark.parametrize("declared_length", [None, "1", "1000"])
def test_upload_limit_handles_unreliable_content_length(client: TestClient, storage: MagicMock, monkeypatch: pytest.MonkeyPatch, declared_length: str | None) -> None:
    monkeypatch.setattr(OpenWebuiModPackage, "MAX_ARCHIVE_BYTES", 256)
    headers = dict(ZIP)
    if declared_length:
        headers["content-length"] = declared_length
    for suffix in ["inspect", "install"]:
        assert client.post(BASE + "/" + suffix, content=iter([b"x" * 200, b"x" * 200]), headers=headers).status_code == 413
    assert storage.mock_calls == []


@pytest.mark.parametrize("existing", [False, True])
def test_failed_compilation_preserves_installed_package(client: TestClient, archive: bytes, publication: bytes, monkeypatch: pytest.MonkeyPatch, existing: bool) -> None:
    if existing:
        install_mod(client, archive, publication)
    previous = client.get(BASE + "/catalog").json()
    monkeypatch.setattr(OpenWebuiModService, "_compile", AsyncMock(side_effect=HTTPException(422, "Invalid Svelte")))
    response = client.post(BASE + "/install?replace=true", content=archive, headers=ZIP)
    assert response.status_code == 422
    assert client.get(BASE + "/catalog").json() == previous


@pytest.mark.parametrize("failure", ["source", "compiled", "metadata"])
def test_failed_storage_preserves_old_package_and_cleans_partial_files(client: TestClient, archive: bytes, publication: bytes, storage: MagicMock, monkeypatch: pytest.MonkeyPatch, failure: str) -> None:
    install_mod(client, archive, publication)
    previous = client.get(BASE + "/catalog").json()
    objects = dict(storage.objects)
    original = storage.put_object.side_effect
    def put(**kwargs):
        if kwargs["Key"].startswith("sources/" if failure == "source" else "publications/"):
            raise RuntimeError("storage unavailable")
        return original(**kwargs)
    if failure == "metadata":
        monkeypatch.setattr(OpenWebuiModEntity, "install", MagicMock(side_effect=RuntimeError("storage unavailable")))
    else:
        storage.put_object.side_effect = put
    with pytest.raises(RuntimeError, match="storage unavailable"):
        install_mod(client, archive, publication, version="2")
    assert client.get(BASE + "/catalog").json() == previous
    assert storage.objects == objects


def test_successful_replacement_prunes_old_archives_and_rollback_is_reupload(client: TestClient, archive: bytes, publication: bytes, storage: MagicMock) -> None:
    first = install_mod(client, archive, publication)
    old = set(storage.objects)
    second = install_mod(client, archive, publication, version="2")
    assert first != second
    assert not old.intersection(storage.objects)
    assert len(storage.objects) == 2
    assert len(client.get(BASE + "/catalog").json()) == 1
    assert install_mod(client, archive, publication) == first
    assert set(storage.objects) == old


def test_cleanup_failure_does_not_report_failed_install_and_next_install_retries(client: TestClient, archive: bytes, publication: bytes, storage: MagicMock, monkeypatch: pytest.MonkeyPatch) -> None:
    install_mod(client, archive, publication)
    with monkeypatch.context() as patch:
        patch.setattr(storage, "delete_objects", MagicMock(side_effect=RuntimeError("offline")))
        installed = install_mod(client, archive, publication, version="2")
        assert len(storage.objects) == 4
        assert OpenWebuiModEntity.objects.get(mod_id="chat-tools").publication == installed
    install_mod(client, archive, publication, version="2")
    assert len(storage.objects) == 2


def test_new_bucket_remains_private(client: TestClient, archive: bytes, storage: MagicMock) -> None:
    storage.head_bucket.side_effect = ClientError({"Error": {"Code": "404"}}, "HeadBucket")
    storage.create_bucket.side_effect = ClientError({"Error": {"Code": "BucketAlreadyOwnedByYou"}}, "CreateBucket")
    assert client.post(BASE + "/install", content=archive, headers=ZIP).status_code == 200
    storage.put_bucket_policy.assert_not_called()
    storage.put_bucket_cors.assert_not_called()
    assert "ACL" not in storage.put_object.call_args.kwargs


def test_store_reads_verify_hash_and_close_stream(client: TestClient, archive: bytes, storage: MagicMock) -> None:
    assert client.post(BASE + "/install", content=archive, headers=ZIP).status_code == 200
    body = BytesIO(b"corrupt")
    storage.get_object.side_effect = lambda **kwargs: {"Body": body}
    with pytest.raises(RuntimeError, match="integrity check"):
        asyncio.run(OpenWebuiModStore(storage).read_archive(hashlib.sha256(archive).hexdigest()))
    assert body.closed


def test_host_change_rejects_stale_compilation_and_keeps_installed(client: TestClient, archive: bytes, host: OpenWebuiModHost) -> None:
    assert client.post(BASE + "/install", content=archive, headers=ZIP).status_code == 200
    previous = client.get(BASE + "/catalog").json()
    host.compatibility = host.compatibility.model_copy(update={"source_commit": "b" * 40})
    assert client.post(BASE + "/install?replace=true", content=archive, headers=ZIP).status_code == 422
    assert client.get(BASE + "/catalog").json() == previous


def test_global_reconciliation_failure_is_reported_as_installed_with_warning(client: TestClient, archive: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_global_service import OpenWebuiModGlobalService
    monkeypatch.setattr(OpenWebuiModGlobalService, "reconcile", AsyncMock(side_effect=RuntimeError("Control unavailable")))
    response = client.post(BASE + "/install", content=archive, headers=ZIP)
    assert response.status_code == 200, response.text
    assert any("Installed, but global activation" in warning for warning in response.json()["warnings"])
    assert OpenWebuiModEntity.find_mod("chat-tools") is not None
