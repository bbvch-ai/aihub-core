import base64
import os

from azure.storage.filedatalake import FileSystemClient
from swiss_ai_hub.core.generative_ai.utils.path_utils import FIGURES_DIRECTORY_NAME

from swiss_ai_hub.pipeline.resources.data_lake.base.abstract_data_lake_client import AbstractDataLakeClient
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.bucket_utils import get_or_create_namespace_for_directory


class AzureDataLakeClient(AbstractDataLakeClient):
    """
    Azure-specific implementation of AbstractDataLakeClient.
    Wraps Azure FileSystemClient and provides cloud-agnostic interface.
    """

    def __init__(self, container_name: str, filesystem_client: FileSystemClient):
        super().__init__(container_name)
        self._client = filesystem_client

    def build_uri(self, file_path: str) -> str:
        """Build Azure Data Lake URI in format: container/path"""
        clean_path = file_path.lstrip("/")
        return f"{self.container_name}/{clean_path}"

    def _extract_storage_key(self, uri: str) -> str:
        """Extract storage key from Azure URI by removing container prefix."""
        parts = uri.split("/", 1)
        return parts[1]

    def get_all_files(self) -> list[DataLakeFile]:
        """Get all files using Azure FileSystemClient.get_paths()"""
        paths = self._client.get_paths(recursive=True)
        data_lake_files: list[DataLakeFile] = []

        for path in paths:
            if path.is_directory:
                continue

            path_parts = path.name.split("/")

            is_root_folder = len(path_parts) == 1
            is_figure_folder = FIGURES_DIRECTORY_NAME in path_parts
            is_dagster_folder = any(part.startswith(".") and part.endswith("dagster") for part in path_parts)
            if is_root_folder or is_figure_folder or is_dagster_folder:
                continue

            document_uri = self.build_uri(path.name)
            data_lake_file = self._create_data_lake_file_from_fs_uri(document_uri)
            data_lake_files.append(data_lake_file)

        return data_lake_files

    def get_file_metadata(self, file_path: str) -> dict:
        """Get file metadata using Azure client"""
        file_client = self._client.get_file_client(file_path)
        properties = file_client.get_file_properties()
        return properties.metadata if properties.metadata else {}

    def create_data_lake_file_from_uri(self, uri: str) -> DataLakeFile:
        """Create a DataLakeFile from Azure URI by fetching file properties."""
        return self._create_data_lake_file_from_fs_uri(uri)

    def _create_data_lake_file_from_fs_uri(self, uri: str) -> DataLakeFile:
        """
        Create a DataLakeFile instance by retrieving file properties from the Azure Data Lake using its URI.
        Fetches the file's metadata and properties from the data lake and
        populates the DataLakeFile instance accordingly.
        """
        uri_parts = uri.split("/")
        directory_name = uri_parts[1]
        namespace_name = get_or_create_namespace_for_directory(self.container_name, directory_name)
        filename = uri_parts[-1]

        _, extension = os.path.splitext(filename)
        file_type = extension.lower()[1:]
        if not file_type:
            file_type = "unknown"

        document_uri = f"{'/'.join(uri_parts[1:])}"
        file_client = self._client.get_file_client(document_uri)
        properties = file_client.get_file_properties()

        content_settings = properties.content_settings
        md5_hash = content_settings.content_md5
        md5_hash_str = base64.b64encode(md5_hash).decode("utf-8") if md5_hash else None

        last_modified = properties["last_modified"]
        last_modified_timestamp = int(last_modified.timestamp())

        created_timestamp = None
        if "creation_time" in properties:
            creation_time = properties["creation_time"]
            created_timestamp = int(creation_time.timestamp())

        meta = properties.metadata

        return DataLakeFile(
            name=filename,
            namespace=namespace_name,
            filetype=file_type,
            uri=uri,
            size=properties.size,
            created=created_timestamp,
            updated=last_modified_timestamp,
            content_type=properties.content_settings.content_type,
            owner=properties.owner,
            hash=md5_hash_str,
            metadata=meta,
        )

    def directory_exists(self, directory_path: str) -> bool:
        """Check if a directory exists using Azure client."""
        try:
            directory_client = self._client.get_directory_client(directory_path)
            return directory_client.exists()
        except Exception:
            return False

    def list_directory_contents(self, directory_path: str) -> list[str]:
        """List contents of a directory using Azure client."""
        try:
            paths = self._client.get_paths(path=f"{directory_path}/", recursive=False)
            return [path.name for path in paths]
        except Exception:
            return []

    def delete_file(self, uri: str) -> None:
        """Delete a file using Azure client and its URI."""
        storage_key = self._extract_storage_key(uri)
        self._client.delete_file(storage_key)

    def delete_directory(self, directory_path: str) -> None:
        """Delete a directory and all its contents using Azure client."""
        self._client.delete_directory(directory_path)

    @property
    def raw_client(self) -> FileSystemClient:
        """Access to the underlying Azure client for backward compatibility"""
        return self._client
