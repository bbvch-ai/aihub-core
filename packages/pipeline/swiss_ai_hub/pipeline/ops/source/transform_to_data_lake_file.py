from dagster import Out, Output, op

from swiss_ai_hub.pipeline.types.DataLakeFile import DataLakeFile
from swiss_ai_hub.pipeline.util.meta_utils import data_lake_file_metadata


@op(code_version="v1", out=Out(io_manager_key="data_lake_io_manager"))
def transform_to_data_lake_file(content: bytes, metadata: dict, uri: str) -> Output[DataLakeFile]:
    """
    Transform raw file content, metadata, and URI into a DataLakeFile.

    This generic operation works with content from any source system and creates
    a standardized DataLakeFile object. The resulting file is saved to the data lake
    via the configured I/O manager.
    """
    data_lake_file = DataLakeFile.from_content(uri=uri, content=content, metadata=metadata)
    return Output(data_lake_file, metadata=data_lake_file_metadata(data_lake_file))
