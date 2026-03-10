from typing import Annotated

from pydantic import Field

from swiss_ai_hub.core.nats.events import BaseEvent


class SourceUpdatedEvent(BaseEvent):
    """
    Signals that a data source has been modified, typically when a file is uploaded or changed in a data lake.
    This event triggers downstream pipeline processing, enabling reactive data ingestion workflows that respond
    to source changes without manual intervention.
    """

    path: Annotated[str, Field(description="The object path for the uploaded file")]
