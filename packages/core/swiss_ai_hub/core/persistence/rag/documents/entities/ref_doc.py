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
from mongoengine.connection import get_db
from mongoengine.context_managers import switch_db

from swiss_ai_hub.core.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from swiss_ai_hub.core.persistence.rag.documents.utils.id_utils import source_to_doc_id

# Index field paths (MongoEngine uses db_field names)
_IDX_NAMESPACE = "data.metadata.namespace"
_IDX_IS_INGESTED = "data.metadata.is_ingested"
_IDX_SOURCE = "data.metadata.source"

# Stored field paths, for queries that bypass MongoEngine's field-name translation
_RAW_NAMESPACE = "__data__.metadata.namespace"
_RAW_IS_INGESTED = "__data__.metadata.is_ingested"
_RAW_SOURCE = "__data__.metadata.source"
_RAW_TEXT = "__data__.text"


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
    def list_ingested_summaries(cls, db_alias: str, namespace: str) -> list["RefDoc"]:
        """Every fully ingested document of a namespace, ordered by source and loaded with its metadata only.

        Queries the alias's database directly instead of through `switch_db`, which rebinds `RefDoc` for the whole
        process: two worker threads reading different knowledge databases at once were each handed the other's rows.
        The parsed text is the bulk of every row, and llama-index stores it twice, in `text` and again in the
        undeclared `text_resource`; projecting onto the fields a listing needs leaves out both. Legacy rows without
        `is_ingested` count as ingested, as everywhere else.
        """
        rows = (
            get_db(db_alias)[cls._meta["collection"]]
            .find(
                {
                    _RAW_NAMESPACE: namespace,
                    _RAW_IS_INGESTED: {"$ne": False},
                    "__type__": {"$ne": "placeholder"},
                },
                {"__type__": 1, "__data__.metadata": 1, "__data__.mimetype": 1},
            )
            .sort(_RAW_SOURCE, 1)
        )
        return [cls._from_son(son) for son in rows]

    @classmethod
    @trace_fn
    def search_ingested_ids(
        cls,
        db_alias: str,
        namespace: str,
        pattern: str,
        options: str,
        max_time_ms: int,
        with_source: bool = False,
    ) -> list[Self]:
        """Fully ingested documents of a namespace whose parsed text matches a PCRE pattern, ordered by id.

        FerretDB's backend decompresses the whole row, both copies of the text included, for every filter operator,
        projection and sort it evaluates, in the order the filter lists them. The regex therefore comes first, so the
        pending checks only run on the rows it matched, and rows carry only their id, sorted by the id column, unless
        the caller needs the source to apply a path glob.
        """
        rows = (
            get_db(db_alias)[cls._meta["collection"]]
            .find(
                {
                    _RAW_TEXT: {"$regex": pattern, "$options": options},
                    _RAW_NAMESPACE: namespace,
                    _RAW_IS_INGESTED: {"$ne": False},
                    "__type__": {"$ne": "placeholder"},
                },
                {_RAW_SOURCE: 1} if with_source else {"_id": 1},
            )
            .sort("_id", 1)
            .max_time_ms(max_time_ms)
        )
        return [cls._from_son(son) for son in rows]

    @classmethod
    @trace_fn
    def search_ingested_ids_among(
        cls,
        db_alias: str,
        namespace: str,
        pattern: str,
        options: str,
        candidate_ids: list[str],
        max_time_ms: int,
        with_source: bool = False,
    ) -> list[Self]:
        """`search_ingested_ids`, restricted to candidates the content search's trigram index found.

        The id filter comes first, so the primary key index picks the rows and only those are decompressed; the regex
        and the pending checks then decide exactly as the scan would.
        """
        rows = (
            get_db(db_alias)[cls._meta["collection"]]
            .find(
                {
                    "_id": {"$in": candidate_ids},
                    _RAW_TEXT: {"$regex": pattern, "$options": options},
                    _RAW_NAMESPACE: namespace,
                    _RAW_IS_INGESTED: {"$ne": False},
                    "__type__": {"$ne": "placeholder"},
                },
                {_RAW_SOURCE: 1} if with_source else {"_id": 1},
            )
            .sort("_id", 1)
            .max_time_ms(max_time_ms)
        )
        return [cls._from_son(son) for son in rows]

    @classmethod
    @trace_fn
    def first_with_text_range(
        cls, db_alias: str, doc_id: str, namespace: str, start: int | None, end: int | None
    ) -> tuple[Self, int, int] | None:
        """A document's metadata and one character range of its parsed text, cut in the database.

        Returns the document, whose text is the range, the full text's length and the range's start. Bounds follow
        Python slicing, negative ones counted from the end, and the database counts code points as Python does, so a
        caller reading a large document piece by piece never receives the rest of it, nor the `text_resource` copy.
        Safe to call from worker threads, unlike the `switch_db` readers: see `list_ingested_summaries`.
        """
        rows = get_db(db_alias)[cls._meta["collection"]].aggregate(
            [
                {"$match": {"_id": doc_id, _RAW_NAMESPACE: namespace}},
                {
                    "$project": {
                        "__type__": 1,
                        "__data__.metadata": 1,
                        "__data__.mimetype": 1,
                        "full_text": {"$ifNull": [f"${_RAW_TEXT}", ""]},
                        "text_length": {"$strLenCP": {"$ifNull": [f"${_RAW_TEXT}", ""]}},
                    }
                },
                {"$addFields": {"range_start": cls._range_bound(start, 0), "range_end": cls._range_bound(end, None)}},
                {
                    "$project": {
                        "__type__": 1,
                        "__data__.metadata": 1,
                        "__data__.mimetype": 1,
                        "__data__.text": {
                            "$substrCP": [
                                "$full_text",
                                "$range_start",
                                {"$max": [0, {"$subtract": ["$range_end", "$range_start"]}]},
                            ]
                        },
                        "text_length": 1,
                        "range_start": 1,
                    }
                },
            ]
        )
        son = next(rows, None)
        if son is None:
            return None
        text_length, range_start = son.pop("text_length"), son.pop("range_start")
        return cls._from_son(son), text_length, range_start

    @staticmethod
    def _range_bound(bound: int | None, default: int | None) -> int | str | dict[str, Any]:
        """A slice bound as a database expression over the text's length; a None default means the length itself."""
        if bound is None:
            return "$text_length" if default is None else default
        if bound < 0:
            return {"$max": [0, {"$add": ["$text_length", bound]}]}
        return {"$min": [bound, "$text_length"]}

    @classmethod
    @trace_fn
    def first_ingested_with_text(cls, db_alias: str, namespace: str, doc_id: str, max_time_ms: int) -> Self | None:
        """Metadata and parsed text of a document that is still fully ingested, never the `text_resource` copy; a
        document that turned pending since its id was found is None."""
        rows = (
            get_db(db_alias)[cls._meta["collection"]]
            .find(
                {
                    "_id": doc_id,
                    _RAW_NAMESPACE: namespace,
                    _RAW_IS_INGESTED: {"$ne": False},
                    "__type__": {"$ne": "placeholder"},
                },
                {"__type__": 1, "__data__.metadata": 1, "__data__.mimetype": 1, _RAW_TEXT: 1},
            )
            .max_time_ms(max_time_ms)
            .limit(1)
        )
        return next((cls._from_son(row) for row in rows), None)

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
    def get_all_ids(cls, db_alias: str) -> set[str]:
        """Ids only, so a scan over a whole database does not load every document's text."""
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return set(SwitchedRefDoc.objects.scalar("id"))

    @classmethod
    @trace_fn
    def get_existing_ids(cls, db_alias: str, doc_ids: list[str]) -> set[str]:
        """The subset of ``doc_ids`` that still has a document."""
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return set(SwitchedRefDoc.objects.filter(id__in=doc_ids).scalar("id"))

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

        An existing document is atomically reset to pending, whatever its current state. The reset is
        deliberately unconditional: document IDs are derived from the source URI, so re-uploading a file
        reuses the ID of the one it replaces, and a re-upload of an *already* pending document would
        otherwise leave the row byte-identical. Bumping ``updated_at`` on every re-upload is what lets
        the UI tell a re-upload apart from a document still awaiting deletion.

        Returns (ref_doc, created) where created is True if new placeholder was created.
        """
        doc_id = source_to_doc_id(source)

        with switch_db(cls, db_alias) as SwitchedRefDoc:
            updated = SwitchedRefDoc.objects(id=doc_id).update_one(
                set__data__metadata__is_ingested=False,
                set__data__metadata__updated_at=int(time.time()),
            )
            if updated:
                return SwitchedRefDoc.objects.get(id=doc_id), False

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
    def delete_by_namespace(cls, db_alias: str, namespace: str) -> int:
        """Delete every RefDoc of a namespace from the doc store in one server-side call; returns the count removed."""
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects.filter(data__metadata__namespace=namespace).delete()

    @classmethod
    @trace_fn
    def drop_database(cls, db_alias: str) -> None:
        """Drop the entire doc-store Mongo database backing a knowledge database.

        Used by database teardown, where every namespace is going away — cheaper and cleaner than
        deleting RefDocs namespace-by-namespace. The alias must already be registered by the caller.
        """
        database = get_db(db_alias)
        database.client.drop_database(database.name)

    @classmethod
    @trace_fn
    def mark_ingested(cls, db_alias: str, doc_id: str) -> bool:
        """Mark a document as fully ingested, returning whether a document was updated.

        Deliberately an atomic single-field `$set` rather than a full `save()`: the ingestion
        pipeline may re-write the same RefDoc concurrently, and a full rewrite would revert it.
        `updated_at` is left alone — it carries the *source file's* timestamp, which feeds asset
        data versions and the default document sort.
        """
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return bool(SwitchedRefDoc.objects(id=doc_id).update_one(set__data__metadata__is_ingested=True))
