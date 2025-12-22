from typing import Annotated

from aihub_lib.auth.access.AccessChecker import AccessChecker
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.i18n.LocaleHandler import LocaleHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.persistence.rag.vectors import VectorStoreFactory
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, HTTPException, Path, Security
from mongoengine import connect
from nats.aio.client import Client as NATS
from pymongo import MongoClient

from aihub_api.i18n.dependencies.use_locale import use_locale
from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.knowledge.dto.CreateNamespaceRequest import CreateNamespaceRequest
from aihub_api.routes.knowledge.dto.DatabaseDTO import DatabaseDTO
from aihub_api.routes.knowledge.dto.DocumentDTO import DocumentDTO
from aihub_api.routes.knowledge.dto.DocumentUploadRequest import DocumentUploadRequest
from aihub_api.routes.knowledge.dto.DocumentUploadResponse import DocumentUploadResponse
from aihub_api.routes.knowledge.dto.DocumentUploadValidationRequest import DocumentUploadValidationRequest
from aihub_api.routes.knowledge.dto.DocumentUploadValidationResponse import DocumentUploadValidationResponse
from aihub_api.routes.knowledge.dto.NamespaceResponse import NamespaceResponse
from aihub_api.routes.knowledge.dto.NodeSummaryDTO import NodeSummaryDTO
from aihub_api.routes.knowledge.dto.PaginatedDocumentsResponse import PaginatedDocumentsResponse
from aihub_api.routes.knowledge.dto.UpdateNamespaceRequest import UpdateNamespaceRequest
from aihub_api.routes.knowledge.KnowledgeService import KnowledgeService


class KnowledgeController(Controller):
    name = LocaleString(en="Knowledge Base", de="Wissensdatenbank", fr="Base de connaissances", it="Base di conoscenza")
    description = LocaleString(
        en="Manage your knowledge base and documents",
        de="Verwalten Sie Ihre Wissensdatenbank und Dokumente",
        fr="Gérez votre base de connaissances et documents",
        it="Gestisci la tua base di conoscenza e documenti",
    )
    icon = "famicons:library-outline"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        vector_store_factory: VectorStoreFactory,
        route: str = "/knowledge",
        additionally_required_permission: str | None = None,
        translation_llm_config: LLMConfig | None = None,
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)
        self.docstore_client: MongoClient = connect(
            host=MongoSettings().CONNECTION_STRING.get_secret_value(), alias="docstore", uuidRepresentation="standard"
        )

        self.vector_store_factory = vector_store_factory
        self.translation_llm_config = translation_llm_config

    def get_databases(self, route: str = "/databases") -> "KnowledgeController":
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
    ) -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_documents_for_namespace(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.{database}.{namespace}"))
            ],
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> PaginatedDocumentsResponse:
            """
            Returns paginated documents for a specific namespace within a database.
            """
            if database in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            total, documents = KnowledgeService.get_paginated_documents(
                db=database, namespace=namespace, page=page, page_size=page_size
            )

            total_pages = (total + page_size - 1) // page_size

            return PaginatedDocumentsResponse(
                documents=documents, total=total, page=page, page_size=page_size, total_pages=total_pages
            )

        return self

    def get_document_by_id(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/{document_id}"
    ) -> "KnowledgeController":
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
    ) -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_nodes_for_document(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            document_id: Annotated[str, Path(title="Document ID")],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.{database}.{namespace}"))
            ],
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
                vector_store_factory=self.vector_store_factory,
            )

        return self

    def get_summary_nodes_for_document(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/{document_id}/summaries"
    ) -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_summary_nodes_for_document(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            document_id: Annotated[str, Path(title="Document ID")],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.user.knowledge.{database}.{namespace}"))
            ],
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
                vector_store_factory=self.vector_store_factory,
            )

        return self

    def create_namespace(self, route: str = "/databases/{database}/namespaces/{namespace}") -> "KnowledgeController":
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

    def update_namespace(self, route: str = "/databases/{database}/namespaces/{namespace}") -> "KnowledgeController":
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
    ) -> "KnowledgeController":
        @self.router.post(route, tags=self.tags)
        async def initiate_document_upload(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            request: DocumentUploadRequest,
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.knowledge.{database}.{namespace}"))
            ],
        ) -> DocumentUploadResponse:
            """
            Initiates file upload by generating a presigned S3/MinIO URL.

            This endpoint validates the upload request and returns a presigned URL
            that allows the client to upload the file directly to S3/MinIO storage.
            """
            return await KnowledgeService.initiate_document_upload(database, namespace, request)

        return self

    def validate_document_upload(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/upload/validate"
    ) -> "KnowledgeController":
        @self.router.post(route, tags=self.tags)
        async def validate_document_upload(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            request: DocumentUploadValidationRequest,
            nc: Annotated[NATS, Depends(use_nats)],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.knowledge.{database}.{namespace}"))
            ],
        ) -> DocumentUploadValidationResponse:
            """
            Validates whether a file was successfully uploaded to the datalake.

            This endpoint checks if a file exists in the configured datalake storage
            (S3/MinIO or Azure Blob Storage) after a presigned URL upload, and publishes
            a SourceUpdatedEvent to NATS to trigger downstream pipeline processing.
            """
            return await KnowledgeService.validate_document_upload(nc, database, namespace, request)

        return self

    def get_supported_file_types(self, route: str = "/supported-types") -> "KnowledgeController":
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

    def delete_document(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents/{document_id}"
    ) -> "KnowledgeController":
        @self.router.delete(route, tags=self.tags, summary="Delete a document")
        async def delete_document(
            database: Annotated[str, Path(title="Database name", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            namespace: Annotated[str, Path(title="Namespace", pattern=r"^[a-zA-Z0-9][a-zA-Z0-9 _\-]*$")],
            document_id: Annotated[str, Path(title="Document ID")],
            nc: Annotated[NATS, Depends(use_nats)],
            _: Annotated[
                UserIdentity, Security(self.user_with_permission("aihub.admin.knowledge.{database}.{namespace}"))
            ],
        ) -> dict[str, bool]:
            """
            Deletes a document from the knowledge base.

            This endpoint permanently removes:
            - The document from the vector store (Milvus)
            - The document from the document store (MongoDB)
            - The source file from the datalake (S3/MinIO)
            - Associated figure images from the datalake

            Requires admin permission for the namespace.
            """
            if database in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to modify this database")
            await KnowledgeService.delete_document(
                nc=nc,
                database=database,
                namespace=namespace,
                document_id=document_id,
                vector_store_factory=self.vector_store_factory,
            )
            return {"success": True}

        return self
