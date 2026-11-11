import asyncio
import errno
import hashlib
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace
from typing import Any
from unittest.mock import AsyncMock, patch
from zipfile import ZipFile

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.testclient import TestClient

from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.global_mod_configuration import GlobalModConfiguration
from aihub_mods.global_mod_control import GlobalModControl
from aihub_mods.global_mod_runtime import GlobalModRuntime
from aihub_mods.global_mod_store import GlobalModStore
from aihub_mods.hub_client import HubClient
from aihub_mods.mod_host import ModHost
from aihub_mods.mod_scope_middleware import ModScopeMiddleware
from aihub_mods.mod_selection import ModSelection


class GlobalModTests(unittest.IsolatedAsyncioTestCase):
    TARGET = "open_webui.fixture:operation"
    FINGERPRINT = {"source_sha256": "a" * 64}

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.compatibility = b'{"protocol":2,"openwebui":"fixture"}'
        self.store = GlobalModStore(self.directory, self.compatibility, "first-boot")
        self.store.initialize()
        self.enterContext(patch.dict(CallableRegistry.catalog, {self.TARGET: self.FINGERPRINT}))
        self.enterContext(patch.object(CallableRegistry, "global_handlers", {}))

    @staticmethod
    def archive(files: dict[str, str]) -> bytes:
        content = BytesIO()
        with ZipFile(content, "w") as archive:
            for path, value in files.items():
                archive.writestr(path, value)
        return content.getvalue()

    def stage(self, *, restart: bool = False, code: str | None = None) -> ModSelection:
        source = self.archive({
            "mod.json": json.dumps({"format": 1, "id": "global-fixture", "backend": "backend.py",
                                    "backend_overrides": {self.TARGET: "operation"}, "backend_restart_required": restart}),
            "backend.py": code or "def operation(next, context, /):\n    context.state['calls'] = context.state.get('calls', 0) + 1\n    return [context.settings['label'], context.state['calls'], context.scope]\n",
        })
        revision = hashlib.sha256(source).hexdigest()
        publication = self.archive({"publication.json": json.dumps({
            "format": 1, "source_revision": revision, "compatibility": json.loads(self.compatibility),
            "frontend": None, "replacements": {}, "backend_targets": {self.TARGET: self.FINGERPRINT},
        })})
        published = hashlib.sha256(publication).hexdigest()
        self.store.stage("sources", revision, source)
        self.store.stage("publications", published, publication)
        return ModSelection(mod_id="global-fixture", publication=published, enabled=True, settings={"label": "Global"})

    def test_ordinary_global_changes_are_live_without_restart(self) -> None:
        selection = self.stage()
        result = self.store.replace(GlobalModConfiguration(mods=[selection]))
        self.assertEqual(result["active_version"], 1)
        self.assertFalse(result["restart_required"])
        self.assertEqual(self.store.live().mods, [selection])

    def test_restart_changes_stage_without_importing_and_survive_new_workers(self) -> None:
        selection = self.stage(restart=True, code="raise RuntimeError('Staging must never execute Python')")
        result = self.store.replace(GlobalModConfiguration(mods=[selection]))
        self.assertTrue(result["restart_required"])
        self.assertEqual(self.store.live().mods, [])
        same_boot = GlobalModStore(self.directory, self.compatibility, "first-boot")
        same_boot.initialize()
        self.assertEqual(same_boot.live().mods, [])
        restarted = GlobalModStore(self.directory, self.compatibility, "second-boot")
        restarted.initialize()
        self.assertEqual(restarted.live().mods, [selection])
        self.assertFalse(restarted.status()["restart_required"])

    def test_restart_can_be_cancelled_and_removing_startup_code_requires_restart(self) -> None:
        selection = self.stage(restart=True)
        self.store.replace(GlobalModConfiguration(mods=[selection]))
        cancelled = self.store.replace(GlobalModConfiguration(version=1))
        self.assertFalse(cancelled["restart_required"])
        self.store.replace(GlobalModConfiguration(version=2, mods=[selection]))
        restarted = GlobalModStore(self.directory, self.compatibility, "second-boot")
        restarted.initialize()
        removed = restarted.replace(GlobalModConfiguration(version=3))
        self.assertTrue(removed["restart_required"])
        self.assertEqual(len(restarted.live().mods), 1)

    def test_restart_confirmation_freezes_changes_until_the_next_boot(self) -> None:
        selection = self.stage(restart=True)
        self.store.replace(GlobalModConfiguration(mods=[selection]))
        self.store.request_restart(1)
        second_admin = GlobalModStore(self.directory, self.compatibility, "first-boot")
        edited = selection.model_copy(update={"settings": {"label": "Unconfirmed"}})
        with self.assertRaises(HTTPException) as rejected:
            second_admin.replace(GlobalModConfiguration(version=1, mods=[edited]))
        self.assertEqual(rejected.exception.status_code, 409)
        self.assertIn("restarting", rejected.exception.detail)
        self.assertEqual(self.store.status()["configuration"]["version"], 1)

        restarted = GlobalModStore(self.directory, self.compatibility, "second-boot")
        restarted.initialize()
        self.assertEqual(restarted.live().mods, [selection])
        saved = restarted.replace(GlobalModConfiguration(version=1, mods=[edited]))
        self.assertEqual(saved["configuration"]["version"], 2)
        self.assertEqual(saved["configuration"]["mods"], [edited.model_dump()])
        self.assertTrue(saved["restart_required"])
        self.assertEqual(restarted.live().mods, [selection])

    def test_persisted_restart_can_be_explicitly_retried(self) -> None:
        selection = self.stage(restart=True)
        self.store.replace(GlobalModConfiguration(mods=[selection]))
        self.store.request_restart(1)
        confirmed_marker = (self.directory / "restart.json").read_bytes()
        same_boot = GlobalModStore(self.directory, self.compatibility, "first-boot")
        app, router = FastAPI(), APIRouter()
        control = GlobalModControl(same_boot, "fixture-provisioning-token")
        control.install(router)
        app.include_router(router)
        with TestClient(app) as client:
            client.headers["Authorization"] = "Bearer fixture-provisioning-token"
            with patch.object(control, "check_restart_environment"), patch.object(control, "restart", AsyncMock()) as restart:
                self.assertEqual(client.post("/control/restart?version=1").status_code, 202)
                restart.assert_awaited_once()
                self.assertEqual(client.post("/control/restart?version=0").status_code, 409)
                restart.assert_awaited_once()
                self.assertEqual(client.put("/control/global", json={"version": 1, "mods": []}).status_code, 409)
        self.assertEqual(same_boot.status()["configuration"]["version"], 1)
        self.assertEqual((self.directory / "restart.json").read_bytes(), confirmed_marker)

    def test_concurrent_restart_retries_keep_configuration_frozen(self) -> None:
        selection = self.stage(restart=True)
        self.store.replace(GlobalModConfiguration(mods=[selection]))
        self.store.request_restart(1)

        def attempt(index: int) -> int:
            if index % 2:
                self.store.request_restart(1)
                return 202
            try:
                self.store.replace(GlobalModConfiguration(version=1))
                return 200
            except HTTPException as error:
                return error.status_code

        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(attempt, range(8)))
        self.assertEqual(results, [409, 202] * 4)
        self.assertEqual(self.store.status()["configuration"], GlobalModConfiguration(version=1, mods=[selection]).model_dump())

    def test_concurrent_admin_edits_use_compare_and_swap(self) -> None:
        def replace(_: int) -> int:
            try:
                self.store.replace(GlobalModConfiguration())
                return 200
            except HTTPException as error:
                return error.status_code
        with ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(replace, range(8)))
        self.assertEqual(results.count(200), 1)
        self.assertEqual(results.count(409), 7)

    def test_incompatible_global_mod_can_be_disabled_after_host_upgrade(self) -> None:
        selection = self.stage(restart=True)
        self.store.replace(GlobalModConfiguration(mods=[selection]))
        upgraded = GlobalModStore(self.directory, b'{"protocol":3,"openwebui":"fixture"}', "second-boot")
        upgraded.initialize()
        with self.assertRaisesRegex(ValueError, "Republish"):
            upgraded.source(selection)
        result = upgraded.replace(GlobalModConfiguration(version=1, mods=[selection.model_copy(update={"enabled": False})]))
        self.assertTrue(result["restart_required"])

    def test_archive_hash_and_target_drift_are_rejected(self) -> None:
        with self.assertRaises(HTTPException):
            self.store.stage("sources", "a" * 64, b"tampered")
        selection = self.stage()
        with patch.dict(CallableRegistry.catalog, {self.TARGET: {"source_sha256": "b" * 64}}):
            with self.assertRaisesRegex(ValueError, "source changed"):
                self.store.replace(GlobalModConfiguration(mods=[selection]))

    def test_control_uses_provisioning_credential_and_restart_checks_version(self) -> None:
        app, router = FastAPI(), APIRouter()
        control = GlobalModControl(self.store, "fixture-provisioning-token")
        control.install(router)
        app.include_router(router)
        with TestClient(app) as client:
            self.assertEqual(client.get("/control/global").status_code, 403)
            client.headers["Authorization"] = "Bearer fixture-provisioning-token"
            self.assertEqual(client.get("/control/global").status_code, 200)
            with patch.object(control, "check_restart_environment"), patch.object(control, "restart", AsyncMock()) as restart:
                self.assertEqual(client.post("/control/restart?version=1").status_code, 409)
                self.assertEqual(client.post("/control/restart?version=0").status_code, 202)
                self.assertEqual(client.post("/control/restart?version=0").status_code, 202)
                self.assertEqual(restart.await_count, 2)

    async def test_global_handlers_get_fresh_request_state_and_keep_old_execution(self) -> None:
        selection = self.stage()
        self.store.replace(GlobalModConfiguration(mods=[selection]))
        host = ModHost(HubClient("http://hub", "key", "secret"), self.compatibility)
        runtime = GlobalModRuntime(self.store, host.runtime)
        await runtime.start(FastAPI())
        try:
            self.assertFalse(self.store.status()["workers"][0]["ready"])
            await runtime.mark_ready()
            self.assertTrue(self.store.status()["workers"][0]["ready"])
            first, second = runtime.handlers(), runtime.handlers()
            self.assertEqual(first[self.TARGET][0](lambda: None), ["Global", 1, "global"])
            self.assertEqual(second[self.TARGET][0](lambda: None), ["Global", 1, "global"])
            changed = selection.model_copy(update={"settings": {"label": "New"}})
            self.store.replace(GlobalModConfiguration(version=1, mods=[changed]))
            await runtime.refresh()
            self.assertEqual(runtime.handlers()[self.TARGET][0](lambda: None), ["New", 1, "global"])
            self.assertEqual(first[self.TARGET][0](lambda: None), ["Global", 2, "global"])
        finally:
            await runtime.close()
            await host.runtime.close()
            await host.client.http.aclose()

    def test_worker_status_does_not_count_a_reused_process_id(self) -> None:
        self.store.worker_status(0, None, True)
        path = next((self.directory / "workers" / "first-boot").glob("*.json"))
        record = json.loads(path.read_text())
        record["process_start"] = "previous-process"
        path.write_text(json.dumps(record))
        self.assertEqual(self.store.status()["workers"], [])

    async def test_failed_activation_is_not_retried_and_control_remains_reachable(self) -> None:
        selection = self.stage()
        self.store.replace(GlobalModConfiguration(mods=[selection]))
        loader = SimpleNamespace(load_package=AsyncMock(side_effect=RuntimeError("Invalid mod")))
        runtime = GlobalModRuntime(self.store, loader)
        with self.assertLogs("aihub_mods.global_mod_runtime", level="ERROR"):
            await runtime.start(FastAPI())
        try:
            await runtime.refresh()
            self.assertEqual(loader.load_package.await_count, 1)
            app = FastAPI()
            app.state.aihub_mods = SimpleNamespace(global_runtime=runtime)
            app.add_middleware(ModScopeMiddleware)
            with TestClient(app) as client:
                self.assertEqual(client.get("/ordinary").status_code, 503)
                self.assertEqual(client.get("/_aihub/mods/control/global").status_code, 404)
            self.store.replace(GlobalModConfiguration(version=1))
            await runtime.refresh()
            self.assertIsNone(runtime.error)
            self.assertEqual(runtime.version, 2)
        finally:
            await runtime.close()

    async def test_polling_recovers_from_storage_errors_without_reimporting_failed_mods(self) -> None:
        self.store.replace(GlobalModConfiguration(mods=[self.stage()]))
        configuration = self.store.live()
        loader = SimpleNamespace(load_package=AsyncMock(side_effect=RuntimeError("Invalid mod")))
        runtime = GlobalModRuntime(self.store, loader)
        ticks: asyncio.Queue[None] = asyncio.Queue()
        waiting: asyncio.Queue[None] = asyncio.Queue()

        async def sleep(delay: float) -> None:
            self.assertEqual(delay, 2)
            waiting.put_nowait(None)
            await ticks.get()

        reads = [configuration, OSError(errno.EIO, "Temporary read failure"), configuration, configuration]
        writes = [None, OSError(errno.ENOSPC, "No space left on device"), None, None]
        with patch("aihub_mods.global_mod_runtime.asyncio.sleep", sleep), \
             patch.object(self.store, "live", side_effect=reads), \
             patch.object(self.store, "worker_status", side_effect=writes), \
             self.assertLogs("aihub_mods.global_mod_runtime", level="ERROR") as logs:
            await runtime.start(FastAPI())
            try:
                await asyncio.wait_for(waiting.get(), 1)
                for _ in range(3):
                    ticks.put_nowait(None)
                    await asyncio.wait_for(waiting.get(), 1)
                self.assertFalse(runtime.poller.done())
                self.assertIsNotNone(runtime.error)
                self.assertEqual(loader.load_package.await_count, 1)
                self.assertEqual(sum("retrying on the next poll" in message for message in logs.output), 2)
            finally:
                await runtime.close()
            self.assertTrue(runtime.poller.cancelled())
