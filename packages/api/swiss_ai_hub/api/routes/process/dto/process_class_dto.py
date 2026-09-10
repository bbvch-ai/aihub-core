from typing import TYPE_CHECKING, Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.events.process import (
    AgentInSpecs,
    HumanInSpecs,
    ProcessClassDiscoveryResponseEvent,
    ProgramInSpecs,
)
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS, ConfigSpecs, TemplateData
from swiss_ai_hub.core.i18n import LocaleString

if TYPE_CHECKING:
    from swiss_ai_hub.core.i18n import LocaleHandler
    from swiss_ai_hub.core.persistence.process import ProcessClassEntity


class ProcessClassDTO(BaseModel):
    """
    Encapsulates the data transfer object (DTO) for a process class.
    Contains class-level metadata (name, description, icon, form) and configuration specifications.
    """

    process_class: Annotated[str, Field(description="The process's class identifier (e.g., 'my_process_class').")]
    name: Annotated[LocaleString, Field(description="Display name for this process class.")]
    description: Annotated[LocaleString, Field(description="Description of this process class.")]
    icon: Annotated[str, Field(description="Icon for this process class.")] = "mage:broadcast"
    form: Annotated[list[ALL_FORM_OPTIONS], Field(description="FormKit elements defining the configuration form.")]
    process_config_specs: Annotated[
        ConfigSpecs,
        Field(description="Configuration specifications of the process class, including schema and parameters."),
    ]
    human_inputs: Annotated[
        list[HumanInSpecs], Field(description="List of human work events that the process can receive.")
    ]
    program_inputs: Annotated[
        list[ProgramInSpecs], Field(description="List of program work events that the process can receive.")
    ]
    agent_inputs: Annotated[
        list[AgentInSpecs],
        Field(
            description="List of agent work events that the process can receive. "
            "Agent work events are used to trigger the execution of an agent."
        ),
    ]
    is_online: Annotated[
        bool | None, Field(description="Indicates whether the process class is online and reachable.")
    ] = None
    templates: Annotated[
        list[TemplateData],
        Field(description="List of profile templates for quick profile creation."),
    ] = []

    @classmethod
    def from_discovery_event(
        cls,
        event: ProcessClassDiscoveryResponseEvent,
    ) -> Self:
        """Converts a ProcessClassDiscoveryResponseEvent to a ProcessClassDTO."""
        return cls(
            process_class=event.process_class,
            name=event.name,
            description=event.description,
            icon=event.icon,
            form=event.form,
            process_config_specs=event.process_config_specs,
            human_inputs=event.human_inputs,
            program_inputs=event.program_inputs,
            agent_inputs=event.agent_inputs,
            is_online=True,
            templates=event.templates,
        )

    @classmethod
    def from_entity(
        cls,
        entity: "ProcessClassEntity",
        t: "LocaleHandler",
    ) -> Self:
        """Converts a ProcessClassEntity to a ProcessClassDTO."""
        return cls(
            process_class=entity.process_class,
            name=entity.name.to_locale_string() if entity.name else LocaleString(en=entity.process_class),
            description=entity.description.to_locale_string() if entity.description else LocaleString(en=""),
            icon=entity.icon,
            form=entity.form_elements,
            process_config_specs=(
                entity.process_config_specs.to_specs() if entity.process_config_specs else ConfigSpecs()
            ),
            human_inputs=[],
            program_inputs=[],
            agent_inputs=[],
            is_online=entity.is_online,
            templates=[TemplateData.model_validate(td) for td in entity.templates] if entity.templates else [],
        )
