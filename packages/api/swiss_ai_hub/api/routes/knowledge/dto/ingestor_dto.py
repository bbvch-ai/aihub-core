from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.rag.datalake.entities import Ingestor, IngestorType

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString


class IngestorDTO(BaseModel):
    name: Annotated[
        str, Field(description="Ingestor identifier, as served by GET /knowledge/ingestors.")
    ]
    display_name: Annotated[str | None, Field(description="Localized name of the ingestion pipeline.")]
    description: Annotated[str | None, Field(description="Localized description of what the pipeline does.")]

    @classmethod
    def from_ingestor_type(cls, ingestor: IngestorType, t: LocaleHandler) -> Self:
        """Build the DTO for a platform ingestor, whose labels live in the API's own i18n files."""
        return cls(
            name=ingestor.value,
            display_name=t.extract(ApiLocaleString.from_i18n_path(f"api.ingestors.{ingestor.value}.display_name")),
            description=t.extract(ApiLocaleString.from_i18n_path(f"api.ingestors.{ingestor.value}.description")),
        )

    @classmethod
    def from_ingestor(cls, ingestor: Ingestor, t: LocaleHandler) -> Self:
        """Build the DTO for a custom ingestor, which carries its own localized labels from the deployment."""
        return cls(
            name=ingestor.id,
            display_name=ingestor.display_name.in_locale(t.locale),
            description=ingestor.description.in_locale(t.locale),
        )
