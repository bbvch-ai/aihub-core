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
        self.gto_text = None

    def inlet(self, body: dict, __user__: Optional[dict] = None) -> dict:

        if not self.gto_text:
            self.get_gto_data()

        messages = body.get("messages", [])

        gto_system_message = {"role": "system", "content": self.gto_text}

        messages.insert(0, gto_system_message)

        body["messages"] = messages

        return body

    def get_gto_data(self):
        if self.gto_text:
            return self.gto_text

        headers = {
            "Authorization": f"Bearer {self.valves.LCDM_HUB_TOKEN}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        response = requests.get(
            f"{self.valves.LCDM_HUB_BASE_URL}availablenames",
            headers=headers,
        )
        names = response.text
        names_list = eval(names)

        gto_definitions = []
        for key, value in names_list:
            r = requests.get(
                f"{self.valves.LCDM_HUB_BASE_URL}{key}",
                headers=headers,
            )
            gto_definitions.append(r.json())

        self.gto_text = f"\n\n<GTO_SCHEMAS>{dict_to_md_table(names_list)}</GTO_SCHEMAS>\n\n<GTO_definitions>{gto_definitions}</GTO_definitions>"


def dict_to_md_table(data):
    """Convert dictionary to markdown table (key-value format)"""
    md = "| ID | Name |\n|-----|-------|\n"
    for key, value in data:
        md += f"| {key} | {value} |\n"
    return md
