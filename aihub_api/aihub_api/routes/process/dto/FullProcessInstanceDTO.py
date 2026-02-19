from typing import TYPE_CHECKING, Annotated, Any, Self

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.nats.events.discovery.process.agent_in.AgentInSpecs import AgentInSpecs
from aihub_lib.nats.events.discovery.process.human_in.HumanInSpecs import HumanInSpecs
from aihub_lib.nats.events.discovery.process.ProcessConfigSpecs import ProcessConfigSpecs
from aihub_lib.nats.events.discovery.process.program_in.ProgramInSpecs import ProgramInSpecs
from aihub_lib.nats.events.form import ALL_FORM_OPTIONS
from pydantic import Field

from aihub_api.routes.process.dto.MinimalProcessInstanceDTO import MinimalProcessInstanceDTO
from aihub_api.routes.process.dto.ProcessConfigDTO import ProcessConfigDTO

if TYPE_CHECKING:
    from aihub_lib.persistence.process.ProcessClassEntity import ProcessClassEntity
    from aihub_lib.persistence.process.ProcessConfigEntityDocument import ProcessConfigEntityDocument


class FullProcessInstanceDTO(MinimalProcessInstanceDTO):
    """
    A data transfer object for representing FULL process INSTANCE information in responses.
    Combines class metadata and instance-specific data.

    NOTE: This represents an INSTANCE (with process_id), not a process CLASS.
    For minimal instance data, use MinimalProcessInstanceDTO.
    For class-level data only, use ProcessClassDTO.
    """

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
    process_config_specs: Annotated[
        ProcessConfigSpecs,
        Field(description="Configuration specifications of the process class, including schema and parameters."),
    ]
    form: Annotated[
        list[ALL_FORM_OPTIONS],
        Field(
            description="FormKit elements defining the process configuration form. "
            "Default values are embedded in the elements themselves.",
        ),
    ]
    configuration: Annotated[
        dict[str, Any],
        Field(
            description="The saved configuration data for this process instance. "
            "Contains the actual values that were submitted via the configuration form.",
        ),
    ] = {}

    @classmethod
    def from_class_and_config(
        cls,
        class_entity: "ProcessClassEntity",
        config_entity: "ProcessConfigEntityDocument",
        t: LocaleHandler,
    ) -> Self:
        """
        Creates a FullProcessInstanceDTO from a class entity and a config entity.
        Class entity provides class-level data (inputs, specs, form), config entity provides instance data.
        """
        process_config_dto = ProcessConfigDTO(
            process_id=config_entity.process_id,
            name=t.extract(config_entity.name.to_locale_string()),
            description=t.extract(config_entity.description.to_locale_string()),
            icon=config_entity.icon,
        )

        process_config_specs = (
            class_entity.process_config_specs.to_specs() if class_entity.process_config_specs else ProcessConfigSpecs()
        )

        return cls(
            process_class=class_entity.process_class,
            process_id=config_entity.process_id,
            process_config=process_config_dto,
            is_online=class_entity.is_online,
            human_inputs=[specs.to_specs() for specs in class_entity.human_inputs],
            program_inputs=[specs.to_specs() for specs in class_entity.program_inputs],
            agent_inputs=[specs.to_specs() for specs in class_entity.agent_inputs],
            process_config_specs=process_config_specs,
            form=class_entity.form_elements,
            configuration=config_entity.config_data or {},
        )
