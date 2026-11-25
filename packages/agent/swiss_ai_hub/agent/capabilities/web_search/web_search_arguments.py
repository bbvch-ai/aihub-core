from typing import Annotated, Any

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler

MAX_QUERIES = 3


class WebSearchArguments(BaseModel):
    """What the model passes when it chooses to search the web."""

    queries: Annotated[
        list[str], Field(description="What to search for, one query per topic.", min_length=1, max_length=MAX_QUERIES)
    ]

    @staticmethod
    def schema_for(t: LocaleHandler) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "queries": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                    "maxItems": MAX_QUERIES,
                    "description": t("agent.web_search.tool.queries", max_queries=MAX_QUERIES),
                },
            },
            "required": ["queries"],
        }
