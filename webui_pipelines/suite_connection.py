from pydantic import BaseModel, Field
from typing import Optional, Union, Generator, Iterator

import json
import os
import requests
import asyncio
import hashlib

from bson import ObjectId


def str_to_object_id(context_id: Optional[str]) -> ObjectId:
    if not context_id:
        return ObjectId()
    hashed = hashlib.md5(context_id.encode()).digest()[:12]
    return str(ObjectId(hashed))


class Action:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()
        pass

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> Optional[dict]:
        try:
            print("body", body)

            code = f"""
            window.parent.postMessage({{
                type: 'show-sources',
                thread_id: '{str_to_object_id(body.get("chat_id"))}',
                display_id: '{str_to_object_id(body.get("id"))}',
              }}, 'http://localhost:3000');
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
            print(e)
