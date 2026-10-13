from pydantic import BaseModel, Field


class OrphanedNodeRepairReport(BaseModel):
    """What one orphaned-node repair run found and deleted, shown as the run's output metadata."""

    dry_run: bool
    nodes_by_document: dict[str, int] = Field(default_factory=dict)
    deleted_nodes: int = 0

    @property
    def orphaned_documents(self) -> int:
        return len(self.nodes_by_document)

    @property
    def orphaned_nodes(self) -> int:
        return sum(self.nodes_by_document.values())

    def add_orphans(self, node_ids_by_document: dict[str, list[str]]) -> None:
        """A document's nodes can be spread over its namespace partition and ``_default``, so counts add up."""
        for document_id, node_ids in node_ids_by_document.items():
            self.nodes_by_document[document_id] = self.nodes_by_document.get(document_id, 0) + len(node_ids)
