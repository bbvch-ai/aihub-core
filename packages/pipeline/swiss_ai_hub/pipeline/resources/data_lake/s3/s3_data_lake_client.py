import base64
import logging
import mimetypes
import os
from datetime import datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError
from swiss_ai_hub.core.generative_ai.utils.path_utils import FIGURES_DIRECTORY_NAME

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.bucket_utils import get_or_create_namespace_for_directory

logger = logging.getLogger(__name__)

S3_PROTOCOL_PREFIX = "s3://"


class S3DataLakeClient(AbstractDataLakeClient):
    """
    S3-specific implementation of AbstractDataLakeClient.

    This class provides a cloud-agnostic interface for S3 operations by wrapping
    the boto3 S3 client. It handles file operations, metadata retrieval, and
    directory management for S3 buckets.
    """

    def __init__(self, container_name: str, s3_client: boto3.client, ensure_bucket: bool = True):
        """
        Initialize the S3 data lake client.

        ``ensure_bucket`` controls whether the bucket is created/CORS-configured at construction time. The
        RAG pipeline builds short-lived per-run clients on the read path and passes
        ``ensure_bucket=False`` to avoid redundant bucket bootstrapping there; the observe/write paths keep
        the default so a brand-new bucket is provisioned on first ingest.
        """
        if not container_name or not container_name.strip():
            raise ValueError("Container name cannot be empty")
        super().__init__(container_name)
        self._client = s3_client
        if ensure_bucket:
            self._ensure_bucket_with_cors()

    def build_uri(self, file_path: str) -> str:
        """Build S3 URI in format: s3://bucket/key"""
        clean_path = file_path.lstrip("/")
        return f"{S3_PROTOCOL_PREFIX}{self.container_name}/{clean_path}"

    def _extract_storage_key(self, uri: str) -> str:
        """Extract storage key from S3 URI by removing s3:// protocol and bucket prefix."""
        if uri.startswith(S3_PROTOCOL_PREFIX):
            without_protocol = uri.removeprefix(S3_PROTOCOL_PREFIX)
            return without_protocol.split("/", 1)[1]
        # If no s3:// prefix, treat as bucket/key format
        return uri.split("/", 1)[1]

    def get_all_files(self) -> list[DataLakeFile]:
        """
        Retrieve all files from the specified directory, excluding figures.

        Answers only "which files exist and has any changed", which ``list_objects_v2`` already
        covers: no per-object ``head_object``, and one namespace lookup per directory rather than
        per file. Cost therefore scales with directories, not with objects in the bucket.
        """
        data_lake_files: list[DataLakeFile] = []
        namespace_cache: dict[str, str] = {}

        paginator = self._client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.container_name,
        )

        for page in page_iterator:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                key = obj["Key"]

                # Skip directories (keys ending with /)
                if key.endswith("/"):
                    continue

                path_parts = key.split("/")

                is_root_folder = len(path_parts) == 1
                is_figure_folder = FIGURES_DIRECTORY_NAME in path_parts
                is_dagster_folder = any(part.startswith(".") and part.endswith("dagster") for part in path_parts)
                if is_root_folder or is_figure_folder or is_dagster_folder:
                    continue

                document_uri = self.build_uri(key)
                data_lake_file = self._create_data_lake_file_from_s3_object(
                    document_uri,
                    obj,
                    key,
                    namespace=self._resolve_namespace(document_uri, namespace_cache),
                )
                data_lake_files.append(data_lake_file)

        return data_lake_files

    def _resolve_namespace(self, document_uri: str, namespace_cache: dict[str, str] | None = None) -> str:
        """Namespace varies only per directory, but the lookup also *registers* directories the
        knowledge UI and namespace-selection agent read, so the first file of each directory must
        still reach it — caching per directory keeps that side effect and drops the rest."""
        directory_name = document_uri.split("/")[3]  # s3://bucket/directory_name/...
        if namespace_cache is None:
            return get_or_create_namespace_for_directory(self.container_name, directory_name)
        if directory_name not in namespace_cache:
            namespace_cache[directory_name] = get_or_create_namespace_for_directory(self.container_name, directory_name)
        return namespace_cache[directory_name]

    def get_file_metadata(self, file_path: str) -> dict:
        """Get file metadata using S3 client"""
        response = self._client.head_object(Bucket=self.container_name, Key=file_path)
        return response.get("Metadata", {})

    def create_data_lake_files_from_uris(self, document_uris: list[str]) -> list[DataLakeFile]:
        """Batch sibling of ``create_data_lake_file_from_uri`` that resolves each namespace once.

        The removal job loads every partition at once, so a per-file namespace lookup there costs
        as much as it did in the observation.
        """
        namespace_cache: dict[str, str] = {}
        return [self.create_data_lake_file_from_uri(document_uri, namespace_cache) for document_uri in document_uris]

    def create_data_lake_file_from_uri(
        self, document_uri: str, namespace_cache: dict[str, str] | None = None
    ) -> DataLakeFile:
        """Create a DataLakeFile from S3 URI by fetching object metadata."""
        if not document_uri.startswith(S3_PROTOCOL_PREFIX):
            if document_uri.startswith(f"{self.container_name}/"):
                logger.warning(f"URI missing '{S3_PROTOCOL_PREFIX}' prefix: {document_uri}. Auto-correcting.")
                document_uri = f"{S3_PROTOCOL_PREFIX}{document_uri}"
            else:
                raise ValueError(
                    f"Invalid S3 URI format or bucket mismatch: {document_uri}. "
                    f"Expected format: '{S3_PROTOCOL_PREFIX}{self.container_name}/path/to/file' or "
                    f"'{self.container_name}/path/to/file'"
                )

        uri_parts = document_uri.removeprefix(S3_PROTOCOL_PREFIX).split("/", 1)
        if len(uri_parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {document_uri}")

        bucket, key = uri_parts
        if bucket != self.container_name:
            raise ValueError(f"URI bucket '{bucket}' doesn't match client bucket '{self.container_name}'")

        try:
            head_response = self._client.head_object(Bucket=self.container_name, Key=key)
        except Exception as e:
            raise ValueError(f"Failed to get object metadata for {document_uri}: {e}")

        s3_object = {
            "Key": key,
            "Size": head_response.get("ContentLength", 0),
            "LastModified": head_response.get("LastModified"),
            "ETag": head_response.get("ETag", "").strip('"'),
        }

        return self._create_data_lake_file_from_s3_object(
            document_uri,
            s3_object,
            key,
            namespace=self._resolve_namespace(document_uri, namespace_cache),
            head_response=head_response,
        )

    def _create_data_lake_file_from_s3_object(
        self,
        document_uri: str,
        s3_object: dict,
        key: str,
        namespace: str,
        head_response: dict | None = None,
    ) -> DataLakeFile:
        """
        Create a DataLakeFile from S3 object metadata.

        ``head_response`` carries the object's user metadata and content type, which only the
        download path needs; callers that already hold one pass it in rather than fetching it
        again, and callers that never read those fields pass None to skip the request entirely.
        ``list_objects_v2`` reports the same ETag, size and modification time either way, so the
        DataVersion is identical on both paths.
        """
        filename = key.split("/")[-1]

        _, extension = os.path.splitext(filename)
        file_type = extension.lower()[1:] if extension else "unknown"

        if head_response is not None:
            content_type = head_response.get("ContentType", "application/octet-stream")
            etag = head_response.get("ETag", "").strip('"')  # Remove quotes from ETag
            metadata = head_response.get("Metadata", {})
            last_modified = head_response.get("LastModified")
        else:
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            etag = s3_object.get("ETag", "").strip('"')
            metadata = {}
            last_modified = s3_object.get("LastModified")

        md5_hash_str: str | None = None
        if etag:
            if len(etag) == 32 and all(c in "0123456789abcdef" for c in etag.lower()):
                # Frozen format: persisted as content_hash and embedded in the DataVersion.
                # Changing it forces a full re-parse and re-embed of every existing corpus.
                md5_hash_str = base64.b64encode(bytes.fromhex(etag)).decode("utf-8")
            else:
                # SeaweedFS >=4.01 chunks objects above 8 MiB and returns "<md5hex>-<chunks>".
                # Kept verbatim: deterministic and content-derived, so it still works as a
                # change-detection token. Do NOT unify with the base64 branch above.
                md5_hash_str = etag

        last_modified_timestamp = int(last_modified.timestamp()) if last_modified else int(datetime.now().timestamp())

        mimetypes.add_type("text/markdown", ".md")

        return DataLakeFile(
            name=filename,
            namespace=namespace,
            filetype=file_type,
            uri=document_uri,
            size=s3_object.get("Size", 0),
            created=last_modified_timestamp,  # S3 doesn't track creation time separately
            updated=last_modified_timestamp,
            content_type=content_type,
            owner=os.getenv("USER") or os.getenv("USERNAME") or "pipeline-user",
            hash=md5_hash_str,
            metadata=metadata,
        )

    def directory_exists(self, directory_path: str) -> bool:
        """Check if a directory (prefix) exists in S3."""
        try:
            # Strip s3://bucket/ prefix if present to get the storage key
            if directory_path.startswith(S3_PROTOCOL_PREFIX):
                directory_path = self._extract_storage_key(directory_path)
            # In S3, directories are just prefixes. Check if any objects exist with this prefix
            response = self._client.list_objects_v2(Bucket=self.container_name, Prefix=f"{directory_path}/", MaxKeys=1)
            return "Contents" in response
        except (ClientError, NoCredentialsError, BotoCoreError) as e:
            logger.exception(f"Failed to check directory existence for {directory_path}: {e}")
            return False

    def list_directory_contents(self, directory_path: str) -> list[str]:
        """
        List contents of a directory (prefix) in S3.
        """
        try:
            # Strip s3://bucket/ prefix if present to get the storage key
            if directory_path.startswith(S3_PROTOCOL_PREFIX):
                directory_path = self._extract_storage_key(directory_path)
            response = self._client.list_objects_v2(
                Bucket=self.container_name, Prefix=f"{directory_path}/", Delimiter="/"
            )

            contents = []
            if "Contents" in response:
                contents.extend([obj["Key"] for obj in response["Contents"]])
            if "CommonPrefixes" in response:
                contents.extend([prefix["Prefix"].rstrip("/") for prefix in response["CommonPrefixes"]])

            return contents
        except (ClientError, NoCredentialsError, BotoCoreError) as e:
            logger.exception(f"Failed to list directory contents for {directory_path}: {e}")
            return []

    def delete_file(self, uri: str) -> None:
        """Delete a file from S3 using its URI."""
        storage_key = self._extract_storage_key(uri)
        self._client.delete_object(Bucket=self.container_name, Key=storage_key)

    def delete_directory(self, directory_path: str) -> None:
        """Delete a directory (prefix) and all its contents from S3."""
        # Strip s3://bucket/ prefix if present to get the storage key
        if directory_path.startswith(S3_PROTOCOL_PREFIX):
            directory_path = self._extract_storage_key(directory_path)
        # List all objects with the prefix (includes contents)
        paginator = self._client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.container_name, Prefix=f"{directory_path}/")

        objects_to_delete = []
        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    objects_to_delete.append({"Key": obj["Key"]})

        if objects_to_delete:
            objects_to_delete.append({"Key": f"{directory_path}/"})

            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i : i + 1000]
                self._client.delete_objects(Bucket=self.container_name, Delete={"Objects": batch})

    def _ensure_bucket_with_cors(self) -> None:
        """Ensure bucket exists and configure CORS for web access."""
        try:
            self._client.head_bucket(Bucket=self.container_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code in ("404", "NoSuchBucket"):
                self._client.create_bucket(Bucket=self.container_name)
            else:
                raise

        # AllowedOrigins is "*" by design: the entitlement lives in the short-lived, signed presigned URL,
        # not in CORS. The origin we would otherwise pin is the browser app's own domain, which is
        # deployment-specific and not known here. Narrow this once the frontend origin is configurable.
        cors_config = {
            "CORSRules": [
                {
                    "AllowedOrigins": ["*"],
                    "AllowedHeaders": ["Content-Type", "x-amz-date", "authorization", "x-amz-security-token"],
                    "AllowedMethods": ["PUT", "POST", "DELETE", "GET", "HEAD"],
                    "MaxAgeSeconds": 3000,
                    "ExposeHeaders": ["ETag"],
                }
            ]
        }

        self._client.put_bucket_cors(Bucket=self.container_name, CORSConfiguration=cors_config)
        logger.info(f"CORS configured for bucket: {self.container_name}")

    @property
    def raw_client(self) -> boto3.client:
        """Access to the underlying S3 client for backward compatibility"""
        return self._client
