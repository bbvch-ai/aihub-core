from typing import Annotated

from pydantic import Field

from aihub_lib.nats.events import BaseEvent


class SourceDeletedEvent(BaseEvent):
    """
    Signals that a data source has been deleted from the data lake.
    This event can be used to trigger cleanup operations in downstream systems
    such as removing corresponding documents from MongoDB docstore and vector stores.
    """

    path: Annotated[str, Field(description="The object path for the deleted file")]
    document_id: Annotated[str | None, Field(description="The document ID in the docstore, if known")] = None
