from aihub_pipeline.resources.data_lake.azure.AzureDataLakeClientResource import AzureDataLakeClientResource


class DataLakeClientResource(AzureDataLakeClientResource):
    """
    Backward compatibility alias for AzureDataLakeClientResource.

    This class is deprecated. Please use AzureDataLakeClientResource directly
    for Azure implementations, or the appropriate cloud-specific resource.
    """

    pass
