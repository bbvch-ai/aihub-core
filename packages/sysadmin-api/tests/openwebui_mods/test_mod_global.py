import hashlib
import json
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from zipfile import ZipFile

import httpx
import pytest
from fastapi.testclient import TestClient

from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_global_service import OpenWebuiModGlobalService
from swiss_ai_hub.sysadmin_api.routes.openwebui_mods.openwebui_mod_service import OpenWebuiModService
from tests.openwebui_mods.test_mod_upload import archive, auth, client, host, publication, storage, ModTestAuth  # noqa: F401

BASE = "/api/v1/admin/openwebui-mods"


@pytest.fixture
def control(monkeypatch: pytest.MonkeyPatch) -> list[httpx.Request]:
    calls = []
    state = {"configuration": {"version": 0, "mods": []}, "active_version": 0, "boot_id": "fixture-boot",
             "expected_workers": 2, "restart_required": False, "workers": []}

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

    monkeypatch.setattr(OpenWebuiModGlobalService, "_client", staticmethod(lambda: httpx.AsyncClient(
        base_url="http://native/_aihub/mods/control/", transport=httpx.MockTransport(respond),
    )))
    return calls


def publish_global(client: TestClient, source: bytes, publication: bytes, *, restart: bool = True) -> str:
    with ZipFile(BytesIO(source)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(files["mod.json"])
    manifest["backend_restart_required"] = restart
    files["mod.json"] = json.dumps(manifest).encode()
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    source = output.getvalue()
    revision = hashlib.sha256(source).hexdigest()
    assert client.post(BASE + "/revisions", content=source, headers={"Content-Type": "application/zip"}).status_code == 200
    with ZipFile(BytesIO(publication)) as archive:
        files = {name: archive.read(name) for name in archive.namelist()}
    manifest = json.loads(files["publication.json"])
    manifest["source_revision"] = revision
    files["publication.json"] = json.dumps(manifest).encode()
    output = BytesIO()
    with ZipFile(output, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    with patch.object(OpenWebuiModService, "_compile", AsyncMock(return_value=output.getvalue())):
        response = client.post(f"{BASE}/revisions/{revision}/publications")
    assert response.status_code == 200, response.text
    return response.json()["revision"]


def test_global_controls_require_sysadmin_before_contacting_host(client: TestClient, auth: ModTestAuth, control: list[httpx.Request]) -> None:
    auth.is_admin = False
    for method, path, body in [("GET", "/global", None), ("PUT", "/global", {"mods": []}),
                                ("POST", "/global/reconcile", None), ("POST", "/global/restart?version=0", None)]:
        assert client.request(method, BASE + path, json=body).status_code == 403
    assert control == []


def test_global_save_stages_private_archives_before_configuration_and_does_not_execute_python(
    client: TestClient, archive: bytes, publication: bytes, control: list[httpx.Request],
) -> None:
    revision = publish_global(client, archive, publication)
    response = client.put(BASE + "/global", json={"version": 0, "mods": [
        {"mod_id": "chat-tools", "publication": revision, "enabled": True, "settings": {"label": "Global"}},
    ]})
    assert response.status_code == 200, response.text
    assert response.json()["restart_required"] is True
    assert response.json()["configuration"]["version"] == 1
    assert [request.url.path.split("/control/")[1] for request in control] == [
        "archives/sources/" + hashlib.sha256(control[0].content).hexdigest(), "archives/publications/" + revision, "global",
    ]
    assert client.post(BASE + "/global/restart?version=1").status_code == 202
    assert client.put(BASE + "/global", json={"version": 0, "mods": []}).status_code == 409


def test_native_filter_only_mod_is_not_misrepresented_as_a_global_override(
    client: TestClient, archive: bytes, publication: bytes, control: list[httpx.Request],
) -> None:
    revision = publish_global(client, archive, publication, restart=False)
    response = client.put(BASE + "/global", json={"mods": [{"mod_id": "chat-tools", "publication": revision}]})
    assert response.status_code == 422, response.text
    assert "declared callable overrides" in response.json()["detail"]
    assert control == []


def test_global_reconcile_is_read_only_without_selected_builtins(client: TestClient, control: list[httpx.Request]) -> None:
    response = client.post(BASE + "/global/reconcile")
    assert response.status_code == 200
    assert response.json()["configuration"]["version"] == 0
    assert [request.method for request in control] == ["GET"]
