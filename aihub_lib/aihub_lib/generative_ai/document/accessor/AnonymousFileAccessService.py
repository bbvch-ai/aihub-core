from datetime import UTC, datetime, timedelta

from azure.storage.blob import BlobSasPermissions, generate_blob_sas

from aihub_lib.infrastructure.azure.blob_storage.BlobStorageAccess import BlobStorageAccess
from aihub_lib.infrastructure.opentelemetry.tracing.decorators.trace_fn import trace_fn


class AnonymousFileAccessService:
    @staticmethod
    @trace_fn
    def generate_sas_url(container: str, file_path: str, lifetime_hours: int = 24) -> str:
        """Generates a temporary read-only SAS URL for a specific blob."""
        access = BlobStorageAccess()
        account_name = access.get_account_name()
        service_endpoint = access.get_service_endpoint()
        blob_service_client = access.get_blob_service_client()

        delegation_key_start_time = datetime.now(UTC)
        delegation_key_expiry_time = delegation_key_start_time + timedelta(hours=lifetime_hours)

        user_delegation_key = blob_service_client.get_user_delegation_key(
            key_start_time=delegation_key_start_time, key_expiry_time=delegation_key_expiry_time
        )

        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container,
            blob_name=file_path,
            user_delegation_key=user_delegation_key,
            permission=BlobSasPermissions(read=True),
            expiry=datetime.now(UTC) + timedelta(hours=lifetime_hours),
        )

        return f"{service_endpoint}/{container}/{file_path}?{sas_token}"
