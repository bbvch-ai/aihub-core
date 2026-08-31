from dataclasses import dataclass

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import NodeContentType


@dataclass(frozen=True)
class TextChunk:
    content: str
    content_type: NodeContentType
