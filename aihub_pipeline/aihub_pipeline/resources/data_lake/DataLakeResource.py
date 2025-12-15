from dagster import ConfigurableResource


class DataLakeResource(ConfigurableResource):
    """
    This simple resource specifies the container name and optional directory name for the data lake.
    """

    container_name: str
    directory_name: str | None = None

    def build_path(self, file_path: str) -> str:
        """
        Build the relative path within this data lake.

        Combines the optional directory_name prefix with the file path to create
        the full relative path as it would be stored in the data lake.
        """
        parts = []
        if self.directory_name is not None:
            parts.append(self.directory_name)
        parts.append(file_path.lstrip("/"))
        return "/".join(parts)
