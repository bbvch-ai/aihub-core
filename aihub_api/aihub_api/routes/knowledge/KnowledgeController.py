from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.document.types.IngestedDocument import IngestedDocument
from aihub_lib.generative_ai.document.types.IngestedNode import IngestedNode
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.mongo.MongoSettings import MongoSettings
from aihub_lib.persistence.rag.vectors import VectorStoreFactory
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Path, Security
from mongoengine import connect
from pymongo import MongoClient

from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.knowledge.dto.DatabaseDTO import DatabaseDTO
from aihub_api.routes.knowledge.dto.NodeSummaryDTO import NodeSummaryDTO
from aihub_api.routes.knowledge.dto.PaginatedDocumentsResponse import PaginatedDocumentsResponse
from aihub_api.routes.knowledge.KnowledgeService import KnowledgeService


class KnowledgeController(Controller):
    name = LocaleString(en="Knowledge")
    description = LocaleString(en="Manage Documents and Files")
    icon = "famicons:library-outline"

    def __init__(
        self,
        *,
        auth: AuthHandler,
        vector_store_factory: VectorStoreFactory,
        route: str = "/knowledge",
        additionally_required_permission: str | None = None,
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)
        self.docstore_client: MongoClient = connect(
            host=MongoSettings().CONNECTION_STRING.get_secret_value(), alias="docstore"
        )

        self.vector_store_factory = vector_store_factory

    def get_databases(self, route: str = "/databases") -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_databases(
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
        ) -> list[DatabaseDTO]:
            """
            Returns all available knowledge namespaces with the number of documents in each.
            """
            return KnowledgeService.get_databases(self.docstore_client)

        return self

    def get_documents_for_namespace(
        self, route: str = "/databases/{database}/namespaces/{namespace}/documents"
    ) -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_documents_for_namespace(
            database: Annotated[str, Path(title="Database name")],
            namespace: Annotated[str, Path(title="Namespace")],
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
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
            database: Annotated[str, Path(title="Database name")],
            namespace: Annotated[str, Path(title="Namespace")],
            document_id: Annotated[str, Path(title="Document ID")],
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
        ) -> IngestedDocument:
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
            database: Annotated[str, Path(title="Database name")],
            namespace: Annotated[str, Path(title="Namespace")],
            document_id: Annotated[str, Path(title="Document ID")],
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
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
            database: Annotated[str, Path(title="Database name")],
            namespace: Annotated[str, Path(title="Namespace")],
            document_id: Annotated[str, Path(title="Document ID")],
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.admin.agent.?>"))],
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
