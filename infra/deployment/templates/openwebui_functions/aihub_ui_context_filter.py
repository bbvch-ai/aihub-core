"""
title: AI-Hub UI Context
description: Tells the AI-Hub shell which model or agent the current turn is using, so a bug report raised outside the chat can name it.
required_open_webui_version: 0.6.0
"""

import hashlib
import json
import logging
import os
from typing import Annotated, Any

from bson import ObjectId
from open_webui.models.models import Models
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

AIHUB_PIPELINE_PREFIX = "aihub-pipeline."


class Filter:
    """Publishes the turn's model or agent to the parent window.

    The chat runs in an iframe, so the shell cannot see which model is selected; it learns only
    what OpenWebUI tells it. A pipe could say so, but only for the turns a pipe handles — and a
    plain model reaches the API through OpenWebUI's own OpenAI connection, never touching one.
    An inlet filter runs on every turn whatever the routing, which is the property that matters
    here: without it a report filed after switching from an agent to a model still named the
    agent, because nothing had overwritten it.

    Every field is sent on every turn, including the empty ones. Leaving a field out would let a
    previous turn's value survive into a report about this one, and a wrong model is worse than
    no model.
    """

    class Valves(BaseModel):
        AIHUB_FRONTEND_URL: str = Field(
            default=os.getenv("AIHUB_FRONTEND_URL", "http://localhost:3333"),
            description="Base URL for the AI-Hub frontend",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _display_id(self, message_id: Annotated[str | None, "OpenWebUI message id"]) -> str:
        """Mirrors the pipes' empty-salt hashing so the shell sees one id for one message."""
        if not message_id:
            return ""
        hashed = hashlib.md5(f":{message_id}".encode()).digest()[:12]
        return str(ObjectId(hashed)).lower()

    async def _resolve_base_id(self, model_id: Annotated[str, "Model id from the request"]) -> str:
        """Workspace models wrap another id, and only the wrapped one says whether this is an agent."""
        try:
            model = await Models.get_model_by_id(model_id)
        except Exception as lookup_error:
            logger.warning(f"Could not resolve model {model_id}: {lookup_error}")
            return model_id
        return (model.base_model_id if model and model.base_model_id else model_id) or model_id

    @staticmethod
    def _describe(
        base_id: Annotated[str, "Resolved base model id"],
        display_name: Annotated[str, "Name as the picker shows it"],
    ) -> dict[str, str]:
        """An agent id carries its class and instance; anything else is a model and names itself."""
        if base_id.startswith(AIHUB_PIPELINE_PREFIX):
            parts = base_id[len(AIHUB_PIPELINE_PREFIX) :].split(".", 1)
            if len(parts) == 2:
                # The LLM an agent picks comes from its own configuration at run time, so the
                # platform cannot name it here — the form says "if applicable" for that reason.
                return {"agent_class": parts[0], "agent_name": parts[1], "model": ""}
        return {"agent_class": "", "agent_name": "", "model": display_name or base_id}

    async def inlet(
        self,
        body: Annotated[dict[str, Any], "Request body"],
        __metadata__: Annotated[dict[str, Any] | None, "Request metadata"] = None,
        __model__: Annotated[dict[str, Any] | None, "Model OpenWebUI resolved"] = None,
        __event_call__: Annotated[Any, "Event caller"] = None,
    ) -> dict[str, Any]:
        if not __event_call__:
            return body

        model_id = str(body.get("model") or "")
        display_name = str((__model__ or {}).get("name") or "")
        described = self._describe(await self._resolve_base_id(model_id), display_name)

        # json.dumps because these values end up inside a script the browser runs, and a model
        # name is third-party data.
        code = f"""
        window.parent.postMessage({{
            type: 'set-model-context',
            display_id: {json.dumps(self._display_id((__metadata__ or {}).get("message_id")))},
            agent_class: {json.dumps(described["agent_class"])},
            agent_name: {json.dumps(described["agent_name"])},
            model: {json.dumps(described["model"])},
        }}, {json.dumps(self.valves.AIHUB_FRONTEND_URL)});
        """
        try:
            await __event_call__({"type": "execute", "data": {"code": code}})
        except Exception as publish_error:
            # The answer the user asked for matters more than the context a later report carries.
            logger.warning(f"Failed to publish UI context: {publish_error}")

        return body
