from aihub_pipeline.resources.data_lake.base.AbstractDataLakeClientResource import AbstractDataLakeClientResource

# Generic alias to the abstract base class
# Concrete implementations should use AzureDataLakeClientResource or S3DataLakeClientResource
DataLakeClientResource = AbstractDataLakeClientResource
