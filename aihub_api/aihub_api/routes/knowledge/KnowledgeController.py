from pathlib import Path
from typing import Annotated, List

from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.infrastructure.azure.cosmos.docstore.CosmosDocstoreAccess import CosmosDocstoreAccess
from aihub_lib.nats.events.semantic.retriever.Node import Node
from aihub_lib.persistence.rag.vectors import VectorStoreFactory
from aihub_lib.routes.Controller import Controller
from fastapi import HTTPException, Security
from mongoengine import connect
from pymongo import MongoClient

from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.knowledge.dto.DatabaseDTO import DatabaseDTO
from aihub_api.routes.knowledge.dto.DocumentDTO import DocumentDTO
from aihub_api.routes.knowledge.dto.NodeSummaryDTO import NodeSummaryDTO
from aihub_api.routes.knowledge.dto.PaginatedDocumentsResponse import PaginatedDocumentsResponse
from aihub_api.routes.knowledge.KnowledgeService import KnowledgeService


class KnowledgeController(Controller):
    name = LocaleString(en="Knowledge")
    description = LocaleString(en="Manage Documents and Files")
    icon = "famicons:library-outline"

    def __init__(
        self,
        vector_store_factory: VectorStoreFactory,
        route: str = "/knowledge",
        auth: AuthHandler | None = None,
        is_admin_only=True,
    ):
        super().__init__(route, auth, is_admin_only=is_admin_only)
        self.docstore_client: MongoClient = connect(
            host=CosmosDocstoreAccess().get_connection_string(), alias="docstore"
        )

        self.vector_store_factory = vector_store_factory

    def get_databases(self, route: str = "/db") -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_databases(
            user: AuthenticatedUser = Security(self.auth),
        ) -> List[DatabaseDTO]:
            """
            Returns all available knowledge namespaces with the number of documents in each.
            """
            return KnowledgeService.get_databases(self.docstore_client)

        return self

    def get_documents_for_namespace(
        self, route: str = "/db/{db}/namespace/{namespace}/document"
    ) -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_documents_for_namespace(
            db: Annotated[str, Path(title="Database name")],
            namespace: Annotated[str, Path(title="Namespace")],
            user: AuthenticatedUser = Security(self.auth),
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> PaginatedDocumentsResponse:
            """
            Returns all threads that the authenticated user is a member of.
            """
            if db in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            total, documents = KnowledgeService.get_paginated_documents(
                db=db, namespace=namespace, page=page, page_size=page_size
            )

            total_pages = (total + page_size - 1) // page_size

            return PaginatedDocumentsResponse(
                documents=documents, total=total, page=page, page_size=page_size, total_pages=total_pages
            )

        return self

    def get_document_by_id(
        self, route: str = "/db/{db}/namespace/{namespace}/document/{document_id}"
    ) -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_document_by_id(
            db: Annotated[str, Path(title="Database name")],
            namespace: Annotated[str, Path(title="Namespace")],
            document_id: Annotated[str, Path(title="Document ID")],
            user: AuthenticatedUser = Security(self.auth),
        ) -> DocumentDTO:
            """
            Returns a single document by its ID.
            """
            if db in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            return KnowledgeService.get_document_by_id(db=db, document_id=document_id)

        return self

    def get_nodes_for_document(
        self, route: str = "/db/{db}/namespace/{namespace}/document/{document_id}/nodes"
    ) -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_nodes_for_document(
            db: Annotated[str, Path(title="Database name")],
            namespace: Annotated[str, Path(title="Namespace")],
            document_id: Annotated[str, Path(title="Document ID")],
            user: AuthenticatedUser = Security(self.auth),
        ) -> List[Node]:
            """
            Returns nodes for a given document.
            """
            if db in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            return KnowledgeService.get_nodes(
                db=db, namespace=namespace, document_id=document_id, vector_store_factory=self.vector_store_factory
            )

        return self

    def get_summary_nodes_for_document(
        self, route: str = "/db/{db}/namespace/{namespace}/document/{document_id}/summaries"
    ) -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_summary_nodes_for_document(
            db: Annotated[str, Path(title="Database name")],
            namespace: Annotated[str, Path(title="Namespace")],
            document_id: Annotated[str, Path(title="Document ID")],
            user: AuthenticatedUser = Security(self.auth),
        ) -> List[NodeSummaryDTO]:
            """
            Returns nodes for a given document.
            """
            if db in ["admin", "local", "config"]:
                raise HTTPException(status_code=403, detail="Not authorized to view this database")
            return KnowledgeService.get_summary_nodes(
                db=db, namespace=namespace, document_id=document_id, vector_store_factory=self.vector_store_factory
            )

        return self
