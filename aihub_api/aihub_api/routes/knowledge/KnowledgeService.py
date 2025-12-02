import logging
import time
import uuid
from functools import lru_cache, wraps
from typing import Annotated

import mongoengine
from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService
from aihub_lib.generative_ai.document.types.FileTypeConfig import FileTypeConfig
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.generative_ai.utils.path_utils import FIGURES_DIRECTORY_NAME
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.events.pipeline.SourceUpdatedEvent import SourceUpdatedEvent
from aihub_lib.nats.publishers.NCPublisher import NCPublisher
from aihub_lib.nats.topic_managers.pipeline.PipelineInstanceTopicManager import PipelineInstanceTopicManager
from aihub_lib.persistence.i18n.LocaleStringEntity import LocaleStringEntity
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from aihub_lib.persistence.rag.documents.entities.RefDoc import RefDoc
from aihub_lib.persistence.rag.vectors import VectorStoreFactory
from aihub_lib.persistence.rag.vectors.node_metadata import (
    DOCUMENT_ID,
    NAMESPACE,
    NODE_TYPE_CONTENT,
    NODE_TYPE_SUMMARY,
    TYPE,
    NodeTypeValue,
)
from fastapi import HTTPException
from llama_index.core.vector_stores import MetadataFilter, MetadataFilters
from mongoengine import DoesNotExist, register_connection
from nats.aio.client import Client as NATS
from pydantic import Field

from aihub_api.routes.knowledge.dto.CreateNamespaceRequest import CreateNamespaceRequest
from aihub_api.routes.knowledge.dto.DatabaseDTO import DatabaseDTO
from aihub_api.routes.knowledge.dto.DocumentDTO import DocumentDTO
from aihub_api.routes.knowledge.dto.DocumentUploadRequest import DocumentUploadRequest
from aihub_api.routes.knowledge.dto.DocumentUploadResponse import DocumentUploadResponse
from aihub_api.routes.knowledge.dto.DocumentUploadValidationRequest import DocumentUploadValidationRequest
from aihub_api.routes.knowledge.dto.DocumentUploadValidationResponse import DocumentUploadValidationResponse
from aihub_api.routes.knowledge.dto.NamespaceDTO import NamespaceDTO
from aihub_api.routes.knowledge.dto.NamespaceResponse import NamespaceResponse
from aihub_api.routes.knowledge.dto.NodeSummaryDTO import NodeSummaryDTO
from aihub_api.routes.knowledge.dto.UpdateNamespaceRequest import UpdateNamespaceRequest
from aihub_api.services.TranslationService import TranslationService

logger = logging.getLogger(__name__)


def ttl_cache(seconds: int, maxsize: int = 128):
    def decorator(func):
        func = lru_cache(maxsize=maxsize)(func)
        func.lifetime = seconds
        func.expiration = time.time() + seconds

        @wraps(func)
        def wrapped_func(*args, **kwargs):
            if time.time() >= func.expiration:
                func.cache_clear()
                func.expiration = time.time() + func.lifetime
            return func(*args, **kwargs)

        def invalidate():
            func.cache_clear()
            func.expiration = time.time() + func.lifetime

        wrapped_func.invalidate = invalidate
        wrapped_func.cache_info = func.cache_info
        wrapped_func.cache_clear = func.cache_clear

        return wrapped_func

    return decorator


class KnowledgeService:
    @staticmethod
    def _ensure_db_exists(db: str):
        try:
            mongoengine.connection.get_connection(alias=db)
        except Exception:
            register_connection(
                alias=db,
                name=db,
                host=MongoSettings().CONNECTION_STRING.get_secret_value(),
                uuidRepresentation="standard",
            )

    @staticmethod
    def _get_datalake_files_in_namespace(bucket_name: str, namespace: str) -> list[DocumentDTO]:
        """
        Get all files from datalake in a specific namespace using the global file access configuration.

        Files in the __figures__ directory are excluded as they are generated artifacts
        from document processing and should not be displayed in the knowledge interface.
        """
        files_info = S3AnonymousFileAccessService().list_files(container=bucket_name, prefix=f"{namespace}/")

        all_files = []
        for file_info in files_info:
            key = file_info["key"]

            if f"/{FIGURES_DIRECTORY_NAME}/" in key:
                continue

            filename = key.split("/")[-1]
            file_namespace = key.split("/")[0]

            document_uri = f"s3://{bucket_name}/{key}"

            all_files.append(
                DocumentDTO(
                    id=key,
                    document_title=filename,
                    namespace=file_namespace,
                    updated_at=file_info.get("last_modified", ""),
                    created_at=file_info.get("last_modified", ""),
                    inserted_at="",
                    source=document_uri,
                    is_ingested=False,
                )
            )

        return all_files

    @staticmethod
    @ttl_cache(seconds=300, maxsize=256)  # 5 minutes TTL, 256 max entries
    def _get_processed_sources(db: str, namespace: str) -> set[str]:
        count = RefDoc.count_by_namespace(db_alias=db, namespace=namespace)
        if count == 0:
            return set()

        docs = RefDoc.get_paginated_by_namespace(db_alias=db, namespace=namespace, skip=0, limit=count)
        return {doc.data.metadata.source for doc in docs}

    @staticmethod
    @ttl_cache(seconds=300, maxsize=256)  # 5 minutes TTL, 256 max entries
    def _get_processed_documents_sorted(db: str, namespace: str) -> list[DocumentDTO]:
        count = RefDoc.count_by_namespace(db_alias=db, namespace=namespace)
        if count == 0:
            return []

        docs = RefDoc.get_paginated_by_namespace(db_alias=db, namespace=namespace, skip=0, limit=count)
        documents = [DocumentDTO.from_ref_doc(doc) for doc in docs]
        documents.sort(key=lambda doc: doc.updated_at, reverse=True)
        return documents

    @classmethod
    @ttl_cache(seconds=300, maxsize=256)  # 5 minutes TTL, 256 max entries
    def _get_unprocessed_files(cls, db: str, namespace: str, bucket_name: str) -> list[DocumentDTO]:
        datalake_files = cls._get_datalake_files_in_namespace(bucket_name, namespace)
        processed_sources = cls._get_processed_sources(db, namespace)

        unprocessed = [f for f in datalake_files if f.source not in processed_sources]
        unprocessed.sort(key=lambda doc: doc.updated_at, reverse=True)
        return unprocessed

    @staticmethod
    def invalidate_cache():
        KnowledgeService._get_processed_sources.invalidate()
        KnowledgeService._get_processed_documents_sorted.invalidate()
        KnowledgeService._get_unprocessed_files.invalidate()

    @staticmethod
    @trace_fn
    def get_paginated_documents(
        db: str, namespace: str, page: int = 1, page_size: int = 20
    ) -> tuple[int, list[DocumentDTO]]:
        """
        Retrieves paginated documents for a given namespace, including both processed (docstore)
        and processing (datalake only) documents.
        """
        skip = (page - 1) * page_size

        KnowledgeService._ensure_db_exists(db)
        bucket = BucketEntity.get_bucket_by_db_name(db)

        unprocessed = KnowledgeService._get_unprocessed_files(db, namespace, bucket.bucket_name)
        unprocessed_count = len(unprocessed)

        processed = KnowledgeService._get_processed_documents_sorted(db, namespace)
        processed_count = len(processed)

        total = unprocessed_count + processed_count

        if skip >= total:
            return total, []

        if skip + page_size <= unprocessed_count:
            return total, unprocessed[skip : skip + page_size]

        if skip < unprocessed_count:
            result = unprocessed[skip:]
            remaining = page_size - len(result)
            result.extend(processed[:remaining])
            return total, result

        processed_skip = skip - unprocessed_count
        return total, processed[processed_skip : processed_skip + page_size]

    @staticmethod
    @trace_fn
    def get_document_by_id(db: str, document_id: str) -> DocumentDTO:
        """
        Retrieves a single document by its ID.
        """
        KnowledgeService._ensure_db_exists(db)
        ref_doc = RefDoc.by_id(db_alias=db, doc_id=document_id)
        return DocumentDTO.from_ref_doc(ref_doc)

    @staticmethod
    @trace_fn
    def get_databases(t: LocaleHandler) -> list[DatabaseDTO]:
        """
        Retrieves all databases (buckets) with their available namespaces with the number of documents in each.
        Gets buckets from BucketEntity and namespaces from NamespaceEntity in MongoDB,
        then enriches with document stats from docstore. Returns format compatible with web frontend.
        """
        database_dtos: list[DatabaseDTO] = []
        buckets = BucketEntity.get_all_buckets()

        for bucket in buckets:
            db_name = bucket.db_name
            KnowledgeService._ensure_db_exists(db_name)

            namespace_entities = NamespaceEntity.get_namespaces_by_bucket(str(bucket.id))

            namespaces = []
            for ns_entity in namespace_entities:
                unprocessed = KnowledgeService._get_unprocessed_files(
                    db_name, ns_entity.namespace_name, bucket.bucket_name
                )
                processed_count = RefDoc.count_by_namespace(db_alias=db_name, namespace=ns_entity.namespace_name)
                total_count = len(unprocessed) + processed_count

                namespaces.append(NamespaceDTO.from_entity(entity=ns_entity, t=t, number_of_documents=total_count))

            display_name = KnowledgeService._safe_extract_locale_string(bucket.name, t)
            database_dtos.append(
                DatabaseDTO(name=db_name, display_name=display_name, auto_sync=bucket.auto_sync, namespaces=namespaces)
            )

        return database_dtos

    @staticmethod
    @trace_fn
    def get_nodes(
        db: str,
        namespace: str,
        document_id: str,
        vector_store_factory: VectorStoreFactory,
        node_type: NodeTypeValue = NODE_TYPE_CONTENT,
    ) -> list[IngestedNode]:
        filters = MetadataFilters(
            filters=[
                MetadataFilter(key=DOCUMENT_ID, value=document_id),
                MetadataFilter(key=TYPE, value=node_type),
                MetadataFilter(key=NAMESPACE, value=namespace),
            ]
        )
        vector_store = vector_store_factory(db)
        raw_nodes = vector_store.get_nodes(filters=filters)
        nodes = [IngestedNode.from_llama_index_node(node) for node in raw_nodes]
        nodes.sort(key=lambda node: node.index or 1)
        return nodes

    @staticmethod
    @trace_fn
    def get_summary_nodes(
        db: str, namespace: str, document_id: str, vector_store_factory: VectorStoreFactory
    ) -> list[NodeSummaryDTO]:
        nodes = KnowledgeService.get_nodes(
            db, namespace, document_id, vector_store_factory, node_type=NODE_TYPE_SUMMARY
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
        text: str | None, t: LocaleHandler, llm_config: LLMConfig
    ) -> LocaleStringEntity | None:
        """Helper to create and translate a LocaleStringEntity."""
        if not text or text.strip() == "":
            return None

        locale_string = LocaleString(**{t.locale: text})

        translated_locale_string = await TranslationService.translate(
            locale_string=locale_string, llm_config=llm_config, t=t, source_locale=t.locale
        )
        return LocaleStringEntity.from_locale_string(translated_locale_string)

    @staticmethod
    async def create_namespace(
        database: str,
        namespace: str,
        request: CreateNamespaceRequest,
        t: LocaleHandler,
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
            text=request.display_name, t=t, llm_config=llm_config
        )
        description_entity = await KnowledgeService._create_and_translate_locale_entity(
            request.description, t, llm_config
        )

        namespace_entity = NamespaceEntity.create_namespace(
            bucket_id=str(bucket.id),
            namespace_name=namespace,
            folder_name=request.folder_name,
            display_name=display_name_entity,
            description=description_entity,
        )

        KnowledgeService.invalidate_cache()

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
        namespace_id: str, request: UpdateNamespaceRequest, t: LocaleHandler, llm_config: LLMConfig | None = None
    ) -> NamespaceResponse:
        """
        Updates display name and description for an existing namespace.
        """
        try:
            NamespaceEntity.get_namespace_by_id(namespace_id)
        except Exception:
            raise HTTPException(status_code=404, detail=f"Folder with ID '{namespace_id}' not found")

        display_name_entity = await KnowledgeService._create_and_translate_locale_entity(
            text=request.display_name, t=t, llm_config=llm_config
        )
        description_entity = await KnowledgeService._create_and_translate_locale_entity(
            request.description, t, llm_config
        )

        updated_entity = NamespaceEntity.update_namespace(
            namespace_id=namespace_id,
            display_name=display_name_entity,
            description=description_entity,
        )

        KnowledgeService.invalidate_cache()

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
        database: str, namespace: str, request: DocumentUploadRequest
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

        presigned_url = S3AnonymousFileAccessService().generate_upload_url(
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
        Publishes a SourceUpdatedEvent to NATS when a file is successfully uploaded.

        This event triggers downstream pipeline processing via Dagster sensors that
        listen for file upload events on the pipeline stream.
        """
        topic_manager = PipelineInstanceTopicManager(
            source_type="datalake",
            source_id=container,
            target_type="knowledge",
            target_id=database,
        )

        event = SourceUpdatedEvent(path=file_path)
        subject = topic_manager.get_subject_for_specific_event_in_pipeline_instance(
            run_key=event.event_id,
            event_name=event.event_name,
            event_id=event.event_id,
        )

        publisher = NCPublisher(name="KnowledgeService", nc=nc)
        await publisher.publish_event(event, subject)

        logger.info(f"Published SourceUpdatedEvent for file {file_path} to subject {subject}")

    @staticmethod
    async def validate_document_upload(
        nc: NATS, database: str, namespace: str, request: DocumentUploadValidationRequest
    ) -> DocumentUploadValidationResponse:
        """
        Validates whether a file was successfully uploaded to the globally configured datalake.

        This method verifies that the uploaded file exists in the datalake storage and publishes
        a SourceUpdatedEvent to NATS to trigger downstream pipeline processing via Dagster sensors.
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

        exists = S3AnonymousFileAccessService().verify_file_exists(container=container, file_path=object_key)

        if exists:
            try:
                KnowledgeService.invalidate_cache()
                await KnowledgeService._publish_source_updated_event(
                    nc=nc,
                    database=database,
                    container=container,
                    file_path=object_key,
                )
            except Exception as e:
                logger.exception(f"Failed to publish SourceUpdatedEvent for {object_key}: {e}")
                # Don't fail the validation - file was successfully uploaded
        return DocumentUploadValidationResponse(exists=exists, file_path=object_key, container=container)

    @staticmethod
    def get_supported_file_types() -> list[str]:
        return FileTypeConfig().get_unique_extensions()
