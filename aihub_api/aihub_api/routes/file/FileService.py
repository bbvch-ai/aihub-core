import hashlib
import hmac
import math
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from aihub_lib.generative_ai.document.accessor.AnonymousFileAccessSettings import AnonymousFileAccessSettings
from aihub_lib.generative_ai.document.types.FileTypeConfig import FileTypeConfig
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse

from aihub_api.routes.file.dto.FileUploadRequest import FileUploadRequest
from aihub_api.routes.file.dto.FileUploadResponse import FileUploadResponse
from aihub_api.routes.file.dto.FileUploadValidationRequest import FileUploadValidationRequest
from aihub_api.routes.file.dto.FileUploadValidationResponse import FileUploadValidationResponse


class FileService:
    """
    Service layer for handling file access logic, including generating
    temporary storage URLs and creating secure, temporary URLs.
    This service uses the global file_access_config for cloud-agnostic file access.
    """

    @staticmethod
    @trace_fn
    def get_authenticated_file_redirect(container: str, file_path: str) -> RedirectResponse:
        """
        For logged-in users. Generates a temporary URL and returns a redirect response.
        """
        file_access_config = AnonymousFileAccessSettings()
        sas_url = file_access_config.service.generate_sas_url(container, file_path)
        return RedirectResponse(url=sas_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @staticmethod
    @trace_fn
    def get_anonymous_file_url(container: str, file_path: str, expires: int, signature: str) -> str:
        """
        For anonymous users. Validates the signature and expiry, then generates a
        temporary URL.
        """
        now_timestamp = datetime.now(UTC).timestamp()

        if now_timestamp > expires:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="This link has expired.")

        expected_signature = FileService._generate_internal_signature(
            container=container, path=file_path, expires=expires
        )
        if not hmac.compare_digest(expected_signature, signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature.")

        remaining_seconds = expires - now_timestamp
        lifetime_hours = math.ceil(remaining_seconds / 3600)

        file_access_config = AnonymousFileAccessSettings()
        return file_access_config.service.generate_sas_url(container, file_path, lifetime_hours=lifetime_hours)

    @staticmethod
    @trace_fn
    def get_anonymous_file_redirect(container: str, file_path: str, expires: int, signature: str) -> RedirectResponse:
        """
        For anonymous users. Validates the signature and expiry, then generates a
        temporary URL and returns a redirect response.
        """
        sas_url = FileService.get_anonymous_file_url(container, file_path, expires, signature)
        return RedirectResponse(url=sas_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @staticmethod
    @trace_fn
    def _generate_internal_signature(container: str, path: str, expires: int) -> str:
        """Generates an HMAC signature for our internal anonymous URL."""
        file_access_config = AnonymousFileAccessSettings()
        secret = file_access_config.service.get_url_signing_secret()
        msg = f"{container}{path}{expires}".encode()
        return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    @staticmethod
    @trace_fn
    def create_anonymous_url(
        get_anonymous_file_redirect_api_endpoint: Annotated[
            str, "https url of FileController.get_anonymous_file_redirect route"
        ],
        container: Annotated[str, "Container/bucket name"],
        file_path: Annotated[str, "Path to file within container"],
        lifetime_hours: Annotated[int, "Link lifetime, can be at most 24 hours"] = 24,
    ) -> str:
        """
        Creates a secure, time-limited URL for anonymous sharing.
        This method would be called by another service when a user wants to "share" a file.
        """
        if lifetime_hours > 24 * 30:
            raise ValueError("Lifetime is too large, can be at most valid for 30 days.")

        if file_path.startswith("/"):
            file_path = file_path[1:]

        expires_dt = datetime.now(UTC) + timedelta(hours=lifetime_hours)
        expires_timestamp = int(expires_dt.timestamp())

        signature = FileService._generate_internal_signature(
            container=container, path=file_path, expires=expires_timestamp
        )

        return (
            f"{get_anonymous_file_redirect_api_endpoint}/{container}/{file_path}"
            f"?expires={expires_timestamp}&signature={signature}"
        )

    @staticmethod
    async def initiate_file_upload(request: FileUploadRequest) -> FileUploadResponse:
        """
        Initiates document upload by generating a presigned URL for the globally configured datalake.

        This method resolves logical database/namespace names to physical storage locations,
        validates the upload request, generates a unique object key, and creates a presigned URL
        for direct upload to the configured datalake storage.
        """

        try:
            bucket_entity = BucketEntity.get_bucket_by_db_name(request.database_name)
            namespace_entity = NamespaceEntity.get_namespace_by_bucket_and_name(
                bucket_id=str(bucket_entity.id), namespace_name=request.namespace_name
            )
        except Exception as e:
            raise HTTPException(
                status_code=404,
                detail=f"Database '{request.database_name}' or namespace '{request.namespace_name}' not found",
            ) from e

        container = bucket_entity.bucket_name
        folder = namespace_entity.folder_name

        upload_id = str(uuid.uuid4())
        object_key = f"{folder}/{request.filename}"

        file_access_config = AnonymousFileAccessSettings()
        presigned_url = file_access_config.service.generate_upload_url(
            container=container,
            file_path=object_key,
            content_type=request.content_type,
            lifetime_hours=1,  # 1 hour expiration
        )

        return FileUploadResponse(
            upload_url=presigned_url,
            upload_id=upload_id,
            container=container,
            object_key=object_key,
            expires_in=3600,  # 1 hour in seconds
            folder=folder,
        )

    @staticmethod
    async def validate_file_upload(request: FileUploadValidationRequest) -> FileUploadValidationResponse:
        """
        Validates whether a file was successfully uploaded to the globally configured datalake.

        This method uses the same global AnonymousFileAccessSettings as upload and download URLs
        to verify that the uploaded file exists in the datalake storage.
        """
        file_access_config = AnonymousFileAccessSettings()

        exists = file_access_config.service.verify_file_exists(container=request.container, file_path=request.file_path)

        return FileUploadValidationResponse(exists=exists, file_path=request.file_path, container=request.container)

    @staticmethod
    def get_supported_file_types() -> list[str]:
        return FileTypeConfig().get_unique_extensions()
