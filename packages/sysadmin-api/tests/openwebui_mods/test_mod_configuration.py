import json
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from keycloak import KeycloakGetError
from swiss_ai_hub.core.auth import KeycloakAdminService
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModHost
from swiss_ai_hub.core.persistence import TenantMetadataEntity

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService
from tests.openwebui_mods.helpers import install_mod

BASE = "/api/v1/admin/openwebui-mods"
TENANT = BASE + "/tenants/one"


pytestmark = pytest.mark.usefixtures("tenants")


@pytest.fixture
def selection(client: TestClient, archive: bytes, publication: bytes) -> dict[str, Any]:
    install_mod(client, archive, publication)
    return {
        "mod_id": "chat-tools",
        "enabled": True,
        "settings": {"label": "Tools", "nested": {"some.key": [True, 3, None]}},
    }


def test_configuration_is_tenant_scoped_and_preserves_other_metadata(
    client: TestClient,
    selection: dict[str, Any],
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
    client: TestClient,
    selection: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
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


def test_default_configuration_reads_do_not_write_archives(client: TestClient, storage: MagicMock) -> None:
    first = client.get(TENANT).json()
    writes = storage.put_object.call_count
    assert client.get(TENANT).json() == first
    assert storage.put_object.call_count == writes == 0
    assert "publication" not in first["mods"][0]


def test_concurrent_default_reads_return_the_same_unsaved_configuration(client: TestClient) -> None:
    def read(_: int) -> dict[str, Any]:
        response = client.get(TENANT)
        assert response.status_code == 200, response.text
        return response.json()

    with ThreadPoolExecutor(max_workers=8) as executor:
        configurations = list(executor.map(read, range(8)))
    assert all(configuration == configurations[0] for configuration in configurations)
    assert TenantMetadataEntity.objects.get(id="one").openwebui_mods_json is None


def test_disable_and_reenable_preserve_settings(client: TestClient, selection: dict[str, Any]) -> None:
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
    client: TestClient,
    selection: dict[str, Any],
    archive: bytes,
    publication: bytes,
) -> None:
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 200
    install_mod(client, archive, publication, "other-tools")
    other = {**selection, "mod_id": "other-tools"}
    rejected = client.put(TENANT, json={"version": 1, "mods": [selection, other]})
    assert rejected.status_code == 409
    assert "both replace" in rejected.json()["detail"]
    assert client.get(TENANT).json() == {"version": 1, "mods": [selection]}
    other["enabled"] = False
    assert client.put(TENANT, json={"version": 1, "mods": [selection, other]}).status_code == 200


def test_incompatible_host_blocks_enabling_but_allows_disabling(
    client: TestClient,
    selection: dict[str, Any],
    host: OpenWebuiModHost,
) -> None:
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 200
    host.compatibility = host.compatibility.model_copy(update={"source_commit": "c" * 40})
    rejected = client.put(TENANT, json={"version": 1, "mods": [selection]})
    assert rejected.status_code == 409
    assert "installation" in rejected.json()["detail"]
    selection["enabled"] = False
    assert client.put(TENANT, json={"version": 1, "mods": [selection]}).status_code == 200


def test_unavailable_host_does_not_prevent_disabling_all_mods(
    client: TestClient,
    selection: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(OpenWebuiModService, "get_host", AsyncMock(side_effect=HTTPException(503, "Host unavailable")))
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 503
    selection["enabled"] = False
    assert client.put(TENANT, json={"version": 0, "mods": [selection]}).status_code == 200


def test_missing_component_is_identified_before_saving(
    client: TestClient,
    selection: dict[str, Any],
    host: OpenWebuiModHost,
) -> None:
    host.components.clear()
    response = client.put(TENANT, json={"version": 0, "mods": [selection]})
    assert response.status_code == 409
    assert "target is absent" in response.json()["detail"]
    assert client.get(TENANT).json()["version"] == 0


@pytest.mark.parametrize("change, status", [({"mod_id": "other"}, 422), ({"publication": "0" * 64}, 422)])
def test_publication_must_exist_and_belong_to_selected_mod(
    client: TestClient,
    selection: dict[str, Any],
    change: dict[str, str],
    status: int,
) -> None:
    assert client.put(TENANT, json={"version": 0, "mods": [{**selection, **change}]}).status_code == status
    assert client.get(TENANT).json()["version"] == 0


def test_disabled_installed_mod_can_keep_settings(
    client: TestClient,
    archive: bytes,
) -> None:
    assert (
        client.post(BASE + "/install", content=archive, headers={"content-type": "application/zip"}).status_code == 200
    )
    selection = {"mod_id": "chat-tools", "enabled": False, "settings": {"label": "Draft"}}
    response = client.put(TENANT, json={"version": 0, "mods": [selection]})
    assert response.status_code == 200, response.text
    assert response.json()["mods"] == [selection]
    assert client.put(TENANT, json={"version": 1, "mods": [{**selection, "mod_id": "unknown"}]}).status_code == 422
    assert client.get(TENANT).json()["version"] == 1


@pytest.mark.parametrize(
    "body",
    [
        {"version": True, "mods": []},
        {"version": -1, "mods": []},
        {"version": 0, "unknown": 1},
        {"version": 0, "mods": [{"mod_id": "tools", "publication": "0" * 64, "enabled": "yes"}]},
    ],
)
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
    monkeypatch.setattr(
        KeycloakAdminService, "get_tenant_group", AsyncMock(side_effect=KeycloakGetError(response_code=404))
    )
    assert client.put(TENANT, json={"mods": []}).status_code == 409
    assert client.get(TENANT).json()["version"] == 0


def test_package_scope_change_preserves_tenant_intent_but_does_not_activate_globally(
    client: TestClient, selection: dict[str, Any], archive: bytes, publication: bytes
) -> None:
    assert client.put(TENANT, json={"mods": [selection]}).status_code == 200
    install_mod(client, archive, publication, backend_restart_required=True)
    assert client.get(TENANT).json()["mods"] == [selection]
    assert client.get(BASE + "/global").json()["configuration"]["mods"] == []
    assert client.get(BASE + "/catalog").json()[0]["scopes"] == ["global"]
    assert client.put(TENANT, json={"version": 1, "mods": [selection]}).status_code == 200


def test_keycloak_failure_is_not_reported_as_an_orphan(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        KeycloakAdminService, "get_tenant_group", AsyncMock(side_effect=KeycloakGetError(response_code=503))
    )
    with pytest.raises(KeycloakGetError):
        client.put(TENANT, json={"mods": []})
    assert client.get(TENANT).json()["version"] == 0


def test_replacement_does_not_validate_or_rewrite_saved_settings(
    client: TestClient, selection: dict[str, Any], archive: bytes, publication: bytes
) -> None:
    assert client.put(TENANT, json={"mods": [selection]}).status_code == 200
    before = TenantMetadataEntity.objects.get(id="one").openwebui_mods_json
    install_mod(client, archive, publication, version="2", settings_fields={"new_required_field": {"required": True}})
    assert TenantMetadataEntity.objects.get(id="one").openwebui_mods_json == before
    form = client.get(BASE + "/catalog").json()[0]["settings_form"]
    assert any(field["name"] == "new_required_field" and field["required"] for field in form)
