from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence import MilvusPartitionState


class DefaultPartitionRepairReport(BaseModel):
    """What one repair of a database's vector collection did, logged by the observation that runs it."""

    partition_state: MilvusPartitionState
    moved_nodes: int = 0
    superseded_nodes: int = 0
    document_ids: list[str] = Field(default_factory=list)

    @property
    def changed_anything(self) -> bool:
        return bool(self.document_ids)
