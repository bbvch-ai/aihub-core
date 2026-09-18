"""
title: Report a bug
description: Reports a problem with this answer to AI-Hub support
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSJjdXJyZW50Q29sb3IiIGQ9Ik0yMCA4aC0yLjgxYy0uNDUtLjc4LTEuMDctMS40NS0xLjgyLTEuOTZMMTcgNC40MUwxNS41OSAzbC0yLjE3IDIuMTdDMTIuOTYgNS4wNiAxMi40OSA1IDEyIDVzLS45Ni4wNi0xLjQxLjE3TDguNDEgM0w3IDQuNDFsMS42MiAxLjYzQzcuODggNi41NSA3LjI2IDcuMjIgNi44MSA4SDR2MmgyLjA5Yy0uMDUuMzMtLjA5LjY2LS4wOSAxdjFINHYyaDJ2MWMwIC4zNC4wNC42Ny4wOSAxSDR2MmgyLjgxYzEuMDQgMS43OSAyLjk3IDMgNS4xOSAzczQuMTUtMS4yMSA1LjE5LTNIMjB2LTJoLTIuMDljLjA1LS4zMy4wOS0uNjYuMDktMXYtMWgydi0yaC0ydi0xYzAtLjM0LS4wNC0uNjctLjA5LTFIMjB6bS02IDhoLTR2LTJoNHptMC00aC00di0yaDR6Ii8+PC9zdmc+
required_open_webui_version: 0.6.0
"""

import json
import os

from pydantic import BaseModel, Field
from typing import Optional, Annotated

import hashlib
import logging

from bson import ObjectId

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

    def _resolve_model(
        self,
        body: Annotated[dict, "Action body"],
        model: Annotated[Optional[dict], "Model injected by OpenWebUI"],
    ) -> Annotated[str, "Model identifier, empty when unknown"]:
        """Name the model that produced this answer.

        OpenWebUI injects `__model__` for actions, but the shape has moved between versions and the message itself
        carries the id on some paths, so both are tried before giving up — an empty value only leaves one form field
        blank, which the reporter can still fill in by hand.
        """
        if isinstance(model, dict):
            resolved = model.get("id") or model.get("name")
            if resolved:
                return str(resolved)
        return str(body.get("model") or "")

    async def action(
        self,
        body: dict,
        __user__=None,
        __model__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> dict | None:
        message_id = body.get("id")

        display_id = self._str_to_object_id(message_id)

        try:
            # json.dumps rather than f-string interpolation: a model identifier is
            # third-party data and must not be able to terminate this script.
            code = f"""
            window.parent.postMessage({{
                type: 'report-issue',
                display_id: {json.dumps(display_id)},
                model: {json.dumps(self._resolve_model(body, __model__))},
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
