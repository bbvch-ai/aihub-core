from pydantic import BaseModel


class BucketNamespacePair(BaseModel):
    """A bucket-namespace selection pair for RAG retrieval filtering."""

    bucket_name: str
    namespace_name: str
