from typing import Annotated, Self

from pydantic import BaseModel, Field
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities import NamespaceEntity


class NamespaceDTO(BaseModel):
    id: Annotated[str, Field(..., description="Unique identifier of the namespace")]
    name: Annotated[str, Field(..., description="Name of namespace")]
    database_id: Annotated[str, Field(..., description="ID of the database containing the namespace")]
    display_name: Annotated[str | None, Field(None, description="Display name of namespace, can be localized")]
    description: Annotated[str | None, Field(None, description="Description of namespace, can be localized")]
    number_of_documents: Annotated[int, Field(..., description="Number of documents in namespace")]
    updated_at: Annotated[
        int, Field(..., description="Latest timestamp when any document in the namespace was updated")
    ]
    inserted_at: Annotated[
        int, Field(..., description="Latest timestamp when any document in the namespace was inserted")
    ]
    created_at: Annotated[
        int, Field(..., description="Oldest timestamp when any document in the namespace was created")
    ]

    @staticmethod
    def _safe_extract_locale_from_entity(entity: LocaleStringEntity | None, t: LocaleHandler) -> str | None:
        """Safely extract a localized string from a LocaleStringEntity, handling None and empty entities."""
        if not entity:
            return None

        try:
            result = t.extract(entity.to_mongo().to_dict())
            return result if result and result.strip() else None
        except (ValueError, AttributeError):
            return None

    @classmethod
    def from_entity(cls, entity: NamespaceEntity, t: LocaleHandler, number_of_documents: int) -> Self:
        return cls(
            id=str(entity.id),
            name=entity.namespace_name,
            database_id=entity.bucket_id,
            display_name=cls._safe_extract_locale_from_entity(entity.display_name, t),
            description=cls._safe_extract_locale_from_entity(entity.description, t),
            updated_at=entity.updated_at,
            inserted_at=entity.inserted_at,
            created_at=entity.created_at,
            number_of_documents=number_of_documents,
        )
