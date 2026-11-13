import asyncio
import json
from io import BytesIO
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient
from swiss_ai_hub.core.infrastructure.openwebui import (
    OpenWebuiModBundles,
    OpenWebuiModConfiguration,
    OpenWebuiModHost,
    OpenWebuiModResolver,
)
from swiss_ai_hub.core.persistence import TenantMetadataEntity
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModEntity

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService

pytestmark = pytest.mark.usefixtures("tenants")

BASE = "/api/v1/admin/openwebui-mods"


def install_builtins(client: TestClient, host: OpenWebuiModHost) -> dict[str, str]:
    sources = OpenWebuiModBundles.packages()
    publications = {}
    for mod_id, package in sources.items():
        manifest = package.manifest.model_dump()
        host.components.update(manifest["replacements"])
        metadata = {
            "format": 1,
            "source_revision": package.revision,
            "compatibility": host.compatibility.model_dump(),
            "bootstrap": "bootstrap/" + manifest["bootstrap"] + ".mjs" if manifest["bootstrap"] else None,
            "frontend": "frontend/" + manifest["frontend"] + ".mjs" if manifest["frontend"] else None,
            "replacements": {target: "frontend/" + path + ".mjs" for target, path in manifest["replacements"].items()},
        }
        buffer = BytesIO()
        with ZipFile(buffer, "w") as zipped:
            zipped.writestr("publication.json", json.dumps(metadata))
            for entry in (metadata["bootstrap"], metadata["frontend"]):
                if entry:
                    zipped.writestr("files/" + entry, "export function activate() {}")
            for filename in metadata["replacements"].values():
                zipped.writestr("files/" + filename, "export default function Component() {}")
        with patch.object(OpenWebuiModService, "_compile", AsyncMock(return_value=buffer.getvalue())):
            response = client.post(f"{BASE}/builtins/{mod_id}/install")
        assert response.status_code == 200, response.text
        publications[manifest["id"]] = OpenWebuiModEntity.find_mod(mod_id).publication
    return publications


def test_initializer_validates_publications_without_rewriting_tenant_settings(
    client: TestClient,
    host: OpenWebuiModHost,
) -> None:
    install_builtins(client, host)
    before = list(TenantMetadataEntity._get_collection().find())
    install_builtins(client, host)
    assert list(TenantMetadataEntity._get_collection().find()) == before
    saved = client.get(BASE + "/tenants/one").json()
    disclaimer = saved["mods"][0]
    assert "publication" not in disclaimer and disclaimer["enabled"]
    disclaimer["enabled"] = False
    disclaimer["settings"] = {"text": {"en": "Custom terms"}, "custom": "Later edit"}
    updated = client.put(BASE + "/tenants/one", json=saved)
    assert updated.status_code == 200, updated.text
    before = list(TenantMetadataEntity._get_collection().find())
    install_builtins(client, host)
    assert list(TenantMetadataEntity._get_collection().find()) == before
    assert client.get(BASE + "/tenants/one").json() == updated.json()


def test_failed_builtin_install_does_not_create_catalog_entry(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from fastapi import HTTPException

    monkeypatch.setattr(OpenWebuiModService, "_compile", AsyncMock(side_effect=HTTPException(422, "Compiler failed")))
    assert client.post(BASE + "/builtins/builtin-default/install").status_code == 422
    assert client.get(BASE + "/catalog").json() == []


def test_initializer_checks_all_bundles_even_without_enabled_defaults(
    client: TestClient,
    host: OpenWebuiModHost,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    install_builtins(client, host)
    monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", "[]")
    install_builtins(client, host)
    assert all(tenant.openwebui_mods_json is None for tenant in TenantMetadataEntity.objects)


def test_builtins_cannot_be_pinned_even_when_disabled(client: TestClient, host: OpenWebuiModHost) -> None:
    publications = install_builtins(client, host)
    for enabled in (True, False):
        response = client.put(
            BASE + "/tenants/one",
            json={
                "mods": [
                    {
                        "mod_id": "builtin-default",
                        "publication": publications["builtin-default"],
                        "enabled": enabled,
                    }
                ]
            },
        )
        assert response.status_code == 422
        assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_builtin_upgrade_changes_code_without_rewriting_tenant_choices(
    client: TestClient,
    host: OpenWebuiModHost,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    previous = install_builtins(client, host)
    install_builtins(client, host)
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
    with pytest.raises(ValueError, match="needs initialization"):
        asyncio.run(OpenWebuiModResolver.resolve(OpenWebuiModConfiguration.model_validate(saved), host.compatibility))
    current = install_builtins(client, host)
    assert current["builtin-default"] != previous["builtin-default"]
    install_builtins(client, host)
    assert client.get(BASE + "/tenants/one").json() == saved
    resolved = asyncio.run(
        OpenWebuiModResolver.resolve(OpenWebuiModConfiguration.model_validate(saved), host.compatibility)
    )
    assert resolved.mods[0].publication == current["builtin-default"]
    assert resolved.mods[0].settings["text"] == {"en": "Keep my text"}
