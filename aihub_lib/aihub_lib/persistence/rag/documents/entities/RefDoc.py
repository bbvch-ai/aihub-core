from typing import Any, Dict, List, Optional

from mongoengine import (
    DictField,
    Document,
    DynamicEmbeddedDocument,
    EmbeddedDocumentField,
    IntField,
    ListField,
    StringField,
)


class Metadata(DynamicEmbeddedDocument):
    namespace = StringField(required=True)
    source = StringField(required=True)
    content_hash = StringField(required=True)
    type = StringField(required=True)
    version = StringField(required=True)
    created_at = IntField(required=True)
    updated_at = IntField(required=True)
    inserted_at = IntField(required=True)


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
    meta = {"collection": "documents-data", "strict": False, "indexes": [{"fields": ["data.metadata.namespace"]}]}
    id = StringField(primary_key=True)
    data = EmbeddedDocumentField(DocumentData, db_field="__data__")  # Renamed for querying convenience
    type_ = StringField(db_field="__type__")  # Renamed for consistency

    # Static methods for querying
    @classmethod
    def by_id(cls, doc_id: str) -> "RefDoc":
        return cls.objects.get(id=doc_id)

    @classmethod
    def by_namespace(
        cls,
        namespace: str,
        exclude_ids: Optional[List[str]] = None,
    ) -> List["RefDoc"]:
        return list(cls.objects.filter(data__metadata__namespace=namespace, id__nin=(exclude_ids or [])))

    @classmethod
    def count_by_namespace(
            cls,
            namespace: str,
    ) -> int:
        """Counts the total number of documents in a given namespace."""
        query_filter = {"data__metadata__namespace": namespace}
        return cls.objects.filter(**query_filter).count()

    @classmethod
    def get_paginated_by_namespace(
        cls,
        namespace: str,
        skip: int,
        limit: int,
    ) -> List["RefDoc"]:
        """
        Retrieves a paginated list of documents from a given namespace.
        Documents are ordered by their internal ID by default MongoEngine behavior without explicit order_by.
        """
        query_filter = {"data__metadata__namespace": namespace}
        return list(cls.objects.filter(**query_filter).skip(skip).limit(limit).order_by('id'))

    @classmethod
    def get_all_namespaces(cls) -> List[str]:
        """
        Returns a list of all unique namespace values.
        """
        return cls.objects.distinct("data.metadata.namespace")

    @classmethod
    def get_namespaces_with_counts(cls) -> List[Dict[str, Any]]:
        """
        Returns a list of dictionaries containing namespace names and document counts.
        Uses MongoDB aggregation pipeline to get this information in a single query.
        """
        pipeline = [
            # Group by namespace and count documents
            {
                "$group": {
                    "_id": "$__data__.metadata.namespace",
                    "count": {"$sum": 1}
                }
            },
            # Format the output
            {
                "$project": {
                    "name": "$_id",
                    "number_of_documents": "$count",
                    "_id": 0
                }
            }
        ]

        return list(cls.objects.aggregate(pipeline))
