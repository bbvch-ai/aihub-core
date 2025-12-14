from typing import Annotated

from pydantic import BaseModel, Field, model_validator


class BucketReference(BaseModel):
    """
    Reference to a data lake bucket, identified by either ID or name.

    At least one of bucket_id or bucket_name must be provided.
    Used by NamespaceSelectionAgent to specify which buckets to fetch namespaces from.
    """

    bucket_id: Annotated[
        str | None,
        Field(default=None, description="The unique bucket ID."),
    ]
    bucket_name: Annotated[
        str | None,
        Field(default=None, description="The bucket name."),
    ]

    @model_validator(mode="after")
    def validate_at_least_one_identifier(self) -> "BucketReference":
        if not self.bucket_id and not self.bucket_name:
            raise ValueError("At least one of bucket_id or bucket_name must be provided")
        return self
