from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.core.generative_ai.retrievers.metadata_filter_pair import MetadataFilterPair


class BucketMetadataFilters(BaseModel):
    """The metadata filters a publisher wants applied to one bucket at retrieval time.

    AND-combined with any namespace narrowing from `selected_namespaces`. Each filter key must be
    listed in the target retriever's `MilvusVectorStoreConfig.allowed_metadata_filter_fields`.
    """

    bucket_name: Annotated[str, Field(description="The name of the bucket these filters apply to.")]
    filters: Annotated[
        list[MetadataFilterPair],
        Field(description="Metadata key/value filters applied AND-wise to retrieval in this bucket."),
    ]
