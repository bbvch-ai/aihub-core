from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.retrievers.bucket_namespace_pair import BucketNamespacePair
from swiss_ai_hub.core.persistence.rag.documents.utils.id_utils import S3_PROTOCOL_PREFIX


class ResolvedKnowledgeCollection(BaseModel):
    """A collection resolved to where its documents live.

    Paths are relative to the collection's folder, never to its namespace name: the two differ whenever a folder name
    had to be sanitised into a namespace name, and stripping the wrong one leaves the folder in every path.
    """

    collection: Annotated[BucketNamespacePair, Field(description="The collection as the caller named it")]
    db_name: Annotated[str, Field(description="Mongo database holding the knowledge database's document store")]
    folder_name: Annotated[str, Field(description="Top-level data lake folder the collection's files live under")]

    @property
    def source_prefix(self) -> str:
        return f"{S3_PROTOCOL_PREFIX}{self.collection.bucket_name}/{self.folder_name}/"

    def source_for(self, path: str) -> str:
        return f"{self.source_prefix}{path}"

    def relative_path(self, source: str) -> str:
        return source.removeprefix(self.source_prefix)
