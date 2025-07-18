"""
title: Sources
description: Opens source-view in AI-Hub
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSJjdXJyZW50Q29sb3IiIGQ9Ik0xNS43NSAxM2EuNzUuNzUgMCAwIDAtLjc1LS43NUg5YS43NS43NSAwIDAgMCAwIDEuNWg2YS43NS43NSAwIDAgMCAuNzUtLjc1bTAgNGEuNzUuNzUgMCAwIDAtLjc1LS43NUg5YS43NS43NSAwIDAgMCAwIDEuNWg2YS43NS43NSAwIDAgMCAuNzUtLjc1Ii8+PHBhdGggZmlsbD0iY3VycmVudENvbG9yIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiIGQ9Ik03IDIuMjVBMi43NSAyLjc1IDAgMCAwIDQuMjUgNXYxNEEyLjc1IDIuNzUgMCAwIDAgNyAyMS43NWgxMEEyLjc1IDIuNzUgMCAwIDAgMTkuNzUgMTlWNy45NjhjMC0uMzgxLS4xMjQtLjc1MS0uMzU0LTEuMDU1bC0yLjk5OC0zLjk2OGExLjc1IDEuNzUgMCAwIDAtMS4zOTYtLjY5NXpNNS43NSA1YzAtLjY5LjU2LTEuMjUgMS4yNS0xLjI1aDcuMjV2NC4zOTdjMCAuNDE0LjMzNi43NS43NS43NWgzLjI1VjE5YzAgLjY5LS41NiAxLjI1LTEuMjUgMS4yNUg3Yy0uNjkgMC0xLjI1LS41Ni0xLjI1LTEuMjV6IiBjbGlwLXJ1bGU9ImV2ZW5vZGQiLz48L3N2Zz4=
required_open_webui_version: 0.6.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator, Annotated

import json
import os
import requests
import asyncio
import hashlib
import logging

from bson import ObjectId

logger = logging.getLogger(__name__)

def str_to_object_id(context_id: str | None) -> ObjectId:
    if not context_id:
        return ObjectId()
    hashed = hashlib.md5(context_id.encode()).digest()[:12]
    return str(ObjectId(hashed))


class Action:
    class Valves(BaseModel):
        AIHUB_FRONTEND_BASE_URL: Annotated[str, Field(
            description="Base URL for accessing AI-Hub Suite Frontend.",
        )] = "http://localhost:3000"

    def __init__(self):
        self.valves = self.Valves()
        pass

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> dict | None:
        try:
            code = f"""
            window.parent.postMessage({{
                type: 'show-sources',
                thread_id: '{str_to_object_id(body.get("chat_id"))}',
                display_id: '{str_to_object_id(body.get("id"))}',
              }}, '{self.valves.AIHUB_FRONTEND_BASE_URL}');
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
