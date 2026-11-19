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
_RAW_CONTENT_HASH = "__data__.metadata.content_hash"
_RAW_METADATA = "__data__.metadata"
_RAW_EXCLUDED_EMBED = "__data__.excluded_embed_metadata_keys"
_RAW_EXCLUDED_LLM = "__data__.excluded_llm_metadata_keys"
# Re-uploading or finishing a document ends whatever failure it was reported with
_CLEARED_INGESTION_FAILURE = {
    "unset__data__metadata__ingestion_failed_attempts": True,
    "unset__data__metadata__ingestion_failed_at": True,
    "unset__data__metadata__ingestion_gave_up": True,
}
# What a summary needs from a row: type, metadata and mimetype, never either copy of the text
_SUMMARY_FIELDS = {"__type__": 1, "__data__.metadata": 1, "__data__.mimetype": 1}
_PROJECT = "$project"
_TEXT_LENGTH = "$text_length"


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

    # Set by the pipeline's retry sensor while the latest ingestion attempt has failed; absent otherwise. A successful
    # parse rewrites the record and mark_ingested clears them, so they never outlive the failure they describe.
    ingestion_failed_attempts = IntField(required=False)
    ingestion_failed_at = IntField(required=False)
    ingestion_gave_up = BooleanField(required=False)

    # Set by classification; absent on a document that was not classified. The attribute values stay dynamic fields,
    # since their keys and value types come from `DocumentTypeCatalog`, not from this schema.
    document_type = StringField(required=False)
    document_types = ListField(StringField(), required=False)
    document_classification_version = IntField(required=False)
    document_type_version = IntField(required=False)
    document_normalizer_version = IntField(required=False)


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
    def list_ingested_summaries(cls, db_alias: str, namespace: str, max_time_ms: int | None = None) -> list["RefDoc"]:
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
                _SUMMARY_FIELDS,
            )
            .sort(_RAW_SOURCE, 1)
        )
        if max_time_ms is not None:
            rows = rows.max_time_ms(max_time_ms)
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
                    _PROJECT: {
                        **_SUMMARY_FIELDS,
                        "full_text": {"$ifNull": [f"${_RAW_TEXT}", ""]},
                        "text_length": {"$strLenCP": {"$ifNull": [f"${_RAW_TEXT}", ""]}},
                    }
                },
                {"$addFields": {"range_start": cls._range_bound(start, 0), "range_end": cls._range_bound(end, None)}},
                {
                    _PROJECT: {
                        **_SUMMARY_FIELDS,
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
            return _TEXT_LENGTH if default is None else default
        if bound < 0:
            return {"$max": [0, {"$add": [_TEXT_LENGTH, bound]}]}
        return {"$min": [bound, _TEXT_LENGTH]}

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
                {**_SUMMARY_FIELDS, _RAW_TEXT: 1},
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
                _PROJECT: {
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
        """Create a placeholder RefDoc for a file that is being uploaded/processed, raising NotUniqueError if one exists.

        Uses deterministic ID based on source path to enable upsert on processing completion. Insert-only, because
        MongoEngine's save() of a document with an id replaces whatever record holds that id: a parse or an upload
        finishing at the same moment would lose its record to an empty placeholder.
        """
        current_time = int(time.time())
        metadata = cls._placeholder_metadata(source, namespace, document_title, timestamp=current_time)
        return cls._insert_placeholder(db_alias, source, metadata)

    @classmethod
    @trace_fn
    def create_failed_placeholder(
        cls,
        db_alias: str,
        source: str,
        namespace: str,
        failed_attempts: int,
        gave_up: bool,
        failed_at: int,
    ) -> bool:
        """Create a placeholder already showing a failed ingestion, returning False when a record exists.

        For a file whose first parse failed, which leaves no record to report the failure on. Created in one insert
        with the failure, so a record that appears meanwhile is never overwritten, and dated to the failure: the file's
        own timestamp is unknown here, and every later attempt starts after it, so its failure passes the date check of
        `record_ingestion_failure`.
        """
        metadata = cls._placeholder_metadata(source, namespace, None, timestamp=failed_at)
        metadata.ingestion_failed_attempts = failed_attempts
        metadata.ingestion_gave_up = gave_up
        metadata.ingestion_failed_at = failed_at
        try:
            cls._insert_placeholder(db_alias, source, metadata)
        except NotUniqueError:
            return False
        return True

    @staticmethod
    def _placeholder_metadata(source: str, namespace: str, document_title: str | None, timestamp: int) -> Metadata:
        return Metadata(
            source=source,
            namespace=namespace,
            version="1",
            is_ingested=False,
            created_at=timestamp,
            updated_at=timestamp,
            inserted_at=timestamp,
            content_hash="",
            type="content",
            document_title=document_title or source.split("/")[-1],
        )

    @classmethod
    def _insert_placeholder(cls, db_alias: str, source: str, metadata: Metadata) -> Self:
        doc_id = source_to_doc_id(source)
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
            ref_doc.save(force_insert=True)
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
                **_CLEARED_INGESTION_FAILURE,
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
            return bool(
                SwitchedRefDoc.objects(id=doc_id).update_one(
                    set__data__metadata__is_ingested=True, **_CLEARED_INGESTION_FAILURE
                )
            )

    @classmethod
    @trace_fn
    def record_ingestion_failure(
        cls,
        db_alias: str,
        doc_id: str,
        failed_attempts: int,
        gave_up: bool,
        failed_at: int,
        attempt_started_at: int,
    ) -> bool:
        """Report a pending document's failed ingestion, returning whether a pending document was updated.

        Matches only a document that is still pending: once its nodes are in the vector store it is retrievable,
        and a later failure (of its summaries, say) must not show it as failed. Matches only a record dated strictly
        before the failed attempt started: a re-upload resets the record and dates it to the upload, even while the
        old run is still going, and that run never saw the new file. A record from the same second is left alone too,
        as it cannot be ordered; the failure of a later attempt, which a retry always brings, is reported. Writes nothing when the stored
        values are already these, so the retry sensor can report the same failure on every tick at the cost of a read.
        """
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            pending = SwitchedRefDoc.objects(
                id=doc_id, data__metadata__is_ingested=False, data__metadata__updated_at__lt=attempt_started_at
            )
            if not pending.count():
                return False
            pending.filter(
                Q(data__metadata__ingestion_failed_attempts__ne=failed_attempts)
                | Q(data__metadata__ingestion_gave_up__ne=gave_up)
            ).update_one(
                set__data__metadata__ingestion_failed_attempts=failed_attempts,
                set__data__metadata__ingestion_gave_up=gave_up,
                set__data__metadata__ingestion_failed_at=failed_at,
            )
            return True

    @classmethod
    @trace_fn
    def clear_ingestion_failures(cls, db_alias: str, doc_ids: list[str]) -> int:
        """Return documents whose file is being ingested afresh to processing, returning how many were reported failed.

        A file that changed at its source gets no new record until its parse succeeds, so without this it would show
        the previous version's failure while the new version is being ingested.
        """
        with switch_db(cls, db_alias) as SwitchedRefDoc:
            return SwitchedRefDoc.objects(
                id__in=doc_ids, data__metadata__ingestion_failed_attempts__exists=True
            ).update(**_CLEARED_INGESTION_FAILURE)

    @classmethod
    @trace_fn
    def list_classification_states(cls, db_alias: str) -> list["RefDoc"]:
        """Every fully ingested document of a database with its metadata and embedding exclusions, without text.

        What a classification backfill decides its work from: the versions a document was classified with, and
        whether frontmatter excluded keys of its own, which marks a synced record. Read straight from the alias's
        database, as `list_ingested_summaries` does, and in source order so a run's progress is reproducible.
        """
        rows = (
            get_db(db_alias)[cls._meta["collection"]]
            .find(
                {_RAW_IS_INGESTED: {"$ne": False}, "__type__": {"$ne": "placeholder"}},
                {"__type__": 1, _RAW_METADATA: 1, _RAW_EXCLUDED_EMBED: 1},
            )
            .sort(_RAW_SOURCE, 1)
        )
        return [cls._from_son(son) for son in rows]

    @classmethod
    @trace_fn
    def text_of(cls, db_alias: str, doc_id: str, content_hash: str) -> str | None:
        """The parsed text of one document, or None when it is gone or its content changed since it was listed."""
        row = get_db(db_alias)[cls._meta["collection"]].find_one(
            {"_id": doc_id, _RAW_CONTENT_HASH: content_hash}, {_RAW_TEXT: 1}
        )
        return row["__data__"].get("text", "") if row else None

    @classmethod
    @trace_fn
    def set_classification(
        cls,
        db_alias: str,
        doc_id: str,
        content_hash: str,
        metadata: dict[str, Any],
        excluded_keys: list[str],
    ) -> bool:
        """Write a document's classification, unless its content changed since it was read; returns whether it did.

        One atomic update of only these keys, like `mark_ingested`, so a concurrent re-ingestion is never reverted.
        The content hash guards the case where it already happened: a re-ingested document is classified by
        ingestion itself, and values read from its old text must not overwrite those.
        """
        result = get_db(db_alias)[cls._meta["collection"]].update_one(
            {"_id": doc_id, _RAW_CONTENT_HASH: content_hash},
            {
                "$set": {f"{_RAW_METADATA}.{key}": value for key, value in metadata.items()},
                "$addToSet": {
                    _RAW_EXCLUDED_EMBED: {"$each": excluded_keys},
                    _RAW_EXCLUDED_LLM: {"$each": excluded_keys},
                },
            },
        )
        return result.matched_count == 1
