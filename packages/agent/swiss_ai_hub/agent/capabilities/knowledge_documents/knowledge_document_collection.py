from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.generative_ai import BucketNamespacePair


class KnowledgeDocumentCollection(BaseModel):
    """One collection a run's document tools work on, under the identifier the model names it by."""

    identifier: Annotated[str, Field(description="'database/collection', as the knowledge search names it too.")]
    collection: Annotated[BucketNamespacePair, Field(description="The collection as the document readers take it.")]
    label: Annotated[str, Field(description="The collection's name as users read it, in the run's locale.")]
