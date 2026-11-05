from typing import Annotated, Any

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler


class WebFetchArguments(BaseModel):
    """What the model passes when it chooses to read web pages."""

    urls: Annotated[list[str], Field(description="The pages to read, by URL.", min_length=1)]

    @staticmethod
    def schema_for(t: LocaleHandler) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "urls": {"type": "array", "items": {"type": "string"}, "description": t("agent.web_fetch.tool.urls")},
            },
            "required": ["urls"],
        }
