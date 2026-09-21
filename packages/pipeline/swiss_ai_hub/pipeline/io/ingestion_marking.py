import logging
from typing import Annotated

from llama_index.core.schema import TextNode
from swiss_ai_hub.core.infrastructure import MongoConnectionRegistry
from swiss_ai_hub.core.persistence import RefDoc
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import DOCUMENT_ID

logger = logging.getLogger(__name__)


def mark_ref_docs_as_ingested(
    nodes: Annotated[list[TextNode], "Nodes just written to the vector store"],
    document_store_name: Annotated[str, "Mongo alias of the doc store holding their RefDocs"],
    log: Annotated[logging.Logger, "Logger of the calling IO manager's context"] = logger,
    document_id_key: Annotated[str, "Node metadata key carrying the document id"] = DOCUMENT_ID,
) -> None:
    """Flags the source documents as queryable, now that their nodes are in the vector store.

    Called from the IO manager rather than an op because the vector store write happens during output
    handling: an op could only ever mark the documents *before* their nodes are actually retrievable.
    """
    MongoConnectionRegistry.ensure_alias(document_store_name)

    document_ids = {
        document_id for node in nodes if (document_id := node.ref_doc_id or node.metadata.get(document_id_key))
    }
    marked = {
        document_id
        for document_id in document_ids
        if RefDoc.mark_ingested(db_alias=document_store_name, doc_id=document_id)
    }
    log.info(f"Marked {len(marked)} document(s) as ingested: {sorted(marked)}")

    unknown = sorted(document_ids - marked)
    if unknown:
        log.warning(f"No RefDoc found to mark as ingested for document IDs: {unknown}")
