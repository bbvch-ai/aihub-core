from aihub_pipeline.resources.data_lake.azure.AzureDataLakeFileSystemResource import AzureDataLakeFileSystemResource


class DataLakeFileSystemResource(AzureDataLakeFileSystemResource):
    """
    Backward compatibility alias for AzureDataLakeFileSystemResource.

    This class is deprecated. Please use AzureDataLakeFileSystemResource directly
    for Azure implementations, or the appropriate cloud-specific resource.
    """

    pass
