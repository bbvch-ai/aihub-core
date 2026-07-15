from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.rag.datalake.entities import IngestorType

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString


class IngestorDTO(BaseModel):
    name: Annotated[str, Field(description="The ingestor identifier stored on the knowledge database.")]
    display_name: Annotated[str | None, Field(description="Localized name of the ingestion pipeline.")]
    description: Annotated[str | None, Field(description="Localized description of what the pipeline does.")]

    @classmethod
    def from_ingestor_type(cls, ingestor: IngestorType, t: LocaleHandler) -> Self:
        return cls(
            name=ingestor.value,
            display_name=t.extract(ApiLocaleString.from_i18n_path(f"api.ingestors.{ingestor.value}.display_name")),
            description=t.extract(ApiLocaleString.from_i18n_path(f"api.ingestors.{ingestor.value}.description")),
        )
