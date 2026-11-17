import json
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request
from pydantic import BaseModel, ConfigDict, Field, JsonValue, PrivateAttr


class ModRunContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, frozen=True)

    id: str
    tenant_id: str
    mod_id: str
    publication: str
    execution_id: str | None
    settings: dict[str, JsonValue]
    request: Request
    user: dict[str, Any]
    metadata: dict[str, Any]
    model: dict[str, Any]
    event_emitter: Callable[[dict[str, Any]], Awaitable[Any]] | None = Field(exclude=True)
    _closed: bool = PrivateAttr(default=False)

    async def emit(self, event_type: str, data: JsonValue) -> None:
        if self._closed or not self.event_emitter or not self.execution_id:
            return
        envelope = {**self.scope(), "modId": self.mod_id, "publication": self.publication, "type": event_type, "data": data}
        if not event_type or len(event_type) > 128 or len(json.dumps(envelope).encode()) > 64 * 1024:
            raise ValueError("Mod event exceeds its type or payload limit. Please contact your administrator.")
        await self.event_emitter({"type": "aihub:mod", "data": envelope})

    def scope(self) -> dict[str, Any]:
        return {
            "version": 1, "contextId": self.id, "tenantId": self.tenant_id,
            "executionId": self.execution_id,
            "chatId": self.metadata.get("chat_id"), "messageId": self.metadata.get("message_id"),
            "taskId": self.metadata.get("task_id"),
        }

    def close(self) -> None:
        self._closed = True
