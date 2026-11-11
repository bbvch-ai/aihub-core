import hashlib
import hmac
import json
from collections.abc import Generator
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from zipfile import ZipFile

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from mongoengine import connect, disconnect
from swiss_ai_hub.core.auth import AuthHandler, KeycloakAdminService, TokenAuthHandler
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoSettings
from swiss_ai_hub.core.infrastructure.openwebui import OpenWebuiModBundles, OpenWebuiModConfiguration, OpenWebuiModPackage, OpenWebuiModPublication
from swiss_ai_hub.core.persistence import RoleEntity, TenantMetadataEntity, UserTenantRoleEntity
from swiss_ai_hub.core.persistence.openwebui import OpenWebuiModPublicationEntity, OpenWebuiModRevisionEntity

from swiss_ai_hub.api.routes.openai.openai_controller import OpenaiController

BASE = "/one/openai/mods"
SIGNING_SECRET = "test-mod-forwarding-secret-" * 4
RESOLVE_ACTIVE_TENANT = AuthHandler._resolve_active_tenant
HOST_COMPATIBILITY = json.loads((Path(__file__).resolve().parents[6] / "infra/deployment/docker/open-webui/mods/compatibility.json").read_text())


def headers(user: str = "reader") -> dict[str, str]:
    message = f"name:{user},email:{user}@example.test".encode()
    return {
        "Authorization": "Bearer service-token", "X-OpenWebUI-User-Name": user,
        "X-OpenWebUI-User-Email": f"{user}@example.test",
        "X-OpenWebUI-Signature": hmac.new(SIGNING_SECRET.encode(), message, hashlib.sha256).hexdigest(),
        "X-AIHub-Mod-Compatibility": json.dumps(HOST_COMPATIBILITY),
    }


@pytest.fixture
def compatibility() -> dict:
    return dict(HOST_COMPATIBILITY)


@pytest.fixture
def storage() -> MagicMock:
    client = MagicMock()
    objects: dict[str, bytes] = {}
    client.put_object.side_effect = lambda **kwargs: objects.update({kwargs["Key"]: kwargs["Body"]})
    client.get_object.side_effect = lambda **kwargs: {"Body": BytesIO(objects[kwargs["Key"]])}
    return client


@pytest.fixture(autouse=True)
def bundled_packages(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    directory = tmp_path / "bundled"
    for name, mod_id in (("default-example", "builtin-default"), ("optional-example", "builtin-optional")):
        manifest = {
            "format": 1, "id": mod_id, "name": name, "version": "1", "frontend": "frontend.js",
            "default_settings": {"text": {"en": "Default fixture text"}},
        }
        package = directory / name
        package.mkdir(parents=True)
        (package / "mod.json").write_text(json.dumps(manifest))
        (package / "frontend.js").write_text("export function activate() {}")
    monkeypatch.setattr(OpenWebuiModBundles, "directory", staticmethod(lambda: directory))
    monkeypatch.setenv("OPENWEBUI_MODS_DEFAULTS", '["builtin-default"]')


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, storage: MagicMock, compatibility: dict) -> Generator[TestClient]:
    connect(db=AIHubSettings().MONGO_MAIN_DB_NAME, host=MongoSettings().CONNECTION_STRING.get_secret_value())
    for entity in [TenantMetadataEntity, OpenWebuiModPublicationEntity, OpenWebuiModRevisionEntity]:
        entity.drop_collection()
    for name in OpenWebuiModBundles.names():
        content = OpenWebuiModBundles.source(name)
        package = OpenWebuiModPackage.from_zip(content)
        metadata = {
            "format": 1, "source_revision": package.revision, "compatibility": compatibility,
            "frontend": package.manifest.frontend + ".mjs" if package.manifest.frontend else None,
            "replacements": {target: source + ".mjs" for target, source in package.manifest.replacements.items()},
        }
        files = {"publication.json": json.dumps(metadata).encode()}
        if metadata["frontend"]:
            files["files/" + metadata["frontend"]] = package.files[package.manifest.frontend]
        for filename in metadata["replacements"].values():
            files["files/" + filename] = b"export default function Component() {}"
        bundle = OpenWebuiModBundles.zip(files)
        publication = OpenWebuiModPublication.from_zip(bundle)
        OpenWebuiModRevisionEntity.record_upload(package, len(content), "initializer")
        OpenWebuiModPublicationEntity.record_publication(publication, package.manifest.id, len(bundle), "initializer")
        storage.put_object(Key=f"sources/{package.revision}.zip", Body=content)
        storage.put_object(Key=f"publications/{publication.revision}.zip", Body=bundle)
    storage.put_object.reset_mock()
    for tenant_id in ["one", "two"]:
        TenantMetadataEntity(id=tenant_id, name=tenant_id, access_rules=["aihub.user.service.openai"]).save()
    monkeypatch.setenv("AUTH_OPEN_WEBUI_SIGNING_SECRET", SIGNING_SECRET)
    monkeypatch.setattr(TenantMetadataEntity, "get_metadata_by_tenant_id", lambda tenant_id: TenantMetadataEntity.objects(id=tenant_id).first())
    monkeypatch.setattr(KeycloakAdminService, "is_user_member_of_tenant", AsyncMock(side_effect=lambda user_id, tenant_id: tenant_id in {"one", "two"}))
    monkeypatch.setattr(KeycloakAdminService, "find_user_by_email", AsyncMock(side_effect=lambda email: SimpleNamespace(id=email.split("@")[0], name=email.split("@")[0], email=email)))
    monkeypatch.setattr(UserTenantRoleEntity, "get_roles_for_user_in_tenant", lambda user_id, tenant_id: [user_id])
    monkeypatch.setattr(RoleEntity, "get_access_rules_for_roles", lambda roles, **kwargs: [] if roles == ["denied"] else ["aihub.user.service.openai"])

    def verify_token(value: str) -> None:
        if value != "service-token":
            raise HTTPException(401, "Invalid service token")

    monkeypatch.setattr(TokenAuthHandler, "verify_token", staticmethod(verify_token))
    ordinary_auth = AsyncMock(side_effect=AssertionError("Runtime archives must use forwarded server authentication"))
    app = FastAPI()
    app.state.s3_client = storage
    OpenaiController(auth=ordinary_auth).with_openwebui_mods().mount(app, SimpleNamespace())
    with TestClient(app) as test_client:
        yield test_client
    ordinary_auth.assert_not_called()
    for entity in [TenantMetadataEntity, OpenWebuiModPublicationEntity, OpenWebuiModRevisionEntity]:
        entity.drop_collection()
    disconnect()


def publish_mod(compatibility: dict, storage: MagicMock, *, version: str = "1", mod_id: str = "tools") -> dict:
    source = BytesIO()
    with ZipFile(source, "w") as zipped:
        zipped.writestr("mod.json", json.dumps({"format": 1, "id": mod_id, "name": "Tools", "version": version, "frontend": "main.js", "backend": "backend.py"}))
        zipped.writestr("main.js", "export function activate() {}")
        zipped.writestr("backend.py", "raise RuntimeError('Do not execute source while serving it')")
    package = OpenWebuiModPackage.from_zip(source.getvalue())
    OpenWebuiModRevisionEntity.record_upload(package, len(source.getvalue()), "sysadmin")
    compiled = BytesIO()
    with ZipFile(compiled, "w") as zipped:
        zipped.writestr("publication.json", json.dumps({"format": 1, "source_revision": package.revision, "compatibility": compatibility, "frontend": "main.js.mjs"}))
        zipped.writestr("files/main.js.mjs", "export function activate() {}")
    publication = OpenWebuiModPublication.from_zip(compiled.getvalue())
    OpenWebuiModPublicationEntity.record_publication(publication, mod_id, len(compiled.getvalue()), "sysadmin")
    storage.put_object(Key=f"sources/{package.revision}.zip", Body=source.getvalue())
    storage.put_object(Key=f"publications/{publication.revision}.zip", Body=compiled.getvalue())
    return {"revision": publication.revision, "source": source.getvalue(), "frontend": compiled.getvalue()}


@pytest.fixture
def published(client: TestClient, compatibility: dict, storage: MagicMock) -> dict:
    publication = publish_mod(compatibility, storage)
    configuration = OpenWebuiModConfiguration(version=7, mods=[
        {"mod_id": "tools", "publication": publication["revision"], "settings": {"label": "Original"}},
    ])
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=configuration.model_dump_json())
    return publication


def resolve_configuration(client: TestClient, compatibility: dict, *, user: str = "reader", base: str = BASE) -> dict:
    response = client.post(base + "/configuration", headers=headers(user), json=compatibility)
    assert response.status_code == 200, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()


def test_runtime_resolves_current_configuration_without_user_contexts(
    client: TestClient, compatibility: dict, published: dict,
) -> None:
    current = resolve_configuration(client, compatibility)
    assert set(current) == {"tenant_id", "compatibility", "configuration", "revision"}
    assert current["tenant_id"] == "one"
    assert current["compatibility"] == compatibility
    assert current["configuration"]["version"] == 7
    assert len(current["revision"]) == 64
    for kind in ["source", "frontend"]:
        response = client.get(f'{BASE}/publications/{published["revision"]}/{kind}', headers=headers())
        assert response.content == published[kind]
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-content-type-options"] == "nosniff"
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json='{"version":8,"mods":[]}')
    updated = resolve_configuration(client, compatibility)
    assert updated["configuration"] == {"version": 8, "mods": []}
    assert updated["revision"] != current["revision"]
    assert client.get(f'{BASE}/publications/{published["revision"]}/source', headers=headers()).status_code == 403
    assert all("/contexts" not in path for path in client.app.openapi()["paths"])


def test_runtime_applies_bundled_defaults_only_to_unconfigured_tenants(
    client: TestClient, compatibility: dict,
) -> None:
    current = resolve_configuration(client, compatibility)
    mods = current["configuration"]["mods"]
    assert [mod["mod_id"] for mod in mods] == ["builtin-default"]
    assert mods[0]["settings"] == {"text": {"en": "Default fixture text"}}
    publication = mods[0]["publication"]
    assert client.get(f'{BASE}/publications/{publication}/frontend', headers=headers()).status_code == 200
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json='{"mods":[]}')
    assert resolve_configuration(client, compatibility)["configuration"]["mods"] == []
    assert client.get(f'{BASE}/publications/{publication}/frontend', headers=headers()).status_code == 403


def test_revision_is_shared_between_users_and_ignores_save_version_and_json_key_order(
    client: TestClient, compatibility: dict, published: dict,
) -> None:
    current = resolve_configuration(client, compatibility)
    configuration = current["configuration"]
    configuration["mods"][0]["settings"] = {"label": "Original", "nested": {"first": 1, "second": 2}}
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=json.dumps(configuration))
    first = resolve_configuration(client, compatibility)
    configuration["version"] += 1
    configuration["mods"][0]["settings"] = {"nested": {"second": 2, "first": 1}, "label": "Original"}
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=json.dumps(configuration))
    second = resolve_configuration(client, compatibility, user="another")
    assert second["configuration"]["version"] == first["configuration"]["version"] + 1
    assert first["revision"] == second["revision"]
    assert second["revision"] == resolve_configuration(client, compatibility)["revision"]


def test_revision_tracks_settings_publications_and_mod_order(
    client: TestClient, compatibility: dict, published: dict, storage: MagicMock,
) -> None:
    current = resolve_configuration(client, compatibility)
    revisions = {current["revision"]}
    configuration = current["configuration"]
    configuration["mods"][0]["settings"]["label"] = "Updated"
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=json.dumps(configuration))
    revisions.add(resolve_configuration(client, compatibility)["revision"])
    replacement = publish_mod(compatibility, storage, version="2")
    configuration["mods"][0]["publication"] = replacement["revision"]
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=json.dumps(configuration))
    revisions.add(resolve_configuration(client, compatibility)["revision"])
    extra = publish_mod(compatibility, storage, mod_id="extra")
    configuration["mods"].append({"mod_id": "extra", "publication": extra["revision"]})
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=json.dumps(configuration))
    revisions.add(resolve_configuration(client, compatibility)["revision"])
    configuration["mods"].reverse()
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=json.dumps(configuration))
    revisions.add(resolve_configuration(client, compatibility)["revision"])
    assert len(revisions) == 5


def test_revision_includes_tenant_and_host_even_for_empty_selections(client: TestClient, compatibility: dict) -> None:
    TenantMetadataEntity.objects.update(set__openwebui_mods_json='{"mods":[]}')
    first = resolve_configuration(client, compatibility)
    other_tenant = resolve_configuration(client, compatibility, base=BASE.replace("/one/", "/two/"))
    other_host = resolve_configuration(client, {**compatibility, "source_commit": "c" * 40})
    assert len({first["revision"], other_tenant["revision"], other_host["revision"]}) == 3


def test_active_alias_resolves_current_tenant_for_configuration_and_assets(
    client: TestClient, compatibility: dict, published: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(AuthHandler, "_resolve_active_tenant", staticmethod(RESOLVE_ACTIVE_TENANT))
    active = AsyncMock(return_value="one")
    monkeypatch.setattr(KeycloakAdminService, "get_active_tenant_id", active)
    monkeypatch.setattr(KeycloakAdminService, "tenant_exists", AsyncMock(return_value=True))
    active_base = BASE.replace("/one/", "/active/")
    assert resolve_configuration(client, compatibility, base=active_base)["tenant_id"] == "one"
    route = f'{active_base}/publications/{published["revision"]}/source'
    assert client.get(route, headers=headers()).status_code == 200
    active.return_value = "two"
    assert client.get(route, headers=headers()).status_code == 403
    assert client.get(route.replace("/active/", "/one/"), headers=headers()).status_code == 200
    current = resolve_configuration(client, compatibility, base=active_base)
    assert current["tenant_id"] == "two"
    assert [mod["mod_id"] for mod in current["configuration"]["mods"]] == ["builtin-default"]


def test_initialized_defaults_need_no_admin_visit_or_runtime_publication(
    client: TestClient, compatibility: dict, storage: MagicMock,
) -> None:
    current = resolve_configuration(client, compatibility)
    mod = current["configuration"]["mods"][0]
    assert mod["mod_id"] == "builtin-default" and mod["enabled"]
    assert TenantMetadataEntity.objects.get(id="one").openwebui_mods_json is None
    assert resolve_configuration(client, compatibility) == current
    assert storage.put_object.call_count == 0
    route = f'{BASE}/publications/{mod["publication"]}'
    source = OpenWebuiModPackage.from_zip(client.get(route + "/source", headers=headers()).content)
    frontend = OpenWebuiModPublication.from_zip(client.get(route + "/frontend", headers=headers()).content)
    assert source.manifest.id == mod["mod_id"]
    assert frontend.files["frontend.js.mjs"] == source.files["frontend.js"]


def test_unverified_default_adapter_does_not_publish(
    client: TestClient, compatibility: dict, storage: MagicMock,
) -> None:
    response = client.post(BASE + "/configuration", headers=headers(), json={**compatibility, "openwebui": "0.12.5"})
    assert response.status_code == 409
    assert "not initialized" in response.json()["detail"]
    storage.put_object.assert_not_called()


def test_runtime_never_publishes_a_missing_builtin(
    client: TestClient, compatibility: dict, storage: MagicMock,
) -> None:
    OpenWebuiModPublicationEntity.drop_collection()
    response = client.post(BASE + "/configuration", headers=headers(), json=compatibility)
    assert response.status_code == 409
    assert "openwebui-mods-init" in response.json()["detail"]
    storage.put_object.assert_not_called()


def test_assets_are_shared_with_authorized_users_but_not_unselected_tenants(client: TestClient, published: dict) -> None:
    route = f'{BASE}/publications/{published["revision"]}/source'
    assert client.get(route, headers=headers("another")).content == published["source"]
    assert client.get(route.replace("/one/", "/two/"), headers=headers()).status_code == 403
    assert client.get(route.replace(published["revision"], "0" * 64), headers=headers()).status_code == 403


@pytest.mark.parametrize("method, suffix", [
    ("POST", "/configuration"), ("GET", "/publications/" + "b" * 64 + "/source"),
    ("GET", "/publications/" + "b" * 64 + "/frontend"), ("HEAD", "/publications/" + "b" * 64 + "/frontend"),
])
def test_runtime_requires_chat_access(client: TestClient, compatibility: dict, method: str, suffix: str) -> None:
    assert client.request(method, BASE + suffix, headers=headers("denied"), json=compatibility).status_code == 403


def test_tenant_membership_is_rechecked_for_configuration_and_assets(
    client: TestClient, compatibility: dict, published: dict, monkeypatch: pytest.MonkeyPatch,
) -> None:
    resolve_configuration(client, compatibility)
    monkeypatch.setattr(KeycloakAdminService, "is_user_member_of_tenant", AsyncMock(return_value=False))
    assert client.post(BASE + "/configuration", headers=headers(), json=compatibility).status_code == 403
    assert client.get(f'{BASE}/publications/{published["revision"]}/source', headers=headers()).status_code == 403


@pytest.mark.parametrize("method, suffix", [
    ("POST", "/configuration"), ("GET", "/publications/" + "b" * 64 + "/source"),
    ("GET", "/publications/" + "b" * 64 + "/frontend"), ("HEAD", "/publications/" + "b" * 64 + "/frontend"),
])
def test_runtime_requires_service_token_and_signed_identity(
    client: TestClient, compatibility: dict, method: str, suffix: str,
) -> None:
    for supplied in [{}, {"Authorization": "Bearer oauth-token"}, {**headers(), "X-OpenWebUI-Signature": "invalid"}]:
        assert client.request(method, BASE + suffix, headers=supplied, json=compatibility).status_code == 401
    assert client.request(method, BASE + suffix, headers={"Authorization": "Bearer service-token"}, json=compatibility).status_code == 400


def test_disabled_mod_is_not_exposed(client: TestClient, compatibility: dict, published: dict) -> None:
    tenant = TenantMetadataEntity.objects.get(id="one")
    configuration = json.loads(tenant.openwebui_mods_json)
    configuration["mods"][0]["enabled"] = False
    tenant.openwebui_mods_json = json.dumps(configuration)
    tenant.save()
    assert resolve_configuration(client, compatibility)["configuration"]["mods"] == []
    for kind in ["source", "frontend"]:
        assert client.get(f'{BASE}/publications/{published["revision"]}/{kind}', headers=headers()).status_code == 403
    assert client.head(f'{BASE}/publications/{published["revision"]}/frontend', headers=headers()).status_code == 403


def test_head_reauthorizes_without_reading_storage(
    client: TestClient, published: dict, storage: MagicMock, monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = f'{BASE}/publications/{published["revision"]}/frontend'
    response = client.head(path, headers=headers())
    assert response.status_code == 200
    assert response.content == b""
    assert response.headers["content-length"] == str(len(published["frontend"]))
    storage.get_object.assert_not_called()
    assert client.head(path, headers=headers("another")).status_code == 200
    assert client.head(path.replace(published["revision"], "0" * 64), headers=headers()).status_code == 403
    monkeypatch.setattr(KeycloakAdminService, "is_user_member_of_tenant", AsyncMock(return_value=False))
    assert client.head(path, headers=headers()).status_code == 403


def test_asset_authorization_reads_only_the_requested_custom_publication(
    client: TestClient, compatibility: dict, published: dict, storage: MagicMock, monkeypatch: pytest.MonkeyPatch,
) -> None:
    configuration = {"mods": [{"mod_id": "tools", "publication": published["revision"]}]}
    for mod_id in ["extra", "another"]:
        publication = publish_mod(compatibility, storage, mod_id=mod_id)
        configuration["mods"].append({"mod_id": mod_id, "publication": publication["revision"]})
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=json.dumps(configuration))
    find_publication = MagicMock(wraps=OpenWebuiModPublicationEntity.find_publication)
    monkeypatch.setattr(OpenWebuiModPublicationEntity, "find_publication", find_publication)
    response = client.head(f'{BASE}/publications/{published["revision"]}/frontend', headers=headers())
    assert response.status_code == 200
    find_publication.assert_called_once_with(published["revision"])


def test_current_configuration_requires_a_compatible_publication(client: TestClient, compatibility: dict, published: dict) -> None:
    response = client.post(BASE + "/configuration", headers=headers(), json={**compatibility, "source_commit": "c" * 40})
    assert response.status_code == 409


def test_only_the_current_selected_publication_is_readable(
    client: TestClient, compatibility: dict, published: dict, storage: MagicMock,
) -> None:
    current = resolve_configuration(client, compatibility)
    replacement = publish_mod(compatibility, storage, version="2")
    configuration = current["configuration"]
    configuration["version"] += 1
    configuration["mods"][0]["publication"] = replacement["revision"]
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=json.dumps(configuration))
    updated = resolve_configuration(client, compatibility)
    assert updated["revision"] != current["revision"]
    assert updated["configuration"]["mods"][0]["publication"] == replacement["revision"]
    for kind in ["source", "frontend"]:
        assert client.get(f'{BASE}/publications/{published["revision"]}/{kind}', headers=headers()).status_code == 403
        response = client.get(f'{BASE}/publications/{replacement["revision"]}/{kind}', headers=headers())
        assert response.status_code == 200, response.text
        assert response.content == replacement[kind]
    assert client.head(f'{BASE}/publications/{published["revision"]}/frontend', headers=headers()).status_code == 403
    assert client.head(f'{BASE}/publications/{replacement["revision"]}/frontend', headers=headers()).status_code == 200


def test_asset_authorization_requires_a_host_compatible_selection(
    client: TestClient, compatibility: dict, published: dict, storage: MagicMock,
) -> None:
    replacement = publish_mod({**compatibility, "source_commit": "c" * 40}, storage, version="2")
    configuration = {"mods": [{"mod_id": "tools", "publication": replacement["revision"]}]}
    TenantMetadataEntity.objects(id="one").update_one(set__openwebui_mods_json=json.dumps(configuration))
    assert client.post(BASE + "/configuration", headers=headers(), json=compatibility).status_code == 409
    for kind in ["source", "frontend"]:
        response = client.get(f'{BASE}/publications/{replacement["revision"]}/{kind}', headers=headers())
        assert response.status_code == 409


@pytest.mark.parametrize("method, kind", [("GET", "source"), ("GET", "frontend"), ("HEAD", "frontend")])
def test_asset_requests_require_a_valid_host_compatibility_header(
    client: TestClient, published: dict, method: str, kind: str,
) -> None:
    path = f'{BASE}/publications/{published["revision"]}/{kind}'
    for value in [None, "not-json", "{}"]:
        supplied = headers()
        if value is None:
            del supplied["X-AIHub-Mod-Compatibility"]
        else:
            supplied["X-AIHub-Mod-Compatibility"] = value
        assert client.request(method, path, headers=supplied).status_code == 422


@pytest.mark.parametrize("kind", ["source", "frontend"])
def test_archive_integrity_is_checked(client: TestClient, published: dict, storage: MagicMock, kind: str) -> None:
    storage.get_object.side_effect = lambda **kwargs: {"Body": BytesIO(b"corrupted archive")}
    with pytest.raises(RuntimeError, match="integrity check"):
        client.get(f'{BASE}/publications/{published["revision"]}/{kind}', headers=headers())
