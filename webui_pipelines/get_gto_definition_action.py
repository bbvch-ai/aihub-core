from typing import Optional, Any

import requests
from pydantic import BaseModel, Field


class Action:
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

    async def action(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Any] = None,
        __event_call__: Optional[Any] = None,
    ) -> Optional[dict]:
        gto_id = await __event_call__(
            {
                "type": "input",
                "data": {
                    "title": "GTO ID",
                    "message": "Bitte geben Sie die GTO ID ein.",
                    "placeholder": "Bsp. 73933488",
                },
            }
        )

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
                return body

        names = response.json()
        keys = [key for key, value in names]
        if gto_id in keys:
            r = requests.get(
                f"{self.valves.LCDM_HUB_BASE_URL}{gto_id}",
                headers=headers,
                timeout=10,
            )

            context_message = {
                "role": "system",
                "content": f"<GTO_DEFINITION>{r.json()}</GTO_DEFINITION>",
            }

            body.setdefault("messages", []).insert(0, context_message)

            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "GTO Schema gefunden!", "done": True},
                    }
                )

                await __event_emitter__(
                    {
                        "type": "message",
                        "data": {"content": f"<GTO_DEFINITION>{r.json()}</GTO_DEFINITION>"},
                    }
                )
        else:
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {"description": "GTO ID ist ungültig!", "done": True},
                    }
                )

        return body
