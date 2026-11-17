import hashlib
import json

import httpx
from fastapi.testclient import TestClient

from tests.openwebui_mods.helpers import ModTestAuth, install_mod

BASE = "/api/v1/admin/openwebui-mods"


def install_global(client: TestClient, source: bytes, publication: bytes, *, restart: bool = True) -> str:
    return install_mod(client, source, publication, backend_restart_required=restart)


def test_global_controls_require_sysadmin_before_contacting_host(
    client: TestClient, auth: ModTestAuth, control: list[httpx.Request]
) -> None:
    auth.is_admin = False
    for method, path, body in [
        ("GET", "/global", None),
        ("PUT", "/global", {"mods": []}),
        ("POST", "/global/reconcile", None),
        ("POST", "/global/restart?version=0", None),
    ]:
        assert client.request(method, BASE + path, json=body).status_code == 403
    assert control == []


def test_global_save_stages_private_archives_before_configuration_and_does_not_execute_python(
    client: TestClient,
    archive: bytes,
    publication: bytes,
    control: list[httpx.Request],
) -> None:
    revision = install_global(client, archive, publication)
    control.clear()
    response = client.put(
        BASE + "/global",
        json={
            "version": 0,
            "mods": [
                {"mod_id": "chat-tools", "enabled": True, "settings": {"label": "Global"}},
            ],
        },
    )
    assert response.status_code == 200, response.text
    assert response.json()["restart_required"] is True
    assert response.json()["configuration"]["version"] == 1
    assert response.json()["configuration"]["mods"] == [
        {"mod_id": "chat-tools", "enabled": True, "settings": {"label": "Global"}},
    ]
    assert json.loads(control[-1].content)["mods"][0]["has_backend"] is True
    assert [request.url.path.split("/control/")[1] for request in control] == [
        "archives/sources/" + hashlib.sha256(control[0].content).hexdigest(),
        "archives/publications/" + revision,
        "global",
    ]
    assert client.post(BASE + "/global/restart?version=1").status_code == 202
    assert client.put(BASE + "/global", json={"version": 0, "mods": []}).status_code == 409


def test_scope_change_preserves_global_settings_without_enabling_tenant_use(
    client: TestClient, archive: bytes, publication: bytes, control: list[httpx.Request]
) -> None:
    old = install_global(client, archive, publication)
    selection = {"mod_id": "chat-tools", "enabled": True, "settings": {"label": "Global"}}
    assert client.put(BASE + "/global", json={"mods": [selection]}).status_code == 200
    new = install_global(client, archive, publication, restart=False)
    assert old != new
    saved = client.get(BASE + "/global").json()["configuration"]
    assert saved == {"version": 2, "mods": [selection]}
    puts = [
        json.loads(request.content)
        for request in control
        if request.method == "PUT" and request.url.path.endswith("/global")
    ]
    assert puts[-1]["mods"][0]["publication"] == new
    assert client.get(BASE + "/catalog").json()[0]["scopes"] == ["tenant"]


def test_global_reconcile_is_read_only_without_selected_mods(client: TestClient, control: list[httpx.Request]) -> None:
    response = client.post(BASE + "/global/reconcile")
    assert response.status_code == 200
    assert response.json()["configuration"]["version"] == 0
    assert [request.method for request in control] == ["GET"]
