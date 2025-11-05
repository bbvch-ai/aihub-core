import hashlib
import hmac
import logging
import math
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated

from aihub_lib.generative_ai.document.accessor.AnonymousFileAccessSettings import AnonymousFileAccessSettings
from aihub_lib.generative_ai.document.types.FileTypeConfig import FileTypeConfig
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from aihub_lib.nats.events.pipeline.SourceUpdatedEvent import SourceUpdatedEvent
from aihub_lib.nats.publishers.JSPublisher import JSPublisher
from aihub_lib.nats.topic_managers.pipeline.PipelineInstanceTopicManager import PipelineInstanceTopicManager
from aihub_lib.persistence.rag.datalake.entities.BucketEntity import BucketEntity
from aihub_lib.persistence.rag.datalake.entities.NamespaceEntity import NamespaceEntity
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from nats.aio.client import Client as NATS

from aihub_api.routes.file.dto.FileUploadRequest import FileUploadRequest
from aihub_api.routes.file.dto.FileUploadResponse import FileUploadResponse
from aihub_api.routes.file.dto.FileUploadValidationRequest import FileUploadValidationRequest
from aihub_api.routes.file.dto.FileUploadValidationResponse import FileUploadValidationResponse

logger = logging.getLogger(__name__)


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
    async def _publish_source_updated_event(nc: NATS, request: FileUploadValidationRequest):
        """Publish SourceUpdatedEvent to NATS for pipeline processing."""
        file_access_config = AnonymousFileAccessSettings()
        path_parts = request.file_path.split("/")
        filename = path_parts[-1] if path_parts else request.file_path

        file_info = file_access_config.service.get_file_metadata(
            container=request.container, file_path=request.file_path
        )
        content_type = file_info.get("content_type", "application/octet-stream")
        content_length = file_info.get("content_length", 0)

        bucket_entity = BucketEntity.get_bucket_by_bucket_name(request.container)
        db_name = bucket_entity.db_name

        event = SourceUpdatedEvent(
            filename=filename,
            content_type=content_type,
            content_length=content_length,
            path=request.file_path,
        )

        topic_manager = PipelineInstanceTopicManager(
            source_type="datalake",
            source_id=request.container,
            target_type="knowledge",
            target_id=db_name,
        )

        js = nc.jetstream()
        stream_name, stream_subject = topic_manager.get_stream()
        publisher = JSPublisher(name="FileService", js=js)
        await publisher.ensure_stream_exists(stream_name, stream_subject)

        subject = topic_manager.get_subject_for_specific_event_in_pipeline_instance(
            run_key=str(uuid.uuid4()), event_name=event.event_name, event_id=event.event_id
        )
        await publisher.publish_event(event, subject)

        logger.info(f"Published SourceUpdatedEvent for {request.file_path} to {stream_name}")

    @staticmethod
    async def validate_file_upload(nc: NATS, request: FileUploadValidationRequest) -> FileUploadValidationResponse:
        """
        Validates whether a file was successfully uploaded to the datalake and triggers pipeline processing.
        """
        file_access_config = AnonymousFileAccessSettings()
        exists = file_access_config.service.verify_file_exists(container=request.container, file_path=request.file_path)

        if exists:
            try:
                await FileService._publish_source_updated_event(nc, request)
            except Exception as e:
                logger.exception(f"Failed to publish SourceUpdatedEvent: {e}")

        return FileUploadValidationResponse(exists=exists, file_path=request.file_path, container=request.container)

    @staticmethod
    def get_supported_file_types() -> list[str]:
        return FileTypeConfig().get_unique_extensions()
