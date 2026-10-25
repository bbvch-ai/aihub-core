import hashlib
import hmac
import json
import math
from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse
from mongoengine import DoesNotExist
from swiss_ai_hub.core.auth.access.access_checker import AccessChecker
from swiss_ai_hub.core.events.agent import UserUploadedFile
from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.infrastructure import trace_fn
from swiss_ai_hub.core.persistence.rag.datalake.entities import BucketEntity, NamespaceEntity

from swiss_ai_hub.api.routes.knowledge.knowledge_service import KnowledgeService

_NOT_AUTHORIZED_TO_VIEW_FILE_DETAIL = "Forbidden: You do not have access to this file."
_AGENT_FILE_KEY_SEGMENTS = 4


class FileService:
    """
    Service layer for handling file access logic, including generating
    temporary storage URLs and creating secure, temporary URLs.
    This service uses the global file_access_config for cloud-agnostic file access.
    """

    @staticmethod
    @trace_fn
    def get_file_url(
        access: AccessChecker, container: str, file_path: str, s3_service: S3AnonymousFileAccessService
    ) -> str:
        """Signs a read URL only for objects of a resource the caller may read, since the URL bypasses every check."""
        FileService.ensure_may_read(access, container, file_path)
        return s3_service.generate_sas_url(container, file_path)

    @staticmethod
    def ensure_may_read(access: AccessChecker, container: str, file_path: str) -> None:
        """Resolves the object to the agent or knowledge namespace owning it; any other bucket is refused."""
        segments = file_path.split("/")
        if any(segment in {"", ".", ".."} for segment in segments):
            raise FileService._not_authorized()
        if container == UserUploadedFile.AGENT_FILES_BUCKET:
            FileService._ensure_may_read_agent_file(access, segments)
        else:
            FileService._ensure_may_read_knowledge_file(access, container, segments)

    @staticmethod
    def _ensure_may_read_agent_file(access: AccessChecker, segments: list[str]) -> None:
        """Agent files live at ``{agent_class}/{agent_id}/{file_id}/{filename}``, readable by the agent's users."""
        if len(segments) != _AGENT_FILE_KEY_SEGMENTS:
            raise FileService._not_authorized()
        agent_class, agent_id = segments[0], segments[1]
        if not access.has_access_to_agent(agent_class, agent_id):
            raise FileService._not_authorized()

    @staticmethod
    def _ensure_may_read_knowledge_file(access: AccessChecker, container: str, segments: list[str]) -> None:
        """Knowledge objects (sources and their figures) live under their namespace's folder."""
        if len(segments) < 2:
            raise FileService._not_authorized()
        try:
            bucket = BucketEntity.get_bucket_by_bucket_name(container)
            namespace = NamespaceEntity.get_namespace_by_bucket_and_folder(str(bucket.id), segments[0])
        except DoesNotExist:
            raise FileService._not_authorized()
        if (
            bucket.deleting
            or namespace.deleting
            or bucket.db_name in KnowledgeService.non_browsable_database_names()
            or not access.has_access_to_knowledge_namespace(bucket.db_name, namespace.namespace_name)
        ):
            raise FileService._not_authorized()

    @staticmethod
    def _not_authorized() -> HTTPException:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=_NOT_AUTHORIZED_TO_VIEW_FILE_DETAIL)

    @staticmethod
    @trace_fn
    def get_anonymous_file_url(
        container: str, file_path: str, expires: int, signature: str, s3_service: S3AnonymousFileAccessService
    ) -> str:
        """
        For anonymous users. Validates the signature and expiry, then generates a
        temporary URL.
        """
        now_timestamp = datetime.now(UTC).timestamp()

        if now_timestamp > expires:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="This link has expired.")

        expected_signature = FileService._generate_internal_signature(
            container=container, path=file_path, expires=expires, s3_service=s3_service
        )
        if not hmac.compare_digest(expected_signature, signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature.")

        remaining_seconds = expires - now_timestamp
        lifetime_hours = math.ceil(remaining_seconds / 3600)

        return s3_service.generate_sas_url(container, file_path, lifetime_hours=lifetime_hours)

    @staticmethod
    @trace_fn
    def get_anonymous_file_redirect(
        container: str, file_path: str, expires: int, signature: str, s3_service: S3AnonymousFileAccessService
    ) -> RedirectResponse:
        """
        For anonymous users. Validates the signature and expiry, then generates a
        temporary URL and returns a redirect response.
        """
        sas_url = FileService.get_anonymous_file_url(container, file_path, expires, signature, s3_service)
        return RedirectResponse(url=sas_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @staticmethod
    @trace_fn
    def _generate_internal_signature(
        container: str, path: str, expires: int, s3_service: S3AnonymousFileAccessService
    ) -> str:
        """Generates an HMAC signature for our internal anonymous URL.

        The fields are signed as a JSON array so that no two different (container, path, expires) triples share a
        message, which plain concatenation would allow.
        """
        secret = s3_service.get_url_signing_secret()
        message = json.dumps([container, path, expires], separators=(",", ":")).encode()
        return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()

    @staticmethod
    @trace_fn
    def create_anonymous_url(
        get_anonymous_file_redirect_api_endpoint: Annotated[
            str, "https url of FileController.get_anonymous_file_redirect route"
        ],
        container: Annotated[str, "Container/bucket name"],
        file_path: Annotated[str, "Path to file within container"],
        s3_service: S3AnonymousFileAccessService,
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
            container=container, path=file_path, expires=expires_timestamp, s3_service=s3_service
        )

        return (
            f"{get_anonymous_file_redirect_api_endpoint}/{container}/{file_path}"
            f"?expires={expires_timestamp}&signature={signature}"
        )
