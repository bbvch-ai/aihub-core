from typing import Annotated, Self

from pydantic import ConfigDict, Field, model_validator

from swiss_ai_hub.core.form.elements.locale_input import LocaleInput
from swiss_ai_hub.core.form.form import Form
from swiss_ai_hub.core.i18n.locale_string import LocaleString


class IngestorConfig(Form):
    """
    The configuration a knowledge database carries for the ingestion pipeline that owns it.

    An ingestion pipeline subclasses this, declares its knobs in form duality (``str | ModelSelect``,
    ``bool | Checkbox``, ...) and announces ``as_form()`` through its registration record. The API renders that
    form in the create-database dialog and validates submissions against its schema, so a pipeline adds a knob
    without any change to the platform — the same contract ``AgentConfig`` gives agent blueprints.

    ``name`` and ``description`` are platform-owned identity fields, stored on the database row itself; everything
    else a subclass adds lands in the database's free-form configuration and is read back by the pipeline per run.
    """

    name: Annotated[LocaleString | LocaleInput, Field(description="The name of the knowledge database.")]
    description: Annotated[
        LocaleString | LocaleInput,
        Field(description="The description of the knowledge database."),
    ]
    model_config = ConfigDict(arbitrary_types_allowed=True, populate_by_name=True, use_enum_values=True, extra="allow")

    @model_validator(mode="after")
    def validate_name_has_content(self) -> Self:
        """Only the name is guarded here: the API requires a description on create, but rows created before that
        rule existed carry an empty one, and the pipeline must still be able to resolve their configuration."""
        if isinstance(self.name, LocaleString) and not self.name.has_content():
            raise ValueError("name must have at least one language with content")
        return self

    @classmethod
    def as_form(cls) -> Self:
        """
        The form-mode config with the identity fields as inputs.

        Subclasses override this, call ``super().as_form()`` for the identity fields and extend the result with
        their own elements.
        """
        return cls(
            name=LocaleInput(
                label=LocaleString.from_i18n_path("lib.ingestors.config.name.label"),
                placeholder=LocaleString.from_i18n_path("lib.ingestors.config.name.placeholder"),
                input_type="text",
                required=True,
            ),
            description=LocaleInput(
                label=LocaleString.from_i18n_path("lib.ingestors.config.description.label"),
                placeholder=LocaleString.from_i18n_path("lib.ingestors.config.description.placeholder"),
                input_type="textarea",
                required=True,
            ),
        )
