import asyncio
import json
from collections.abc import AsyncIterator, Callable
from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import StreamingResponse
from open_webui.routers.users import get_user_info_by_session_user
from open_webui.tasks import create_task

gate = asyncio.Event()
pending: tuple[str, asyncio.Task[Any]] | None = None


async def info(next: Callable[..., Any], context: Any, /, *args: Any, **kwargs: Any) -> dict[str, Any]:
    if context.settings.get("reject"):
        raise HTTPException(418, "Deliberate mod rejection")
    original = await next(*args, **kwargs)
    await asyncio.sleep(0.005)
    context.state["calls"] = context.state.get("calls", 0) + 1
    label = context.settings["label"]
    context.settings["label"] = "Only this request changes"
    return {**(original or {}), "tenant": context.tenant_id, "label": label, "calls": context.state["calls"]}


async def handle(request: Request, context: Any) -> Any:
    global pending

    if context.path == "stream":
        async def stream() -> AsyncIterator[str]:
            yield json.dumps(await get_user_info_by_session_user(request.state.user)) + "\n"
        return StreamingResponse(stream(), media_type="application/x-ndjson", status_code=201)
    if context.path == "background":
        async def work() -> Any:
            await gate.wait()
            return await get_user_info_by_session_user(request.state.user)
        pending = await create_task(None, work(), id=context.tenant_id)
        return {"task_id": pending[0]}
    native = await get_user_info_by_session_user(request.state.user)
    return {"path": context.path, "method": request.method, "native": native, "calls": context.state["calls"]}
