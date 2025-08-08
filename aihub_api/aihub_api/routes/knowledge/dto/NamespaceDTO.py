from typing import Annotated

from pydantic import BaseModel, Field

from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.persistence.rag.documents.entities.NamespaceEntity import NamespaceEntity


class NamespaceDTO(BaseModel):
    name: Annotated[str, Field(..., description="Name of namespace")]
    display_name: Annotated[str | None, Field(None, description="Display name of namespace, can be localized")]
    description: Annotated[str | None, Field(None, description="Description of namespace, can be localized")]
    number_of_documents: Annotated[int, Field(..., description="Number of documents in namespace")]
    last_updated_at: Annotated[
        int, Field(..., description="Latest timestamp when any document in the namespace was updated")
    ]
    last_inserted_at: Annotated[
        int, Field(..., description="Latest timestamp when any document in the namespace was inserted")
    ]
    created_at: Annotated[
        int, Field(..., description="Oldest timestamp when any document in the namespace was created")
    ]

    @classmethod
    def from_entity(cls, entity: NamespaceEntity, t: LocaleHandler, number_of_documents: int) -> "NamespaceDTO":
        return cls(
            name=entity.namespace_name,
            display_name=t.extract(entity.display_name.to_mongo().to_dict()),
            description=t.extract(entity.description.to_mongo().to_dict()),
            last_updated_at=entity.last_updated,
            last_inserted_at=entity.inserted_at,
            created_at=entity.created_at,
            number_of_documents=number_of_documents,
        )
