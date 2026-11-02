import hashlib
from collections.abc import Callable
from typing import Annotated, NoReturn

import dlt
from botocore.exceptions import ClientError
from dagster import OpExecutionContext
from dlt.common.destination.exceptions import DestinationTerminalException
from dlt.common.schema import TTableSchema
from dlt.common.typing import TDataItems

from swiss_ai_hub.pipeline.io.s3_data_lake_io_manager import S3DataLakeIOManager
from swiss_ai_hub.pipeline.resources.data_lake.s3.s3_data_lake_client import S3DataLakeClient
from swiss_ai_hub.pipeline.source_pipelines.abstract_structured_source_adapter import AbstractStructuredSourceAdapter
from swiss_ai_hub.pipeline.source_pipelines.structured_file_unavailable_error import StructuredFileUnavailableError
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.structured_file_reference import StructuredFileReference
from swiss_ai_hub.pipeline.util.source_updated_notifier import notify_source_updated
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client

_NOT_FOUND = {"404", "NoSuchKey", "NotFound"}
_PERMANENT = {"AccessDenied", "NoSuchBucket", "InvalidAccessKeyId", "SignatureDoesNotMatch"}


class StructuredDataLakeDestination:
    """dlt custom destination that lands rendered records, and the files a source offers, in one knowledge database's
    data lake.

    dlt delivers at least once: it retries a failed load job and re-delivers everything after a lost state. A file is
    therefore written only when its MD5 differs from the stored object's ETag, which is what keeps a run with no
    changes at the source from writing or announcing anything. The comparison uses the ETag rather than a hash kept as
    object metadata, because ingestion copies a file's metadata into its document and into every chunk it embeds.

    A file arrives as a reference and is read through the adapter here, while loading, so a run holds one file at a
    time. It goes through the same comparison and the same single-part write, whose ETag is the content's MD5 at any
    size. A file the source will not serve is skipped and named in ``failed_keys``.
    """

    BATCH_SIZE = 100

    def __init__(
        self,
        bucket: Annotated[str, "Bucket name of the knowledge database the records are written to"],
        context: Annotated[OpExecutionContext, "The step writing the files, for its log"],
        read_file: Annotated[
            Callable[[StructuredFileReference], bytes] | None,
            "Reads a file the adapter offered; None when it offers none",
        ] = None,
    ):
        self.bucket = bucket
        self.context = context
        self.read_file = read_file
        self.written_keys: list[str] = []
        self.failed_keys: list[str] = []
        self.unchanged_count = 0

    def as_dlt_destination(self) -> Callable[[TDataItems, TTableSchema], None]:
        """Loads sequentially, so the counters stay exact and batches are announced in the order they were written."""

        # The name is kept from before files were written here: dlt keeps it in every database's stored state.
        @dlt.destination(
            batch_size=self.BATCH_SIZE,
            loader_file_format="typed-jsonl",
            name="markdown_data_lake",
            skip_dlt_columns_and_tables=True,
            max_table_nesting=0,
            loader_parallelism_strategy="sequential",
        )
        def markdown_data_lake(items: TDataItems, table: TTableSchema) -> None:
            self._write_batch(items)

        return markdown_data_lake

    def _write_batch(self, rows: TDataItems) -> None:
        """Files written before a write fails are announced all the same: dlt's retry finds them unchanged and would
        never announce them, leaving them to the ingestion pipeline's next daily observation."""
        client = build_s3_data_lake_client(self.bucket, ensure_bucket=False)
        key_column = AbstractStructuredSourceAdapter.OBJECT_KEY_COLUMN
        written: list[str] = []
        try:
            for row in rows:
                if self._write_if_changed(client, row):
                    written.append(row[key_column])
        finally:
            self.written_keys.extend(written)
            notify_source_updated(self.bucket, written)

    def _write_if_changed(self, client: S3DataLakeClient, row: dict) -> bool:
        object_key = row[AbstractStructuredSourceAdapter.OBJECT_KEY_COLUMN]
        contents = self._contents_of(row)
        if contents is None:
            return False
        content, metadata = contents
        if self._stored_etag(client, object_key) == hashlib.md5(content, usedforsecurity=False).hexdigest():
            self.unchanged_count += 1
            return False
        data_lake_file = DataLakeFile.from_content(uri=client.build_uri(object_key), content=content, metadata=metadata)
        try:
            S3DataLakeIOManager.write_data_lake_file(client.raw_client, data_lake_file, self.context)
        except ClientError as error:
            self._reraise(error)
        return True

    def _contents_of(self, row: dict) -> tuple[bytes, dict[str, str]] | None:
        """A record's rendered markdown, or a file's content with the title and link ingestion reads; None for a file
        the source would not serve."""
        file = row.get(AbstractStructuredSourceAdapter.FILE_COLUMN)
        if not file:
            return row[AbstractStructuredSourceAdapter.MARKDOWN_COLUMN].encode(), {}
        reference = StructuredFileReference.model_validate_json(file)
        if self.read_file is None:
            raise DestinationTerminalException(
                f"{reference.object_key} is a file, but nothing reads this source's files."
            )
        try:
            return self.read_file(reference), reference.metadata()
        except StructuredFileUnavailableError as unavailable:
            self.context.log.warning(f"{reference.object_key} is skipped and tried again next run: {unavailable}")
            self.failed_keys.append(reference.object_key)
            return None

    def _stored_etag(self, client: S3DataLakeClient, object_key: str) -> str | None:
        """A multipart upload's ETag is not an MD5 and never matches, so such a file is rewritten; records are small
        enough to be uploaded in one part."""
        try:
            head = client.raw_client.head_object(Bucket=client.container_name, Key=object_key)
        except ClientError as error:
            if error.response["Error"]["Code"] in _NOT_FOUND:
                return None
            self._reraise(error)
        return head["ETag"].strip('"')

    @staticmethod
    def _reraise(error: ClientError) -> NoReturn:
        """Errors no retry can fix fail the run at once instead of being retried five times by dlt."""
        if error.response["Error"]["Code"] in _PERMANENT:
            raise DestinationTerminalException(f"The data lake refused the write: {error}") from error
        raise error
