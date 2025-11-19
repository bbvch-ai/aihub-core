from typing import Annotated

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.EventSpecs import EventSpecs
from aihub_lib.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS
from aihub_lib.persistence.process.ProcessEntity import HumanInSpecsEntity
from pydantic import BaseModel, Field


class HumanInDTO(BaseModel):
    name: Annotated[str, Field(description="The name of the work event.")]
    description: Annotated[
        str, Field(description="A description of the work event, providing details about its purpose.")
    ]
    route: Annotated[str, Field(description="The route of the work event.")]
    method: Annotated[str, Field(description="The HTTP method of the work event.")]
    is_process_start: Annotated[bool, Field(description="Whether the work event is a process start event.")]
    event_specs: Annotated[EventSpecs, Field(description="The event specs of the work event.")]
    form: Annotated[list[ALL_FORM_OPTIONS], Field(description="Formkit elements of the work event.")] = []

    @classmethod
    def from_human_in_specs(cls, human_in_specs: HumanInSpecs, t: LocaleHandler) -> "HumanInDTO":
        human_in_dto = cls(
            name=t.extract(human_in_specs.name),
            description=t.extract(human_in_specs.description),
            route=human_in_specs.route,
            method=human_in_specs.method,
            is_process_start=human_in_specs.is_process_start,
            event_specs=human_in_specs.event_specs,
            form=human_in_specs.form,
        )
        human_in_dto.form = [form.in_locale(t) for form in human_in_dto.form]
        return human_in_dto

    @classmethod
    def from_entity_specs(cls, human_in_specs_entity: HumanInSpecsEntity, t: LocaleHandler) -> "HumanInDTO":
        human_in_dto = cls(
            name=t.extract(human_in_specs_entity.name.to_locale_string()),
            description=t.extract(human_in_specs_entity.description.to_locale_string()),
            route=human_in_specs_entity.route,
            method=human_in_specs_entity.method,
            is_process_start=human_in_specs_entity.is_process_start,
            event_specs=EventSpecs(
                event_name=human_in_specs_entity.event_specs.event_name,
                event_schema=human_in_specs_entity.event_specs.event_schema,
                event_parents=human_in_specs_entity.event_specs.event_parents,
            ),
            form=human_in_specs_entity.form,
        )
        human_in_dto.form = [form.in_locale(t) for form in human_in_dto.form]
        return human_in_dto
