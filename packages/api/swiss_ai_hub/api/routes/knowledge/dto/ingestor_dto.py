from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.form import ALL_FORM_OPTIONS
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.rag.datalake.entities import Ingestor


class IngestorDTO(BaseModel):
    name: Annotated[str, Field(description="Ingestor identifier, as served by GET /knowledge/ingestors.")]
    display_name: Annotated[str | None, Field(description="Localized name of the ingestion pipeline.")]
    description: Annotated[str | None, Field(description="Localized description of what the pipeline does.")]
    form: Annotated[
        list[ALL_FORM_OPTIONS],
        Field(description="FormKit elements a database of this ingestor is configured through, localized."),
    ] = []

    @classmethod
    def from_ingestor(cls, ingestor: Ingestor, t: LocaleHandler) -> Self:
        """Every ingestor carries its own labels and form, announced by the pipeline that owns it."""
        return cls(
            name=ingestor.id,
            display_name=ingestor.display_name.in_locale(t.locale),
            description=ingestor.description.in_locale(t.locale),
            form=[element.in_locale(t) for element in ingestor.form],
        )
