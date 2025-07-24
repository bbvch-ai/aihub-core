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
                data_lake_file = DataLakeFile.from_uri(uri=document_uri, fs_client=self._client)
                data_lake_files.append(data_lake_file)

        return data_lake_files

    def get_file_metadata(self, file_path: str) -> dict:
        """Get file metadata using S3 client"""
        response = self._client.head_object(Bucket=self.container_name, Key=file_path)
        return response.get("Metadata", {})

    @property
    def raw_client(self) -> boto3.client:
        """Access to the underlying S3 client for backward compatibility"""
        return self._client
