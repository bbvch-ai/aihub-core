from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events import EventSpecs
from swiss_ai_hub.core.events.process import AgentInSpecs
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.process.process_class_entity import AgentInSpecsEntity


class AgentInDTO(BaseModel):
    agent_class: Annotated[str, Field(description="The class or category of the agent.")]
    agent_id: Annotated[str, Field(description="A unique identifier for the agent instance.")]
    is_process_start: Annotated[bool, Field(description="Whether the work event is a process start event.")]
    event_specs: Annotated[EventSpecs, Field(description="The event specs of the work event.")]

    @classmethod
    def from_agent_in_specs(cls, agent_in_specs: AgentInSpecs, t: LocaleHandler) -> Self:
        return cls(
            agent_class=agent_in_specs.agent_class,
            agent_id=agent_in_specs.agent_id,
            is_process_start=agent_in_specs.is_process_start,
            event_specs=agent_in_specs.event_specs,
        )

    @classmethod
    def from_entity_specs(cls, agent_in_specs_entity: AgentInSpecsEntity, t: LocaleHandler) -> Self:
        return cls(
            agent_class=agent_in_specs_entity.agent_class,
            agent_id=agent_in_specs_entity.agent_id,
            is_process_start=agent_in_specs_entity.is_process_start,
            event_specs=EventSpecs(
                event_name=agent_in_specs_entity.event_specs.event_name,
                event_schema=agent_in_specs_entity.event_specs.event_schema,
                event_parents=agent_in_specs_entity.event_specs.event_parents,
            ),
        )
