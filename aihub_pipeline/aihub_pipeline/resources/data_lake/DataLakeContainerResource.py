from dagster import ConfigurableResource


class DataLakeContainerResource(ConfigurableResource):
    """
    This resource specifies the container name for a data lake.
    Unlike DataLakeResource, this processes all directories within the container,
    mapping each directory to a separate namespace.
    """

    container_name: str
    figures_directory_name: str
