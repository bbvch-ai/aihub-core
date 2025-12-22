from typing import Any

from mongoengine import (
    DictField,
    Document,
    DynamicEmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    StringField,
)
from mongoengine.context_managers import switch_db

from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


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

    meta = {"collection": "documents-data", "strict": False, "indexes": [{"fields": ["data.metadata.namespace"]}]}
    id = StringField(primary_key=True)
    data = EmbeddedDocumentField(DocumentData, db_field="__data__")
    type_ = StringField(db_field="__type__")

    @classmethod
    @trace_fn
    def by_id(cls, db_alias: str, doc_id: str) -> "RefDoc":
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects.get(id=doc_id)

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
    def delete_by_id(cls, db_alias: str, doc_id: str) -> bool:
        """
        Deletes a document by its ID from the specified database.

        Returns True if the document was deleted, False if it was not found.
        """
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            result = SwitchedRefDoc.objects.filter(id=doc_id).delete()
            return result > 0
