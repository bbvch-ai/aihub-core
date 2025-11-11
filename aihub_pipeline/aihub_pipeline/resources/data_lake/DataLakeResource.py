from dagster import ConfigurableResource


class DataLakeResource(ConfigurableResource):
    """
    This simple resource specifies the container name and optional directory name for the data lake.
    """

    container_name: str
    directory_name: str | None = None
