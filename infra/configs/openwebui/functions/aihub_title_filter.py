"""
title: AI-Hub Conversation Title
description: Restores the agent-generated conversation title after the OpenWebUI first-turn title fallback.
required_open_webui_version: 0.6.0
"""

import logging
from typing import Annotated, Any, Optional

from open_webui.models.chats import Chats
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# Must stay in sync with ``aihub_pipeline.py`` (which stashes the title under this key).
AIHUB_TITLE_REDIS_KEY = "aihub:title:{chat_id}"


class Filter:
    """Outlet filter that re-applies the agent-produced conversation title.

    The AI-Hub agent pipeline (``aihub_pipeline``) generates the chat title during the turn and stashes
    it in Redis. On the first turn OpenWebUI's post-response ``background_tasks_handler`` overwrites the
    chat title with the user's prompt — its built-in fallback, which fires regardless of
    ``ENABLE_TITLE_GENERATION`` and cannot be disabled by config. OpenWebUI runs outlet filters *after*
    that handler (``middleware.py``: ``background_tasks_handler`` → ``outlet_filter_handler``), so this
    outlet wins the race: it reads the stashed title, re-persists it, and notifies the UI.
    """

    class Valves(BaseModel):
        pass

    def __init__(self) -> None:
        self.valves = self.Valves()

    async def outlet(
        self,
        body: Annotated[dict[str, Any], "Outlet payload (messages, chat_id, ...)"],
        __request__: Annotated[Any, "FastAPI request, for app.state.redis"] = None,
        __metadata__: Annotated[Optional[dict[str, Any]], "Request metadata"] = None,
        __event_emitter__: Annotated[Any, "Socket event emitter"] = None,
        **kwargs: Any,
    ) -> Annotated[dict[str, Any], "Unmodified outlet payload"]:
        """Re-apply the agent title stashed by the pipeline, overriding OpenWebUI's fallback."""
        chat_id = (__metadata__ or {}).get("chat_id")
        if not chat_id or chat_id.startswith(("local:", "channel:")):
            return body

        redis = getattr(getattr(getattr(__request__, "app", None), "state", None), "redis", None)
        if redis is None:
            return body

        key = AIHUB_TITLE_REDIS_KEY.format(chat_id=chat_id)
        title = await redis.get(key)
        if not title:
            return body
        if isinstance(title, bytes):
            title = title.decode()

        await Chats.update_chat_title_by_id(chat_id, title)
        if __event_emitter__:
            await __event_emitter__({"type": "chat:title", "data": title})
        await redis.delete(key)
        logger.info(f"Restored agent conversation title for chat {chat_id}")
        return body
