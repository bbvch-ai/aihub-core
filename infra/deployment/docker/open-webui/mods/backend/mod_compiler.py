import asyncio
import fcntl
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import BadZipFile

from fastapi import HTTPException

from aihub_mods.backend_package import BackendPackage
from aihub_mods.callable_registry import CallableRegistry


class ModCompiler:
    MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
    TIMEOUT_SECONDS = 60
    COMMAND = Path("/opt/aihub/compiler-cli.mjs")
    COMPONENTS = Path("/app/build/_aihub/mods/components.json")

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    async def compile(self, content: bytes) -> bytes:
        if len(content) > self.MAX_ARCHIVE_BYTES:
            raise HTTPException(413, "Mod archive exceeds 16 MiB")
        self.directory.mkdir(parents=True, exist_ok=True)
        # A process-local semaphore would allow one compiler per Uvicorn worker.
        with (self.directory / "compiler.lock").open("a") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise HTTPException(429, "Another mod is compiling; retry when it finishes", headers={"Retry-After": "1"}) from error
            with TemporaryDirectory(prefix="aihub-mod-compile-") as temporary:
                root = Path(temporary)
                try:
                    await asyncio.to_thread(BackendPackage.read_files, content)
                except (BadZipFile, ValueError) as error:
                    raise HTTPException(422, str(error)) from error
                catalog = {"components": json.loads(self.COMPONENTS.read_bytes()), "callables": CallableRegistry.catalog}
                await asyncio.to_thread((root / "source.zip").write_bytes, content)
                await asyncio.to_thread((root / "host.json").write_text, json.dumps(catalog))
                await self._run(root)
                publication = root / "publication.zip"
                if publication.stat().st_size > self.MAX_ARCHIVE_BYTES:
                    raise HTTPException(422, "Compiled mod archive exceeds 16 MiB")
                return await asyncio.to_thread(publication.read_bytes)

    async def _run(self, root: Path) -> None:
        spec = importlib.util.find_spec("playwright")
        if spec is None or spec.origin is None:
            raise RuntimeError("The host image's Playwright Node runtime is missing")
        node = Path(spec.origin).parent / "driver" / "node"
        with (root / "diagnostics.txt").open("w+b") as diagnostics:
            process = await asyncio.create_subprocess_exec(
                str(node), "--max-old-space-size=256", str(self.COMMAND), str(root / "source.zip"),
                str(root / "host.json"), str(root / "publication.zip"),
                stdout=asyncio.subprocess.DEVNULL, stderr=diagnostics,
            )
            try:
                await asyncio.wait_for(process.wait(), timeout=self.TIMEOUT_SECONDS)
            except TimeoutError as error:
                raise HTTPException(504, "Mod compilation exceeded 60 seconds") from error
            finally:
                if process.returncode is None:
                    process.kill()
                    await process.wait()
            if process.returncode:
                diagnostics.seek(0)
                message = diagnostics.read(4000).decode("utf-8", errors="replace")
                raise HTTPException(422, f"Mod compilation failed: {message}")
