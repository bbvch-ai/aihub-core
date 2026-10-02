from typing import Annotated, Self

from fastapi import File, Query, Response, Security, UploadFile
from swiss_ai_hub.core.auth.dependencies.auth_handler import AuthHandler
from swiss_ai_hub.core.auth.identity.user_identity import UserIdentity
from swiss_ai_hub.core.routes import TenantScopedController

from swiss_ai_hub.api.decorators.access_catalog import access_catalog_entry
from swiss_ai_hub.api.i18n.api_locale_string import ApiLocaleString
from swiss_ai_hub.api.routes.user_knowledge.dto.create_folder_request import CreateFolderRequest
from swiss_ai_hub.api.routes.user_knowledge.dto.file_path_dto import FilePathDTO
from swiss_ai_hub.api.routes.user_knowledge.dto.folder_listing_dto import FolderListingDTO
from swiss_ai_hub.api.routes.user_knowledge.dto.move_file_request import MoveFileRequest
from swiss_ai_hub.api.routes.user_knowledge.user_knowledge_service import UserKnowledgeService

OWN_FILES = "aihub.user.files.own"


class UserKnowledgeController(TenantScopedController):
    """The signed-in user's own file space, the files they and their agents work with in the code sandbox."""

    name = ApiLocaleString.from_i18n_path("api.controllers.user_knowledge.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.user_knowledge.description")
    icon = "mage:folder"

    def __init__(self, *, auth: AuthHandler, route: str = "/user-knowledge", **kwargs):
        super().__init__(auth=auth, route=route, **kwargs)

    @access_catalog_entry(i18n_path="api.access.capabilities.ops.files.own")
    def list_user_files(self, route: str = "") -> Self:
        @self.router.get(route, tags=self.tags, response_model=FolderListingDTO)
        async def list_user_files(
            user: Annotated[UserIdentity, Security(self.user_with_permission(OWN_FILES))],
            folder: Annotated[str, Query(description="The folder to list; '.' is the top.")] = ".",
        ) -> FolderListingDTO:
            return await UserKnowledgeService.list_folder(user, folder)

        return self

    def get_user_file_content(self, route: str = "/content") -> Self:
        @self.router.get(route, tags=self.tags, response_class=Response)
        async def get_user_file_content(
            user: Annotated[UserIdentity, Security(self.user_with_permission(OWN_FILES))],
            path: Annotated[str, Query(description="The file to read.")],
            download: Annotated[
                bool, Query(description="Whether the browser saves the file instead of showing it.")
            ] = False,
        ) -> Response:
            return await UserKnowledgeService.file_content(user, path, download)

        return self

    def upload_user_file(self, route: str = "/files") -> Self:
        @self.router.post(route, tags=self.tags, response_model=FilePathDTO)
        async def upload_user_file(
            user: Annotated[UserIdentity, Security(self.user_with_permission(OWN_FILES))],
            file: Annotated[UploadFile, File(description="The file to add; one with the same name is replaced.")],
            folder: Annotated[str, Query(description="The folder to add it to.")] = ".",
        ) -> FilePathDTO:
            return await UserKnowledgeService.upload(user, folder, file)

        return self

    def create_user_folder(self, route: str = "/folders") -> Self:
        @self.router.post(route, tags=self.tags, response_model=FilePathDTO)
        async def create_user_folder(
            user: Annotated[UserIdentity, Security(self.user_with_permission(OWN_FILES))],
            request: CreateFolderRequest,
        ) -> FilePathDTO:
            return await UserKnowledgeService.create_folder(user, request.path)

        return self

    def move_user_file(self, route: str = "/move") -> Self:
        @self.router.post(route, tags=self.tags, response_model=FilePathDTO)
        async def move_user_file(
            user: Annotated[UserIdentity, Security(self.user_with_permission(OWN_FILES))],
            request: MoveFileRequest,
        ) -> FilePathDTO:
            return await UserKnowledgeService.move(user, request.source, request.destination)

        return self

    def delete_user_file(self, route: str = "") -> Self:
        @self.router.delete(route, tags=self.tags, response_model=FilePathDTO)
        async def delete_user_file(
            user: Annotated[UserIdentity, Security(self.user_with_permission(OWN_FILES))],
            path: Annotated[str, Query(description="The file, or folder with everything in it, to delete.")],
        ) -> FilePathDTO:
            return await UserKnowledgeService.delete(user, path)

        return self
