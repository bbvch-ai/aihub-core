from typing import Annotated

from pydantic import Field
from swiss_ai_hub.core.form.form import Form

from swiss_ai_hub.agent.capabilities.agent_tools.agent_tools_config import AgentToolsConfig


class AgentToolFields(Form):
    """The agent-calling setting a blueprint's config gains by listing this mixin as a base; off unless set."""

    agent_tools: Annotated[
        AgentToolsConfig | None,
        Field(
            description="Let the model ask other agents the user may use, each offered as a tool.",
            title="Ask Other Agents",
        ),
    ] = None
