"""Run in a fresh interpreter: native imports must pass through the real host entrypoint."""

import asyncio
import hashlib
import hmac
import inspect
import json
import os
import sys
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch
from uuid import uuid4
from zipfile import ZipFile

import httpx
from fastapi import HTTPException

Path(os.environ["DATA_DIR"]).mkdir(parents=True, exist_ok=True)

from aihub_mods.main import app, host
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.global_mod_configuration import GlobalModConfiguration
from aihub_mods.global_mod_runtime import GlobalModRuntime
from aihub_mods.global_mod_store import GlobalModStore
from aihub_mods.mod_compiler import ModCompiler
from aihub_mods.mod_selection import ModSelection
from open_webui.models.users import Users
from open_webui.tasks import item_tasks, tasks
from open_webui.utils.auth import create_token


class NativeBackendAcceptance(unittest.IsolatedAsyncioTestCase):
    TARGET = "open_webui.routers.users:get_user_info_by_session_user"
    NATIVE_URL = "/api/v1/users/user/info"

    async def asyncSetUp(self) -> None:
        self.compatibility = json.loads(host.compatibility)
        self.requests: list[httpx.Request] = []
        self.hub_available = True
        self.users = {tenant: f"{tenant}-{uuid4().hex}" for tenant in ("one", "two")}
        self.tokens: dict[str, str] = {}
        self.source = self._archive({
            "mod.json": json.dumps({"format": 1, "id": "native-info", "name": "Native information", "version": "1",
                                    "backend": "backend.py", "backend_overrides": {self.TARGET: "info"}}),
            "backend.py": Path(__file__).with_name("fixtures").joinpath("native_override.py").read_text(),
        })
        self.source_revision = hashlib.sha256(self.source).hexdigest()
        self.publication = self._archive({"publication.json": json.dumps({
            "format": 1, "source_revision": self.source_revision, "compatibility": self.compatibility,
            "frontend": None, "replacements": {}, "backend_targets": {self.TARGET: CallableRegistry.catalog[self.TARGET]},
        })})
        self.revision = hashlib.sha256(self.publication).hexdigest()
        self.snapshots = {
            "one": self._snapshot("one", {"label": "First"}),
            "two": self._snapshot("two", {"label": "Second"}),
        }
        await host.client.http.aclose()
        host.client.http = httpx.AsyncClient(base_url="http://hub", transport=httpx.MockTransport(self._respond))
        for tenant, user_id in self.users.items():
            self.assertIsNotNone(await Users.insert_new_user(id=user_id, name=tenant, email=user_id + "@example.test", role="user"))
            self.tokens[tenant] = create_token({"id": user_id})
        self.client = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://native")

    async def asyncTearDown(self) -> None:
        await self.client.aclose()
        await host.runtime.close()
        host.archives.clear()
        await host.client.http.aclose()

    @staticmethod
    def _archive(files: dict[str, str]) -> bytes:
        output = BytesIO()
        with ZipFile(output, "w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        return output.getvalue()

    def _snapshot(self, tenant: str, settings: dict[str, Any]) -> dict[str, Any]:
        snapshot = {"tenant_id": tenant, "compatibility": self.compatibility,
                    "configuration": {"mods": [{"mod_id": "native-info", "publication": self.revision,
                                                "has_backend": True, "enabled": True, "settings": settings}]}}
        snapshot["revision"] = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        return snapshot

    def _respond(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if not self.hub_available:
            return httpx.Response(503)
        self.assertEqual(request.headers["authorization"], "Bearer " + host.client.api_key)
        email = request.headers["x-openwebui-user-email"]
        name = request.headers["x-openwebui-user-name"]
        self.assertEqual(request.headers["x-openwebui-signature"], hmac.new(
            host.client.signing_secret, f"name:{name},email:{email}".encode(), hashlib.sha256,
        ).hexdigest())
        tenant = next((tenant for tenant, user_id in self.users.items() if email == user_id + "@example.test"), None)
        if tenant is None or request.url.path.split("/")[3] not in {"active", tenant}:
            return httpx.Response(403)
        selected = self.snapshots[tenant]
        suffix = request.url.path.split("/mods/", 1)[1]
        if suffix == "configuration":
            self.assertEqual(request.method, "POST")
            self.assertEqual(json.loads(request.content), self.compatibility)
            return httpx.Response(200, json=selected)
        self.assertEqual(json.loads(request.headers["x-aihub-mod-compatibility"]), self.compatibility)
        publication = suffix.split("/")[1]
        if not any(mod["enabled"] and mod["publication"] == publication for mod in selected["configuration"]["mods"]):
            return httpx.Response(403)
        if request.method == "HEAD":
            return httpx.Response(200)
        for ending, content in (("/source", self.source), ("/frontend", self.publication)):
            if suffix.endswith(ending):
                return httpx.Response(200, content=content, headers={"content-type": "application/zip"})
        return httpx.Response(404)

    def _headers(self, tenant: str, view: str | None = None, *, view_tenant: str | None = None) -> dict[str, str]:
        headers = {"Authorization": "Bearer " + self.tokens[tenant]}
        if view:
            headers["X-AIHub-Mod-View"] = view
            headers["X-AIHub-Mod-Tenant"] = view_tenant or tenant
        return headers

    def _api(self, path: str) -> str:
        return f"/_aihub/mods/tenants/one/mods/native-info/api/{path}"

    async def test_native_authentication_precedes_hub_and_unscoped_requests_remain_native(self) -> None:
        denied = await self.client.get(self.NATIVE_URL, headers={"X-AIHub-Mod-View": "a" * 32, "X-AIHub-Mod-Tenant": "one"})
        self.assertEqual(denied.status_code, 401)
        ordinary = await self.client.get(self.NATIVE_URL, headers=self._headers("one"))
        self.assertEqual(ordinary.status_code, 200, ordinary.text)
        self.assertIsNone(ordinary.json())
        self.assertEqual(self.requests, [])

    async def test_concurrent_tenants_share_code_but_not_settings_or_state(self) -> None:
        async def selected(tenant: str, view: str, label: str) -> None:
            headers = {**self._headers(tenant, view), "X-OpenWebUI-User-Email": "forged@example.test"}
            response = await self.client.get(self.NATIVE_URL, headers=headers)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json(), {"tenant": tenant, "label": label, "calls": 1})

        await asyncio.gather(*[selected("one", "a" * 32, "First") if index % 2
                               else selected("two", "b" * 32, "Second") for index in range(12)])
        self.assertEqual(len(host.runtime.packages), 1)
        restored = await self.client.get(self.NATIVE_URL, headers=self._headers("one"))
        self.assertIsNone(restored.json())

    async def test_cross_tenant_view_and_mod_rejections_keep_their_status(self) -> None:
        forbidden = await self.client.get(self.NATIVE_URL, headers=self._headers("one", "b" * 32, view_tenant="two"))
        self.assertEqual(forbidden.status_code, 403)
        self.snapshots["one"] = self._snapshot("one", {"label": "Reject", "reject": True})
        rejection = await self.client.get(self.NATIVE_URL, headers=self._headers("one", "a" * 32))
        self.assertEqual(rejection.status_code, 418)
        self.assertEqual(rejection.json()["detail"], "Deliberate mod rejection")

    async def test_same_view_uses_updated_tenant_settings_and_another_nonce_cannot_choose_settings(self) -> None:
        headers = self._headers("one", "a" * 32)
        first = await self.client.get(self.NATIVE_URL, headers=headers)
        self.assertEqual(first.json()["label"], "First")
        self.snapshots["one"] = self._snapshot("one", {"label": "Current"})
        current = await self.client.get(self.NATIVE_URL, headers=headers)
        self.assertEqual(current.json(), {"tenant": "one", "label": "Current", "calls": 1})
        another = await self.client.get(self.NATIVE_URL, headers=self._headers("one", "b" * 32))
        self.assertEqual(another.json()["label"], "Current")

    async def test_native_cancellation_keeps_owner_and_admin_checks_when_mod_delivery_fails(self) -> None:
        self.hub_available = False
        chat_id = "owned-chat"
        url = f"/api/tasks/chat/{chat_id}/stop"
        result = {"status": True, "message": "Stopped tasks."}
        with patch("open_webui.main.Chats.get_chat_by_id", AsyncMock(return_value=SimpleNamespace(user_id=self.users["one"]))), \
             patch("open_webui.main.stop_item_tasks", AsyncMock(return_value=result)) as stop_chat, \
             patch("open_webui.main.stop_task", AsyncMock()) as stop_task, \
             patch.object(app.state, "redis", None, create=True):
            unauthenticated = await self.client.post(url, headers={
                "X-AIHub-Mod-View": "a" * 32, "X-AIHub-Mod-Tenant": "one",
            })
            self.assertEqual(unauthenticated.status_code, 401)
            other_user = await self.client.post(url, headers=self._headers("two", "b" * 32))
            self.assertEqual(other_user.status_code, 404)
            stop_chat.assert_not_awaited()
            stopped = await self.client.post(url, headers=self._headers("one", "a" * 32))
            self.assertEqual(stopped.status_code, 200, stopped.text)
            self.assertEqual(stopped.json(), result)
            stop_chat.assert_awaited_once_with(None, chat_id)
            admin_only = await self.client.post("/api/tasks/stop/owned-task", headers=self._headers("one", "a" * 32))
            self.assertEqual(admin_only.status_code, 401, admin_only.text)
            stop_task.assert_not_awaited()
        self.assertEqual(self.requests, [])

    async def test_lazy_native_target_publishes_and_activates_before_import(self) -> None:
        target = "open_webui.utils.subagents:process_pending_internal_messages"
        self.assertNotIn("open_webui.utils.subagents", sys.modules)
        catalog = json.dumps(CallableRegistry.catalog, sort_keys=True)
        self.assertIn(target, CallableRegistry.catalog)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            marker = root / "mod-imported"
            code = f"from pathlib import Path\nPath({str(marker)!r}).touch()\n" + '''
async def intercept(next, context, /, *args, **kwargs):
    if getattr(context, 'scope', None) == 'global':
        return [context.settings['label']]
    return [context.settings['label'], *await next(*args, **kwargs)]
async def handle(request, context):
    from open_webui.utils.subagents import process_pending_internal_messages
    return await process_pending_internal_messages(request, 'unused-chat', context.user['id'], {})
'''
            manifest = {"format": 1, "id": "native-info", "name": "Lazy native target", "version": "1",
                        "backend": "backend.py", "backend_overrides": {target: "intercept"}}
            self.source = self._archive({"mod.json": json.dumps(manifest), "backend.py": code})
            compiler = ModCompiler(root)
            missing = {**manifest, "backend_overrides": {target + "_absent": "intercept"}}
            with self.assertRaises(HTTPException) as rejected:
                await compiler.compile(self._archive({"mod.json": json.dumps(missing), "backend.py": code}))
            self.assertEqual(rejected.exception.status_code, 422)
            self.assertIn("absent", rejected.exception.detail)
            self.publication = await compiler.compile(self.source)
            self.assertFalse(marker.exists())
            self.assertNotIn("open_webui.utils.subagents", sys.modules)
            self.source_revision = hashlib.sha256(self.source).hexdigest()
            self.revision = hashlib.sha256(self.publication).hexdigest()
            self.snapshots = {tenant: self._snapshot(tenant, snapshot["configuration"]["mods"][0]["settings"])
                              for tenant, snapshot in self.snapshots.items()}
            store = GlobalModStore(root, host.compatibility, "lazy-native-test")
            store.initialize()
            store.stage("sources", self.source_revision, self.source)
            store.stage("publications", self.revision, self.publication)
            selected = ModSelection(mod_id="native-info", publication=self.revision, has_backend=True, enabled=True, settings={"label": "Global"})
            self.assertFalse(store.replace(GlobalModConfiguration(mods=[selected]))["restart_required"])
            runtime = GlobalModRuntime(store, host.runtime)
            await runtime.start(app)
            try:
                self.assertIsNone(runtime.error)
                self.assertTrue(marker.exists())
                self.assertIn(target, runtime.handlers())
                self.assertNotIn("open_webui.utils.subagents", sys.modules)
                with patch.object(host, "global_runtime", runtime):
                    response = await self.client.get(self._api("lazy"), headers=self._headers("one"))
                self.assertEqual(response.status_code, 200, response.text)
                self.assertEqual(response.json(), ["First", "Global"])
                from open_webui.utils.subagents import process_pending_internal_messages

                token = CallableRegistry.active.set(None)
                try:
                    self.assertEqual(await process_pending_internal_messages(None, "unused-chat", "unused-user", {}), ["Global"])
                finally:
                    CallableRegistry.active.reset(token)
                self.assertEqual(json.dumps(CallableRegistry.catalog, sort_keys=True), catalog)
            finally:
                await runtime.close()

    async def test_loaded_native_catalog_targets_have_dispatchers(self) -> None:
        conditional = {
            "open_webui.internal.db:create_sqlcipher_connection",
            "open_webui.routers.retrieval:get_embeddings",
            "open_webui.utils.json_codec:ORJSONCodec.dumps",
            "open_webui.utils.json_codec:ORJSONCodec.loads",
        }
        verified = 0
        for target in CallableRegistry.catalog:
            module, qualified_name = target.split(":", 1)
            if module not in sys.modules:
                continue
            value = sys.modules[module]
            try:
                for part in qualified_name.split("."):
                    value = inspect.getattr_static(value, part)
            except AttributeError:
                self.assertIn(target, conditional)
                continue
            if isinstance(value, (staticmethod, classmethod)):
                value = value.__func__
            self.assertEqual(inspect.getattr_static(value, "__aihub_target__", None), target)
            verified += 1
        self.assertGreater(verified, 0)

    async def test_private_api_and_native_override_share_request_state(self) -> None:
        response = await self.client.post(self._api("status"), headers=self._headers("one"), json={"value": 1})
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"path": "status", "method": "POST", "calls": 1,
                                          "native": {"tenant": "one", "label": "First", "calls": 1}})
        catalog = await self.client.get("/_aihub/mods/callables.json")
        self.assertEqual(catalog.status_code, 200)
        self.assertEqual(catalog.json()[self.TARGET], CallableRegistry.catalog[self.TARGET])

    async def test_private_api_checks_identity_origin_tenant_enabled_mod_and_view(self) -> None:
        url = self._api("status")
        for candidate, headers, expected in [
            (url, self._headers("two"), 403),
            (url, {**self._headers("one"), "Origin": "http://elsewhere.test"}, 403),
            (url.replace("/tenants/one/", "/tenants/two/"), self._headers("one"), 403),
            (url.replace("/mods/native-info/", "/mods/not-enabled/"), self._headers("one"), 403),
            (url, self._headers("one", "b" * 32, view_tenant="two"), 403),
            (url, self._headers("one", "invalid"), 400),
        ]:
            response = await self.client.post(candidate, headers=headers)
            self.assertEqual(response.status_code, expected, response.text)

    async def test_stable_private_api_selects_changed_publication_without_replacing_the_view(self) -> None:
        headers = self._headers("one", "a" * 32)
        first = await self.client.get(self._api("status"), headers=headers)
        self.assertEqual(first.json()["native"]["label"], "First")
        code = Path(__file__).with_name("fixtures").joinpath("native_override.py").read_text()
        self.source = self._archive({
            "mod.json": json.dumps({"format": 1, "id": "native-info", "backend": "backend.py",
                                    "backend_overrides": {self.TARGET: "info"}}),
            "backend.py": code.replace('label = context.settings["label"]', 'label = "Current code: " + context.settings["label"]'),
        })
        self.source_revision = hashlib.sha256(self.source).hexdigest()
        self.publication = self._archive({"publication.json": json.dumps({
            "format": 1, "source_revision": self.source_revision, "compatibility": self.compatibility,
            "frontend": None, "replacements": {}, "backend_targets": {self.TARGET: CallableRegistry.catalog[self.TARGET]},
        })})
        self.revision = hashlib.sha256(self.publication).hexdigest()
        self.snapshots["one"] = self._snapshot("one", {"label": "Updated"})
        current = await self.client.get(self._api("status"), headers=headers)
        self.assertEqual(current.status_code, 200, current.text)
        self.assertEqual(current.json()["native"]["label"], "Current code: Updated")
        self.assertEqual(len(host.runtime.packages), 2)

    async def test_streamed_response_keeps_overrides_after_handler_returns(self) -> None:
        response = await self.client.get(self._api("stream"), headers=self._headers("one"))
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json(), {"tenant": "one", "label": "First", "calls": 1})
        restored = await self.client.get(self.NATIVE_URL, headers=self._headers("one"))
        self.assertIsNone(restored.json())

    async def test_native_background_task_keeps_scope_after_http_request_finishes(self) -> None:
        response = await self.client.post(self._api("background"), headers=self._headers("one"))
        self.assertEqual(response.status_code, 200, response.text)
        entry = host.runtime.packages[self.source_revision].entry
        task_id, task = entry.pending
        self.assertFalse(task.done())
        self.snapshots["one"] = self._snapshot("one", {"label": "Changed after admission"})
        request_count = len(self.requests)
        self.hub_available = False
        entry.gate.set()
        self.assertEqual(await asyncio.wait_for(task, 5), {"tenant": "one", "label": "First", "calls": 1})
        self.assertEqual(len(self.requests), request_count)
        for _ in range(10):
            if task_id not in tasks:
                break
            await asyncio.sleep(0)
        self.assertNotIn(task_id, tasks)
        self.assertNotIn("one", item_tasks)
        restored = await self.client.get(self.NATIVE_URL, headers=self._headers("one"))
        self.assertIsNone(restored.json())


if __name__ == "__main__":
    unittest.main()
