import sys
from collections.abc import Sequence
from importlib.abc import MetaPathFinder
from importlib.machinery import ModuleSpec, PathFinder, SourceFileLoader
from pathlib import Path
from types import ModuleType

from fastapi import FastAPI
from fastapi.dependencies.models import Dependant
from fastapi.routing import APIRoute, APIWebSocketRoute

from aihub_mods.callable_loader import CallableLoader
from aihub_mods.callable_registry import CallableRegistry
from aihub_mods.callable_transform import CallableTransform


class CallableImports(MetaPathFinder):
    def find_spec(
        self, fullname: str, path: Sequence[str] | None = None, target: ModuleType | None = None,
    ) -> ModuleSpec | None:
        if not fullname.startswith("open_webui."):
            return None
        spec = PathFinder.find_spec(fullname, path)
        if spec and isinstance(spec.loader, SourceFileLoader):
            spec.loader = CallableLoader(fullname, spec.origin)
        return spec

    @classmethod
    def install(cls) -> None:
        if any(name.startswith("open_webui.") for name in sys.modules):
            raise RuntimeError("Install the mod callable adapter before importing Open WebUI")
        if not any(isinstance(finder, cls) for finder in sys.meta_path):
            spec = PathFinder.find_spec("open_webui")
            if spec is None or spec.origin is None:
                raise RuntimeError("Open WebUI source is unavailable for the mod callable adapter")
            CallableRegistry.catalog = CallableTransform.catalog(Path(spec.origin).parent)
            sys.meta_path.insert(0, cls())

    @classmethod
    def bind_routes(cls, app: FastAPI) -> None:
        # Framework decorators retain references before the source assignment runs.
        for error, call in app.exception_handlers.items():
            if getattr(call, "__module__", "").startswith("open_webui."):
                app.exception_handlers[error] = CallableRegistry.decorate(call.__module__ + ":" + call.__qualname__, call)
        for route in app.routes:
            if isinstance(route, (APIRoute, APIWebSocketRoute)):
                cls._bind_dependency(route.dependant)
                call = route.endpoint
                if getattr(call, "__module__", "").startswith("open_webui."):
                    route.endpoint = CallableRegistry.decorate(call.__module__ + ":" + call.__qualname__, call)

    @classmethod
    def _bind_dependency(cls, dependant: Dependant) -> None:
        call = dependant.call
        if call and getattr(call, "__module__", "").startswith("open_webui."):
            dependant.call = CallableRegistry.decorate(call.__module__ + ":" + call.__qualname__, call)
        for dependency in dependant.dependencies:
            cls._bind_dependency(dependency)
