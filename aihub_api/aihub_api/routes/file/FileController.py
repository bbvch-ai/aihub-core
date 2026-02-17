from typing import Annotated, Self

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService
from aihub_lib.infrastructure.s3.use_s3 import use_s3_service
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Query, Security

from aihub_api.i18n.ApiLocaleString import ApiLocaleString
from aihub_api.routes.file.dto.SignedUrlDto import SignedUrlDto
from aihub_api.routes.file.FileService import FileService


class FileController(Controller):
    """
    A controller that manages secure access to files stored in Azure Blob Storage.

    Instead of proxying files, this controller generates a temporary, secure Azure SAS
    URL and redirects the client, offloading the bandwidth to Azure.
    """

    name = ApiLocaleString.from_i18n_path("api.controllers.file.name")
    description = ApiLocaleString.from_i18n_path("api.controllers.file.description")
    icon = "mage:file"

    def __init__(
        self, *, auth: AuthHandler, route: str = "/files", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_file_url(self, route: str = "/logged-in/url/{container}/{file_path:path}") -> Self:
        @self.router.get(route, tags=self.tags, summary="Get signed file URL")
        async def get_file_url(
            container: str,
            file_path: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            s3_service: Annotated[S3AnonymousFileAccessService, Depends(use_s3_service)],
        ) -> SignedUrlDto:
            """
            Generates a short-lived secure link to the blob resource, and returns the URL.
            """
            sas_url = s3_service.generate_sas_url(container, file_path)
            return SignedUrlDto(url=sas_url)

        return self

    def get_file_redirect(self, route: str = "/logged-in/redirect/{container}/{file_path:path}") -> Self:
        @self.router.get(route, tags=self.tags, summary="Access file as logged-in user")
        async def get_file_redirect(
            container: str,
            file_path: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
            s3_service: Annotated[S3AnonymousFileAccessService, Depends(use_s3_service)],
        ):
            """
            Generates a short-lived secure link to the blob resource, and redirects the user to it.
            """
            return FileService.get_authenticated_file_redirect(container, file_path, s3_service)

        return self

    def get_anonymous_file_url(self, route: str = "/anonymous/url/{container}/{file_path:path}") -> Self:
        @self.router.get(route, tags=self.tags, summary="Access file url via shared link")
        async def get_anonymous_file_url(
            container: str,
            file_path: str,
            s3_service: Annotated[S3AnonymousFileAccessService, Depends(use_s3_service)],
            expires: int = Query(..., description="The UNIX timestamp when the link expires."),
            signature: str = Query(..., description="The signature to validate the request."),
        ):
            """
            Provides access to a file via a temporary, signed URL and returns the URL.
            """
            return SignedUrlDto(
                url=FileService.get_anonymous_file_url(container, file_path, expires, signature, s3_service)
            )

        return self

    def get_anonymous_file_redirect(self, route: str = "/anonymous/redirect/{container}/{file_path:path}") -> Self:
        @self.router.get(route, tags=self.tags, summary="Access file via shared link")
        async def get_anonymous_file_redirect(
            container: str,
            file_path: str,
            s3_service: Annotated[S3AnonymousFileAccessService, Depends(use_s3_service)],
            expires: int = Query(..., description="The UNIX timestamp when the link expires."),
            signature: str = Query(..., description="The signature to validate the request."),
        ):
            """
            Provides access to a file via a temporary URL and redirects the user to it.
            """
            return FileService.get_anonymous_file_redirect(container, file_path, expires, signature, s3_service)

        return self
