import hashlib
import json
from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock
from zipfile import ZipFile

import httpx
import pytest
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth import KeycloakAdminService
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModBundles, OpenWebuiModHost
from swiss_ai_hub.core.persistence import TenantMetadataEntity
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModEntity

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_controller import OpenWebuiModController
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_global_service import OpenWebuiModGlobalService
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService
from swiss_ai_hub.sysadmin_api.sysadmin_runner import SysadminApiRunner
from tests.openwebui_mods.helpers import ModTestAuth


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
    client.get_paginator.return_value.paginate.side_effect = lambda **kwargs: [
        {"Contents": [{"Key": key} for key in objects]}
    ]

    def delete_objects(**kwargs: Any) -> dict[str, Any]:
        for item in kwargs["Delete"]["Objects"]:
            objects.pop(item["Key"], None)
        return {}

    client.delete_objects.side_effect = delete_objects
    client.objects = objects
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
    OpenWebuiModEntity.drop_collection()
    monkeypatch.setattr(OpenWebuiModService, "get_host", AsyncMock(return_value=host))
    monkeypatch.setattr(OpenWebuiModService, "_compile", AsyncMock(return_value=publication))
    runner = SysadminApiRunner()
    runner.mount(
        OpenWebuiModController(auth=auth)
        .get_host()
        .catalog()
        .inspect()
        .install()
        .get_configuration()
        .replace_configuration()
        .get_builtins()
        .install_builtin()
        .global_configuration()
    )
    runner._api_app.state.s3_client = storage
    yield TestClient(runner.create_app())
    OpenWebuiModEntity.drop_collection()
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


@pytest.fixture(autouse=True)
def bundled_packages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    directory = tmp_path / "bundled"
    for name, mod_id in (("default-example", "builtin-default"), ("optional-example", "builtin-optional")):
        manifest = {
            "format": 1,
            "id": mod_id,
            "name": name,
            "version": "1",
            "frontend": "frontend.js",
            "default_settings": {"text": {"en": "Default fixture text"}},
        }
        package = directory / name
        package.mkdir(parents=True)
        (package / "mod.json").write_text(json.dumps(manifest))
        (package / "frontend.js").write_text("export function activate() {}")
    monkeypatch.setattr(OpenWebuiModBundles, "directory", staticmethod(lambda: directory))
    monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", '["builtin-default"]')


@pytest.fixture(autouse=True)
def control(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    calls = []
    state = {
        "configuration": {"version": 0, "mods": []},
        "active_version": 0,
        "boot_id": "fixture-boot",
        "expected_workers": 2,
        "restart_required": False,
        "workers": [],
    }

    def respond(request: httpx.Request) -> httpx.Response:
        calls.append(request)
        if request.url.path.endswith("/global"):
            if request.method == "PUT":
                configuration = json.loads(request.content)
                if configuration["version"] != state["configuration"]["version"]:
                    return httpx.Response(409, json={"detail": "Global mod settings changed"})
                state["configuration"] = {**configuration, "version": configuration["version"] + 1}
                state["restart_required"] = True
            return httpx.Response(200, json=state)
        if "/archives/" in request.url.path:
            return httpx.Response(204)
        return httpx.Response(202, json={"status": "restarting", "version": state["configuration"]["version"]})

    monkeypatch.setattr(
        OpenWebuiModGlobalService,
        "_client",
        staticmethod(
            lambda: httpx.AsyncClient(
                base_url="http://native/_aihub/mods/control/",
                transport=httpx.MockTransport(respond),
            )
        ),
    )
    return calls


@pytest.fixture
def tenants(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    TenantMetadataEntity.drop_collection()
    for tenant_id in ("one", "two"):
        TenantMetadataEntity(id=tenant_id, name=tenant_id, access_rules=["aihub.user.>"]).save()
    monkeypatch.setattr(
        TenantMetadataEntity,
        "get_metadata_by_tenant_id",
        lambda tenant_id: TenantMetadataEntity.objects(id=tenant_id).first(),
    )
    monkeypatch.setattr(KeycloakAdminService, "get_tenant_group", AsyncMock())
    yield
    TenantMetadataEntity.drop_collection()
