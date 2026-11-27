from typing import Annotated, Any

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler


class AgentToolArguments(BaseModel):
    """What the model passes when it asks a conversational agent."""

    message: Annotated[str, Field(description="The request to the agent.", min_length=1)]

    @staticmethod
    def schema_for(t: LocaleHandler) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {"message": {"type": "string", "description": t("agent.agent_tools.tool.message")}},
            "required": ["message"],
        }
