from typing import Dict, Optional

from llama_index.core.schema import NodeWithScore
from openinference.semconv.trace import DocumentAttributes
from pydantic import BaseModel, Field

from aihub_lib.nats.events.semantic.retriever.Node import Node


class Document(BaseModel):
    id: str = Field(..., description="Unique identifier for the document.")
    score: Optional[float] = Field(None, description="Score representing the relevance of the document.")
    content: Optional[str] = Field(None, description="Content of the document.")
    metadata: Node = Field(
        ...,
        description="Optional metadata associated with the document as a dictionary.",
    )

    def to_semantic_convention(self, key: str, i: int) -> Dict[str, str]:
        return {
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_ID}": self.id,
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_SCORE}": self.score,
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_CONTENT}": self.content,
            f"{key}.{i}.{DocumentAttributes.DOCUMENT_METADATA}": self.metadata.model_dump_json(),
        }

    @classmethod
    def from_node(cls, node: NodeWithScore) -> "Document":
        return cls(
            id=node.id_,
            score=node.score,
            content=node.text,
            metadata=Node.from_llama_index_node_with_score(node),
        )
