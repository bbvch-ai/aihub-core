import inspect
from unittest.mock import MagicMock

from dagster import build_op_context

from swiss_ai_hub.pipeline.ops.data_lake.delete_data_lake_files_from_data_lake import (
    delete_data_lake_files_from_data_lake,
)
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile

URI = "s3://researchdocs/reports/a.pdf"


class TestDeleteDataLakeFilesFromDataLake:
    def test_deletes_the_file_and_its_figures(self):
        data_lake_client = MagicMock()
        data_lake_client.directory_exists.return_value = True

        delete_data_lake_files_from_data_lake(
            build_op_context(), [DataLakeFile.from_content(URI, b"body", {})], data_lake_client
        )

        data_lake_client.delete_file.assert_called_once_with(uri=URI)
        data_lake_client.delete_directory.assert_called_once()

    def test_leaves_the_record_for_the_ingestion_removal(self):
        """#1925: deleting the record here hid the document from the removal run that deletes its vectors."""
        parameters = inspect.signature(delete_data_lake_files_from_data_lake.compute_fn.decorated_fn).parameters

        assert "doc_store" not in parameters
