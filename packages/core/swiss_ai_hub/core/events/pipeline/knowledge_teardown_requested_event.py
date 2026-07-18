from typing import Annotated, Literal, Self

from pydantic import Field

from swiss_ai_hub.core.events.base_event import BaseEvent


class KnowledgeTeardownRequestedEvent(BaseEvent):
    """
    Requests asynchronous teardown of a knowledge database or one of its namespaces.

    Published by the API on a ``202 Accepted`` delete and consumed by the pipeline teardown sensor,
    which performs the heavy multi-store purge (Milvus, doc store, S3) and hard-deletes the entity
    rows as its final step. The rows are flagged ``deleting`` (and excluded from every enumeration
    path) before this event is published, so ingestion stops immediately while the rows survive long
    enough for the job to read ``db_name`` / ``bucket_name`` / ``folder_name``.
    """

    teardown_type: Annotated[
        Literal["database", "namespace"],
        Field(description="Whole database (drop collection + doc-store DB + bucket) or a single namespace"),
    ]
    bucket_id: Annotated[str, Field(description="BucketEntity id, hard-deleted as the job's final step")]
    bucket_name: Annotated[str, Field(description="S3 container name")]
    db_name: Annotated[str, Field(description="Milvus collection name and doc-store Mongo database name")]
    namespace_id: Annotated[str | None, Field(default=None, description="NamespaceEntity id — namespace teardown only")]
    namespace_name: Annotated[
        str | None, Field(default=None, description="Milvus/RefDoc metadata filter value — namespace teardown only")
    ]
    folder_name: Annotated[str | None, Field(default=None, description="S3 object prefix — namespace teardown only")]

    @classmethod
    def for_database(cls, bucket_id: str, bucket_name: str, db_name: str) -> Self:
        return cls(teardown_type="database", bucket_id=bucket_id, bucket_name=bucket_name, db_name=db_name)

    @classmethod
    def for_namespace(
        cls,
        bucket_id: str,
        bucket_name: str,
        db_name: str,
        namespace_id: str,
        namespace_name: str,
        folder_name: str,
    ) -> Self:
        return cls(
            teardown_type="namespace",
            bucket_id=bucket_id,
            bucket_name=bucket_name,
            db_name=db_name,
            namespace_id=namespace_id,
            namespace_name=namespace_name,
            folder_name=folder_name,
        )
