from typing import Dict

from dagster import Out, Output, op

from aihub_pipeline.types.DataLakeFile import DataLakeFile
from aihub_pipeline.util.meta_utils import data_lake_file_metadata


@op(code_version="v1", out=Out(io_manager_key="data_lake_io_manager"))
def transform_to_data_lake_file(content: bytes, metadata: Dict, uri: str) -> Output[DataLakeFile]:
    data_lake_file = DataLakeFile.from_content(uri=uri, content=content, metadata=metadata)
    return Output(data_lake_file, metadata=data_lake_file_metadata(data_lake_file))
