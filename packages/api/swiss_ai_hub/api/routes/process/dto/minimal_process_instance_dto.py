from typing import TYPE_CHECKING, Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler

from swiss_ai_hub.api.routes.process.dto.process_config_dto import ProcessConfigDTO

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.process import ProcessClassEntity
    from swiss_ai_hub.core.persistence.process.process_config_entity_document import ProcessConfigEntityDocument


class MinimalProcessInstanceDTO(BaseModel):
    """
    Encapsulates the data transfer object (DTO) for a minimal process INSTANCE.
    Only contains minimal information about a specific process instance.

    NOTE: This represents an INSTANCE (with process_id), not a process CLASS.
    For class-level data only, use ProcessClassDTO.
    """

    process_class: Annotated[str, Field(description="The process's class identifier (e.g., 'my_process_class').")]
    process_id: Annotated[str, Field(description="Unique identifier for the process instance (e.g., 'process_123').")]
    process_config: Annotated[
        ProcessConfigDTO,
        Field(description="Configuration details of the process, including name, description, and icon."),
    ]
    is_online: Annotated[
        bool | None, Field(description="Indicates whether the process class is online and reachable.")
    ] = None

    @classmethod
    def from_class_and_config(
        cls,
        class_entity: "ProcessClassEntity",
        config_entity: "ProcessConfigEntityDocument",
        t: LocaleHandler,
    ) -> Self:
        """
        Creates a MinimalProcessInstanceDTO from a class entity and a config entity.
        Class entity provides is_online, config entity provides instance-specific data.
        """
        process_config_dto = ProcessConfigDTO(
            process_id=config_entity.process_id,
            name=t.extract_required(config_entity.name.to_locale_string(), field_name="process.name"),
            description=t.extract_required(config_entity.description.to_locale_string(), field_name="process.description"),
            icon=config_entity.icon,
        )
        return cls(
            process_class=class_entity.process_class,
            process_id=config_entity.process_id,
            process_config=process_config_dto,
            is_online=class_entity.is_online,
        )
