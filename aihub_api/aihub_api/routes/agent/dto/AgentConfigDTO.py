from aihub_lib.agents.AgentConfig import AgentConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from pydantic import BaseModel, Field


class AgentConfigDTO(BaseModel):
    agent_id: str = Field(..., description="The id of the agent.")
    name: str = Field(..., description="The name of the agent.")
    description: str = Field(..., description="The description of the agent.")
    system_prompt: str = Field(..., description="The system prompt of the agent.")
    color: str = Field("#10A37F", description="The color of the agent UI theme.")
    voice: str = Field("de-DE-ChristophNeural", description="The TTS voice ID the agent uses.")
    icon: str = Field("meteor-icons:robot", description="The icon representing the agent.")

    @classmethod
    def from_agent_config(cls, agent_config: AgentConfig, t: LocaleHandler) -> "AgentConfigDTO":
        return cls(
            agent_id=agent_config.agent_id,
            name=t.extract(agent_config.name),
            description=t.extract(agent_config.description),
            system_prompt=t.extract(agent_config.system_prompt),
            color=agent_config.color,
            voice=agent_config.voice,
            icon=agent_config.icon,
        )
