import logging

import mongoengine
from aihub_lib.generative_ai.document.accessor.AnonymousFileAccessSettings import AnonymousFileAccessSettings
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
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

from aihub_api.routes.knowledge.dto.CreateNamespaceRequest import CreateNamespaceRequest
from aihub_api.routes.knowledge.dto.DatabaseDTO import DatabaseDTO
from aihub_api.routes.knowledge.dto.DocumentDTO import DocumentDTO
from aihub_api.routes.knowledge.dto.NamespaceDTO import NamespaceDTO
from aihub_api.routes.knowledge.dto.NamespaceResponse import NamespaceResponse
from aihub_api.routes.knowledge.dto.NodeSummaryDTO import NodeSummaryDTO
from aihub_api.routes.knowledge.dto.UpdateNamespaceRequest import UpdateNamespaceRequest
from aihub_api.services.TranslationService import TranslationService

logger = logging.getLogger(__name__)


class KnowledgeService:
    @staticmethod
    def _ensure_db_exists(db: str):
        if db not in mongoengine.connection._connections:
            register_connection(alias=db, name=db, host=MongoSettings().CONNECTION_STRING.get_secret_value())

    @staticmethod
    def _get_datalake_files_in_namespace(bucket_name: str, namespace: str) -> list[DocumentDTO]:
        """
        Get all files from datalake in a specific namespace using the global file access configuration.

        This method supports both S3/MinIO and Azure Blob Storage based on the
        ANONYMOUS_FILE_ACCESS_SERVICE_STORAGE_BACKEND environment variable.
        """
        file_access_config = AnonymousFileAccessSettings()

        try:
            files_info = file_access_config.service.list_files(container=bucket_name, prefix=f"{namespace}/")

            all_files = []
            for file_info in files_info:
                key = file_info["key"]
                filename = key.split("/")[-1]
                file_namespace = key.split("/")[0]

                storage_backend = file_access_config.STORAGE_BACKEND
                if storage_backend == "azure":
                    document_uri = f"azure://{bucket_name}/{key}"
                else:
                    document_uri = f"s3://{bucket_name}/{key}"

                datalake_file = DocumentDTO(
                    id=key,
                    document_title=filename,
                    namespace=file_namespace,
                    updated_at=file_info.get("last_modified", ""),
                    created_at=file_info.get("last_modified", ""),
                    inserted_at="",
                    source=document_uri,
                    is_ingested=False,
                )
                all_files.append(datalake_file)

            return all_files

        except Exception as e:
            logger.error(f"Failed to list datalake files in {bucket_name}/{namespace}: {e}")
            # Fallback to empty list to prevent breaking the UI
            return []

    @staticmethod
    def _filter_processing_documents(
        datalake_files: list[DocumentDTO], processed_doc_sources: set[str]
    ) -> list[DocumentDTO]:
        """
        Filter datalake files to only include those not already processed (not in docstore).
        """
        processing_files = []
        for file in datalake_files:
            if file.source not in processed_doc_sources:
                processing_files.append(file)

        return processing_files

    @staticmethod
    def get_paginated_documents(
        db: str, namespace: str, page: int = 1, page_size: int = 20
    ) -> tuple[int, list[DocumentDTO]]:
        """
        Retrieves paginated documents for a given namespace, including both processed (docstore)
        and processing (datalake only) documents.
        """
        skip = (page - 1) * page_size

        KnowledgeService._ensure_db_exists(db)
        processed_count = RefDoc.count_by_namespace(db_alias=db, namespace=namespace)

        bucket = BucketEntity.get_bucket_by_db_name(db)
        datalake_files = KnowledgeService._get_datalake_files_in_namespace(bucket.bucket_name, namespace)

        processed_ref_docs = RefDoc.get_paginated_by_namespace(
            db_alias=db, namespace=namespace, skip=0, limit=processed_count
        )
        processed_doc_sources = {doc.data.metadata.source for doc in processed_ref_docs}

        processing_files = KnowledgeService._filter_processing_documents(datalake_files, processed_doc_sources)
        processing_count = len(processing_files)

        total = processed_count + processing_count

        if skip >= total:
            return total, []

        processed_documents = [DocumentDTO.from_ref_doc(doc) for doc in processed_ref_docs]

        all_documents = processed_documents + processing_files
        all_documents.sort(key=lambda doc: doc.updated_at, reverse=True)

        paginated_documents = all_documents[skip : skip + page_size]

        return total, paginated_documents

    @staticmethod
    def get_document_by_id(db: str, document_id: str) -> DocumentDTO:
        """
        Retrieves a single document by its ID.
        """
        KnowledgeService._ensure_db_exists(db)
        ref_doc = RefDoc.by_id(db_alias=db, doc_id=document_id)
        return DocumentDTO.from_ref_doc(ref_doc)

    @staticmethod
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
                processed_count = RefDoc.count_by_namespace(db_alias=db_name, namespace=ns_entity.namespace_name)

                datalake_files = KnowledgeService._get_datalake_files_in_namespace(
                    bucket.bucket_name, ns_entity.namespace_name
                )
                processed_docs = RefDoc.get_paginated_by_namespace(
                    db_alias=db_name, namespace=ns_entity.namespace_name, skip=0, limit=processed_count
                )
                processed_doc_sources = {doc.data.metadata.source for doc in processed_docs}
                processing_files = KnowledgeService._filter_processing_documents(datalake_files, processed_doc_sources)
                processing_count = len(processing_files)

                total_document_count = processed_count + processing_count
                namespaces.append(
                    NamespaceDTO.from_entity(entity=ns_entity, t=t, number_of_documents=total_document_count)
                )

            display_name = KnowledgeService._safe_extract_locale_string(bucket.name, t)
            database_dtos.append(
                DatabaseDTO(name=db_name, display_name=display_name, auto_sync=bucket.auto_sync, namespaces=namespaces)
            )

        return database_dtos

    @staticmethod
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
        entity = LocaleStringEntity.from_locale_string(locale_string)

        return await TranslationService.translate(
            translatable=entity, llm_config=llm_config, t=t, source_locale=t.locale
        )

    @staticmethod
    async def create_namespace(
        request: CreateNamespaceRequest, t: LocaleHandler, llm_config: LLMConfig | None = None
    ) -> NamespaceResponse:
        """
        Creates a new namespace (folder) in the specified database.
        """
        bucket = BucketEntity.get_bucket_by_db_name(request.database_name)

        try:
            NamespaceEntity.get_namespace_by_bucket_and_name(str(bucket.id), request.namespace_name)
            raise HTTPException(
                status_code=409,
                detail=f"Folder '{request.namespace_name}' already exists in database '{request.database_name}'.",
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
            namespace_name=request.namespace_name,
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

        return NamespaceResponse(
            id=str(updated_entity.id),
            bucket_id=updated_entity.bucket_id,
            namespace_name=updated_entity.namespace_name,
            folder_name=updated_entity.folder_name,
            display_name=KnowledgeService._safe_extract_locale_string(updated_entity.display_name, t),
            description=KnowledgeService._safe_extract_locale_string(updated_entity.description, t),
        )
