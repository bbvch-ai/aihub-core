import hashlib
import json
import unittest
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

import httpx

from aihub_mods.initialize import ModInitializer


class ModInitializerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.compatibility = json.loads(Path("/app/backend/aihub_mods/compatibility.json").read_bytes())
        self.sources = []
        self.archives = {}
        self.publications = {}
        self.compiled = 0
        self.verified = 0
        self.reject_publication = False
        self.callables = {"open_webui.routers.fixture:run": {"source_sha256": "a" * 64}}
        for mod_id in ("first-mod", "second-mod"):
            manifest = {"format": 1, "id": mod_id, "name": mod_id, "version": "1",
                        "replacements": {"src/lib/Menu.svelte": "Menu.svelte"}, "backend": "private.py",
                        "backend_overrides": {"open_webui.routers.fixture:run": "override"}}
            buffer = BytesIO()
            with ZipFile(buffer, "w") as archive:
                archive.writestr("mod.json", json.dumps(manifest))
                archive.writestr("Menu.svelte", '<script lang="ts">enum Mode { Value = "Ready" }</script><span>{Mode.Value}</span>')
                archive.writestr("private.py", "raise RuntimeError('Compilation must not execute Python')")
            content = buffer.getvalue()
            revision = hashlib.sha256(content).hexdigest()
            self.sources.append({"revision": revision, "manifest": manifest})
            self.archives[revision] = content

    def respond(self, request: httpx.Request) -> httpx.Response:
        self.assertEqual(request.headers["authorization"], "Bearer test-initializer-token")
        path = request.url.path.split("/admin/openwebui-mods/")[1]
        if path == "host":
            return httpx.Response(200, json={"compatibility": self.compatibility, "components": ["src/lib/Menu.svelte"],
                                            "callables": self.callables})
        if path == "builtins":
            return httpx.Response(200, json=self.sources)
        if path == "global/reconcile":
            self.assertGreater(self.verified, 0)
            return httpx.Response(200, json={"restart_required": False})
        if path == "initialize":
            expected = {source["manifest"]["id"]: source["revision"] for source in self.sources}
            self.assertEqual(json.loads(request.content), expected)
            self.assertEqual(set(self.publications), set(expected.values()))
            self.verified += 1
            return httpx.Response(204)
        _, revision, action = path.split("/")
        if action == "source":
            return httpx.Response(200, content=self.archives[revision])
        if request.method == "GET":
            return httpx.Response(200, json=self.publications.get(revision, []))
        if self.reject_publication:
            return httpx.Response(409, text="Test host changed")
        self.assertEqual(request.content, b"")
        metadata = {"source_revision": revision, "compatibility": self.compatibility}
        self.compiled += 1
        self.publications[revision] = [{"manifest": metadata}]
        return httpx.Response(200, json={"revision": "a" * 64, "manifest": metadata})

    async def run_initializer(self) -> None:
        initializer = ModInitializer("http://sysadmin/api/v1", "test-initializer-token")
        await initializer.http.aclose()
        initializer.http = httpx.AsyncClient(base_url="http://sysadmin/api/v1/",
                                             headers={"Authorization": "Bearer test-initializer-token"},
                                             transport=httpx.MockTransport(self.respond))
        await initializer.run()

    async def test_publication_is_reused_and_verification_runs_only_after_publication(self) -> None:
        await self.run_initializer()
        self.assertEqual((self.compiled, self.verified), (2, 1))
        await self.run_initializer()
        self.assertEqual((self.compiled, self.verified), (2, 2))

    async def test_publication_failure_prevents_verification_and_retry_recovers(self) -> None:
        self.reject_publication = True
        with self.assertRaisesRegex(RuntimeError, "HTTP 409"):
            await self.run_initializer()
        self.assertEqual(self.verified, 0)
        self.reject_publication = False
        await self.run_initializer()
        self.assertEqual((self.compiled, self.verified), (2, 1))

    async def test_mismatched_host_never_compiles_or_verifies(self) -> None:
        self.compatibility["source_commit"] = "0" * 40
        with self.assertRaisesRegex(RuntimeError, "differs"):
            await self.run_initializer()
        self.assertEqual((self.compiled, self.verified), (0, 0))
