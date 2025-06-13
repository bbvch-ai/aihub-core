import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Annotated

from aihub_lib.infrastructure.azure.blob_storage.BlobStorageAccess import BlobStorageAccess


class AnonymousFileAccessService:
    @staticmethod
    def generate_internal_signature(container: str, path: str, expires: int) -> str:
        """Generates an HMAC signature for our internal anonymous URL."""
        secret = BlobStorageAccess().get_url_signing_secret()
        msg = f"{container}{path}{expires}".encode("utf-8")
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
        if lifetime_hours > 24:
            raise ValueError("Lifetime hours cannot be greater than 24.")
        if file_path.startswith("/"):
            file_path = file_path[1:]

        expires_dt = datetime.now(timezone.utc) + timedelta(hours=lifetime_hours)
        expires_timestamp = int(expires_dt.timestamp())

        signature = AnonymousFileAccessService.generate_internal_signature(
            container=container, path=file_path, expires=expires_timestamp
        )

        return f"{get_anonymous_file_redirect_api_endpoint}/{container}/{file_path}?expires={expires_timestamp}&signature={signature}"
