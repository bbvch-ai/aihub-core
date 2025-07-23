"""
title: Get GTO Definition Tool
author: Noah Hermann
description: Retrieves GTO Definition based on ID passed to the tool, by passing {"gto_id": "some_gto_id"} to the tool.
version: 0.1.0
"""

from typing import Optional, Any

import requests
from pydantic import BaseModel, Field


class Tools:

    class Valves(BaseModel):
        LCDM_HUB_BASE_URL: str = Field(
            default="https://dev.swisslcdmhub.bbv.ch/restapi/1.0/gto/",
            description="URL for accessing LCDM Hub API endpoints.",
        )
        LCDM_HUB_TOKEN: str = Field(
            default="",
            description="Token to authenticate requests to the LCDM Hub API.",
        )

    def __init__(self):
        self.valves = self.Valves()

    async def get_gto_definition(
        self,
        gto_id: str,
        __event_emitter__: Optional[Any] = None,
    ) -> str:
        """
        Retrieves a GTO definition string and returns it to use in the chat.

        Args:
            gto_id (str): The GTO type identifier.

        Returns:
            str: Result message with GTO definition or failure message.
        """

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "GTO Schema wird gesucht...",
                        "done": False,
                    },
                }
            )

        try:
            headers = {
                "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            response = requests.get(
                f"{self.valves.LCDM_HUB_BASE_URL}availablenames",
                headers=headers,
            )

            names = response.json()
            keys = [key for key, value in names]
            if gto_id in keys:
                r = requests.get(
                    f"{self.valves.LCDM_HUB_BASE_URL}{gto_id}",
                    headers=headers,
                    timeout=10,
                )

                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "GTO Schema gefunden!",
                                "done": True,
                            },
                        }
                    )

                return f"<GTO_DEFINITION>{r.json()}</GTO_DEFINITION>"

            else:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "GTO ID ist ungültig!",
                                "done": True,
                            },
                        }
                    )

                return "GTO ID ist ungültig!"

        except Exception as e:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": f"Ein Fehler ist aufgetreten: {e}",
                            "done": True,
                        },
                    }
                )
                return f"Ein Fehler ist aufgetreten: {e}"
