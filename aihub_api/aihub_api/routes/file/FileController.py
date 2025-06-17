from aihub_lib.auth.AuthenticatedUser import AuthenticatedUser
from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.routes.Controller import Controller
from fastapi import Query, Security

from aihub_api.routes.file.dto.SignedUrlDto import SignedUrlDto
from aihub_api.routes.file.FileService import FileService


class FileController(Controller):
    """
    A controller that manages secure access to files stored in Azure Blob Storage.

    Instead of proxying files, this controller generates a temporary, secure Azure SAS
    URL and redirects the client, offloading the bandwidth to Azure.
    """

    name = LocaleString(en="File Access")
    description = LocaleString(en="Provides secure access to stored files")
    icon = "line-md:file"

    def __init__(self, route: str = "/file", auth: AuthHandler | None = None, is_admin_only=False):
        super().__init__(route, auth, is_admin_only=is_admin_only)

    def get_file_url(self, route: str = "/logged-in/url/{container}/{file_path:path}"):
        @self.router.get(route, tags=self.tags, summary="Get signed file URL")
        async def get_file_url(
            container: str,
            file_path: str,
            user: AuthenticatedUser = Security(self.auth),
        ) -> SignedUrlDto:
            """
            Generates a short-lived secure link to the blob resource, and returns the URL.
            """
            return SignedUrlDto(url=FileService.generate_sas_url(container, file_path))

        return self

    def get_file_redirect(self, route: str = "/logged-in/redirect/{container}/{file_path:path}") -> "FileController":
        @self.router.get(route, tags=self.tags, summary="Access file as logged-in user")
        async def get_file_redirect(
            container: str,
            file_path: str,
            user: AuthenticatedUser = Security(self.auth),
        ):
            """
            Generates a short-lived secure link to the blob resource, and redirects the user to it.
            """
            return FileService.get_authenticated_file_redirect(container, file_path)

        return self

    def get_anonymous_file_url(self, route: str = "/anonymous/url/{container}/{file_path:path}") -> "FileController":
        @self.router.get(route, tags=self.tags, summary="Access file url via shared link")
        async def get_anonymous_file_redirect(
            container: str,
            file_path: str,
            expires: int = Query(..., description="The UNIX timestamp when the link expires."),
            signature: str = Query(..., description="The signature to validate the request."),
        ):
            """
            Provides access to a file via a temporary, signed URL and returns the URL.
            """
            return SignedUrlDto(url=FileService.get_anonymous_file_url(container, file_path, expires, signature))

        return self

    def get_anonymous_file_redirect(
        self, route: str = "/anonymous/redirect/{container}/{file_path:path}"
    ) -> "FileController":
        @self.router.get(route, tags=self.tags, summary="Access file via shared link")
        async def get_anonymous_file_redirect(
            container: str,
            file_path: str,
            expires: int = Query(..., description="The UNIX timestamp when the link expires."),
            signature: str = Query(..., description="The signature to validate the request."),
        ):
            """
            Provides access to a file via a temporary URL and redirects the user to it.
            """
            return FileService.get_anonymous_file_redirect(container, file_path, expires, signature)

        return self
