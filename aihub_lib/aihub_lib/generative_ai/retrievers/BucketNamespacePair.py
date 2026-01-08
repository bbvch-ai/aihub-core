from pydantic import BaseModel


class BucketNamespacePair(BaseModel):
    """A bucket-namespace selection pair for RAG retrieval filtering."""

    bucket_name: Annotated[str, Field(description="The name of the bucket"]
    namespace_name: Annotated[str, Field(description="The name of the selected namespace in the bucket"]
