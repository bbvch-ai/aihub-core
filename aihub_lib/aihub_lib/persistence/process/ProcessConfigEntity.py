from typing import Self

from mongoengine import DictField, EmbeddedDocumentField, StringField
from mongoengine.base import BaseDocument

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity
from aihub_lib.processes.ProcessConfig import ProcessConfig


class ProcessConfigEntity(BaseDocument):
    """
    This is the base class for storing a process configuration.
    Never use this class directly; instead, use the `ProcessConfigEntityDocument` or
    `ProcessConfigEntityEmbeddedDocument`
    subclasses for persistence in MongoDB.
    This class is only used to define the common fields and methods for process configs.
    """

    process_class = StringField(required=True)
    process_id = StringField(
        required=True, description="Unique, URL-safe ID for the process instance (e.g., 'process_123')."
    )
    name = EmbeddedDocumentField(
        LocaleStringEntity, required=True, description="Name of the process, used for display in the UI."
    )
    description = EmbeddedDocumentField(
        LocaleStringEntity, required=True, description="Description of the process's purpose or functionality."
    )
    icon = StringField(required=True, description="Icon representing the process, e.g., 'meteor-icons:robot'.")
    config_data = DictField(required=True, description="The configuration data matching the Pydantic model.")

    @classmethod
    @trace_fn
    def from_process_config(cls, process_config: ProcessConfig) -> Self:
        """Create an instance entity from a ProcessConfig."""
        return cls(
            process_class=process_config.process_class,
            process_id=process_config.process_id,
            name=LocaleStringEntity.from_locale_string(process_config.name),
            description=LocaleStringEntity.from_locale_string(process_config.description),
            icon=process_config.icon,
            config_data=process_config.model_dump(),
        )

    @trace_fn
    def update_from_process_config(self, process_config: ProcessConfig) -> Self:
        """Update an existing instance entity from a ProcessConfig."""
        self.process_class = process_config.process_class
        self.process_id = process_config.process_id
        self.name = LocaleStringEntity.from_locale_string(process_config.name)
        self.description = LocaleStringEntity.from_locale_string(process_config.description)
        self.icon = process_config.icon
        self.config_data = process_config.model_dump()
        return self
