from typing import Annotated

from pydantic import BaseModel, Field


class BucketReference(BaseModel):
    """
    Reference to a data lake bucket by name.

    Used by NamespaceSelectionAgent to specify which buckets to fetch namespaces from.
    """

    bucket_name: Annotated[
        str,
        Field(description="The bucket name."),
    ]
