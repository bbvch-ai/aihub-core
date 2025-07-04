from typing import Annotated

from aihub_lib.nats.events import ControlEvent
from pydantic import Field


class KnowledgeSnippetEvent(ControlEvent):
    """Event representing a knowledge snippet generated based on the users question and the expert answers."""

    content: Annotated[str, Field(description="Content of the knowledge snippet")]
