import logging
import uuid
from typing import Annotated

from fastapi import HTTPException
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from mongoengine import DoesNotExist, NotUniqueError
from nats.aio.client import Client as NATS
from pydantic import Field
from swiss_ai_hub.core.auth import UserIdentity
from swiss_ai_hub.core.events.pipeline import SourceUpdatedEvent
from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.generative_ai.document.types.file_type_config import FileTypeConfig
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler, LocaleString
from swiss_ai_hub.core.infrastructure import AIHubSettings, MongoConnectionRegistry, trace_fn
from swiss_ai_hub.core.persistence.i18n.locale_string_entity import LocaleStringEntity
from swiss_ai_hub.core.persistence.rag.datalake.entities import (
    BucketEntity,
    IngestorEntity,
    IngestorType,
    NamespaceEntity,
)
from swiss_ai_hub.core.persistence.rag.documents.entities.ref_doc import RefDoc
from swiss_ai_hub.core.persistence.rag.vectors import VectorStoreFactory
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    DOCUMENT_ID,
    NAMESPACE,
    NODE_TYPE_CONTENT,
    NODE_TYPE_SUMMARY,
    TYPE,
    NodeTypeValue,
)
from swiss_ai_hub.core.publishers import JSPublisher
from swiss_ai_hub.core.topic_managers import (
    PipelineInstanceTopicManager,
    PipelineSourceType,
    PipelineTargetType,
    PipelineTypeTopicManager,
)

from swiss_ai_hub.api.routes.knowledge.dto.batch_delete_documents_response import (
    BatchDeleteDocumentsResponse,
    DocumentDeletionResult,
)
from swiss_ai_hub.api.routes.knowledge.dto.create_database_request import CreateDatabaseRequest
from swiss_ai_hub.api.routes.knowledge.dto.create_namespace_request import CreateNamespaceRequest
from swiss_ai_hub.api.routes.knowledge.dto.database_dto import DatabaseDTO
from swiss_ai_hub.api.routes.knowledge.dto.database_response import DatabaseResponse
from swiss_ai_hub.api.routes.knowledge.dto.document_dto import DocumentDTO
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_request import DocumentUploadRequest
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_response import DocumentUploadResponse
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_validation_request import DocumentUploadValidationRequest
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_validation_response import DocumentUploadValidationResponse
from swiss_ai_hub.api.routes.knowledge.dto.ingestor_dto import IngestorDTO
from swiss_ai_hub.api.routes.knowledge.dto.namespace_dto import NamespaceDTO
from swiss_ai_hub.api.routes.knowledge.dto.namespace_response import NamespaceResponse
from swiss_ai_hub.api.routes.knowledge.dto.node_summary_dto import NodeSummaryDTO
from swiss_ai_hub.api.routes.knowledge.dto.update_namespace_request import UpdateNamespaceRequest
from swiss_ai_hub.api.routes.translation.translation_service import TranslationService

logger = logging.getLogger(__name__)

_S3_URI_SCHEME = "s3://"

class KnowledgeService:
    @staticmethod
    def _ensure_db_exists(db: str):
        MongoConnectionRegistry.ensure_alias(db)

    @staticmethod
    @trace_fn
    def get_paginated_documents(
        db: str,
        namespace: str,
        page: int = 1,
        page_size: int = 20,
        search: str | None = None,
        sort_field: str | None = None,
        sort_order: int = 1,
    ) -> tuple[int, list[DocumentDTO]]:
        """Retrieves paginated documents for a namespace.

        Default sort is by updated_at (newest first).
        Use sort_field=is_ingested to see pending documents first.
        """
        skip = (page - 1) * page_size
        KnowledgeService._ensure_db_exists(db)

        if search:
            total = RefDoc.count_search_in_namespace(db_alias=db, namespace=namespace, query=search)
            if skip >= total:
                return total, []
            ref_docs = RefDoc.search_in_namespace(
                db_alias=db,
                namespace=namespace,
                query=search,
                skip=skip,
                limit=page_size,
                sort_field=sort_field,
                sort_order=sort_order,
            )
        else:
            total = RefDoc.count_by_namespace(db_alias=db, namespace=namespace)
            if skip >= total:
                return total, []
            ref_docs = RefDoc.get_all_in_namespace(
                db_alias=db,
                namespace=namespace,
                skip=skip,
                limit=page_size,
                sort_field=sort_field,
                sort_order=sort_order,
            )

        return total, [DocumentDTO.from_ref_doc(doc) for doc in ref_docs]

    @staticmethod
    @trace_fn
    def get_document_by_id(db: str, document_id: str) -> DocumentDTO:
        """Retrieves a single document by its ID from the knowledge database."""
        KnowledgeService._ensure_db_exists(db)
        ref_doc = RefDoc.by_id(db_alias=db, doc_id=document_id)
        return DocumentDTO.from_ref_doc(ref_doc)

    @staticmethod
    @trace_fn
    def get_databases(t: LocaleHandler) -> list[DatabaseDTO]:
        """
        Retrieves all databases (buckets) with their available namespaces with the number of documents in each.

        Gets buckets from BucketEntity and namespaces from NamespaceEntity in MongoDB,
        then enriches with document counts from RefDoc (both pending and ingested).
        """
        database_dtos: list[DatabaseDTO] = []
        buckets = BucketEntity.get_all_buckets()
        show_legacy = AIHubSettings().SHOW_LEGACY_KNOWLEDGE

        for bucket in buckets:
            # A bucket flagged for teardown is being purged by the pipeline; hide it so it disappears
            # from the UI immediately and cannot be re-selected while the teardown job runs.
            if bucket.deleting:
                continue

            # The legacy default_rag / shared_rag databases are obsolete once their deploy-bound pipelines
            # are switched off, so they are hidden unless a deployment opts back in via SHOW_LEGACY_KNOWLEDGE.
            if not show_legacy and KnowledgeService._is_legacy_bucket(bucket):
                continue

            db_name = bucket.db_name
            KnowledgeService._ensure_db_exists(db_name)

            namespace_entities = NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))

            namespaces = []
            for ns_entity in namespace_entities:
                if ns_entity.deleting:
                    continue
                total_count = RefDoc.count_by_namespace(db_alias=db_name, namespace=ns_entity.namespace_name)
                namespaces.append(NamespaceDTO.from_entity(entity=ns_entity, t=t, number_of_documents=total_count))

            display_name = KnowledgeService._safe_extract_locale_string(bucket.name, t)
            database_dtos.append(
                DatabaseDTO(
                    name=db_name,
                    display_name=display_name,
                    auto_sync=bucket.auto_sync,
                    deletable=KnowledgeService._is_database_deletable(bucket),
                    namespaces=namespaces,
                )
            )

        return database_dtos

    @staticmethod
    @trace_fn
    def get_nodes(
        db: str,
        namespace: str,
        document_id: str,
        vector_store_factory: VectorStoreFactory,
        t: LocaleHandler,
        node_type: NodeTypeValue = NODE_TYPE_CONTENT,
    ) -> list[IngestedNode]:
        """Retrieves nodes for a document from the vector store."""
        filters = MetadataFilters(
            filters=[
                MetadataFilter(key=DOCUMENT_ID, value=document_id),
                MetadataFilter(key=TYPE, value=node_type),
                MetadataFilter(key=NAMESPACE, value=namespace),
            ]
        )
        vector_store = vector_store_factory(db)
        raw_nodes = vector_store.get_nodes(filters=filters, namespaces=[namespace])
        nodes = [IngestedNode.from_llama_index_node(node) for node in raw_nodes]
        nodes.sort(key=lambda node: node.index or 1)
        return nodes

    @staticmethod
    @trace_fn
    def get_summary_nodes(
        db: str, namespace: str, document_id: str, vector_store_factory: VectorStoreFactory, t: LocaleHandler
    ) -> list[NodeSummaryDTO]:
        nodes = KnowledgeService.get_nodes(
            db, namespace, document_id, vector_store_factory, t=t, node_type=NODE_TYPE_SUMMARY
        )
        summaries: dict[int, NodeSummaryDTO] = {i: NodeSummaryDTO(level=i, nodes=[]) for i in range(0, 7)}
        for node in nodes:
            summaries[node.heading_level].nodes.append(node)
        for level in range(0, 7):
            summaries[level].nodes.sort(key=lambda node: node.index)
        return list(summaries.values())

    @staticmethod
    def _safe_extract_locale_string(entity: LocaleStringEntity | None, t: LocaleHandler) -> str | None:
        if not entity:
            return None

        try:
            result = t.extract(entity.to_locale_string())
            return result if result and result.strip() else None
        except (ValueError, AttributeError):
            return None

    @staticmethod
    async def _create_and_translate_locale_entity(
        text: str | None, t: LocaleHandler, llm_config: LLMConfig, user: UserIdentity
    ) -> LocaleStringEntity | None:
        """Helper to create and translate a LocaleStringEntity."""
        if not text or text.strip() == "":
            return None

        locale_string = LocaleString(**{t.locale: text})

        translated_locale_string = await TranslationService.translate(
            locale_string=locale_string, llm_config=llm_config, t=t, user=user, source_locale=t.locale
        )
        return LocaleStringEntity.from_locale_string(translated_locale_string)

    @staticmethod
    @trace_fn
    def get_ingestors(t: LocaleHandler) -> list[IngestorDTO]:
        """Returns the ingestion pipelines a user may pick when creating a knowledge database.

        The platform's own pipelines come from ``IngestorType.selectable()``; any custom pipelines a
        deployment registered from its own pipeline container are appended, so they are offered in the UI too.
        """
        platform = [IngestorDTO.from_ingestor_type(ingestor, t) for ingestor in IngestorType.selectable()]
        custom = [IngestorDTO.from_ingestor(ingestor, t) for ingestor in IngestorEntity.custom()]
        return platform + custom

    @staticmethod
    async def create_database(
        database: str,
        request: CreateDatabaseRequest,
        t: LocaleHandler,
        s3_service: S3AnonymousFileAccessService,
        user: UserIdentity,
        llm_config: LLMConfig | None = None,
    ) -> DatabaseResponse:
        """
        Creates a new self-service knowledge database (bucket).

        The database name doubles as the S3 bucket, Mongo store, and Milvus collection name. The bucket
        records the ingestor that owns it, so the matching deployed pipeline picks it up without any
        redeployment.

        The S3 bucket is provisioned (with browser-upload CORS) up front so documents can be uploaded
        immediately, before the pipeline's first lazy ingest.
        """
        if not IngestorEntity.is_selectable(request.ingestor):
            raise HTTPException(
                status_code=400,
                detail=f"Ingestor '{request.ingestor}' cannot be assigned to a self-service database.",
            )

        try:
            BucketEntity.get_bucket_by_bucket_name(database)
            raise HTTPException(status_code=409, detail=f"Database '{database}' already exists.")
        except DoesNotExist:
            pass

        if s3_service.container_exists(database):
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Storage container '{database}' already exists but is not a knowledge database. "
                    "Choose a different name."
                ),
            )

        display_name_entity = await KnowledgeService._create_and_translate_locale_entity(
            text=request.display_name, t=t, llm_config=llm_config, user=user
        )
        description_entity = await KnowledgeService._create_and_translate_locale_entity(
            request.description, t, llm_config, user
        )

        # Persist the entity before provisioning storage: the unique bucket_name index serialises
        # concurrent admin calls (the loser gets NotUniqueError, not a second bucket), so any failure
        # before this point leaves no orphan. If provisioning fails, roll back both the container and
        # the row so a retry starts clean.
        try:
            bucket = BucketEntity.create_bucket(
                bucket_name=database,
                db_name=database,
                name=display_name_entity,
                description=description_entity,
                ingestor=request.ingestor,
            )
        except NotUniqueError:
            raise HTTPException(status_code=409, detail=f"Database '{database}' already exists.") from None

        try:
            s3_service.ensure_bucket_with_cors(database)
        except Exception:
            s3_service.delete_container(database)
            BucketEntity.delete_bucket(str(bucket.id))
            raise

        return DatabaseResponse(
            name=bucket.db_name,
            bucket_name=bucket.bucket_name,
            ingestor=bucket.ingestor,
            display_name=KnowledgeService._safe_extract_locale_string(bucket.name, t),
            description=KnowledgeService._safe_extract_locale_string(bucket.description, t),
        )

    @staticmethod
    async def create_namespace(
        database: str,
        namespace: str,
        request: CreateNamespaceRequest,
        t: LocaleHandler,
        user: UserIdentity,
        llm_config: LLMConfig | None = None,
    ) -> NamespaceResponse:
        """
        Creates a new namespace (folder) in the specified database.
        """
        bucket = BucketEntity.get_bucket_by_db_name(database)

        try:
            NamespaceEntity.get_namespace_by_bucket_and_name(str(bucket.id), namespace)
            raise HTTPException(
                status_code=409,
                detail=f"Folder '{namespace}' already exists in database '{database}'.",
            )
        except DoesNotExist:
            pass

        display_name_entity = await KnowledgeService._create_and_translate_locale_entity(
            text=request.display_name, t=t, llm_config=llm_config, user=user
        )
        description_entity = await KnowledgeService._create_and_translate_locale_entity(
            request.description, t, llm_config, user
        )

        namespace_entity = NamespaceEntity.create_namespace(
            bucket_id=str(bucket.id),
            namespace_name=namespace,
            folder_name=request.folder_name,
            display_name=display_name_entity,
            description=description_entity,
        )

        return NamespaceResponse(
            id=str(namespace_entity.id),
            bucket_id=namespace_entity.bucket_id,
            namespace_name=namespace_entity.namespace_name,
            folder_name=namespace_entity.folder_name,
            display_name=KnowledgeService._safe_extract_locale_string(namespace_entity.display_name, t),
            description=KnowledgeService._safe_extract_locale_string(namespace_entity.description, t),
        )

    @staticmethod
    async def update_namespace(
        namespace_id: str,
        request: UpdateNamespaceRequest,
        t: LocaleHandler,
        user: UserIdentity,
        llm_config: LLMConfig | None = None,
    ) -> NamespaceResponse:
        """
        Updates display name and description for an existing namespace.
        """
        try:
            NamespaceEntity.get_namespace_by_id(namespace_id)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Folder with ID '{namespace_id}' not found")

        display_name_entity = await KnowledgeService._create_and_translate_locale_entity(
            text=request.display_name, t=t, llm_config=llm_config, user=user
        )
        description_entity = await KnowledgeService._create_and_translate_locale_entity(
            request.description, t, llm_config, user
        )

        updated_entity = NamespaceEntity.update_namespace(
            namespace_id=namespace_id,
            display_name=display_name_entity,
            description=description_entity,
        )

        return NamespaceResponse(
            id=str(updated_entity.id),
            bucket_id=updated_entity.bucket_id,
            namespace_name=updated_entity.namespace_name,
            folder_name=updated_entity.folder_name,
            display_name=KnowledgeService._safe_extract_locale_string(updated_entity.display_name, t),
            description=KnowledgeService._safe_extract_locale_string(updated_entity.description, t),
        )

    @staticmethod
    async def initiate_document_upload(
        database: str, namespace: str, request: DocumentUploadRequest, s3_service: S3AnonymousFileAccessService
    ) -> DocumentUploadResponse:
        """
        Initiates document upload by generating a presigned URL for the globally configured datalake.

        This method resolves logical database/namespace names to physical storage locations,
        validates the upload request, generates a unique object key, and creates a presigned URL
        for direct upload to the configured datalake storage.
        """

        try:
            bucket_entity = BucketEntity.get_bucket_by_db_name(database)
            namespace_entity = NamespaceEntity.get_namespace_by_bucket_and_name(
                bucket_id=str(bucket_entity.id), namespace_name=namespace
            )
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Database '{database}' or namespace '{namespace}' not found",
            ) from e

        container = bucket_entity.bucket_name
        folder = namespace_entity.folder_name

        upload_id = str(uuid.uuid4())
        object_key = f"{folder}/{request.filename}"

        presigned_url = s3_service.generate_upload_url(
            container=container,
            file_path=object_key,
            content_type=request.content_type,
            lifetime_hours=1,  # 1 hour expiration
        )

        return DocumentUploadResponse(
            upload_url=presigned_url,
            upload_id=upload_id,
            container=container,
            object_key=object_key,
            expires_in=3600,  # 1 hour in seconds
            folder=folder,
        )

    @staticmethod
    @trace_fn
    async def _publish_source_updated_event(
        nc: Annotated[NATS, Field(description="NATS client connection")],
        database: Annotated[str, Field(description="Target knowledge database name")],
        container: Annotated[str, Field(description="Container/bucket name")],
        file_path: Annotated[str, Field(description="Path to the uploaded file")],
    ) -> None:
        """
        Publishes a SourceUpdatedEvent to NATS after a source file is added or removed.

        The Dagster observe job reacts by scanning the data lake, so the same event drives
        both ingestion (file uploaded) and cleanup (file deleted, picked up as an orphan).

        The subject is keyed on the owning ingestor rather than on the bucket, so a pipeline needs one
        JetStream stream and one consumer however many databases it serves. Frozen legacy pipelines
        keep the old per-instance subject: their images can no longer be changed to read a new one.
        """
        bucket = BucketEntity.get_bucket_by_db_name(database)

        if KnowledgeService._is_legacy_bucket(bucket):
            topic_manager = PipelineInstanceTopicManager(
                source_type=PipelineSourceType.DATALAKE,
                source_id=container,
                target_type=PipelineTargetType.KNOWLEDGE,
                target_id=database,
            )
            stream_name, stream_subject = topic_manager.get_stream()
            subject_for = topic_manager.get_subject_for_specific_event_in_pipeline_instance
        else:
            type_topic_manager = PipelineTypeTopicManager(pipeline_type=bucket.ingestor)
            stream_name, stream_subject = type_topic_manager.get_stream()

            def subject_for(run_key: str, event_name: str, event_id: str) -> str:
                return type_topic_manager.get_subject_for_source_updated(
                    bucket_name=container,
                    db_name=database,
                    run_key=run_key,
                    event_name=event_name,
                    event_id=event_id,
                )

        event = SourceUpdatedEvent(path=file_path)
        subject = subject_for(run_key=event.event_id, event_name=event.event_name, event_id=event.event_id)

        # JetStream, and the stream ensured first: an upload that lands before the sensor's first tick
        # created the stream would otherwise be dropped, leaving the document pending until the next
        # scheduled observation.
        publisher = JSPublisher(name="KnowledgeService", js=nc.jetstream())
        await publisher.ensure_stream_exists(stream_name, stream_subject)
        await publisher.publish_event(event, subject)

        logger.info(f"Published SourceUpdatedEvent for file {file_path} to subject {subject}")

    @staticmethod
    async def validate_document_upload(
        nc: NATS,
        database: str,
        namespace: str,
        request: DocumentUploadValidationRequest,
        s3_service: S3AnonymousFileAccessService,
    ) -> DocumentUploadValidationResponse:
        """
        Validates whether a file was successfully uploaded to the globally configured datalake.

        This method verifies that the uploaded file exists in the datalake storage, creates
        a placeholder RefDoc to track the file with status=pending, and publishes a
        SourceUpdatedEvent to NATS to trigger downstream pipeline processing via Dagster sensors.
        """
        try:
            bucket_entity = BucketEntity.get_bucket_by_db_name(database)
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Database '{database}' or namespace '{namespace}' not found",
            ) from e

        container = bucket_entity.bucket_name
        object_key = request.file_path

        exists = s3_service.verify_file_exists(container=container, file_path=object_key)

        if exists:
            KnowledgeService._ensure_db_exists(database)
            source = f"{_S3_URI_SCHEME}{container}/{object_key}"
            document_title = object_key.split("/")[-1]

            try:
                RefDoc.get_or_create_placeholder(
                    db_alias=database,
                    source=source,
                    namespace=namespace,
                    document_title=document_title,
                )
            except Exception as e:
                logger.warning(f"Failed to create placeholder for {object_key}: {e}")

            # Publish event to trigger pipeline - this must succeed or upload fails
            try:
                await KnowledgeService._publish_source_updated_event(
                    nc=nc,
                    database=database,
                    container=container,
                    file_path=object_key,
                )
            except Exception as e:
                logger.exception(f"Failed to publish event for {object_key}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Upload succeeded but processing could not be initiated. Please try again.",
                ) from e

        return DocumentUploadValidationResponse(exists=exists, file_path=object_key, container=container)

    @staticmethod
    @trace_fn
    def get_document_url(
        db: str,
        namespace: str,
        document_id: str,
        s3_service: S3AnonymousFileAccessService,
        as_attachment: bool = False,
    ) -> str:
        """Generates a presigned S3 URL for a document's source file.

        `as_attachment` forces a browser download via `Content-Disposition: attachment`
        instead of inline preview (requires SeaweedFS ≥ 4.01 to honor the override).
        """
        KnowledgeService._ensure_db_exists(db)
        try:
            ref_doc = RefDoc.by_id_and_namespace(db_alias=db, doc_id=document_id, namespace=namespace)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Document not found")
        source = ref_doc.data.metadata.source
        source = source.removeprefix(_S3_URI_SCHEME)
        parts = source.split("/", 1)
        container = parts[0]
        file_path = parts[1] if len(parts) > 1 else ""
        content_disposition = None
        if as_attachment:
            filename = file_path.rsplit("/", 1)[-1]
            content_disposition = f'attachment; filename="{filename}"'
        return s3_service.generate_sas_url(container, file_path, response_content_disposition=content_disposition)

    @staticmethod
    def get_supported_file_types() -> list[str]:
        return FileTypeConfig().get_unique_extensions()

    @staticmethod
    @trace_fn
    async def delete_document(
        nc: NATS,
        db: str,
        namespace: str,
        document_id: str,
        s3_service: S3AnonymousFileAccessService,
    ) -> None:
        """
        Schedules permanent deletion of a document by removing its source file from the data lake.

        Only the S3 file (and its figures) is deleted directly. The published SourceUpdatedEvent
        triggers the pipeline's observe job, which drops the partition; the chained remove job
        then cleans the doc store and vector store. Keeping the pipeline as the single writer for
        those stores avoids races with in-flight ingestion runs.
        """
        KnowledgeService._ensure_db_exists(db)
        try:
            ref_doc = RefDoc.by_id_and_namespace(db_alias=db, doc_id=document_id, namespace=namespace)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail="Document not found")

        source = ref_doc.data.metadata.source
        container, file_path = KnowledgeService._delete_source_from_data_lake(s3_service, source)
        await KnowledgeService._publish_source_updated_event(
            nc=nc, database=db, container=container, file_path=file_path
        )

    @staticmethod
    def _delete_source_from_data_lake(s3_service: S3AnonymousFileAccessService, source: str) -> tuple[str, str]:
        if not source.startswith(_S3_URI_SCHEME):
            raise HTTPException(status_code=500, detail=f"Document source '{source}' is not an {_S3_URI_SCHEME} URI")

        parts = source.removeprefix(_S3_URI_SCHEME).split("/", 1)
        container = parts[0]
        file_path = parts[1] if len(parts) > 1 else ""
        if not file_path:
            raise HTTPException(status_code=500, detail=f"Document source '{source}' has no object key")

        s3_service.delete_file(container=container, file_path=file_path)
        return container, file_path

    @staticmethod
    @trace_fn
    async def batch_delete_documents(
        nc: NATS,
        db: str,
        namespace: str,
        document_ids: list[str],
        s3_service: S3AnonymousFileAccessService,
    ) -> BatchDeleteDocumentsResponse:
        """Best-effort batch deletion: each document is scheduled independently with a per-document result."""
        results = []
        for document_id in document_ids:
            try:
                await KnowledgeService.delete_document(nc, db, namespace, document_id, s3_service)
                status = "scheduled"
            except HTTPException as e:
                status = "not_found" if e.status_code == 404 else "failed"
            except Exception:
                logger.exception(f"Failed to schedule deletion of document {document_id} in {db}/{namespace}")
                status = "failed"
            results.append(DocumentDeletionResult(document_id=document_id, status=status))
        return BatchDeleteDocumentsResponse(results=results)

    @staticmethod
    def _is_legacy_bucket(bucket: BucketEntity) -> bool:
        """Whether the bucket belongs to a legacy deploy-bound pipeline (``default_rag`` / ``shared_rag``)."""
        return bucket.ingestor in (IngestorType.DEFAULT_RAG.value, IngestorType.SHARED_RAG.value)

    @staticmethod
    def _is_database_deletable(bucket: BucketEntity) -> bool:
        """Whether the whole database may be torn down.

        Auto-synced databases are refilled by their source, and the legacy ``default_rag`` / ``shared_rag``
        buckets are bound to a deploy-time pipeline that expects the bucket to keep existing — so neither
        database itself is deletable. Namespaces inside them remain individually deletable.
        """
        return not bucket.auto_sync and not KnowledgeService._is_legacy_bucket(bucket)

    @staticmethod
    def _reject_if_auto_synced(bucket: BucketEntity) -> None:
        """Guard shared by database and namespace deletion: an auto-synced database's content is owned by its
        external source and would just be re-synced, so nothing in it may be deleted from the UI."""
        if bucket.auto_sync:
            raise HTTPException(
                status_code=403, detail=f"Database '{bucket.db_name}' is auto-synced and cannot be deleted."
            )

    @staticmethod
    def _reject_undeletable_database(bucket: BucketEntity) -> None:
        """Whole-database deletion guard: auto-synced and legacy databases are protected.

        Only the database itself is protected for legacy buckets — their namespaces stay deletable — because
        the legacy per-bucket pipeline expects the bucket to exist. Mongo-internal / main-db names are rejected
        earlier, at the controller, via the reserved-name guard.
        """
        KnowledgeService._reject_if_auto_synced(bucket)
        if KnowledgeService._is_legacy_bucket(bucket):
            raise HTTPException(status_code=403, detail=f"Legacy database '{bucket.db_name}' cannot be deleted.")

    @staticmethod
    @trace_fn
    def delete_database(database: str) -> None:
        """Flag a knowledge database (and its namespaces) for teardown; the pipeline does the heavy purge.

        The synchronous work is O(1): flip the ``deleting`` flag, which excludes the rows from every
        enumeration path so ingestion stops at once. The flag *is* the durable teardown request — the
        pipeline's teardown sensor reads it directly, so there is no message that could be published,
        acknowledged and then lost, leaving the database hidden but never purged. The Dagster job drops the
        Milvus collection, the doc-store database and the S3 bucket, and hard-deletes the rows last.
        """
        try:
            bucket = BucketEntity.get_bucket_by_db_name(database)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Database '{database}' not found") from None

        KnowledgeService._reject_undeletable_database(bucket)

        BucketEntity.mark_deleting(str(bucket.id))
        NamespaceEntity.mark_all_deleting_for_bucket(str(bucket.id))

    @staticmethod
    @trace_fn
    def delete_namespace(database: str, namespace: str) -> None:
        """Flag a single namespace for teardown; the bucket and its other namespaces survive.

        Same flag-as-request shape as ``delete_database``. The teardown job deletes the namespace's S3
        folder, its doc-store rows and its Milvus vectors (by metadata filter — never a partition drop,
        since namespaces share hashed partitions), then hard-deletes the row.
        """
        try:
            bucket = BucketEntity.get_bucket_by_db_name(database)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Database '{database}' not found") from None

        KnowledgeService._reject_if_auto_synced(bucket)

        try:
            namespace_entity = NamespaceEntity.get_namespace_by_bucket_and_name(str(bucket.id), namespace)
        except DoesNotExist:
            raise HTTPException(
                status_code=404, detail=f"Folder '{namespace}' not found in database '{database}'"
            ) from None

        NamespaceEntity.mark_deleting(str(namespace_entity.id))
