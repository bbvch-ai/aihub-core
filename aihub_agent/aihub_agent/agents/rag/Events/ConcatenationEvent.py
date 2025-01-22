from typing import List

from llama_index.core.schema import NodeWithScore
from pydantic import Field

from aihub_lib.nats.events import ControlEvent
from aihub_lib.nats.events.semantic.retriever import Document


class ConcatenationEvent(ControlEvent):
    """
    Allows for concatenation of retrieved documents.
    """

    nodes: List[Document] = Field(..., description="The message including the context nodes information in order.")
