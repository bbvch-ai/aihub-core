import asyncio
import concurrent.futures
from collections.abc import Coroutine
from typing import Any


def run_async[T](coroutine: Coroutine[Any, Any, T]) -> T:
    """Run a coroutine from synchronous Dagster code, also when a loop is already running on this thread.

    Dagster ops and IO managers are synchronous; the rclone client is async. When a test harness or framework
    already runs a loop, ``asyncio.run`` would raise, so the coroutine is handed to a fresh thread instead.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coroutine)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        return executor.submit(asyncio.run, coroutine).result()
