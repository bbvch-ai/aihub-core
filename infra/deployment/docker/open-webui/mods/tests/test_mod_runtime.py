import asyncio
import hashlib
import json
import sys
import unittest
from io import BytesIO
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile, ZipInfo

import httpx
from fastapi import FastAPI, HTTPException, Request

from aihub_mods.backend_package import BackendPackage
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.hub_client import HubClient
from aihub_mods.mod_host import ModHost
from aihub_mods.native_filter import NativeFilter


class ModRuntimeTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.compatibility = {"openwebui": "0.11.4", "python": "3.11"}
        self.calls: list[httpx.Request] = []
        self.events: list[dict] = []
        self.configurations: dict[str, dict] = {}
        self.objects: dict[str, bytes] = {}
        self.denied = False
        self.archive_status = 200
        self.source = """
from .helper import label

class Filter:
    def __init__(self):
        self.count = 0

    async def inlet(self, body, context):
        self.count += 1
        await context.emit('ready', {'label': context.settings['label']})
        return {**body, 'label': label(context.settings), 'count': self.count}

    async def request(self, body, context):
        return {**body, 'request_count': self.count}

    async def stream(self, event, context):
        return None if event.get('hide') else {**event, 'count': self.count}

    async def outlet(self, body, context):
        return {**body, 'outlet_count': self.count}
"""
        self.install("one", "First")
        self.install("two", "Second")
        self.client = HubClient("http://hub", "token", "secret", transport=httpx.MockTransport(self.respond))
        self.host = ModHost(self.client, json.dumps(self.compatibility).encode())
        self.app = FastAPI()
        self.app.state.aihub_mods = self.host
        self.users = {tenant: {"id": f"native-{tenant}", "name": "Reader", "email": f"{tenant}@example.test"}
                      for tenant in ("one", "two")}
        self.user = self.users["one"]

    async def asyncTearDown(self) -> None:
        await self.host.runtime.close()
        await self.client.http.aclose()

    @staticmethod
    def zip(files: dict[str, str]) -> bytes:
        output = BytesIO()
        with ZipFile(output, "w") as archive:
            for name, content in files.items():
                archive.writestr(ZipInfo(name), content)
        return output.getvalue()

    def install(self, tenant: str, label: str, source: str | None = None, *, restart: bool = False) -> str:
        content = self.zip({
            "mod.json": json.dumps({"format": 1, "id": "tools", "backend": "backend/main.py", "backend_restart_required": restart}),
            "backend/main.py": source or self.source,
            "backend/helper.py": "from pathlib import Path\ndef label(settings):\n return settings['label'] + Path(__file__).with_name('suffix.txt').read_text()",
            "backend/suffix.txt": " from asset",
        })
        revision = hashlib.sha256(content).hexdigest()
        publication = self.zip({"publication.json": json.dumps({
            "format": 1, "source_revision": revision, "compatibility": self.compatibility,
            "frontend": None, "replacements": {},
        })})
        published = hashlib.sha256(publication).hexdigest()
        self.objects[f"{published}/frontend"] = publication
        self.objects[f"{published}/source"] = content
        snapshot = {
            "tenant_id": tenant, "compatibility": self.compatibility,
            "configuration": {"mods": [{"mod_id": "tools", "publication": published, "has_backend": True, "enabled": True, "settings": {"label": label}}]},
        }
        snapshot["revision"] = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        self.configurations[tenant] = snapshot
        return published

    def respond(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        if self.denied:
            return httpx.Response(403)
        self.assertEqual(request.headers["authorization"], "Bearer token")
        tenant = next((tenant for tenant, user in self.users.items()
                       if user["email"] == request.headers["x-openwebui-user-email"]), None)
        if tenant is None:
            return httpx.Response(403)
        requested_tenant = request.url.path.split("/")[3]
        if requested_tenant not in {"active", tenant}:
            return httpx.Response(403)
        suffix = request.url.path.split("/mods/", 1)[1]
        if suffix == "configuration":
            self.assertEqual(request.method, "POST")
            self.assertEqual(json.loads(request.content), self.compatibility)
            return httpx.Response(200, json=self.configurations[tenant])
        self.assertEqual(json.loads(request.headers["x-aihub-mod-compatibility"]), self.compatibility)
        publication = suffix.split("/")[1]
        if not any(mod["enabled"] and mod["publication"] == publication
                   for mod in self.configurations[tenant]["configuration"]["mods"]):
            return httpx.Response(403)
        if self.archive_status != 200:
            return httpx.Response(self.archive_status)
        if request.method == "HEAD":
            return httpx.Response(200)
        if suffix.startswith("publications/"):
            content = self.objects["/".join(suffix.split("/")[-2:])]
            return httpx.Response(200, content=content, headers={"content-type": "application/zip"})
        return httpx.Response(404)

    def request(self, view: str | None = "a" * 32, execution: str | None = "e" * 32, tenant: str = "one") -> Request:
        headers = []
        if view is not None:
            headers.extend([(b"x-aihub-mod-view", view.encode()), (b"x-aihub-mod-tenant", tenant.encode())])
        if execution is not None:
            headers.append((b"x-aihub-mod-execution", execution.encode()))
        return Request({"type": "http", "method": "POST", "path": "/api/chat/completions", "headers": headers, "app": self.app})

    async def apply(
        self, request: Request, hook: str = "inlet", message: str = "message", body: dict | None = None,
        user: dict | None = None,
    ) -> dict | None:
        async def emit(event: dict) -> None:
            self.events.append(event)

        handler = getattr(NativeFilter(), hook)
        return await handler(body or {}, request, user or self.user, {"chat_id": "chat", "message_id": message, "task_id": message + "-task"}, {"id": "model"}, emit)

    async def test_tenant_rejects_startup_mod_before_python_import(self) -> None:
        self.install("one", "Startup", source="raise RuntimeError('Tenant activation must not import this')", restart=True)
        with self.assertRaises(HTTPException) as rejected:
            await self.apply(self.request())
        self.assertEqual(rejected.exception.status_code, 409)
        self.assertEqual(self.host.runtime.packages, {})

    async def test_relative_imports_assets_and_all_native_hooks_share_one_run(self) -> None:
        request = self.request()
        self.assertEqual(await self.apply(request), {"label": "First from asset", "count": 1})
        self.assertEqual(await self.apply(request, "request"), {"request_count": 1})
        self.assertEqual(await self.apply(request, "stream"), {"count": 1})
        self.assertIsNone(await self.apply(request, "stream", body={"hide": True}))
        self.assertEqual(await self.apply(request, "outlet"), {"outlet_count": 1})
        self.assertEqual(len([call for call in self.calls if "/active/" in call.url.path]), 1)

    async def test_concurrent_tenants_and_fanout_get_distinct_instances_and_settings(self) -> None:
        first, second = self.request(), self.request("b" * 32, tenant="two")
        results = await asyncio.gather(self.apply(first), self.apply(second, user=self.users["two"]), self.apply(first, message="other"))
        self.assertEqual([result["count"] for result in results], [1, 1, 1])
        self.assertEqual([result["label"] for result in results], ["First from asset", "Second from asset", "First from asset"])
        self.assertEqual((await self.apply(first))["count"], 2)
        self.assertEqual(len(self.host.runtime.packages), 1)

    async def test_event_envelope_carries_view_tenant_revision_and_native_execution(self) -> None:
        await self.apply(self.request())
        self.assertEqual(self.events, [{"type": "aihub:mod", "data": {
            "version": 1, "contextId": "a" * 32, "tenantId": "one", "modId": "tools",
            "publication": self.configurations["one"]["configuration"]["mods"][0]["publication"], "executionId": "e" * 32,
            "chatId": "chat", "messageId": "message", "taskId": "message-task", "type": "ready", "data": {"label": "First"},
        }}])

    async def test_browserless_requests_resolve_current_configuration_without_view_records(self) -> None:
        request = self.request(None, None)
        result = await self.apply(request)
        self.assertEqual(result["label"], "First from asset")
        self.assertEqual(self.calls[0].method, "POST")
        self.assertTrue(self.calls[0].url.path.endswith("/mods/configuration"))
        snapshot = await request.state.aihub_mod_snapshot
        self.assertTrue({"id", "user_id", "expires_at"}.isdisjoint(snapshot.model_dump()))
        self.install("one", "Current")
        self.assertEqual((await self.apply(self.request(None, None)))["label"], "Current from asset")
        self.assertEqual(self.events, [])

    async def test_prepared_bindings_survive_changes_and_old_view_uses_current_selection_on_new_requests(self) -> None:
        old_request = self.request()
        await self.host.runtime.request_overrides(old_request, self.user)
        prepared_calls = len(self.calls)
        source = self.source.replace("self.count = 0", "self.count = 40")
        self.install("one", "Updated", source)
        self.assertEqual((await self.apply(old_request))["label"], "First from asset")
        self.assertEqual((await self.apply(old_request, "request"))["request_count"], 1)
        self.assertEqual((await self.apply(old_request, message="other"))["label"], "First from asset")
        self.assertEqual(len(self.calls), prepared_calls)
        current = await self.apply(self.request())
        self.assertEqual(current["count"], 41)
        self.assertEqual(current["label"], "Updated from asset")
        self.assertEqual(len(self.host.runtime.packages), 2)

    async def test_view_nonce_does_not_choose_a_tenant_and_wrong_tenant_is_rejected(self) -> None:
        self.assertEqual((await self.apply(self.request("b" * 32)))["label"], "First from asset")
        with self.assertRaises(HTTPException) as rejected:
            await self.apply(self.request("b" * 32, tenant="two"))
        self.assertEqual(rejected.exception.status_code, 403)

    async def test_stable_private_api_uses_the_current_publication_with_the_same_view(self) -> None:
        async def call() -> dict:
            token = CallableRegistry.active.set({})
            try:
                return await self.host.runtime.handle("one", "tools", "status", self.request(execution=None), self.user)
            finally:
                CallableRegistry.active.reset(token)

        code = self.source + "\nasync def handle(request, context):\n return {'version': 1, 'label': context.settings['label'], 'view': context.id}\n"
        self.install("one", "First", code)
        self.assertEqual(await call(), {"version": 1, "label": "First", "view": "a" * 32})
        self.install("one", "Updated", code.replace("'version': 1", "'version': 2"))
        self.assertEqual(await call(), {"version": 2, "label": "Updated", "view": "a" * 32})

    async def test_empty_configuration_does_not_load_or_authorize_archives(self) -> None:
        self.configurations["one"]["configuration"]["mods"] = []
        self.assertEqual(await self.apply(self.request(None, None)), {})
        self.assertEqual(len(self.calls), 1)
        self.assertTrue(self.calls[0].url.path.endswith("/configuration"))
        self.assertEqual(self.host.runtime.packages, {})

    async def test_cached_packages_do_not_bypass_current_authorization(self) -> None:
        await self.apply(self.request())
        self.denied = True
        with self.assertRaises(HTTPException) as raised:
            await self.apply(self.request())
        self.assertEqual(raised.exception.status_code, 403)

    async def test_frontend_only_mods_do_not_load_archives_when_delivery_is_unavailable(self) -> None:
        self.configurations["one"]["configuration"]["mods"] = [
            {"mod_id": f"frontend-{index}", "publication": "f" * 64, "has_backend": False, "enabled": True, "settings": {}}
            for index in range(5)
        ]

        self.archive_status = 503
        for view, execution in [("a" * 32, "e" * 32), (None, None)]:
            for _ in range(2):
                self.calls.clear()
                request = self.request(view, execution)
                self.assertEqual(await self.apply(request), {})
                self.assertEqual(len(self.calls), 1)
                self.assertTrue(self.calls[0].url.path.endswith("/configuration"))
                self.assertEqual(request.state.aihub_mod_bindings, {})
        self.assertEqual(self.host.runtime.packages, {})
        self.calls.clear()
        with self.assertRaises(HTTPException) as missing:
            await self.host.runtime.handle("one", "frontend-0", "status", self.request(), self.user)
        self.assertEqual(missing.exception.status_code, 404)
        self.assertEqual(len(self.calls), 1)
        self.denied = True
        with self.assertRaises(HTTPException) as raised:
            await self.apply(self.request())
        self.assertEqual(raised.exception.status_code, 403)

    async def test_mixed_configuration_loads_only_backend_packages(self) -> None:
        self.configurations["one"]["configuration"]["mods"].insert(0, {
            "mod_id": "frontend", "publication": "f" * 64, "has_backend": False, "enabled": True, "settings": {},
        })
        for _ in range(2):
            self.assertEqual((await self.apply(self.request()))["label"], "First from asset")
        self.assertEqual(len(self.host.runtime.packages), 1)
        self.assertFalse(any("f" * 64 in call.url.path for call in self.calls))

    async def test_cached_backend_packages_still_require_archive_authorization_and_delivery(self) -> None:
        await self.apply(self.request())
        for status in (403, 503):
            self.archive_status = status
            self.calls.clear()
            with self.assertRaises(HTTPException) as raised:
                await self.apply(self.request())
            self.assertEqual(raised.exception.status_code, status)
            self.assertEqual([call.method for call in self.calls], ["POST", "HEAD"])

    async def test_invalid_execution_header_fails_before_source_or_identity_access(self) -> None:
        for request in [self.request(execution="bad"), self.request(None)]:
            with self.assertRaises(HTTPException) as raised:
                await self.apply(request)
            self.assertEqual(raised.exception.status_code, 400)
        self.assertEqual(self.calls, [])

    async def test_invalid_or_unpaired_view_headers_fail_before_hub_access(self) -> None:
        requests = [self.request("invalid"), self.request(tenant="")]
        for missing in (b"x-aihub-mod-view", b"x-aihub-mod-tenant"):
            request = self.request(execution=None)
            request.scope["headers"] = [item for item in request.scope["headers"] if item[0] != missing]
            requests.append(request)
        for request in requests:
            with self.assertRaises(HTTPException) as rejected:
                await self.apply(request)
            self.assertEqual(rejected.exception.status_code, 400)
        self.assertEqual(self.calls, [])

    async def test_failed_import_does_not_block_chat_or_change_enablement(self) -> None:
        self.install("one", "Broken", "raise RuntimeError('Import failed')")
        with self.assertLogs("aihub_mods.mod_runtime", level="ERROR"):
            result = await self.apply(self.request())
        self.assertEqual(result, {})
        self.assertTrue(self.configurations["one"]["configuration"]["mods"][0]["enabled"])
        self.install("one", "Fixed")
        self.assertEqual((await self.apply(self.request()))["label"], "Fixed from asset")

    async def test_failed_filter_constructor_does_not_block_chat(self) -> None:
        self.install("one", "Broken", "class Filter:\n def __init__(self): raise ValueError('Invalid settings')")
        with self.assertLogs("aihub_mods.mod_runtime", level="ERROR"):
            self.assertEqual(await self.apply(self.request()), {})

    async def test_backend_hook_errors_are_not_silently_skipped(self) -> None:
        self.install("one", "Broken", "class Filter:\n async def inlet(self, body, context):\n  raise ValueError('fixture failure')")
        with self.assertRaisesRegex(ValueError, "fixture failure"):
            await self.apply(self.request())

    async def test_native_filter_parameter_injection_matches_the_pinned_upstream(self) -> None:
        from open_webui.utils.filter import process_filter_functions

        request = self.request()
        params = {"__request__": request, "__user__": self.user, "__metadata__": {"task_id": "native-task"}, "__model__": {"id": "model"}}
        with patch("open_webui.utils.filter.get_function_module", AsyncMock(return_value=NativeFilter())):
            result, _ = await process_filter_functions(request, None, [SimpleNamespace(id="aihub_mods")], "inlet", {}, params)
        self.assertEqual(result["label"], "First from asset")

    async def test_private_package_files_and_imports_are_removed_on_host_shutdown(self) -> None:
        await self.apply(self.request())
        package = next(iter(self.host.runtime.packages.values()))
        self.assertIn(package.namespace + ".backend.main", sys.modules)
        await self.host.runtime.close()
        self.assertFalse(any(name.startswith(package.namespace) for name in sys.modules))

    async def test_native_task_completion_closes_events_and_emits_a_scoped_end(self) -> None:
        request = self.request()
        await asyncio.create_task(self.apply(request))
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        run = await next(iter(request.state.aihub_mod_runs.values()))
        context = run.filters[0][1]
        self.assertEqual(self.events[-1], {"type": "aihub:mods:end", "data": context.scope()})
        before = len(self.events)
        await context.emit("late", {"ignored": True})
        self.assertEqual(len(self.events), before)

    async def test_native_task_cancellation_also_closes_the_execution(self) -> None:
        request = self.request()
        started = asyncio.Event()

        async def execute() -> None:
            await self.apply(request)
            started.set()
            await asyncio.Future()

        task = asyncio.create_task(execute())
        await started.wait()
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        self.assertEqual(self.events[-1]["type"], "aihub:mods:end")

    def test_source_integrity_and_unsafe_zip_paths_are_checked_before_import(self) -> None:
        for path in ["../outside.py", "/outside.py", "backend/../outside.py", "backend\\outside.py"]:
            content = self.zip({"mod.json": '{"id":"tools","backend":"main.py"}', path: "raise RuntimeError('must not import')"})
            with self.assertRaisesRegex(ValueError, "path"):
                BackendPackage(hashlib.sha256(content).hexdigest(), content, "tools")
        with self.assertRaisesRegex(ValueError, "integrity"):
            BackendPackage("f" * 64, b"wrong bytes", "tools")


if __name__ == "__main__":
    unittest.main()
