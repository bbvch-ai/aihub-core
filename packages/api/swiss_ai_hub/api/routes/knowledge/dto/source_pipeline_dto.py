from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.rag.datalake.entities import SourcePipeline


class SourcePipelineDTO(BaseModel):
    name: Annotated[str, Field(description="Source pipeline identifier, as served by GET /knowledge/source-pipelines.")]
    display_name: Annotated[str | None, Field(description="Localized name of the source pipeline.")]
    description: Annotated[str | None, Field(description="Localized description of where the files come from.")]
    form: Annotated[
        list[ALL_FORM_OPTIONS],
        Field(description="FormKit elements a database's source is configured through, localized."),
    ] = []

    @classmethod
    def from_source_pipeline(cls, source_pipeline: SourcePipeline, t: LocaleHandler) -> Self:
        return cls(
            name=source_pipeline.id,
            display_name=source_pipeline.display_name.in_locale(t.locale),
            description=source_pipeline.description.in_locale(t.locale),
            form=[element.in_locale(t) for element in source_pipeline.form],
        )
