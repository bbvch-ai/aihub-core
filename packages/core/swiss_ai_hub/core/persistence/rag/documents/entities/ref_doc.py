import time
from typing import Any, Self

from mongoengine import (
    BooleanField,
    DictField,
    Document,
    DynamicEmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    NotUniqueError,
    Q,
    StringField,
)
from mongoengine.context_managers import switch_db

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.documents.utils.id_utils import source_to_doc_id

# Index field paths (MongoEngine uses db_field names)
_IDX_NAMESPACE = "data.metadata.namespace"
_IDX_IS_INGESTED = "data.metadata.is_ingested"
_IDX_SOURCE = "data.metadata.source"


class Metadata(DynamicEmbeddedDocument):
    source = StringField(required=True)
    source_origin = StringField(required=False)
    namespace = StringField(required=True)
    version = StringField(required=True)

    number_of_pages = IntField(required=False)
    document_title = StringField(required=False)
    language = StringField(required=False)

    created_at = IntField(required=True)
    updated_at = IntField(required=True)
    inserted_at = IntField(required=True)

    content_hash = StringField(required=True)
    type = StringField(required=True)

    # False = pending (not yet processed), True = ingested (fully processed)
    # Legacy docs without this field are treated as ingested
    is_ingested = BooleanField(default=True)


class DocumentData(DynamicEmbeddedDocument):
    id = StringField(required=True, db_field="id_")
    metadata = EmbeddedDocumentField(Metadata)
    excluded_embed_metadata_keys = ListField(StringField())
    excluded_llm_metadata_keys = ListField(StringField())
    relationships = DictField()
    text = StringField(required=True)
    mimetype = StringField(required=True)
    start_char_idx = IntField()
    end_char_idx = IntField()
    text_template = StringField(default="{metadata_str}\n\n{content}")
    metadata_template = StringField(default="{key}: {value}")
    metadata_seperator = StringField(default="\n")
    class_name = StringField(default="Document")


class RefDoc(Document):
    """
    This RefDoc document is closely modelled after the RefDoc by llama-index. Hence, we can NOT freely change how
    this document is stored in the database. We have some creative freedom over the Metadata, but not at all over the
    DocumentData.
    """

    meta = {
        "collection": "documents-data",
        "strict": False,
        "indexes": [
            {"fields": [_IDX_NAMESPACE]},
            {"fields": [_IDX_NAMESPACE, _IDX_IS_INGESTED]},
            {"fields": [_IDX_NAMESPACE, _IDX_SOURCE]},
            {"fields": [_IDX_SOURCE], "unique": True},
        ],
    }
    id = StringField(primary_key=True)
    data = EmbeddedDocumentField(DocumentData, db_field="__data__")
    type_ = StringField(db_field="__type__")

    @classmethod
    @trace_fn
    def by_id(cls, db_alias: str, doc_id: str) -> Self:
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects.get(id=doc_id)

    @classmethod
    @trace_fn
    def by_id_and_namespace(cls, db_alias: str, doc_id: str, namespace: str) -> Self:
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects.get(id=doc_id, data__metadata__namespace=namespace)

    @classmethod
    @trace_fn
    def by_namespace(
        cls,
        db_alias: str,
        namespace: str,
        exclude_ids: list[str] | None = None,
    ) -> list["RefDoc"]:
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return list(SwitchedRefDoc.objects.filter(data__metadata__namespace=namespace, id__nin=(exclude_ids or [])))

    @classmethod
    @trace_fn
    def get_documents(
        cls,
        db_alias: str,
        exclude_ids: list[str] | None = None,
    ) -> list["RefDoc"]:
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return list(SwitchedRefDoc.objects.filter(id__nin=(exclude_ids or [])))

    @classmethod
    @trace_fn
    def count_by_namespace(
        cls,
        db_alias: str,
        namespace: str,
    ) -> int:
        """Counts the total number of documents in a given namespace."""
        query_filter = {"data__metadata__namespace": namespace}
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects.filter(**query_filter).count()

    @classmethod
    @trace_fn
    def get_paginated_by_namespace(
        cls,
        db_alias: str,
        namespace: str,
        skip: int,
        limit: int,
    ) -> list["RefDoc"]:
        """
        Retrieves a paginated list of documents from a given namespace.
        Documents are ordered by their internal ID by default MongoEngine behavior without explicit order_by.
        """
        query_filter = {"data__metadata__namespace": namespace}
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return list(SwitchedRefDoc.objects.filter(**query_filter).skip(skip).limit(limit).order_by("id"))

    @classmethod
    @trace_fn
    def get_all_namespaces(cls, db_alias: str) -> list[str]:
        """
        Returns a list of all unique namespace values.
        """
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects.distinct("data.metadata.namespace")

    @classmethod
    @trace_fn
    def get_namespaces(cls, db_alias: str) -> list[dict[str, Any]]:
        """
        Returns a list of dictionaries containing namespace names and document counts.
        Also includes the latest updated_at, latest inserted_at, oldest created_at timestamps,
        and a set of all document types in each namespace.
        Uses MongoDB aggregation pipeline to get this information in a single query.
        """
        pipeline = [
            # Group by namespace and count documents
            {
                "$group": {
                    "_id": "$__data__.metadata.namespace",
                    "count": {"$sum": 1},
                    "last_updated_at": {"$max": "$__data__.metadata.updated_at"},
                    "last_inserted_at": {"$max": "$__data__.metadata.inserted_at"},
                    "created_at": {"$min": "$__data__.metadata.created_at"},
                }
            },
            # Format the output
            {
                "$project": {
                    "name": "$_id",
                    "number_of_documents": "$count",
                    "last_updated_at": 1,
                    "last_inserted_at": 1,
                    "created_at": 1,
                    "_id": 0,
                }
            },
        ]

        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return list(SwitchedRefDoc.objects.aggregate(pipeline))

    @classmethod
    @trace_fn
    def count_pending_by_namespace(cls, db_alias: str, namespace: str) -> int:
        """Count pending (not yet ingested) documents in a namespace."""
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects.filter(
                data__metadata__namespace=namespace,
                data__metadata__is_ingested=False,
            ).count()

    @classmethod
    @trace_fn
    def count_ingested_by_namespace(cls, db_alias: str, namespace: str) -> int:
        """Count ingested documents in a namespace.

        Legacy docs without is_ingested field are treated as ingested.
        """
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects.filter(
                Q(data__metadata__namespace=namespace) & Q(data__metadata__is_ingested__ne=False)
            ).count()

    @classmethod
    @trace_fn
    def search_in_namespace(
        cls,
        db_alias: str,
        namespace: str,
        query: str,
        skip: int = 0,
        limit: int = 100,
        sort_field: str | None = None,
        sort_order: int = 1,
    ) -> list["RefDoc"]:
        """Search documents by title or source filename (case-insensitive)."""
        order_by = cls._get_order_by(sort_field, sort_order)

        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return list(
                SwitchedRefDoc.objects.filter(
                    Q(data__metadata__namespace=namespace)
                    & (Q(data__metadata__document_title__icontains=query) | Q(data__metadata__source__icontains=query))
                )
                .skip(skip)
                .limit(limit)
                .order_by(order_by)
            )

    @classmethod
    @trace_fn
    def count_search_in_namespace(
        cls,
        db_alias: str,
        namespace: str,
        query: str,
    ) -> int:
        """Count documents matching search query in namespace."""
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects.filter(
                Q(data__metadata__namespace=namespace)
                & (Q(data__metadata__document_title__icontains=query) | Q(data__metadata__source__icontains=query))
            ).count()

    @classmethod
    @trace_fn
    def get_all_in_namespace(
        cls,
        db_alias: str,
        namespace: str,
        skip: int = 0,
        limit: int = 100,
        sort_field: str | None = None,
        sort_order: int = 1,
    ) -> list["RefDoc"]:
        """Get all documents in a namespace with sorting support."""
        order_by = cls._get_order_by(sort_field, sort_order)
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return list(
                SwitchedRefDoc.objects.filter(data__metadata__namespace=namespace)
                .skip(skip)
                .limit(limit)
                .order_by(order_by)
            )

    @staticmethod
    def _get_order_by(sort_field: str | None, sort_order: int) -> str:
        """Convert sort field and order to MongoEngine order_by string."""
        field_mapping = {
            "document_title": "data.metadata.document_title",
            "created_at": "data.metadata.created_at",
            "updated_at": "data.metadata.updated_at",
            "is_ingested": "data.metadata.is_ingested",
        }
        if sort_field and sort_field in field_mapping:
            prefix = "-" if sort_order == -1 else ""
            return f"{prefix}{field_mapping[sort_field]}"
        # Default: newest first
        return "-data.metadata.updated_at"

    @classmethod
    @trace_fn
    def create_placeholder(
        cls,
        db_alias: str,
        source: str,
        namespace: str,
        document_title: str | None = None,
    ) -> Self:
        """Create a placeholder RefDoc for a file that is being uploaded/processed.

        Uses deterministic ID based on source path to enable upsert on processing completion.
        """
        doc_id = source_to_doc_id(source)
        current_time = int(time.time())

        if not document_title:
            document_title = source.split("/")[-1]

        metadata = Metadata(
            source=source,
            namespace=namespace,
            version="1",
            is_ingested=False,
            created_at=current_time,
            updated_at=current_time,
            inserted_at=current_time,
            content_hash="",
            type="content",
            document_title=document_title,
        )

        document_data = DocumentData(
            id=doc_id,
            metadata=metadata,
            text="",
            mimetype="application/octet-stream",
            excluded_embed_metadata_keys=[],
            excluded_llm_metadata_keys=[],
            relationships={},
        )

        with switch_db(cls, db_alias) as SwitchedRefDoc:
            ref_doc = SwitchedRefDoc(
                id=doc_id,
                data=document_data,
                type_="placeholder",
            )
            ref_doc.save()
            return ref_doc

    @classmethod
    @trace_fn
    def get_or_create_placeholder(
        cls,
        db_alias: str,
        source: str,
        namespace: str,
        document_title: str | None = None,
    ) -> tuple["RefDoc", bool]:
        """Get existing RefDoc by source or create a placeholder.

        If the document exists and is already ingested, it atomically resets the status
        to pending (for re-upload/re-processing scenarios).

        Returns (ref_doc, created) where created is True if new placeholder was created.
        """
        doc_id = source_to_doc_id(source)

        with switch_db(cls, db_alias) as SwitchedRefDoc:
            # Atomic update: only reset to pending if currently ingested
            updated = SwitchedRefDoc.objects(id=doc_id, data__metadata__is_ingested=True).update_one(
                set__data__metadata__is_ingested=False,
                set__data__metadata__updated_at=int(time.time()),
            )
            if updated:
                return SwitchedRefDoc.objects.get(id=doc_id), False

            try:
                existing = SwitchedRefDoc.objects.get(id=doc_id)
                return existing, False
            except SwitchedRefDoc.DoesNotExist:
                pass

        try:
            new_doc = cls.create_placeholder(db_alias, source, namespace, document_title)
            return new_doc, True
        except NotUniqueError:
            # Another process created it - fetch and return
            with switch_db(cls, db_alias) as SwitchedRefDoc:
                existing = SwitchedRefDoc.objects.get(id=doc_id)
                return existing, False

    @classmethod
    @trace_fn
    def delete_by_source(cls, db_alias: str, source: str) -> bool:
        """Delete a RefDoc by its source path."""
        doc_id = source_to_doc_id(source)
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            try:
                ref_doc = SwitchedRefDoc.objects.get(id=doc_id)
                ref_doc.delete()
                return True
            except SwitchedRefDoc.DoesNotExist:
                return False

    @classmethod
    @trace_fn
    def mark_ingested(cls, db_alias: str, doc_id: str) -> "RefDoc | None":
        """Mark a document as fully ingested."""
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            try:
                ref_doc = SwitchedRefDoc.objects.get(id=doc_id)
                ref_doc.data.metadata.is_ingested = True
                ref_doc.data.metadata.updated_at = int(time.time())
                ref_doc.save()
                return ref_doc
            except SwitchedRefDoc.DoesNotExist:
                return None
