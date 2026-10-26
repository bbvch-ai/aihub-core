from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID, NAMESPACE, TYPE


class StoredNodeKey(BaseModel):
    """What identifies a stored node without its text or vector, which a scan over a whole partition cannot afford."""

    node_id: Annotated[str, Field(description="Primary key of the node in the collection")]
    document_id: Annotated[str, Field(description="Document the node was chunked or summarised from")]
    namespace: Annotated[str, Field(description="Namespace the node's partition is hashed from")]
    node_type: Annotated[str | None, Field(description="Content or summary; None for nodes written without one")]

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> Self:
        return cls(node_id=row["id"], document_id=row[DOCUMENT_ID], namespace=row[NAMESPACE], node_type=row.get(TYPE))

    @classmethod
    def output_fields(cls) -> list[str]:
        return ["id", DOCUMENT_ID, NAMESPACE, TYPE]
