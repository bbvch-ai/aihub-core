import logging
import uuid

import boto3
import mongoengine

from aihub_api.routes.knowledge.dto.DocumentDTO import DocumentDTO
from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService
from aihub_lib.generative_ai.document.types.IngestedDocument import IngestedDocument
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.infrastructure.s3.S3StorageSettings import S3StorageSettings
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
from aihub_api.routes.knowledge.dto.DocumentUploadCompleteRequest import DocumentUploadCompleteRequest
from aihub_api.routes.knowledge.dto.DocumentUploadCompleteResponse import DocumentUploadCompleteResponse
from aihub_api.routes.knowledge.dto.DocumentUploadRequest import DocumentUploadRequest
from aihub_api.routes.knowledge.dto.DocumentUploadResponse import DocumentUploadResponse
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
    def _get_s3_client():
        """Get S3 client for datalake operations."""
        s3_config = S3StorageSettings()
        return boto3.client(
            "s3",
            endpoint_url=s3_config.ENDPOINT,
            aws_access_key_id=s3_config.ACCESS_KEY,
            aws_secret_access_key=s3_config.SECRET_KEY.get_secret_value(),
            region_name=s3_config.REGION,
        )

    @staticmethod
    def _get_datalake_files_in_namespace(bucket_name: str, namespace: str) -> list[DocumentDTO]:
        """
        Get all files from datalake in a specific namespace using direct S3 API calls.
        """
        s3_client = KnowledgeService._get_s3_client()

        all_files = []
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=bucket_name,
            Prefix=f"{namespace}/",
        )

        for page in page_iterator:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]
                if key.endswith("/"):
                    continue

                filename = key.split("/")[-1]
                file_namespace = key.split("/")[0]

                document_uri = f"s3://{bucket_name}/{key}"
                datalake_file = DocumentDTO(
                    id=key,
                    document_title=filename,
                    namespace=file_namespace,
                    updated_at="",
                    created_at="",
                    inserted_at="",
                    source=document_uri,
                    is_ingested=False
                )
                all_files.append(datalake_file)

        return all_files

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
        ref_docs_page = RefDoc.get_paginated_by_namespace(
            db_alias=db, namespace=namespace, skip=0, limit=1000000
        )
        processed_documents = [DocumentDTO.from_ref_doc(doc) for doc in ref_docs_page]

        processed_doc_sources = {doc.source for doc in processed_documents}

        bucket = BucketEntity.get_bucket_by_db_name(db)
        datalake_files = KnowledgeService._get_datalake_files_in_namespace(bucket.bucket_name, namespace)
        processing_files = KnowledgeService._filter_processing_documents(datalake_files, processed_doc_sources)

        all_documents = processed_documents + processing_files
        all_documents.sort(key=lambda doc: doc.updated_at, reverse=True)

        total = len(all_documents)
        paginated_documents = all_documents[skip : skip + page_size]

        return total, paginated_documents

    @staticmethod
    def get_document_by_id(db: str, document_id: str) -> IngestedDocument:
        """
        Retrieves a single document by its ID.
        """
        KnowledgeService._ensure_db_exists(db)
        ref_doc = RefDoc.by_id(db_alias=db, doc_id=document_id)
        return IngestedDocument.from_entity(ref_doc)

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
                    db_alias=db_name, namespace=ns_entity.namespace_name, skip=0, limit=1000000
                )
                processed_doc_sources = {doc.data.metadata.source for doc in processed_docs}
                processing_files = KnowledgeService._filter_processing_documents(datalake_files, processed_doc_sources)
                processing_count = len(processing_files)

                total_document_count = processed_count + processing_count
                namespaces.append(
                    NamespaceDTO.from_entity(entity=ns_entity, t=t, number_of_documents=total_document_count)
                )

            database_dtos.append(DatabaseDTO(name=db_name, namespaces=namespaces))

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
    async def _create_and_translate_locale_entity(
        text: str | None, t: LocaleHandler, llm_config: LLMConfig
    ) -> LocaleStringEntity | None:
        """Helper to create and translate a LocaleStringEntity."""
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
            display_name=t.extract(namespace_entity.display_name),
            description=t.extract(namespace_entity.description),
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
            display_name=t.extract(updated_entity.display_name) if updated_entity.display_name else None,
            description=t.extract(updated_entity.description) if updated_entity.description else None,
        )

    @staticmethod
    async def initiate_document_upload(request: DocumentUploadRequest) -> DocumentUploadResponse:
        """
        Initiates document upload by generating a presigned S3/MinIO URL.

        This method validates the upload request, generates a unique object key,
        and creates a presigned URL for direct upload to S3/MinIO storage.
        """

        try:
            bucket = BucketEntity.get_bucket_by_db_name(request.database)
        except DoesNotExist:
            raise HTTPException(status_code=404, detail=f"Database '{request.database}' not found")

        upload_id = str(uuid.uuid4())
        safe_filename = "".join(c for c in request.filename if c.isalnum() or c in ".-_").rstrip()
        object_key = f"{request.namespace}/{safe_filename}"

        container = bucket.bucket_name

        file_service = S3AnonymousFileAccessService()
        presigned_url = file_service.generate_upload_url(
            container=container,
            file_path=object_key,
            content_type=request.content_type,
            lifetime_hours=1,  # 1 hour expiration
        )

        logger.info(f"Generated presigned URL for upload: {upload_id}")

        return DocumentUploadResponse(
            upload_url=presigned_url,
            upload_id=upload_id,
            container=container,
            object_key=object_key,
            expires_in=3600,  # 1 hour in seconds
            namespace=request.namespace,
            database=request.database,
        )
