from typing import Annotated, Any

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler


class KnowledgeSearchArguments(BaseModel):
    """What the model passes when it chooses to search our knowledge."""

    query: Annotated[str, Field(description="What to search for.", min_length=1)]
    collections: Annotated[
        list[str] | None, Field(description="Which of the offered collections to search; all of them when omitted.")
    ] = None

    @staticmethod
    def schema_for(collection_ids: list[str], t: LocaleHandler) -> dict[str, Any]:
        """The schema the model sees, the offered collections spelled out so it can only pick among them."""
        return {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": t("agent.knowledge.tool.query")},
                "collections": {
                    "type": "array",
                    "items": {"type": "string", "enum": collection_ids},
                    "description": t("agent.knowledge.tool.collections"),
                },
            },
            "required": ["query"],
        }
