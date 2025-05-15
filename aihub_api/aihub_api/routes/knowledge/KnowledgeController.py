from pathlib import Path
from typing import Annotated, List

from fastapi import Security

from aihub_api.pagination.type.PageNumber import PageNumber
from aihub_api.pagination.type.PageSize import PageSize
from aihub_api.routes.knowledge.KnowledgeService import KnowledgeService
from aihub_api.routes.knowledge.dto.DocumentDTO import DocumentDTO
from aihub_api.routes.knowledge.dto.PaginatedDocumentsResponse import PaginatedDocumentsResponse
from aihub_lib.persistence.rag.documents.entities.types.Namespace import Namespace
from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller


class KnowledgeController(Controller):

    name = LocaleString(en="Knowledge")
    description = LocaleString(en="Manage Documents and Files")
    icon = "simple-icons:threads"

    def __init__(self, route: str = "/knowledge", auth: AuthHandler | None = None, is_admin_only=True):
        super().__init__(route, auth, is_admin_only=is_admin_only)

    def get_documents_for_namespace(self, route: str = "/{namespace}/document") -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_documents_for_namespace(
            namespace: Annotated[str, Path(title="Namespace")],
            user: AuthenticatedUser = Security(self.auth),
            page: PageNumber = 1,
            page_size: PageSize = 20,
        ) -> PaginatedDocumentsResponse:
            """
            Returns all threads that the authenticated user is a member of.
            """
            total, documents = KnowledgeService.get_paginated_documents(
                namespace, page=page, page_size=page_size
            )

            total_pages = (total + page_size - 1) // page_size

            return PaginatedDocumentsResponse(
                documents=documents, total=total, page=page, page_size=page_size, total_pages=total_pages
            )

        return self

    def get_document_by_id(self, route: str = "/document/{document_id}") -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_document_by_id(
            document_id: Annotated[str, Path(title="Document ID")],
            user: AuthenticatedUser = Security(self.auth),
        ) -> DocumentDTO:
            """
            Returns a single document by its ID.
            """
            return KnowledgeService.get_document_by_id(document_id=document_id)

        return self

    def get_namespaces(self, route: str = "/namespace") -> "KnowledgeController":
        @self.router.get(route, tags=self.tags)
        async def get_namespaces(
            user: AuthenticatedUser = Security(self.auth),
        ) -> List[Namespace]:
            """
            Returns all available knowledge namespaces with the number of documents in each.
            """
            return KnowledgeService.get_all_namespaces()

        return self
