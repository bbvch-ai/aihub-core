from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.discovery.EventSpecs import EventSpecs
from swiss_ai_hub.core.events.process.discovery.program_in.ProgramInSpecs import ProgramInSpecs
from swiss_ai_hub.core.persistence.process.ProcessClassEntity import ProgramInSpecsEntity


class ProgramInDTO(BaseModel):
    route: Annotated[str, Field(description="The route of the work event.")]
    method: Annotated[str, Field(description="The HTTP method of the work event.")]
    is_process_start: Annotated[bool, Field(description="Whether the work event is a process start event.")]
    event_specs: Annotated[EventSpecs, Field(description="The event specs of the work event.")]

    @classmethod
    def from_program_in_specs(cls, program_in_specs: ProgramInSpecs) -> Self:
        return cls(
            route=program_in_specs.route,
            method=program_in_specs.method,
            is_process_start=program_in_specs.is_process_start,
            event_specs=program_in_specs.event_specs,
        )

    @classmethod
    def from_entity_specs(cls, program_in_specs_entity: ProgramInSpecsEntity) -> Self:
        return cls(
            route=program_in_specs_entity.route,
            method=program_in_specs_entity.method,
            is_process_start=program_in_specs_entity.is_process_start,
            event_specs=EventSpecs(
                event_name=program_in_specs_entity.event_specs.event_name,
                event_schema=program_in_specs_entity.event_specs.event_schema,
                event_parents=program_in_specs_entity.event_specs.event_parents,
            ),
        )
