from typing import TYPE_CHECKING, Annotated, Any, Self

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from swiss_ai_hub.core.form.form import Form


class ConfigSpecs(BaseModel):
    """
    Validation specification for a form-duality configuration, as announced by the service that owns it.

    Carries only the JSON schema the API validates submissions against, so a configuration class defined in
    an agent, process or pipeline container can be enforced by the API without that class being installed there.
    """

    config_class: Annotated[str, Field(description="The class name of the configuration this schema describes.")] = ""
    config_schema: Annotated[
        dict[str, Any],
        Field(
            description="JSON schema for validating form submissions. "
            "Generated from the configuration's configurable fields via to_configurable_submission_model()."
        ),
    ] = {}

    @classmethod
    def from_form(cls, form: "Form", config_class: str) -> Self:
        """Schema of the fields that are configurable on this form-mode instance."""
        submission_model = form.to_configurable_submission_model()
        return cls(config_class=config_class, config_schema=submission_model.model_json_schema())

    @classmethod
    def from_form_class(cls, form_class: type["Form"]) -> Self:
        """Schema of the whole class, for callers that have no form-mode instance at hand."""
        return cls(config_class=form_class.__name__, config_schema=form_class.model_json_schema())
