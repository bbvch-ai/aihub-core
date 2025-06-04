from dagster import ConfigurableResource


class DataLakeResource(ConfigurableResource):
    """
    This simple resources specifies the container name and directory name of a data lake.
    """

    container_name: str
    directory_name: str
    figures_directory_name: str
