from typing import Annotated

from pydantic import BaseModel, Field


class BucketNamespaceSelection(BaseModel):
    """Selection of namespaces for a specific bucket.

    Used to pass namespace selections from NamespaceSelectionAgent to RAGAgent.
    The RAGAgent maps the bucket_name to the appropriate retrieval agent.
    """

    bucket_name: Annotated[
        str,
        Field(description="The bucket name to select namespaces for."),
    ]
    namespaces: Annotated[
        list[str],
        Field(description="Selected namespace names within the bucket.", min_length=1),
    ]
