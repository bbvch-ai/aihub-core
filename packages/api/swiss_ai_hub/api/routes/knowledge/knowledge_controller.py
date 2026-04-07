from typing import Annotated, Self

from fastapi import Depends, HTTPException, Path, Query, Security
from mongoengine import connect
from nats.aio.client import Client as NATS
from pymongo import MongoClient
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.dependencies import use_nats
from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.generative_ai.document.types.ingested_node import IngestedNode
from swiss_ai_hub.core.generative_ai.resources.models.llm.llm_config import LLMConfig
from swiss_ai_hub.core.i18n import LocaleHandler
from swiss_ai_hub.core.infrastructure import MongoSettings, use_s3_service, use_vector_store_factory
from swiss_ai_hub.core.persistence.rag.vectors import VectorStoreFactory
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.i18n.dependencies.use_locale import use_locale
from swiss_ai_hub.api.pagination.type.page_number import PageNumber
from swiss_ai_hub.api.pagination.type.page_size import PageSize
from swiss_ai_hub.api.routes.file.dto.signed_url_dto import SignedUrlDto
from swiss_ai_hub.api.routes.knowledge.dto.create_namespace_request import CreateNamespaceRequest
from swiss_ai_hub.api.routes.knowledge.dto.database_dto import DatabaseDTO
from swiss_ai_hub.api.routes.knowledge.dto.document_dto import DocumentDTO
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_request import DocumentUploadRequest
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_response import DocumentUploadResponse
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_validation_request import DocumentUploadValidationRequest
from swiss_ai_hub.api.routes.knowledge.dto.document_upload_validation_response import DocumentUploadValidationResponse
from swiss_ai_hub.api.routes.knowledge.dto.namespace_response import NamespaceResponse
from swiss_ai_hub.api.routes.knowledge.dto.node_summary_dto import NodeSummaryDTO
from swiss_ai_hub.api.routes.knowledge.dto.paginated_documents_response import PaginatedDocumentsResponse
from swiss_ai_hub.api.routes.knowledge.dto.update_namespace_request import UpdateNamespaceRequest
from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService


class KnowledgeController(TenantScopedController):
    name = ApiLocaleString.from_i18n_path("api.controllers.knowledge.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.knowledge.description")
    icon = "mage:book"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        route: str = "/knowledge",
        additionally_required_permission: str | None = None,
        translation_llm_config: LLMConfig | None = None,
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)
        self.docstore_client: MongoClient = connect(
            host=MongoSettings().CONNECTION_STRING.get_secret_value(), alias="docstore", uuidRepresentation="standard"
        )

        self.translation_llm_config = translation_llm_config

    def get_databases(self, route: str = "/databases") -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_databases(
            user: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.?>"))],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[DatabaseDTO]:
            """
            Returns all available buckets with their namespaces and document counts.
            Gets data from BucketEntity and NamespaceEntity in MongoDB.
            """
            all_databases = KnowledgeService.get_databases(t)
            accessible_databases = []
            access_checker = AccessChecker.from_user(user)
            for db in all_databases:
                if access_checker.has_access(f"aihub.user.knowledge.{db.name}.?>"):
                    accessible_namespaces = [
                        ns
                        for ns in db.namespaces
                        if access_checker.has_access(f"aihub.user.knowledge.{db.name}.{ns.name}")
                    ]
                    accessible_databases.append(
                        DatabaseDTO(
                            name=db.name,
                            display_name=db.display_name,
                            auto_sync=db.auto_sync,
                            namespaces=accessible_namespaces,
                        )
                    )
            return accessible_databases

        return self

    def get_documents_for_namespace(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents"
    ) -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_documents_for_namespace(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.{database}.{namespace}"))
            ],
            page: PageNumber = 1,
            page_size: PageSize = 20,
            search: Annotated[
                str | None, Query(min_length=1, max_length=200, description="Search by document title or filename")
            ] = None,
            sort_field: Annotated[
                str | None,
                Query(description="Field to sort by: document_title, created_at, updated_at"),
            ] = None,
            sort_order: Annotated[int, Query(description="Sort order: 1 for ascending, -1 for descending")] = 1,
        ) -> PaginatedDocumentsResponse:
            """
            Returns paginated documents for a specific namespace within a database.
            Optionally filter by document title or filename using the search parameter.
            Supports sorting by document_title, created_at, or updated_at.
            """
            if database in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            total, documents = KnowledgeService.get_paginated_documents(
                db=database,
                namespace=namespace,
                page=page,
                page_size=page_size,
                search=search,
                sort_field=sort_field,
                sort_order=sort_order,
            )

            total_pages = (total + page_size - 1) // page_size

            return PaginatedDocumentsResponse(
                documents=documents, total=total, page=page, page_size=page_size, total_pages=total_pages
            )

        return self

    def get_document_by_id(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/{document_id}"
    ) -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_document_by_id(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            document_id: Annotated[str, Path(title="Document ID")],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.{database}.{namespace}"))
            ],
        ) -> DocumentDTO:
            """
            Returns a single document by its ID.
            """
            if database in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            return KnowledgeService.get_document_by_id(db=database, document_id=document_id)

        return self

    def get_nodes_for_document(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/{document_id}/nodes"
    ) -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_nodes_for_document(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            document_id: Annotated[str, Path(title="Document ID")],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.{database}.{namespace}"))
            ],
            vector_store_factory: Annotated[VectorStoreFactory, Depends(use_vector_store_factory)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[IngestedNode]:
            """
            Returns nodes for a given document.
            """
            if database in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            return KnowledgeService.get_nodes(
                db=database,
                namespace=namespace,
                document_id=document_id,
                vector_store_factory=vector_store_factory,
                t=t,
            )

        return self

    def get_summary_nodes_for_document(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/{document_id}/summaries"
    ) -> Self:
        @self.router.get(route, tags=self.tags)
        async def get_summary_nodes_for_document(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            document_id: Annotated[str, Path(title="Document ID")],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.{database}.{namespace}"))
            ],
            vector_store_factory: Annotated[VectorStoreFactory, Depends(use_vector_store_factory)],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> list[NodeSummaryDTO]:
            """
            Returns nodes for a given document.
            """
            if database in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            return KnowledgeService.get_summary_nodes(
                db=database,
                namespace=namespace,
                document_id=document_id,
                vector_store_factory=vector_store_factory,
                t=t,
            )

        return self

    def create_namespace(self, route: str = "/databases/{database}/namespaces/{namespace}") -> Self:
        @self.router.post(route, tags=self.tags)
        async def create_namespace(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            request: CreateNamespaceRequest,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.knowledge.{database}.{namespace}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> NamespaceResponse:
            """
            Creates a new namespace (folder) in the specified database.
            """
            return await KnowledgeService.create_namespace(database, namespace, request, t, self.translation_llm_config)

        return self

    def update_namespace(self, route: str = "/databases/{database}/namespaces/{namespace}") -> Self:
        @self.router.put(route, tags=self.tags)
        async def update_namespace(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            request: UpdateNamespaceRequest,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.knowledge.{database}.{namespace}"))
            ],
            t: Annotated[LocaleHandler, Depends(use_locale)],
        ) -> NamespaceResponse:
            """
            Updates display name and description for an existing namespace.
            """
            return await KnowledgeService.update_namespace(namespace, request, t, self.translation_llm_config)

        return self

    def initiate_document_upload(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/upload/initiate"
    ) -> Self:
        @self.router.post(route, tags=self.tags)
        async def initiate_document_upload(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            request: DocumentUploadRequest,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.knowledge.{database}.{namespace}"))
            ],
            s3_service: Annotated[S3AnonymousFileAccessService, Depends(use_s3_service)],
        ) -> DocumentUploadResponse:
            """
            Initiates file upload by generating a presigned S3/MinIO URL.

            This endpoint validates the upload request and returns a presigned URL
            that allows the client to upload the file directly to S3/MinIO storage.
            """
            return await KnowledgeService.initiate_document_upload(database, namespace, request, s3_service)

        return self

    def validate_document_upload(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/upload/validate"
    ) -> Self:
        @self.router.post(route, tags=self.tags)
        async def validate_document_upload(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            request: DocumentUploadValidationRequest,
            nc: Annotated[NATS, Depends(use_nats)],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.knowledge.{database}.{namespace}"))
            ],
            s3_service: Annotated[S3AnonymousFileAccessService, Depends(use_s3_service)],
        ) -> DocumentUploadValidationResponse:
            """
            Validates whether a file was successfully uploaded to the datalake.

            This endpoint checks if a file exists in the configured datalake storage
            (S3/MinIO or Azure Blob Storage) after a presigned URL upload, and publishes
            a SourceUpdatedEvent to NATS to trigger downstream pipeline processing.
            """
            return await KnowledgeService.validate_document_upload(nc, database, namespace, request, s3_service)

        return self

    def get_document_url(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/{document_id}/url"
    ) -> Self:
        @self.router.get(route, tags=self.tags, summary="Get signed document URL")
        async def get_document_url(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            document_id: Annotated[str, Path(title="Document ID")],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.{database}.{namespace}"))
            ],
            s3_service: Annotated[S3AnonymousFileAccessService, Depends(use_s3_service)],
        ) -> SignedUrlDto:
            """Generates a presigned URL for downloading a document's source file."""
            if database in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            url = KnowledgeService.get_document_url(
                db=database, namespace=namespace, document_id=document_id, s3_service=s3_service
            )
            return SignedUrlDto(url=url)

        return self

    def get_supported_file_types(self, route: str = "/supported-types") -> Self:
        @self.router.get(route, tags=self.tags, summary="Get supported file types")
        async def get_supported_file_types(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.?>"))],
        ) -> list[str]:
            """
            Returns a list of supported file extensions (e.g., [".pdf", ".docx"])
            that can be used for client-side validation.
            """
            return KnowledgeService.get_supported_file_types()

        return self
