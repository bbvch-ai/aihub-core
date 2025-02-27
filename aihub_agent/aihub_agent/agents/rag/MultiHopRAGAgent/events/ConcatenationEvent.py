from aihub_lib.nats.events import ControlEvent
from aihub_lib.nats.events.semantic.retriever import Document
from pydantic import Field
from typing import List


class ConcatenationEvent(ControlEvent):
    """
    Allows for concatenation of retrieved documents.
    """

    documents: List[Document] = Field(..., description="The message including the context nodes information in order.")
