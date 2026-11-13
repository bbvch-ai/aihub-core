import hashlib
import importlib
import inspect
import json
import stat
import sys
from collections.abc import Callable
from io import BytesIO
from pathlib import Path, PurePosixPath
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Any
from zipfile import ZipFile

from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.mod_request_context import ModRequestContext
from aihub_mods.global_mod_context import GlobalModContext

class BackendPackage:
    """An immutable, private Python package; instances and tenant settings belong to runs."""

    def __init__(self, revision: str, content: bytes, mod_id: str) -> None:
        if hashlib.sha256(content).hexdigest() != revision:
            raise ValueError("Backend source failed its integrity check")
        self.directory = TemporaryDirectory(prefix="aihub-mod-")
        self.namespace = f"_aihub_mod_{revision}"
        self.entry: ModuleType | None = None
        self.overrides: dict[str, str] = {}
        self.restart_required = False
        try:
            files = self.read_files(content)
            manifest = json.loads(files["mod.json"])
            if manifest["id"] != mod_id:
                raise ValueError("Backend source belongs to another mod")
            backend = manifest.get("backend")
            self.overrides = manifest.get("backend_overrides", {})
            self.restart_required = bool(manifest.get("backend_restart_required") or "open_webui.main:lifespan" in self.overrides)
            if backend is not None:
                self.entry = self._import(files, backend)
                for handler in self.overrides.values():
                    if not callable(getattr(self.entry, handler, None)):
                        raise ValueError(f"Backend entry does not export callable handler '{handler}'")
        except BaseException:
            self.close()
            raise

    @staticmethod
    def read_files(content: bytes) -> dict[str, bytes]:
        with ZipFile(BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > 512 or sum(entry.file_size for entry in entries) > 32 * 1024 * 1024:
                raise ValueError("Backend source exceeds the expansion limit")
            files: dict[str, bytes] = {}
            names: set[str] = set()
            for entry in entries:
                name = entry.filename.removesuffix("/") if entry.is_dir() else entry.filename
                path = PurePosixPath(name)
                if (not name or path.is_absolute() or path.as_posix() != name
                    or any(part in {".", ".."} for part in path.parts)
                    or "\\" in name or entry.orig_filename != entry.filename or name in names):
                    raise ValueError("Invalid backend source path")
                names.add(name)
                mode = stat.S_IFMT(entry.external_attr >> 16)
                if mode not in {0, stat.S_IFDIR if entry.is_dir() else stat.S_IFREG}:
                    raise ValueError("Backend source cannot contain links or special files")
                if not entry.is_dir():
                    files[name] = archive.read(entry)
            return files

    def _import(self, files: dict[str, bytes], backend: str) -> ModuleType:
        path = PurePosixPath(backend)
        parts = (*path.parts[:-1], path.stem)
        if backend not in files or path.suffix != ".py" or any(not part.isidentifier() for part in parts):
            raise ValueError("Backend entry must be an importable Python module path")
        for filename, content in files.items():
            target = Path(self.directory.name, filename)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        package = ModuleType(self.namespace)
        package.__path__ = [self.directory.name]
        package.__package__ = self.namespace
        sys.modules[self.namespace] = package
        return importlib.import_module(f"{self.namespace}.{'.'.join(parts)}")

    def create_filter(self) -> Any | None:
        if self.entry is None:
            return None
        factory = getattr(self.entry, "Filter", None)
        if factory is None:
            if self.overrides or callable(getattr(self.entry, "handle", None)):
                return None
            raise ValueError(
                "Backend entry must export Filter, handle or declared callable handlers. Please contact your administrator."
            )
        if not isinstance(factory, type):
            raise ValueError("Backend entry must export a Filter class. Please contact your administrator.")
        return factory()

    def check_targets(self, declared: dict[str, Any]) -> None:
        expected = {}
        for target in self.overrides:
            if target not in CallableRegistry.catalog:
                raise ValueError(f"Backend callable target is absent: {target}")
            expected[target] = CallableRegistry.catalog[target]
        if declared != expected:
            changed = sorted(
                target for target in declared.keys() | expected.keys() if declared.get(target) != expected.get(target)
            )
            raise ValueError(f"Backend callable source changed: {', '.join(changed)}. Reinstall the mod for this host.")

    def bind_overrides(self, context: ModRequestContext | GlobalModContext) -> dict[str, tuple[Callable[..., Any], ...]]:
        return {target: (self._bind(getattr(self.entry, handler), context),) for target, handler in self.overrides.items()}

    async def handle(self, context: ModRequestContext) -> Any:
        handler = getattr(self.entry, "handle", None)
        if handler is None:
            from fastapi import HTTPException
            raise HTTPException(404, "This mod has no HTTP handler")
        if not inspect.iscoroutinefunction(handler):
            raise TypeError("The mod HTTP handle(request, context) function must be async")
        return await handler(context.request, context)

    @staticmethod
    def _bind(handler: Callable[..., Any], context: ModRequestContext | GlobalModContext) -> Callable[..., Any]:
        def invoke(next: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
            return handler(next, context, *args, **kwargs)
        return invoke

    def close(self) -> None:
        for name in tuple(sys.modules):
            if name == self.namespace or name.startswith(self.namespace + "."):
                del sys.modules[name]
        self.directory.cleanup()
