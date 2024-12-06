from typing import Optional, Dict, Type

from pydantic import BaseModel, Field

from lib_core.i18n.LocaleString import LocaleString


class StepConfig(BaseModel):
    pass


class AgentConfig(BaseModel):
    agent_id: str = Field(..., description="The id of the agent.")
    name: LocaleString = Field(..., description="The name of the agent.")
    description: LocaleString = Field(..., description="The description of the agent.")
    system_prompt: LocaleString = Field(..., description="The system prompt of the agent.")
    color: Optional[str] = Field("#10A37F", description="The color of the agent.")
    voice: Optional[str] = Field("de-DE-ChristophNeural", description="The voice of the agent.")

    def get_step_configs(self) -> Dict[Type[StepConfig], StepConfig]:
        step_configs = {}
        for field_name in self.model_fields.keys():
            field_value = getattr(self, field_name, None)
            if isinstance(field_value, StepConfig):
                step_configs[type(field_value)] = field_value
        return step_configs
