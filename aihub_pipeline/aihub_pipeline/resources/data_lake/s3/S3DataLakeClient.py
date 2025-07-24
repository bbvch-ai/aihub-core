import base64
import mimetypes
import os
from datetime import datetime

import boto3

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeClient import AbstractDataLakeClient
from aihub_pipeline.types.DataLakeFile import DataLakeFile


class S3DataLakeClient(AbstractDataLakeClient):
    """
    S3-specific implementation of AbstractDataLakeClient.
    Wraps boto3 S3 client and provides cloud-agnostic interface.
    """

    def __init__(self, container_name: str, s3_client: boto3.client):
        super().__init__(container_name)
        self._client = s3_client

    def get_all_files(
        self,
        directory_name: str,
        figures_directory_name: str,
    ) -> list[DataLakeFile]:
        """Get all files using S3 client list_objects_v2"""
        data_lake_files: list[DataLakeFile] = []

        paginator = self._client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(
            Bucket=self.container_name,
            Prefix=f"{directory_name}/",
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
                dir_name = path_parts[0]

                is_root_folder = len(path_parts) == 1
                is_wrong_name = dir_name != directory_name
                is_figure_folder = figures_directory_name in path_parts
                if is_root_folder or is_wrong_name or is_figure_folder:
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
        """Create a DataLakeFile from S3 object metadata without calling Azure-specific methods."""
        uri_parts = document_uri.split("/")
        namespace = uri_parts[2]  # s3://bucket/namespace/...
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
        except Exception:
            # Fallback if head_object fails
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            etag = s3_object.get("ETag", "").strip('"')
            metadata = {}
            last_modified = s3_object.get("LastModified")

        # Convert ETag to MD5 hash format (base64)
        try:
            md5_hash_str = base64.b64encode(bytes.fromhex(etag)).decode("utf-8") if etag else None
        except ValueError:
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

    @property
    def raw_client(self) -> boto3.client:
        """Access to the underlying S3 client for backward compatibility"""
        return self._client
