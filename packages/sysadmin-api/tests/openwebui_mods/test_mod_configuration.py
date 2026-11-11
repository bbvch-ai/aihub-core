import hashlib
import json
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import Any
from unittest.mock import patch, AsyncMock, MagicMock
from zipfile import ZipFile

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from keycloak import KeycloakGetError
from swiss_ai_hub.core.auth import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModHost
from swiss_ai_hub.core.persistence import TenantMetadataEntity

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService
from tests.openwebui_mods.test_mod_upload import archive, auth, client, host, publication, storage  # noqa: F401
from tests.openwebui_mods.test_mod_global import publish_global

BASE = "/api/v1/admin/openwebui-mods"
TENANT = BASE + "/tenants/one"


@pytest.fixture(autouse=True)
def tenants(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    TenantMetadataEntity.drop_collection()
    for tenant_id in ("one", "two"):
        TenantMetadataEntity(id=tenant_id, name=tenant_id, access_rules=["aihub.user.>"]).save()
    monkeypatch.setattr(
        TenantMetadataEntity, "get_metadata_by_tenant_id", lambda tenant_id: TenantMetadataEntity.objects(id=tenant_id).first()
    )
    monkeypatch.setattr(KeycloakAdminService, "get_tenant_group", AsyncMock())
    yield
    TenantMetadataEntity.drop_collection()


def publish_mod(client: TestClient, archive: bytes, publication: bytes, mod_id: str = "chat-tools") -> str:
    with ZipFile(BytesIO(archive)) as zipped:
        files = {name: zipped.read(name) for name in zipped.namelist()}
    manifest = json.loads(files["mod.json"])
    manifest["id"] = mod_id
    files["mod.json"] = json.dumps(manifest).encode()
    source = BytesIO()
    with ZipFile(source, "w") as zipped:
        for name, content in files.items():
            zipped.writestr(name, content)
    response = client.post(BASE + "/revisions", content=source.getvalue(), headers={"content-type": "application/zip"})
    assert response.status_code == 200, response.text
    with ZipFile(BytesIO(publication)) as zipped:
        files = {name: zipped.read(name) for name in zipped.namelist()}
    metadata = json.loads(files["publication.json"])
    metadata["source_revision"] = hashlib.sha256(source.getvalue()).hexdigest()
    files["publication.json"] = json.dumps(metadata).encode()
    bundle = BytesIO()
    with ZipFile(bundle, "w") as zipped:
        for name, content in files.items():
            zipped.writestr(name, content)
    with patch.object(OpenWebuiModService, "_compile", AsyncMock(return_value=bundle.getvalue())):
        response = client.post(f'{BASE}/revisions/{metadata["source_revision"]}/publications')
    assert response.status_code == 200, response.text
    return response.json()["revision"]


@pytest.fixture
def selection(client: TestClient, archive: bytes, publication: bytes) -> dict[str, Any]:
    return {"mod_id": "chat-tools", "publication": publish_mod(client, archive, publication), "enabled": True,
            "settings": {"label": "Tools", "nested": {"some.key": [True, 3, None]}}}


def test_configuration_is_tenant_scoped_and_preserves_other_metadata(
    client: TestClient, selection: dict[str, Any],
) -> None:
    default = client.get(TENANT).json()
    assert default["version"] == 0
    assert [mod["mod_id"] for mod in default["mods"] if mod["enabled"]] == ["builtin-default"]
    assert default["mods"][0]["enabled"] is True
    assert "openwebui_mods_json" not in TenantMetadataEntity.objects.get(id="one").to_mongo()
    saved = client.put(TENANT, json={"version": 0, "mods": [selection]})
    assert saved.status_code == 200, saved.text
    assert saved.json() == {"version": 1, "mods": [selection]}
    assert client.get(TENANT).json() == saved.json()
    assert client.get(BASE + "/tenants/two").json() == default
    tenant = TenantMetadataEntity.objects.get(id="one")
    assert tenant.access_rules == ["aihub.user.>"]


def test_removing_the_default_is_persistent(client: TestClient) -> None:
    default = client.get(TENANT).json()
    assert client.put(TENANT, json={"version": default["version"], "mods": []}).status_code == 200
    assert client.get(TENANT).json() == {"version": 1, "mods": []}


def test_uploaded_mod_is_configured_in_database_independently_of_deployment_defaults(
    client: TestClient, selection: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
) -> None:
    defaults = client.get(TENANT).json()
    assert [mod["mod_id"] for mod in defaults["mods"] if mod["enabled"]] == ["builtin-default"]
    catalog = client.get(BASE + "/catalog").json()
    assert next(mod for mod in catalog if mod["manifest"]["id"] == selection["mod_id"])["builtin"] is False
    saved = client.put(TENANT, json={"version": defaults["version"], "mods": [selection]})
    assert saved.status_code == 200, saved.text
    assert json.loads(TenantMetadataEntity.objects.get(id="one").openwebui_mods_json)["mods"] == [selection]
    monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", "[]")
    assert client.get(TENANT).json() == saved.json()
    assert all(not mod["enabled"] for mod in client.get(BASE + "/tenants/two").json()["mods"])


def test_default_configuration_reads_never_compile_or_publish(client: TestClient, storage: MagicMock) -> None:
    first = client.get(TENANT).json()
    writes = storage.put_object.call_count
    assert client.get(TENANT).json() == first
    assert storage.put_object.call_count == writes == 0
    assert first["mods"][0]["publication"] is None


def test_concurrent_default_reads_return_one_publication(client: TestClient) -> None:
    def read(_: int) -> dict[str, Any]:
        response = client.get(TENANT)
        assert response.status_code == 200, response.text
        return response.json()

    with ThreadPoolExecutor(max_workers=8) as executor:
        configurations = list(executor.map(read, range(8)))
    assert all(configuration == configurations[0] for configuration in configurations)
    assert TenantMetadataEntity.objects.get(id="one").openwebui_mods_json is None


def test_disable_and_reenable_keep_revision_and_settings(client: TestClient, selection: dict[str, Any]) -> None:
    for version, enabled in enumerate([True, False, True]):
        selection["enabled"] = enabled
        response = client.put(TENANT, json={"version": version, "mods": [selection]})
        assert response.status_code == 200, response.text
        assert response.json() == {"version": version + 1, "mods": [selection]}


def test_stale_configuration_cannot_overwrite_a_newer_save(client: TestClient, selection: dict[str, Any]) -> None:
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 200
    rejected = client.put(TENANT, json={"version": 0, "mods": []})
    assert rejected.status_code == 409
    assert client.get(TENANT).json()["mods"] == [selection]


def test_concurrent_saves_have_one_winner(client: TestClient, selection: dict[str, Any]) -> None:
    def save(index: int) -> int:
        mod = {**selection, "settings": {"writer": index}}
        return client.put(TENANT, json={"version": 0, "mods": [mod]}).status_code

    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(executor.map(save, range(8)))
    assert sorted(statuses) == [200] + [409] * 7
    assert client.get(TENANT).json()["version"] == 1


def test_conflicting_replacements_do_not_change_saved_settings(
    client: TestClient, selection: dict[str, Any], archive: bytes, publication: bytes,
) -> None:
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 200
    other = {**selection, "mod_id": "other-tools", "publication": publish_mod(client, archive, publication, "other-tools")}
    rejected = client.put(TENANT, json={"version": 1, "mods": [selection, other]})
    assert rejected.status_code == 409
    assert "both replace" in rejected.json()["detail"]
    assert client.get(TENANT).json() == {"version": 1, "mods": [selection]}
    other["enabled"] = False
    assert client.put(TENANT, json={"version": 1, "mods": [selection, other]}).status_code == 200


def test_incompatible_host_blocks_enabling_but_allows_disabling(
    client: TestClient, selection: dict[str, Any], host: OpenWebuiModHost,
) -> None:
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 200
    host.compatibility = host.compatibility.model_copy(update={"source_commit": "c" * 40})
    rejected = client.put(TENANT, json={"version": 1, "mods": [selection]})
    assert rejected.status_code == 409
    assert "Recompile" in rejected.json()["detail"]
    selection["enabled"] = False
    assert client.put(TENANT, json={"version": 1, "mods": [selection]}).status_code == 200


def test_unavailable_host_does_not_prevent_disabling_all_mods(
    client: TestClient, selection: dict[str, Any], monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(OpenWebuiModService, "get_host", AsyncMock(side_effect=HTTPException(503, "Host unavailable")))
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 503
    selection["enabled"] = False
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 200


def test_missing_component_is_identified_before_saving(
    client: TestClient, selection: dict[str, Any], host: OpenWebuiModHost,
) -> None:
    host.components.clear()
    response = client.put(TENANT, json={"version": 0, "mods": [selection]})
    assert response.status_code == 409
    assert "target is absent" in response.json()["detail"]
    assert client.get(TENANT).json()["version"] == 0


@pytest.mark.parametrize("change, status", [({"mod_id": "other"}, 422), ({"publication": "0" * 64}, 404)])
def test_publication_must_exist_and_belong_to_selected_mod(
    client: TestClient, selection: dict[str, Any], change: dict[str, str], status: int,
) -> None:
    assert client.put(TENANT, json={"version": 0, "mods": [{**selection, **change}]}).status_code == status
    assert client.get(TENANT).json()["version"] == 0


def test_disabled_catalog_entry_can_keep_settings_before_publication(
    client: TestClient, archive: bytes,
) -> None:
    assert client.post(BASE + '/revisions', content=archive, headers={'content-type': 'application/zip'}).status_code == 200
    selection = {'mod_id': 'chat-tools', 'enabled': False, 'publication': None, 'settings': {'label': 'Draft'}}
    response = client.put(TENANT, json={'version': 0, 'mods': [selection]})
    assert response.status_code == 200, response.text
    assert response.json()['mods'] == [selection]
    assert client.put(TENANT, json={'version': 1, 'mods': [{**selection, 'mod_id': 'unknown'}]}).status_code == 422
    assert client.get(TENANT).json()['version'] == 1


@pytest.mark.parametrize("body", [
    {"version": True, "mods": []}, {"version": -1, "mods": []}, {"version": 0, "unknown": 1},
    {"version": 0, "mods": [{"mod_id": "tools", "publication": "0" * 64, "enabled": "yes"}]},
])
def test_invalid_configuration_is_rejected_before_writing(client: TestClient, body: dict[str, Any]) -> None:
    assert client.put(TENANT, json=body).status_code == 422
    assert client.get(TENANT).json()["version"] == 0


def test_duplicate_mods_and_oversized_settings_are_rejected(client: TestClient, selection: dict[str, Any]) -> None:
    assert client.put(TENANT, json={"version": 0, "mods": [selection, selection]}).status_code == 422
    selection["settings"] = {"large": "x" * (16 * 1024)}
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 422
    assert client.get(TENANT).json()["version"] == 0


def test_missing_and_orphaned_tenants_cannot_be_edited(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    assert client.get(BASE + "/tenants/missing").status_code == 404
    assert client.put(BASE + "/tenants/missing", json={"mods": []}).status_code == 404
    monkeypatch.setattr(KeycloakAdminService, "get_tenant_group", AsyncMock(side_effect=KeycloakGetError(response_code=404)))
    assert client.put(TENANT, json={"mods": []}).status_code == 409
    assert client.get(TENANT).json()["version"] == 0


def test_startup_mod_cannot_be_activated_for_a_tenant(client: TestClient, archive: bytes, publication: bytes) -> None:
    revision = publish_global(client, archive, publication)
    response = client.put(TENANT, json={"mods": [{"mod_id": "chat-tools", "publication": revision, "enabled": True}]})
    assert response.status_code == 422, response.text
    assert "requires global activation" in response.json()["detail"]
    assert TenantMetadataEntity.objects.get(id="one").openwebui_mods_json is None


def test_keycloak_failure_is_not_reported_as_an_orphan(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(KeycloakAdminService, "get_tenant_group", AsyncMock(side_effect=KeycloakGetError(response_code=503)))
    with pytest.raises(KeycloakGetError):
        client.put(TENANT, json={"mods": []})
    assert client.get(TENANT).json()["version"] == 0
