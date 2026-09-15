from typing import TYPE_CHECKING, Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.config_specs import ConfigSpecs
from swiss_ai_hub.core.i18n.locale_string import LocaleString

if TYPE_CHECKING:
    from swiss_ai_hub.core.ingestors.ingestor_config import IngestorConfig


class Ingestor(BaseModel):
    """A user-selectable ingestion pipeline, as the pipeline itself advertises it.

    ``id`` is stored on ``BucketEntity.ingestor`` and must equal the ``ingestor`` a pipeline passes to
    ``document_ingestion_pipeline_definitions`` — that string is the routing guard by which the pipeline claims the
    databases it owns. Labels, form and schema are carried on the object rather than resolved by the API because the
    configuration class lives in the pipeline's deployment, not in core: the API renders and validates what it was
    told, the way it does for agent classes.
    """

    id: Annotated[
        str,
        Field(
            pattern=r"^[a-z][a-z0-9_]*$",
            description="Routing id stored on the database and passed to the pipeline (lowercase, alphanumeric/_).",
        ),
    ]
    display_name: Annotated[LocaleString, Field(description="Localized name shown in the create-database selector.")]
    description: Annotated[LocaleString, Field(description="Localized description of what the pipeline does.")]
    form: Annotated[
        list[ALL_FORM_OPTIONS],
        Field(description="FormKit elements defining the configuration form of a database owned by this ingestor."),
    ] = []
    config_specs: Annotated[
        ConfigSpecs,
        Field(description="JSON schema the API validates a database's configuration against."),
    ] = ConfigSpecs()

    @classmethod
    def from_config(
        cls,
        ingestor_id: str,
        display_name: LocaleString,
        description: LocaleString,
        config: Annotated["IngestorConfig", "The pipeline's configuration in form mode"],
    ) -> Self:
        """Both announced surfaces — rendered form and submission schema — from one form-mode config."""
        return cls(
            id=ingestor_id,
            display_name=display_name,
            description=description,
            form=config.to_formkit_form(),
            config_specs=ConfigSpecs.from_form(config, type(config).__name__),
        )
