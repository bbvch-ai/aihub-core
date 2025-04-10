from pydantic import Field

from aihub_lib.nats.events import ControlEvent


class KnowledgeSnippetEvent(ControlEvent):
    """Event representing a knowledge snippet generated based on the users question and the expert answers."""
    content: str = Field(..., description="Content of the knowledge snippet")