import hmac
from datetime import datetime, timedelta, timezone

from aihub_lib.generative_ai.document.accessor.AnonymousFileAccessService import AnonymousFileAccessService
from aihub_lib.infrastructure.azure.blob_storage.BlobStorageAccess import BlobStorageAccess
from azure.storage.blob import BlobSasPermissions, generate_blob_sas
from fastapi import HTTPException, status
from fastapi.responses import RedirectResponse


class FileService:
    """
    Service layer for handling file access logic, including generating
    Azure Blob Storage SAS tokens and creating secure, temporary URLs.
    """

    @staticmethod
    def generate_sas_url(container: str, file_path: str) -> str:
        """Generates a temporary read-only SAS URL for a specific blob."""
        access = BlobStorageAccess()
        account_name = access.get_account_name()
        service_endpoint = access.get_service_endpoint()
        blob_service_client = access.get_blob_service_client()

        delegation_key_start_time = datetime.now(timezone.utc)
        delegation_key_expiry_time = delegation_key_start_time + timedelta(hours=24)

        user_delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=delegation_key_start_time, key_expiry_time=delegation_key_expiry_time
        )

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=file_path,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(timezone.utc) + timedelta(hours=24),
        )

        return f"{service_endpoint}/{container}/{file_path}?{sas_token}"

    @staticmethod
    def get_authenticated_file_redirect(container: str, file_path: str) -> RedirectResponse:
        """
        For logged-in users. Generates a SAS URL and returns a redirect response.
        """
        sas_url = FileService.generate_sas_url(container, file_path)
        return RedirectResponse(url=sas_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    @staticmethod
    def get_anonymous_file_url(container: str, file_path: str, expires: int, signature: str) -> str:
        if datetime.now(timezone.utc).timestamp() > expires:
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="This link has expired.")

        expected_signature = AnonymousFileAccessService.generate_internal_signature(
            container=container, path=file_path, expires=expires
        )
        if not hmac.compare_digest(expected_signature, signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid signature.")

        return FileService.generate_sas_url(container, file_path)

    @staticmethod
    def get_anonymous_file_redirect(container: str, file_path: str, expires: int, signature: str) -> RedirectResponse:
        """
        For anonymous users. Validates the signature and expiry, then generates a
        SAS URL and returns a redirect response.
        """
        sas_url = FileService.get_anonymous_file_url(container, file_path, expires, signature)
        return RedirectResponse(url=sas_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
