from typing import Annotated

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.skipped_data_lake_file import SkippedDataLakeFile


class DataLakeListing(BaseModel):
    """One pass over a database's data lake. A file that cannot be mapped to a namespace is skipped instead of
    failing the pass, so one bad folder does not stop ingestion and removal for the whole database."""

    files: Annotated[list[DataLakeFile], Field(description="Files mapped to a namespace, ready to ingest.")] = []
    skipped: Annotated[list[SkippedDataLakeFile], Field(description="Files left out, with the reason.")] = []

    def skipped_as_markdown(self) -> str:
        rows = [f"| {self._escape(file.uri)} | {self._escape(file.reason)} |" for file in self.skipped]
        return "\n".join(["| URI | Reason |", "| --- | --- |", *rows])

    @staticmethod
    def _escape(cell: str) -> str:
        return cell.replace("|", "\\|")
