import functools
from collections.abc import Callable
from typing import Any

from aiocache import cached


class CallableCache:
    """Bypass known cache decorators while overrides can change their nested calls."""

    STDLIB_CACHE = type(functools.lru_cache()(lambda: None))

    @classmethod
    def uncached(cls, original: Callable[..., Any]) -> Callable[..., Any]:
        if isinstance(original, cls.STDLIB_CACHE):
            return cls.uncached(original.__wrapped__)
        if cls._aiocache_wrapper(original):
            return cls.uncached(original.__wrapped__)
        return original

    @staticmethod
    def _aiocache_wrapper(original: Callable[..., Any]) -> bool:
        if not hasattr(original, "__wrapped__"):
            return False
        for cell in getattr(original, "__closure__", None) or ():
            try:
                value = cell.cell_contents
            except ValueError:
                continue
            if isinstance(value, cached):
                return True
        return False
