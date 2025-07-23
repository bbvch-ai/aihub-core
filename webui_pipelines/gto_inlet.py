"""
title: GTO inlet
author: Noah Hermann
version: 0.1.0
"""

from typing import Optional

import requests
from pydantic import BaseModel, Field

query_prompt = """Based on the following question generate a standalone quey, that 
can be used to search for data transfer objects. <question>{question}</question>"""


class Filter:
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

    async def inlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__=None) -> dict:
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": "GTO Daten werden geladen...",
                        "done": False,
                    },
                }
            )
        headers = {
            "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"{self.valves.LCDM_HUB_BASE_URL}availablenames",
            headers=headers,
        )
        if response.status_code == 200:
            names = eval(response.text)

            gto_text = f"\n\n<GTO_SCHEMAS>{dict_to_md_table(names)}</GTO_SCHEMAS>"
        else:
            raise Exception(f"Failed to fetch GTO data: {response.status_code} - {response.text}")

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {"description": "GTO Daten sind bereit!", "done": True},
                }
            )

        context_message = {
            "role": "system",
            "content": gto_text,
        }

        body.setdefault("messages", []).insert(0, context_message)

        return body


def dict_to_md_table(data):
    """Convert dictionary to markdown table (key-value format)"""
    md = "| ID | Name |\n|-----|-------|\n"
    for key, value in data:
        md += f"| {key} | {value} |\n"
    return md
