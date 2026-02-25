import hashlib
import hmac
import math
from datetime import UTC, datetime, timedelta
from typing import Annotated

from aihub_lib.generative_ai.document.accessor.S3AnonymousFileAccessService import S3AnonymousFileAccessService
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse


class FileService:
    """
    Service layer for handling file access logic, including generating
    temporary storage URLs and creating secure, temporary URLs.
    This service uses the global file_access_config for cloud-agnostic file access.
    """

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
        """Generates an HMAC signature for our internal anonymous URL."""
        secret = s3_service.get_url_signing_secret()
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
