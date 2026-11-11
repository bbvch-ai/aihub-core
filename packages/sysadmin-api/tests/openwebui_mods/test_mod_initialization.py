import asyncio
import json
from io import BytesIO
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModBundles, OpenWebuiModConfiguration, OpenWebuiModHost, OpenWebuiModResolver,
)
from swiss_ai_hub.core.persistence import TenantMetadataEntity

from tests.openwebui_mods.test_mod_configuration import tenants  # noqa: F401
from tests.openwebui_mods.test_mod_upload import archive, auth, client, host, publication, storage  # noqa: F401
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService

BASE = "/api/v1/admin/openwebui-mods"


def publish_builtins(client: TestClient, host: OpenWebuiModHost) -> tuple[dict[str, str], dict[str, str]]:
    sources = client.get(BASE + "/builtins").json()
    revisions, publications = {}, {}
    for source in sources:
        manifest = source["manifest"]
        host.components.update(manifest["replacements"])
        metadata = {
            "format": 1, "source_revision": source["revision"], "compatibility": host.compatibility.model_dump(),
            "frontend": manifest["frontend"] + ".mjs" if manifest["frontend"] else None,
            "replacements": {target: path + ".mjs" for target, path in manifest["replacements"].items()},
        }
        buffer = BytesIO()
        with ZipFile(buffer, "w") as zipped:
            zipped.writestr("publication.json", json.dumps(metadata))
            if metadata["frontend"]:
                zipped.writestr("files/" + metadata["frontend"], "export function activate() {}")
            for filename in metadata["replacements"].values():
                zipped.writestr("files/" + filename, "export default function Component() {}")
        with patch.object(OpenWebuiModService, "_compile", AsyncMock(return_value=buffer.getvalue())):
            response = client.post(f'{BASE}/revisions/{source["revision"]}/publications')
        assert response.status_code == 200, response.text
        revisions[manifest["id"]] = source["revision"]
        publications[manifest["id"]] = response.json()["revision"]
    return revisions, publications


def test_initializer_validates_publications_without_rewriting_tenant_settings(
    client: TestClient, host: OpenWebuiModHost,
) -> None:
    revisions, _ = publish_builtins(client, host)
    before = list(TenantMetadataEntity._get_collection().find())
    initialized = client.post(BASE + "/initialize", json=revisions)
    assert initialized.status_code == 204, initialized.text
    assert initialized.content == b""
    assert list(TenantMetadataEntity._get_collection().find()) == before
    saved = client.get(BASE + "/tenants/one").json()
    disclaimer = saved["mods"][0]
    assert disclaimer["publication"] is None and disclaimer["enabled"]
    disclaimer["enabled"] = False
    disclaimer["settings"] = {"text": {"en": "Custom terms"}, "custom": "Later edit"}
    updated = client.put(BASE + "/tenants/one", json=saved)
    assert updated.status_code == 200, updated.text
    before = list(TenantMetadataEntity._get_collection().find())
    assert client.post(BASE + "/initialize", json=revisions).status_code == 204
    assert list(TenantMetadataEntity._get_collection().find()) == before
    assert client.get(BASE + "/tenants/one").json() == updated.json()


def test_initializer_waits_for_all_publications_and_rejects_stale_sources(client: TestClient) -> None:
    sources = client.get(BASE + "/builtins").json()
    revisions = {source["manifest"]["id"]: source["revision"] for source in sources}
    assert client.post(BASE + "/initialize", json=revisions).status_code == 409
    assert client.post(BASE + "/initialize", json={}).status_code == 409
    assert all(tenant.openwebui_mods_json is None for tenant in TenantMetadataEntity.objects)


def test_initializer_checks_all_bundles_even_without_enabled_defaults(
    client: TestClient, host: OpenWebuiModHost, monkeypatch: pytest.MonkeyPatch,
) -> None:
    revisions, _ = publish_builtins(client, host)
    monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", "[]")
    assert client.post(BASE + "/initialize", json=revisions).status_code == 204
    assert all(tenant.openwebui_mods_json is None for tenant in TenantMetadataEntity.objects)


def test_builtins_cannot_be_pinned_even_when_disabled(client: TestClient, host: OpenWebuiModHost) -> None:
    _, publications = publish_builtins(client, host)
    for enabled in (True, False):
        response = client.put(BASE + "/tenants/one", json={"mods": [{
            "mod_id": "builtin-default", "publication": publications["builtin-default"], "enabled": enabled,
        }]})
        assert response.status_code == 422
        assert "cannot be pinned" in response.json()["detail"]


def test_builtin_upgrade_changes_code_without_rewriting_tenant_choices(
    client: TestClient, host: OpenWebuiModHost, monkeypatch: pytest.MonkeyPatch,
) -> None:
    revisions, previous = publish_builtins(client, host)
    assert client.post(BASE + "/initialize", json=revisions).status_code == 204
    configuration = client.get(BASE + "/tenants/one").json()
    configuration["mods"][0]["settings"]["text"] = {"en": "Keep my text"}
    saved = client.put(BASE + "/tenants/one", json=configuration).json()
    original_source = OpenWebuiModBundles.source

    def upgraded_source(name: str) -> bytes:
        content = original_source(name)
        if name != "default-example":
            return content
        with ZipFile(BytesIO(content)) as archive:
            files = {name: archive.read(name) for name in archive.namelist()}
        files["frontend.js"] += b"\n// Test release changes its implementation.\n"
        return OpenWebuiModBundles.zip(files)

    monkeypatch.setattr(OpenWebuiModBundles, "source", upgraded_source)
    with pytest.raises(ValueError, match="not initialized"):
        asyncio.run(OpenWebuiModResolver.resolve(OpenWebuiModConfiguration.model_validate(saved), host.compatibility))
    assert client.post(BASE + "/initialize", json=revisions).status_code == 409
    revisions, current = publish_builtins(client, host)
    assert current["builtin-default"] != previous["builtin-default"]
    assert client.post(BASE + "/initialize", json=revisions).status_code == 204
    assert client.get(BASE + "/tenants/one").json() == saved
    resolved = asyncio.run(OpenWebuiModResolver.resolve(OpenWebuiModConfiguration.model_validate(saved), host.compatibility))
    assert resolved.mods[0].publication == current["builtin-default"]
    assert resolved.mods[0].settings["text"] == {"en": "Keep my text"}
