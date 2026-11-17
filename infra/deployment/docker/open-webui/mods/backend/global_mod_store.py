import fcntl
import hashlib
import json
import logging
import os
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Literal

from fastapi import HTTPException

from aihub_mods.backend_package import BackendPackage
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.frontend_archive import FrontendArchive
from aihub_mods.global_mod_configuration import GlobalModConfiguration
from aihub_mods.mod_selection import ModSelection


class GlobalModStore:
    """One atomic selection on the existing data volume coordinates all local workers."""

    def __init__(self, directory: Path, compatibility: bytes, boot_id: str | None = None) -> None:
        self.directory = directory
        self.compatibility = json.loads(compatibility)
        self.boot_id = boot_id or Path("/proc/1/stat").read_text().rsplit(")", 1)[1].split()[19]

    @contextmanager
    def _lock(self) -> Iterator[None]:
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / "control.lock").open("a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _write(self, path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
            try:
                temporary.write(content)
                temporary.flush()
                os.fsync(temporary.fileno())
                os.replace(temporary.name, path)
            finally:
                Path(temporary.name).unlink(missing_ok=True)

    def _configuration(self, name: str) -> GlobalModConfiguration:
        path = self.directory / name
        return GlobalModConfiguration.model_validate_json(path.read_bytes()) if path.exists() else GlobalModConfiguration()

    def initialize(self) -> None:
        with self._lock():
            marker = self.directory / "boot.json"
            if marker.exists() and json.loads(marker.read_bytes())["id"] == self.boot_id:
                return
            configuration = self._configuration("desired.json")
            self._write(self.directory / "live.json", configuration.model_dump_json().encode())
            self._write(marker, json.dumps({"id": self.boot_id, "configuration": configuration.model_dump()}).encode())
            self._prune()

    def live(self) -> GlobalModConfiguration:
        with self._lock():
            return self._configuration("live.json")

    def status(self) -> dict[str, Any]:
        with self._lock():
            desired, live = self._configuration("desired.json"), self._configuration("live.json")
            workers = [json.loads(path.read_bytes()) for path in (self.directory / "workers" / self.boot_id).glob("*.json")]
            return {"configuration": desired.model_dump(), "active_version": live.version, "boot_id": self.boot_id,
                    "restart_required": desired.version != live.version,
                    "expected_workers": int(os.environ.get("UVICORN_WORKERS", "1")),
                    "workers": [worker for worker in workers if time.time() - worker["updated_at"] < 15 and self._alive(worker)]}

    @staticmethod
    def _alive(worker: dict[str, Any]) -> bool:
        try:
            return Path(f"/proc/{worker['pid']}/stat").read_text().rsplit(")", 1)[1].split()[19] == worker["process_start"]
        except FileNotFoundError:
            return False

    def stage(self, kind: Literal["sources", "publications"], revision: str, content: bytes) -> None:
        if len(content) > 16 * 1024 * 1024 or hashlib.sha256(content).hexdigest() != revision:
            raise HTTPException(422, "Global mod archive size or hash is invalid")
        if kind == "sources":
            json.loads(BackendPackage.read_files(content)["mod.json"])
        else:
            FrontendArchive(revision, content)
        self._write(self.directory / kind / f"{revision}.zip", content)

    def source(self, mod: ModSelection, *, validate: bool = True) -> tuple[str, bytes, dict[str, Any]]:
        publication = (self.directory / "publications" / f"{mod.publication}.zip").read_bytes()
        archive = FrontendArchive(mod.publication, publication)
        manifest = json.loads(archive.read("publication.json", manifest=True))
        if validate and manifest["compatibility"] != self.compatibility:
            raise ValueError(f"Reinstall '{mod.mod_id}' for this Open WebUI host")
        revision = manifest["source_revision"]
        if not isinstance(revision, str) or len(revision) != 64 or any(char not in "0123456789abcdef" for char in revision):
            raise ValueError("Invalid global source revision")
        source = (self.directory / "sources" / f"{revision}.zip").read_bytes()
        if hashlib.sha256(source).hexdigest() != revision:
            raise ValueError("Global source failed its integrity check")
        declared = json.loads(BackendPackage.read_files(source)["mod.json"])
        if declared["id"] != mod.mod_id:
            raise ValueError("Global source belongs to another mod")
        if not validate:
            return revision, source, declared
        expected = {}
        for target in declared.get("backend_overrides", {}):
            if target not in CallableRegistry.catalog:
                raise ValueError(f"Native backend target is absent: {target}")
            expected[target] = CallableRegistry.catalog[target]
        published = manifest.get("backend_targets", {})
        if published != expected:
            changed = sorted(
                target for target in published.keys() | expected.keys() if published.get(target) != expected.get(target)
            )
            raise ValueError(f"Native callable source changed for '{mod.mod_id}': {', '.join(changed)}. Reinstall it.")
        return revision, source, declared

    def _startup(self, configuration: GlobalModConfiguration) -> list[dict[str, Any]]:
        selections = []
        for mod in configuration.mods:
            if mod.enabled:
                _, _, manifest = self.source(mod, validate=False)
                if manifest.get("backend_restart_required") or "open_webui.main:lifespan" in manifest.get("backend_overrides", {}):
                    selections.append(mod.model_dump())
        return selections

    def replace(self, configuration: GlobalModConfiguration) -> dict[str, Any]:
        for mod in configuration.mods:
            self.source(mod, validate=mod.enabled)
        with self._lock():
            desired = self._configuration("desired.json")
            if desired.version != configuration.version:
                raise HTTPException(409, "Global mod settings changed; reload before saving")
            restart_request = self.directory / "restart.json"
            if restart_request.exists() and json.loads(restart_request.read_bytes())["boot_id"] == self.boot_id:
                raise HTTPException(409, "Open WebUI is restarting; wait for recovery before saving")
            boot = GlobalModConfiguration.model_validate(json.loads((self.directory / "boot.json").read_bytes())["configuration"])
            restart = self._startup(configuration) != self._startup(boot)
            updated = configuration.model_copy(update={"version": desired.version + 1})
            self._write(self.directory / "desired.json", updated.model_dump_json().encode())
            if not restart:
                self._write(self.directory / "live.json", updated.model_dump_json().encode())
            self._prune()
        return self.status()

    def _prune(self) -> None:
        try:
            boot = GlobalModConfiguration.model_validate(json.loads((self.directory / "boot.json").read_bytes())["configuration"])
            configurations = [boot, self._configuration("desired.json"), self._configuration("live.json")]
            publications = {mod.publication for config in configurations for mod in config.mods}
            sources = {self.source(mod, validate=False)[0] for config in configurations for mod in config.mods}
            for kind, keep in (("sources", sources), ("publications", publications)):
                for archive in (self.directory / kind).glob("*.zip"):
                    if archive.stem not in keep:
                        archive.unlink()
        except Exception:
            logging.getLogger(__name__).exception("Could not clean global mod archives; retrying on the next save or startup")

    def worker_status(self, version: int, error: str | None, ready: bool = False) -> None:
        content = {"pid": os.getpid(), "version": version, "error": error, "ready": ready, "updated_at": time.time(),
                   "process_start": Path("/proc/self/stat").read_text().rsplit(")", 1)[1].split()[19]}
        self._write(self.directory / "workers" / self.boot_id / f"{os.getpid()}.json", json.dumps(content).encode())

    def request_restart(self, version: int) -> None:
        with self._lock():
            if self._configuration("desired.json").version != version:
                raise HTTPException(409, "Global mod settings changed; reload before restarting")
            path = self.directory / "restart.json"
            if path.exists() and json.loads(path.read_bytes())["boot_id"] == self.boot_id:
                # An earlier request may have ended before its background task signalled PID 1.
                return
            self._write(path, json.dumps({"boot_id": self.boot_id, "version": version, "requested_at": time.time()}).encode())
