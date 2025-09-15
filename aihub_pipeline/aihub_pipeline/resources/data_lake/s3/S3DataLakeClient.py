import base64
import logging
import mimetypes
import os
from datetime import datetime

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeClient import AbstractDataLakeClient
from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.util.bucket_utils import get_or_create_namespace_for_directory

logger = logging.getLogger(__name__)


class S3DataLakeClient(AbstractDataLakeClient):
    """
    S3-specific implementation of AbstractDataLakeClient.

    This class provides a cloud-agnostic interface for S3 operations by wrapping
    the boto3 S3 client. It handles file operations, metadata retrieval, and
    directory management for S3 buckets.
    """

    def __init__(self, container_name: str, s3_client: boto3.client):
        """
        Initialize the S3 data lake client.
        """
        if not container_name or not container_name.strip():
            raise ValueError("Container name cannot be empty")
        super().__init__(container_name)
        self._client = s3_client

    def get_all_files(
        self,
        figures_directory_name: str,
    ) -> list[DataLakeFile]:
        """
        Retrieve all files from the specified directory, excluding figures.
        """
        data_lake_files: list[DataLakeFile] = []

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
                is_figure_folder = figures_directory_name in path_parts
                is_dagster_folder = any(part.startswith(".") and part.endswith("dagster") for part in path_parts)
                if is_root_folder or is_figure_folder or is_dagster_folder:
                    continue

                # S3 URI format: s3://bucket/key
                document_uri = f"s3://{self.container_name}/{key}"
                data_lake_file = self._create_data_lake_file_from_s3_object(document_uri, obj, key)
                data_lake_files.append(data_lake_file)

        return data_lake_files

    def get_file_metadata(self, file_path: str) -> dict:
        """Get file metadata using S3 client"""
        response = self._client.head_object(Bucket=self.container_name, Key=file_path)
        return response.get("Metadata", {})

    def create_data_lake_file_from_uri(self, document_uri: str) -> DataLakeFile:
        """Create a DataLakeFile from S3 URI by fetching object metadata."""
        # Parse S3 URI to get key
        if not document_uri.startswith("s3://"):
            raise ValueError(f"Invalid S3 URI format: {document_uri}")

        # Extract key from s3://bucket/key format
        uri_parts = document_uri[5:].split("/", 1)  # Remove 's3://' and split
        if len(uri_parts) != 2:
            raise ValueError(f"Invalid S3 URI format: {document_uri}")

        bucket, key = uri_parts
        if bucket != self.container_name:
            raise ValueError(f"URI bucket '{bucket}' doesn't match client bucket '{self.container_name}'")

        # Get object metadata
        try:
            head_response = self._client.head_object(Bucket=self.container_name, Key=key)
        except Exception as e:
            raise ValueError(f"Failed to get object metadata for {document_uri}: {e}")

        # Create a mock s3_object dict to reuse existing logic
        s3_object = {
            "Key": key,
            "Size": head_response.get("ContentLength", 0),
            "LastModified": head_response.get("LastModified"),
            "ETag": head_response.get("ETag", "").strip('"'),
        }

        return self._create_data_lake_file_from_s3_object(document_uri, s3_object, key)

    def _create_data_lake_file_from_s3_object(self, document_uri: str, s3_object: dict, key: str) -> DataLakeFile:
        """
        Create a DataLakeFile from S3 object metadata.

        This method constructs a DataLakeFile object from S3 object metadata,
        handling content type detection, hash conversion, and timestamp processing.
        """
        uri_parts = document_uri.split("/")
        directory_name = uri_parts[3]  # s3://bucket/directory_name/...
        namespace = get_or_create_namespace_for_directory(self.container_name, directory_name)
        filename = key.split("/")[-1]

        _, extension = os.path.splitext(filename)
        file_type = extension.lower()[1:] if extension else "unknown"

        # Get additional metadata from S3 if needed
        try:
            head_response = self._client.head_object(Bucket=self.container_name, Key=key)
            content_type = head_response.get("ContentType", "application/octet-stream")
            etag = head_response.get("ETag", "").strip('"')  # Remove quotes from ETag
            metadata = head_response.get("Metadata", {})
            last_modified = head_response.get("LastModified")
        except (ClientError, NoCredentialsError, BotoCoreError) as e:
            # Fallback if head_object fails - use data from list operation
            logger.warning(f"Could not fetch detailed metadata for {key}, using fallback values: {e}")
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            etag = s3_object.get("ETag", "").strip('"')
            metadata = {}
            last_modified = s3_object.get("LastModified")

        # Convert ETag to MD5 hash format (base64)
        md5_hash_str: str | None = None
        if etag:
            try:
                # Only convert if ETag looks like a hex string (standard MD5)
                if len(etag) == 32 and all(c in "0123456789abcdef" for c in etag.lower()):
                    md5_hash_str = base64.b64encode(bytes.fromhex(etag)).decode("utf-8")
                else:
                    # For multipart uploads or other ETag formats, keep as-is
                    logger.debug(f"Non-standard ETag format for {key}: {etag}")
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to convert ETag to MD5 hash for {key}: {e}")
                md5_hash_str = None

        last_modified_timestamp = int(last_modified.timestamp()) if last_modified else int(datetime.now().timestamp())

        # Add custom MIME type for markdown files
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
            # In S3, directories are just prefixes. Check if any objects exist with this prefix
            response = self._client.list_objects_v2(Bucket=self.container_name, Prefix=f"{directory_path}/", MaxKeys=1)
            return "Contents" in response
        except (ClientError, NoCredentialsError, BotoCoreError) as e:
            logger.error(f"Failed to check directory existence for {directory_path}: {e}")
            return False

    def list_directory_contents(self, directory_path: str) -> list[str]:
        """
        List contents of a directory (prefix) in S3.
        """
        try:
            response = self._client.list_objects_v2(
                Bucket=self.container_name, Prefix=f"{directory_path}/", Delimiter="/"
            )

            contents = []
            # Add files
            if "Contents" in response:
                contents.extend([obj["Key"] for obj in response["Contents"]])
            # Add subdirectories (common prefixes)
            if "CommonPrefixes" in response:
                contents.extend([prefix["Prefix"].rstrip("/") for prefix in response["CommonPrefixes"]])

            return contents
        except (ClientError, NoCredentialsError, BotoCoreError) as e:
            logger.error(f"Failed to list directory contents for {directory_path}: {e}")
            return []

    def delete_file(self, file_path: str) -> None:
        """Delete a file from S3."""
        self._client.delete_object(Bucket=self.container_name, Key=file_path)

    def delete_directory(self, directory_path: str) -> None:
        """Delete a directory (prefix) and all its contents from S3."""
        # List all objects with the prefix
        paginator = self._client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=self.container_name, Prefix=f"{directory_path}/")

        # Collect all objects to delete
        objects_to_delete = []
        for page in pages:
            if "Contents" in page:
                for obj in page["Contents"]:
                    objects_to_delete.append({"Key": obj["Key"]})

        # Delete objects in batches (S3 allows max 1000 per request)
        if objects_to_delete:
            for i in range(0, len(objects_to_delete), 1000):
                batch = objects_to_delete[i : i + 1000]
                self._client.delete_objects(Bucket=self.container_name, Delete={"Objects": batch})

    @property
    def raw_client(self) -> boto3.client:
        """Access to the underlying S3 client for backward compatibility"""
        return self._client
