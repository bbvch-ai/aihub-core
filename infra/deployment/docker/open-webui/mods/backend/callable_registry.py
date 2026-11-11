import functools
import inspect
from collections.abc import AsyncGenerator, Callable, Generator, Mapping
from contextvars import ContextVar
from typing import Any, ClassVar

from aihub_mods.callable_cache import CallableCache


class CallableRegistry:
    """Stable dispatchers keep imported aliases valid; selections belong to execution contexts."""

    active: ClassVar[ContextVar[Mapping[str, tuple[Callable[..., Any], ...]] | None]] = ContextVar(
        "aihub_mod_callables", default=None
    )
    global_handlers: ClassVar[Mapping[str, tuple[Callable[..., Any], ...]]] = {}
    system_handlers: ClassVar[Mapping[str, tuple[Callable[..., Any], ...]]] = {}
    catalog: ClassVar[dict[str, dict[str, Any]]] = {}

    @classmethod
    def selection(
        cls, tenant: Mapping[str, tuple[Callable[..., Any], ...]],
        global_handlers: Mapping[str, tuple[Callable[..., Any], ...]] | None = None,
    ) -> Mapping[str, tuple[Callable[..., Any], ...]]:
        global_handlers = cls.global_handlers if global_handlers is None else global_handlers
        return {target: tenant.get(target, ()) + global_handlers.get(target, ())
                for target in tenant.keys() | global_handlers.keys()}

    @classmethod
    def decorate(cls, target: str, original: Any) -> Any:
        if isinstance(original, (staticmethod, classmethod)):
            return type(original)(cls.decorate(target, original.__func__))
        if not callable(original) or not (inspect.isfunction(original) or hasattr(original, "__wrapped__")):
            return original
        if getattr(original, "__aihub_target__", None) == target:
            return original
        uncached = CallableCache.uncached(original)

        def invoke(args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
            selection = cls.active.get()
            if selection is None:
                selection = cls.global_handlers
            handlers = cls.system_handlers.get(target, ()) + selection.get(target, ())
            native = uncached if selection else original
            if not handlers:
                return native(*args, **kwargs)

            def step(index: int, *args: Any, **kwargs: Any) -> Any:
                if index == len(handlers):
                    return native(*args, **kwargs)
                return handlers[index](lambda *a, **k: step(index + 1, *a, **k), *args, **kwargs)

            return step(0, *args, **kwargs)

        wrapper = cls._wrapper(original, invoke)
        functools.update_wrapper(wrapper, original)
        for name in ("cache_info", "cache_clear", "cache_parameters"):
            if hasattr(original, name):
                setattr(wrapper, name, getattr(original, name))
        wrapper.__aihub_target__ = target
        return wrapper

    @classmethod
    def _wrapper(cls, original: Callable[..., Any], invoke: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.isasyncgenfunction(original):
            return cls._async_generator(invoke)
        if inspect.iscoroutinefunction(original):
            async def coroutine(*args: Any, **kwargs: Any) -> Any:
                return await invoke(args, kwargs)
            return coroutine
        if inspect.isgeneratorfunction(original):
            def generator(*args: Any, **kwargs: Any) -> Generator[Any, Any, Any]:
                return (yield from invoke(args, kwargs))
            return generator

        def synchronous(*args: Any, **kwargs: Any) -> Any:
            return invoke(args, kwargs)
        return synchronous

    @staticmethod
    def _async_generator(invoke: Callable[..., Any]) -> Callable[..., AsyncGenerator[Any, Any]]:
        async def generator(*args: Any, **kwargs: Any) -> AsyncGenerator[Any, Any]:
            iterator = invoke(args, kwargs)
            try:
                item = await iterator.__anext__()
                while True:
                    try:
                        sent = yield item
                    except GeneratorExit:
                        raise
                    except BaseException as error:
                        item = await iterator.athrow(error)
                    else:
                        item = await iterator.asend(sent)
            except StopAsyncIteration:
                return
            finally:
                await iterator.aclose()
        return generator
