from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request

Emitter = Callable[[dict[str, Any]], Awaitable[Any]] | None


class NativeFilter:
    async def inlet(
        self, body: dict[str, Any], __request__: Request, __user__: dict[str, Any],
        __metadata__: dict[str, Any], __model__: dict[str, Any], __event_emitter__: Emitter = None,
    ) -> dict[str, Any]:
        return await __request__.app.state.aihub_mods.runtime.apply(
            "inlet", body, __request__, __user__, __metadata__, __model__, __event_emitter__,
        )

    async def request(
        self, body: dict[str, Any], __request__: Request, __user__: dict[str, Any],
        __metadata__: dict[str, Any], __model__: dict[str, Any], __event_emitter__: Emitter = None,
    ) -> dict[str, Any]:
        return await __request__.app.state.aihub_mods.runtime.apply(
            "request", body, __request__, __user__, __metadata__, __model__, __event_emitter__,
        )

    async def stream(
        self, event: dict[str, Any], __request__: Request, __user__: dict[str, Any],
        __metadata__: dict[str, Any], __model__: dict[str, Any], __event_emitter__: Emitter = None,
    ) -> dict[str, Any] | None:
        return await __request__.app.state.aihub_mods.runtime.apply(
            "stream", event, __request__, __user__, __metadata__, __model__, __event_emitter__,
        )

    async def outlet(
        self, body: dict[str, Any], __request__: Request, __user__: dict[str, Any],
        __metadata__: dict[str, Any], __model__: dict[str, Any], __event_emitter__: Emitter = None,
    ) -> dict[str, Any]:
        return await __request__.app.state.aihub_mods.runtime.apply(
            "outlet", body, __request__, __user__, __metadata__, __model__, __event_emitter__,
        )
