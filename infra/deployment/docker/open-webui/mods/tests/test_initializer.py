import json
import unittest
from pathlib import Path

import httpx

from aihub_mods.initialize import ModInitializer


class ModInitializerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.compatibility = json.loads(Path("/app/backend/aihub_mods/compatibility.json").read_bytes())
        self.installed = []
        self.reconciled = 0
        self.fail_install = False

    def respond(self, request: httpx.Request) -> httpx.Response:
        self.assertEqual(request.headers["authorization"], "Bearer test-initializer-token")
        path = request.url.path.split("/admin/openwebui-mods/")[1]
        if path == "host":
            return httpx.Response(200, json={"compatibility": self.compatibility})
        if path == "builtins":
            return httpx.Response(200, json=["first-mod", "second-mod"])
        if path == "global/reconcile":
            self.assertEqual(self.installed[-2:], ["first-mod", "second-mod"])
            self.reconciled += 1
            return httpx.Response(200, json={"restart_required": False})
        self.assertEqual(request.method, "POST")
        self.assertEqual(request.content, b"")
        if self.fail_install:
            return httpx.Response(422, json={"detail": "Compilation failed"})
        self.installed.append(path.split("/")[1])
        return httpx.Response(200, json={})

    async def run_initializer(self) -> None:
        initializer = ModInitializer("http://sysadmin/api/v1", "test-initializer-token")
        await initializer.http.aclose()
        initializer.http = httpx.AsyncClient(base_url="http://sysadmin/api/v1/",
                                             headers={"Authorization": "Bearer test-initializer-token"},
                                             transport=httpx.MockTransport(self.respond))
        await initializer.run()

    async def test_initialization_installs_all_builtins_before_reconciling(self) -> None:
        await self.run_initializer()
        self.assertEqual(self.installed, ["first-mod", "second-mod"])
        self.assertEqual(self.reconciled, 1)

    async def test_failed_install_stops_initialization_and_retry_recovers(self) -> None:
        self.fail_install = True
        with self.assertRaisesRegex(RuntimeError, "HTTP 422"):
            await self.run_initializer()
        self.assertEqual(self.reconciled, 0)
        self.fail_install = False
        await self.run_initializer()
        self.assertEqual(self.reconciled, 1)

    async def test_mismatched_host_never_installs_or_reconciles(self) -> None:
        self.compatibility["source_commit"] = "0" * 40
        with self.assertRaisesRegex(RuntimeError, "differs"):
            await self.run_initializer()
        self.assertEqual(self.installed, [])
        self.assertEqual(self.reconciled, 0)
