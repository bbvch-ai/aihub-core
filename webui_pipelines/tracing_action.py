"""
title: Tracing
description: Opens tracing-view in AI-Hub
icon_url: data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0Ij48cGF0aCBmaWxsPSJjdXJyZW50Q29sb3IiIGQ9Ik0xOCAxNmgtLjU4bC0uODEtLjgxQTcuMDcgNy4wNyAwIDAgMCAxOCAxMWMwLTMuODctMy4xMy03LTctN2MtMS41IDAtMyAuNS00LjIxIDEuNGMtMy4wOSAyLjMyLTMuNzIgNi43MS0xLjQgOS44czYuNzEgMy43MiA5LjggMS40bC44MS44MVYxOGw1IDVsMi0yem0tNyAwYy0yLjc2IDAtNS0yLjI0LTUtNXMyLjI0LTUgNS01czUgMi4yNCA1IDVzLTIuMjQgNS01IDVNMyA2TDEgOFYxaDdMNiAzSDN6bTE4LTV2N2wtMi0yVjNoLTNsLTItMnpNNiAxOWwyIDJIMXYtN2wyIDJ2M3oiLz48L3N2Zz4=
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
                type: 'show-traces',
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
