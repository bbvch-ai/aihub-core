import asyncio
import hashlib
import json
import signal
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.testclient import TestClient

from aihub_mods.global_mod_control import GlobalModControl
from aihub_mods.global_mod_store import GlobalModStore
from aihub_mods.mod_compiler import ModCompiler


class ModCompilerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.compiler = ModCompiler(self.root)
        self.target = "src/lib/Menu.svelte"
        catalog = self.root / "components.json"
        catalog.write_text(json.dumps([self.target]))
        self.enterContext(patch.object(ModCompiler, "COMPONENTS", catalog))

    def source(self, component: str | None = None) -> bytes:
        content = BytesIO()
        with ZipFile(content, "w") as archive:
            archive.writestr("mod.json", json.dumps({
                "format": 1, "id": "compiler-test", "name": "Compiler test", "version": "1",
                "frontend": "main.ts", "backend": "private.py", "replacements": {self.target: "Menu.svelte"},
            }))
            archive.writestr("main.ts", "throw new Error('Compilation must not execute frontend code'); export function activate() {}")
            archive.writestr("private.py", "raise RuntimeError('Compilation must not execute backend code')")
            archive.writestr("Menu.svelte", component or '<script lang="ts">import { user } from "@openwebui/stores"; enum Label { Text = "Hello" }</script><img src="x"><span>{Label.Text} {$user?.name}</span>')
        return content.getvalue()

    async def test_real_compiler_preserves_shared_runtime_warnings_and_source_hash(self) -> None:
        source = self.source()
        result = await self.compiler.compile(source)
        with ZipFile(BytesIO(result)) as archive:
            manifest = json.loads(archive.read("publication.json"))
            self.assertEqual(manifest["source_revision"], hashlib.sha256(source).hexdigest())
            self.assertTrue(any("alt" in warning for warning in manifest["warnings"]))
            compiled = archive.read("files/Menu.svelte.mjs").decode()
            self.assertIn('getModule("svelte/internal/client")', compiled)
            self.assertIn("@openwebui/stores", compiled)
            self.assertNotIn("files/private.py", archive.namelist())

    def test_control_requires_service_authentication(self) -> None:
        app = FastAPI()
        router = APIRouter()
        GlobalModControl(GlobalModStore(self.root, b"{}", "test-boot"), "test-credential").install(router)
        app.include_router(router)
        with TestClient(app) as client:
            self.assertEqual(client.post("/control/compile", content=self.source()).status_code, 403)
            result = client.post("/control/compile", content=self.source(), headers={"Authorization": "Bearer test-credential"})
            self.assertEqual(result.status_code, 200, result.text[:500])
            self.assertEqual(result.headers["content-type"], "application/zip")

    async def test_invalid_source_returns_diagnostics_and_releases_slot(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            await self.compiler.compile(self.source("<script>let = ;</script>"))
        self.assertEqual(caught.exception.status_code, 422)
        self.assertIn("compilation failed", caught.exception.detail)
        await self.compiler.compile(self.source())
        with self.assertRaises(HTTPException) as caught:
            await self.compiler.compile(b"not a zip")
        self.assertEqual(caught.exception.status_code, 422)

    async def test_another_process_holds_the_shared_compilation_slot(self) -> None:
        process = await asyncio.create_subprocess_exec(
            "python", "-c", "import fcntl,sys,time; f=open(sys.argv[1],'a'); fcntl.flock(f,fcntl.LOCK_EX); print('ready',flush=True); time.sleep(30)",
            str(self.root / "compiler.lock"), stdout=asyncio.subprocess.PIPE,
        )
        try:
            self.assertEqual(await asyncio.wait_for(process.stdout.readline(), 5), b"ready\n")
            with self.assertRaises(HTTPException) as caught:
                await self.compiler.compile(self.source())
            self.assertEqual(caught.exception.status_code, 429)
        finally:
            process.kill()
            await process.wait()
        await self.compiler.compile(self.source())

    async def test_timeout_and_cancellation_reap_the_compiler(self) -> None:
        script = self.root / "wait.mjs"
        script.write_text("setInterval(() => {}, 1000)")
        spawn = asyncio.create_subprocess_exec
        for cancel in (False, True):
            started = asyncio.Event()
            processes = []

            async def capture(*args, **kwargs):
                process = await spawn(*args, **kwargs)
                processes.append(process)
                started.set()
                return process

            with patch.object(ModCompiler, "COMMAND", script), patch.object(ModCompiler, "TIMEOUT_SECONDS", 0.2), patch("asyncio.create_subprocess_exec", capture):
                task = asyncio.create_task(self.compiler.compile(self.source()))
                await asyncio.wait_for(started.wait(), 5)
                if cancel:
                    task.cancel()
                    with self.assertRaises(asyncio.CancelledError):
                        await task
                else:
                    with self.assertRaises(HTTPException) as caught:
                        await task
                    self.assertEqual(caught.exception.status_code, 504)
                self.assertEqual(processes[0].returncode, -signal.SIGKILL)
        await self.compiler.compile(self.source())

    async def test_archive_limits_precede_compilation(self) -> None:
        with patch.object(ModCompiler, "MAX_ARCHIVE_BYTES", 8):
            with self.assertRaises(HTTPException) as caught:
                await self.compiler.compile(self.source())
            self.assertEqual(caught.exception.status_code, 413)
