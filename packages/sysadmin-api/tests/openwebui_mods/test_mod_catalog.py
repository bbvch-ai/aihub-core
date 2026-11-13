from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModEntity
from tests.openwebui_mods.helpers import BASE, install_mod


def test_catalog_reads_do_not_install_builtins(client: TestClient, storage: MagicMock) -> None:
    assert client.get(BASE + "/catalog").json() == []
    assert client.get(BASE + "/builtins").json() == ["builtin-default", "builtin-optional"]
    assert OpenWebuiModEntity.objects.count() == 0
    assert storage.mock_calls == []


def test_catalog_paginates_installed_mods_with_one_entry_per_id(client: TestClient, archive: bytes, publication: bytes) -> None:
    install_mod(client, archive, publication, "a-first")
    install_mod(client, archive, publication, "z-last")
    for version in ["2", "3", "4"]:
        install_mod(client, archive, publication, "a-first", version=version)
    first = client.get(BASE + "/catalog", params={"offset": 0, "limit": 1}).json()
    last = client.get(BASE + "/catalog", params={"offset": 1, "limit": 1}).json()
    assert first[0]["manifest"]["id"] == "a-first"
    assert first[0]["manifest"]["version"] == "4"
    assert last[0]["manifest"]["id"] == "z-last"
    assert client.get(BASE + "/catalog", params={"offset": 2, "limit": 1}).json() == []
    assert not first[0]["builtin"]
