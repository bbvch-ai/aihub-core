import hashlib
import hmac
import math
from datetime import UTC, datetime, timedelta
from typing import Annotated

from aihub_lib.generative_ai.document.accessor.AnonymousFileAccessService import AnonymousFileAccessService
from aihub_lib.infrastructure.azure.blob_storage.BlobStorageAccess import BlobStorageAccess
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse


class FileService:
    """
    Service layer for handling file access logic, including generating
    Azure Blob Storage SAS tokens and creating secure, temporary URLs.
    """

    @staticmethod
    def get_authenticated_file_redirect(container: str, file_path: str) -> RedirectResponse:
        """
        For logged-in users. Generates a SAS URL and returns a redirect response.
        """
        sas_url = AnonymousFileAccessService.generate_sas_url(container, file_path)
        return RedirectResponse(url=sas_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @staticmethod
    def get_anonymous_file_url(container: str, file_path: str, expires: int, signature: str) -> str:
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

        return AnonymousFileAccessService.generate_sas_url(container, file_path, lifetime_hours=lifetime_hours)

    @staticmethod
    def get_anonymous_file_redirect(container: str, file_path: str, expires: int, signature: str) -> RedirectResponse:
        """
        For anonymous users. Validates the signature and expiry, then generates a
        SAS URL and returns a redirect response.
        """
        sas_url = FileService.get_anonymous_file_url(container, file_path, expires, signature)
        return RedirectResponse(url=sas_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @staticmethod
    def _generate_internal_signature(container: str, path: str, expires: int) -> str:
        """Generates an HMAC signature for our internal anonymous URL."""
        secret = BlobStorageAccess().get_url_signing_secret()
        msg = f"{container}{path}{expires}".encode()
        return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

    @staticmethod
    def create_anonymous_url(
        get_anonymous_file_redirect_api_endpoint: Annotated[
            str, "https url of FileController.get_anonymous_file_redirect route"
        ],
        container: Annotated[str, "Blob container name (or - in data lake settings - usually root folder name)"],
        file_path: Annotated[str, "Path to file within container (or within root folder)"],
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
