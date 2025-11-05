from typing import Annotated

from aihub_lib.auth.dependencies.AuthHandler import AuthHandler
from aihub_lib.auth.identity.UserIdentity import UserIdentity
from aihub_lib.generative_ai.document.accessor.AnonymousFileAccessSettings import AnonymousFileAccessSettings
from aihub_lib.i18n.LocaleString import LocaleString
from aihub_lib.nats.dependencies.use_nats import use_nats
from aihub_lib.routes.Controller import Controller
from fastapi import Depends, Query, Security
from nats.aio.client import Client as NATS

from aihub_api.routes.file.dto.FileUploadRequest import FileUploadRequest
from aihub_api.routes.file.dto.FileUploadResponse import FileUploadResponse
from aihub_api.routes.file.dto.FileUploadValidationRequest import FileUploadValidationRequest
from aihub_api.routes.file.dto.FileUploadValidationResponse import FileUploadValidationResponse
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

    def __init__(
        self, *, auth: AuthHandler, route: str = "/files", additionally_required_permission: str | None = None
    ):
        super().__init__(auth=auth, route=route, additionally_required_permission=additionally_required_permission)

    def get_file_url(self, route: str = "/logged-in/url/{container}/{file_path:path}") -> "FileController":
        @self.router.get(route, tags=self.tags, summary="Get signed file URL")
        async def get_file_url(
            container: str,
            file_path: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ) -> SignedUrlDto:
            """
            Generates a short-lived secure link to the blob resource, and returns the URL.
            """
            file_access_config = AnonymousFileAccessSettings()
            sas_url = file_access_config.service.generate_sas_url(container, file_path)
            return SignedUrlDto(url=sas_url)

        return self

    def get_file_redirect(self, route: str = "/logged-in/redirect/{container}/{file_path:path}") -> "FileController":
        @self.router.get(route, tags=self.tags, summary="Access file as logged-in user")
        async def get_file_redirect(
            container: str,
            file_path: str,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.?>"))],
        ):
            """
            Generates a short-lived secure link to the blob resource, and redirects the user to it.
            """
            return FileService.get_authenticated_file_redirect(container, file_path)

        return self

    def get_anonymous_file_url(self, route: str = "/anonymous/url/{container}/{file_path:path}") -> "FileController":
        @self.router.get(route, tags=self.tags, summary="Access file url via shared link")
        async def get_anonymous_file_url(
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

    def initiate_file_upload(self, route: str = "/upload/initiate") -> "FileController":
        @self.router.post(route, tags=self.tags)
        async def initiate_file_upload(
            request: FileUploadRequest,
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.?>"))],
        ) -> FileUploadResponse:
            """
            Initiates file upload by generating a presigned S3/MinIO URL.

            This endpoint validates the upload request and returns a presigned URL
            that allows the client to upload the file directly to S3/MinIO storage.
            """
            return await FileService.initiate_file_upload(request)

        return self

    def validate_file_upload(self, route: str = "/upload/validate") -> "FileController":
        @self.router.post(route, tags=self.tags)
        async def validate_file_upload(
            request: FileUploadValidationRequest,
            nc: Annotated[NATS, Depends(use_nats)],
            _: Annotated[UserIdentity, Security(self.user_with_permission("aihub.user.agent.?>"))],
        ) -> FileUploadValidationResponse:
            """
            Validates whether a file was successfully uploaded to the datalake.

            This endpoint checks if a file exists in the configured datalake storage
            (S3/MinIO or Azure Blob Storage) after a presigned URL upload.
            """
            return await FileService.validate_file_upload(nc, request)

        return self

    def get_supported_file_types(self, route: str = "/upload/supported-types") -> "FileController":
        @self.router.get(route, tags=self.tags, summary="Get supported file types")
        async def get_supported_file_types() -> list[str]:
            """
            Returns a list of supported file extensions (e.g., [".pdf", ".docx"])
            that can be used for client-side validation.
            """
            return FileService.get_supported_file_types()

        return self
