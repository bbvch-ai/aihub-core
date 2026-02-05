"""
title: View Agent Memories
description: Display all memories collected by agents during this conversation
icon_url: data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAEBUlEQVR4AbSWWWxNURSGb02RmIUSksZYpYaaikgRJSU0XoS+1NAIJRpDePFAQipemhiCmqolUdIHQrRpmlCkD6UI1WoJIR76UCqkaKp6ff/J3de57blDr96b9Z219lp7r73OPufus3u4IvRzu90r4DH0DjRFxApg0r0wF1aBX+lSAdzNMEiEIX4zEiA+BbUUJDt08UdIBZAwBspI0giV0ET7GSRg+wg+LfkZnD1BshzfehlOBC2AwYMYWA7LQFLN5RfMhHLi49EudA9Iwq6CxWCXQmI5MNLulB20ADqlwlh4DdFRUVHT0YPhFKi4zyTeit0ED0FxlI9E0dI70UDflzCRtiUBC6DjKHptAck1JtcjcKFbcZwDid4Ht4wQMY/G6u5YABOPgIv0+AhmOe9je4UiajyNXOwL2ENhETwFJ1HBMfSNh7emg2MBBIsgA67DJkhgUAXaSVLkJN4Oj7DnQwnYJYNYJnyyO2V3KoA730lAL9MhBqRDAbzAF5LQt42OyvEbLanAd1mGE50KoFM6SK7oEg5M+J5xxSA5rYuBG9R7ZZoupwIGeqKdlsvjD1WdpaPek9toS5hc/4YnaO8/JVABo61RYV5YhVKYCj9sKfRotALZFNFLfqcCbikAB6BbhMlS4QHJToJkNZc6fEedCthP8ANk0qEYNkIS9MEXrujF7DhWj6PFqQBtlw2e3ivR+aAd7hg6LOExlID2E/NhukuiOHyHfQrgLmMI6C+3AP0H9BJp6e5hd/xv4+qaMKFeTL3c+otbf1OfAkinr1h/tO56OAP0Ei1BJ4O+hoT+W1LI5d0tvQV47l6Hh29MkUWnr+huFebYR8IZ6Di0Jd4CaOkQgXJVMXmzjAgwj5yFMA0ssRdgvlI/rUhkLn09ab17g70A/fUUn6RLhDCr/M7ktxegA0cdgVie0WZ0two5t5FwHLziEdejLfEWgLMdj9n98hhQCdshGn9YorGQBTpH5nqSmDmsprcAtSjiJlonIJ1wErH1t6whgQ6aNP8Jvn6mhT3A2Ebj016vO9X2q1y6wQ3Mccf0kfYpQA46XEKPgDTQZ3UYWud7lI/MsbWSbbYxF2Lo7KjnvQ47mtxX0T7SqQBF6dgIN7DN9nueO4qlbQn2GIwcMJKPz5yadUJWX7Pk2eQqgi+ms107FmDrkIddCvFQzyS18AZbKzMbraObDh46HZcRU7wWv5Zem42Wu4C2XwlYAFXre7CW0XqO2rsnY+tIrbs5QlxLuwbfCfgOiosW7OOQRh89e0xnCViAhpCgGXZh6xsxCz2Btr4TB7F1RG+jvRtbz1srpdPOQHx7IOimFrQAEltCslZ4DnqpLJ/9gt8NtVANWi172K8dcgF+MwQJBAv/BQAA//88V+daAAAABklEQVQDAA71WFD8uyvOAAAAAElFTkSuQmCC
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
            default=os.getenv("AIHUB_FRONTEND_URL", "http://localhost:3000"),
            description="Base URL for the AI-Hub frontend",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _str_to_object_id(
        self, context_id: Annotated[Optional[str], "Context ID to hash"]
    ) -> Annotated[str, "ObjectId string"]:
        """Convert a string to an ObjectId by hashing it with MD5."""
        if not context_id:
            return str(ObjectId())
        hashed = hashlib.md5(context_id.encode()).digest()[:12]
        return str(ObjectId(hashed)).lower()

    async def action(
        self,
        body: dict,
        __user__=None,
        __event_emitter__=None,
        __event_call__=None,
    ) -> dict | None:
        chat_id = body.get("chat_id")
        message_id = body.get("id")

        thread_id = self._str_to_object_id(chat_id)
        display_id = self._str_to_object_id(message_id)

        try:
            code = f"""
            window.parent.postMessage({{
                type: 'show-memories',
                thread_id: '{thread_id}',
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
