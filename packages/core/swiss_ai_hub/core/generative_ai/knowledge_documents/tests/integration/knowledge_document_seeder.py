from typing import Any

from mongoengine.connection import get_db

from swiss_ai_hub.core.persistence.rag.documents.utils.id_utils import source_to_doc_id


class KnowledgeDocumentSeeder:
    """Writes document-store rows shaped as ingestion writes them, the parsed text twice included."""

    @staticmethod
    def row(
        namespace: str,
        source: str,
        text: str = "parsed text",
        is_ingested: bool | None = True,
        type_: str = "4",
    ) -> dict[str, Any]:
        doc_id = source_to_doc_id(source)
        metadata: dict[str, Any] = {
            "source": source,
            "namespace": namespace,
            "version": "1",
            "created_at": 1735689600,
            "updated_at": 1735689600,
            "inserted_at": 1735689600,
            "content_hash": "hash",
            "type": "content",
            "document_title": None,
        }
        if is_ingested is not None:
            metadata["is_ingested"] = is_ingested
        return {
            "_id": doc_id,
            "__type__": type_,
            "__data__": {
                "id_": doc_id,
                "text": text,
                "text_resource": {"text": text},
                "mimetype": "text/plain",
                "metadata": metadata,
            },
        }

    @staticmethod
    def insert(
        db_name: str,
        namespace: str,
        source: str,
        text: str = "parsed text",
        is_ingested: bool | None = True,
        type_: str = "4",
    ) -> str:
        row = KnowledgeDocumentSeeder.row(namespace, source, text, is_ingested, type_)
        get_db(db_name)["documents-data"].insert_one(row)
        return row["_id"]
