from typing import Annotated

from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from pydantic import BaseModel, Field


class AgentConfigDTO(BaseModel):
    agent_id: Annotated[str, Field(description="The id of the agent.")]
    name: Annotated[str, Field(description="The name of the agent.")]
    description: Annotated[str, Field(description="The description of the agent.")]
    color: Annotated[str, Field(description="The color of the agent UI theme.")] = "#10A37F"
    voice: Annotated[str, Field(description="The TTS voice ID the agent uses.")] = "de-DE-ChristophNeural"
    icon: Annotated[str, Field(description="The icon representing the agent.")] = "meteor-icons:robot"

    @classmethod
    def from_agent_config(cls, agent_config: AgentConfig, t: LocaleHandler) -> "AgentConfigDTO":
        return cls(
            agent_id=agent_config.agent_id,
            name=t.extract(agent_config.name),
            description=t.extract(agent_config.description),
            color=agent_config.color,
            voice=agent_config.voice,
            icon=agent_config.icon,
        )
