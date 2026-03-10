import logging
from typing import TYPE_CHECKING, Annotated, Self

from pydantic import ConfigDict, Field, model_validator

from swiss_ai_hub.core.i18n.LocaleString import LocaleString
from swiss_ai_hub.core.nats.events.form.constraints import Pattern
from swiss_ai_hub.core.nats.events.form.elements.IconSelector import IconSelector
from swiss_ai_hub.core.nats.events.form.elements.InputText import InputText
from swiss_ai_hub.core.nats.events.form.elements.LocaleInput import LocaleInput
from swiss_ai_hub.core.nats.events.form.Form import Form

if TYPE_CHECKING:
    from swiss_ai_hub.core.persistence.process import ProcessConfigEntity

logger = logging.getLogger(__name__)


def _locale_string_has_content(value: LocaleString) -> bool:
    """Check if a LocaleString has at least one non-empty locale value."""
    return any(getattr(value, locale, None) not in (None, "") for locale in ("de", "en", "fr", "it"))


class ProcessConfig(Form):
    """
    Each process instance can be configured with its own parameters.

    The process config follows the same duality pattern as AgentConfig:
    - **Form mode** (via `as_form()`): Fields contain FormKit elements for UI rendering.
    - **Data mode**: Fields contain actual primitive values for runtime use.

    This ensures the form schema and the data model can never de-sync.

    Subclasses can add domain-specific config fields for process-level settings.
    """

    process_id: Annotated[
        str | InputText,
        Field(description="Used to uniquely identify this process instance."),
        Pattern(r"^[a-z0-9_-]+$"),
    ]
    name: Annotated[LocaleString | LocaleInput, Field(description="The name of the process.")]
    description: Annotated[
        LocaleString | LocaleInput,
        Field(description="The description of the process."),
    ]
    icon: Annotated[
        str | IconSelector,
        Field(description="The icon representing the process."),
    ] = "mage:broadcast"

    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, use_enum_values=True, extra="allow")

    @model_validator(mode="after")
    def validate_locale_strings_have_content(self) -> Self:
        """Validate that name and description LocaleStrings have at least one non-empty value."""
        if isinstance(self.name, LocaleString) and not _locale_string_has_content(self.name):
            raise ValueError("name must have at least one language with content")
        if isinstance(self.description, LocaleString) and not _locale_string_has_content(self.description):
            raise ValueError("description must have at least one language with content")
        return self

    @classmethod
    def as_form(cls) -> Self:
        """
        Creates a form-mode ProcessConfig with FormKit input elements.

        Subclasses should override this method and call super().as_form() to get
        the base identity fields, then extend with their own fields.
        """
        return cls(
            process_id=InputText(
                label=LocaleString.from_i18n_path("lib.process_steps.config.process_id.label"),
                help=LocaleString.from_i18n_path("lib.process_steps.config.process_id.help"),
                placeholder=LocaleString.from_i18n_path("lib.process_steps.config.process_id.placeholder"),
                required=True,
            ),
            name=LocaleInput(
                label=LocaleString.from_i18n_path("lib.process_steps.config.name.label"),
                placeholder=LocaleString.from_i18n_path("lib.process_steps.config.name.placeholder"),
                input_type="text",
            ),
            description=LocaleInput(
                label=LocaleString.from_i18n_path("lib.process_steps.config.description.label"),
                placeholder=LocaleString.from_i18n_path("lib.process_steps.config.description.placeholder"),
                input_type="textarea",
            ),
            icon=IconSelector(
                label=LocaleString.from_i18n_path("lib.process_steps.config.icon.label"),
                help=LocaleString.from_i18n_path("lib.process_steps.config.icon.help"),
                placeholder=LocaleString.from_i18n_path("lib.process_steps.config.icon.placeholder"),
            ),
        )

    @classmethod
    def _process_identity_inputs(cls) -> dict[str, InputText | LocaleInput | IconSelector]:
        """
        Shared input elements for process identity fields used by subclasses.

        Returns a dict of field names to FormkitElements for form rendering.
        """
        return {
            "name": LocaleInput(
                label=LocaleString.from_i18n_path("lib.process_steps.config.name.label"),
                input_type="text",
            ),
            "description": LocaleInput(
                label=LocaleString.from_i18n_path("lib.process_steps.config.description.label"),
                input_type="textarea",
            ),
            "icon": IconSelector(
                label=LocaleString.from_i18n_path("lib.process_steps.config.icon.label"),
                help=LocaleString.from_i18n_path("lib.process_steps.config.icon.help"),
            ),
            "process_id": InputText(
                label=LocaleString.from_i18n_path("lib.process_steps.config.process_id.label"),
                help=LocaleString.from_i18n_path("lib.process_steps.config.process_id.help"),
            ),
        }

    @classmethod
    def from_entity(cls, entity: "ProcessConfigEntity") -> Self:
        data = {
            "process_id": entity.process_id,
            "name": entity.name.to_locale_string(),
            "description": entity.description.to_locale_string(),
            "icon": entity.icon,
            **entity.config_data,
        }
        config = cls(**data)
        return config
