"""
title: My Files
description: Open your files, starting with this chat's attachments and the files agents made in it
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIGZpbGw9Im5vbmUiIHZpZXdCb3g9IjAgMCAyNCAyNCIgc3Ryb2tlLXdpZHRoPSIxLjUiIHN0cm9rZT0iY3VycmVudENvbG9yIj48cGF0aCBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiIGQ9Ik0yLjI1IDEyLjc1VjEyQTIuMjUgMi4yNSAwIDAgMSA0LjUgOS43NWgxNWEyLjI1IDIuMjUgMCAwIDEgMi4yNSAyLjI1di43NW0tOC42OS02LjQ0LTIuMTItMi4xMmExLjUgMS41IDAgMCAwLTEuMDYxLS40NEg0LjVBMi4yNSAyLjI1IDAgMCAwIDIuMjUgNnYxMmEyLjI1IDIuMjUgMCAwIDAgMi4yNSAyLjI1aDE1QTIuMjUgMi4yNSAwIDAgMCAyMS43NSAxOFY5YTIuMjUgMi4yNSAwIDAgMC0yLjI1LTIuMjVoLTUuMzc5YTEuNSAxLjUgMCAwIDEtMS4wNi0uNDRaIiAvPjwvc3ZnPg==
required_open_webui_version: 0.6.0
"""

import hashlib
import logging
import os
from typing import Annotated, Optional

from bson import ObjectId
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Action:
    class Valves(BaseModel):
        AIHUB_FRONTEND_URL: str = Field(
            default=os.getenv("AIHUB_FRONTEND_URL", "http://localhost:3333"),
            description="Base URL for the AI-Hub frontend",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _str_to_object_id(
        self, context_id: Annotated[Optional[str], "Context ID to hash"]
    ) -> Annotated[str, "ObjectId string"]:
        """Convert a string to an ObjectId by hashing it with MD5.

        Mirrors the producing pipe's `_str_to_object_id` exactly (empty-salt form `md5(":" + context_id)`) so the
        `display_id` matches the persisted events the AI-Hub frontend resolves the thread from.
        """
        if not context_id:
            return str(ObjectId())
        hashed = hashlib.md5(f":{context_id}".encode()).digest()[:12]
        return str(ObjectId(hashed)).lower()

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> dict | None:
        message_id = body.get("id")

        display_id = self._str_to_object_id(message_id)

        try:
            code = f"""
            window.parent.postMessage({{
                type: 'show-files',
                display_id: '{display_id}',
            }}, '{self.valves.AIHUB_FRONTEND_URL}');
            """

            await __event_call__(
                {
                    "type": "execute",
                    "data": {
                        "code": code,
                    },
                }
            )
        except Exception as e:
            logger.error(e)
