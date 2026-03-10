from typing import TYPE_CHECKING, Annotated, Any, Self

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from swiss_ai_hub.core.processes.ProcessConfig import ProcessConfig


class ProcessConfigSpecs(BaseModel):
    """
    Validation specification for process configuration form submissions.

    Contains the process class identifier and JSON schema for validation.
    Instance-level fields (name, description, icon, process_id) are stored
    separately in ProcessConfigEntityDocument and provided by the Process class.

    The JSON schema is generated from the process's configurable fields via
    to_configurable_submission_model() and is used to validate form submissions.
    """

    process_class: Annotated[str, Field(description="The class name of the process.")] = ""
    process_config_schema: Annotated[
        dict[str, Any],
        Field(
            description="JSON schema for validating form submissions. "
            "Generated from the process's configurable fields via to_configurable_submission_model().",
        ),
    ] = {}

    @classmethod
    def from_process_config(cls, process_config: "ProcessConfig", process_class: str) -> Self:
        """
        Creates a ProcessConfigSpecs from a ProcessConfig instance.

        Extracts the JSON schema from the configurable submission model.
        Instance-level metadata (name, description, icon, process_id) is NOT included -
        those come from the Process class definition or ProcessConfigEntityDocument.
        """
        submission_model = process_config.to_configurable_submission_model()

        return cls(
            process_class=process_class,
            process_config_schema=submission_model.model_json_schema(),
        )

    @classmethod
    def from_process_config_class(cls, process_config_class: type["ProcessConfig"]) -> Self:
        """Legacy method: Creates specs from the full class schema (not instance-based)."""
        return cls(
            process_config_schema=process_config_class.model_json_schema(),
        )
