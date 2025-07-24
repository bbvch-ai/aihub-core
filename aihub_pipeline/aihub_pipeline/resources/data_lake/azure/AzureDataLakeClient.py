from azure.storage.filedatalake import FileSystemClient

from aihub_pipeline.resources.data_lake.base.AbstractDataLakeClient import AbstractDataLakeClient
from aihub_pipeline.types.DataLakeFile import DataLakeFile


class AzureDataLakeClient(AbstractDataLakeClient):
    """
    Azure-specific implementation of AbstractDataLakeClient.
    Wraps Azure FileSystemClient and provides cloud-agnostic interface.
    """

    def __init__(self, container_name: str, filesystem_client: FileSystemClient):
        super().__init__(container_name)
        self._client = filesystem_client

    def get_all_files(
        self,
        directory_name: str,
        figures_directory_name: str,
    ) -> list[DataLakeFile]:
        """Get all files using Azure FileSystemClient.get_paths()"""
        paths = self._client.get_paths(path=f"{directory_name}/", recursive=True)
        data_lake_files: list[DataLakeFile] = []

        for path in paths:
            if path.is_directory:
                continue

            path_parts = path.name.split("/")
            dir_name = path_parts[0]

            is_root_folder = len(path_parts) == 1
            is_wrong_name = dir_name != directory_name
            is_figure_folder = figures_directory_name in path_parts
            if is_root_folder or is_wrong_name or is_figure_folder:
                continue

            # Azure URI format: container/path
            document_uri = f"{self.container_name}/{path.name.lstrip('/')}"
            data_lake_file = DataLakeFile.from_uri(uri=document_uri, fs_client=self._client)
            data_lake_files.append(data_lake_file)

        return data_lake_files

    def get_file_metadata(self, file_path: str) -> dict:
        """Get file metadata using Azure client"""
        file_client = self._client.get_file_client(file_path)
        properties = file_client.get_file_properties()
        return properties.metadata if properties.metadata else {}

    @property
    def raw_client(self) -> FileSystemClient:
        """Access to the underlying Azure client for backward compatibility"""
        return self._client
