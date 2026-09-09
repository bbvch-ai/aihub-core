from typing import TYPE_CHECKING, Annotated, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.form.all_form_options import ALL_FORM_OPTIONS
from swiss_ai_hub.core.form.config_specs import ConfigSpecs
from swiss_ai_hub.core.i18n.locale_string import LocaleString

if TYPE_CHECKING:
    from swiss_ai_hub.core.source_pipelines.source_pipeline_config import SourcePipelineConfig


class SourcePipeline(BaseModel):
    """A user-selectable source pipeline, as the pipeline itself advertises it.

    ``id`` is stored on ``BucketEntity.source`` and must equal the ``source`` a pipeline passes to its
    definitions factory — that string is the routing guard by which the pipeline claims the databases it
    fills. Labels, form and schema travel on the object for the same reason they do on ``Ingestor``: the
    configuration class lives in the pipeline's deployment, and the API renders and validates what it was told.
    """

    id: Annotated[
        str,
        Field(
            pattern=r"^[a-z][a-z0-9_]*$",
            description="Routing id stored on the database and passed to the pipeline (lowercase, alphanumeric/_).",
        ),
    ]
    display_name: Annotated[LocaleString, Field(description="Localized name shown in the source selector.")]
    description: Annotated[LocaleString, Field(description="Localized description of where the files come from.")]
    form: Annotated[
        list[ALL_FORM_OPTIONS],
        Field(description="FormKit elements defining the source configuration of a database filled by this pipeline."),
    ] = []
    config_specs: Annotated[
        ConfigSpecs,
        Field(description="JSON schema the API validates a database's source configuration against."),
    ] = ConfigSpecs()

    @classmethod
    def from_config(
        cls,
        source_id: str,
        display_name: LocaleString,
        description: LocaleString,
        config: Annotated["SourcePipelineConfig", "The pipeline's configuration in form mode"],
    ) -> Self:
        """Both announced surfaces — rendered form and submission schema — from one form-mode config."""
        return cls(
            id=source_id,
            display_name=display_name,
            description=description,
            form=config.to_formkit_form(),
            config_specs=ConfigSpecs.from_form(config, type(config).__name__),
        )
