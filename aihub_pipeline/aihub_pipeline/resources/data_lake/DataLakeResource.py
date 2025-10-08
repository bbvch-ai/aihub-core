from dagster import ConfigurableResource


class DataLakeResource(ConfigurableResource):
    """
    This simple resources specifies the container name and figures directory name for the data lake.
    """

    container_name: str
    figures_directory_name: str
    directory_name: str | None = None
