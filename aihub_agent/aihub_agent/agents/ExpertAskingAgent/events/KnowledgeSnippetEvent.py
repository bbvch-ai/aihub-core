from pydantic import Field

from aihub_lib.nats.events import ControlEvent


class KnowledgeSnippetEvent(ControlEvent):
    content: str = Field(..., description="Content of the knowledge snippet")