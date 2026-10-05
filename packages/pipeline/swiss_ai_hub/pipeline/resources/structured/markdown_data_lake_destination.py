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
from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.util.source_updated_notifier import notify_source_updated
from swiss_ai_hub.pipeline.util.store_builders import build_s3_data_lake_client

_NOT_FOUND = {"404", "NoSuchKey", "NotFound"}
_PERMANENT = {"AccessDenied", "NoSuchBucket", "InvalidAccessKeyId", "SignatureDoesNotMatch"}


class MarkdownDataLakeDestination:
    """dlt custom destination that lands rendered records in one knowledge database's data lake.

    dlt delivers at least once: it retries a failed load job and re-delivers everything after a lost state. A file is
    therefore written only when its MD5 differs from the stored object's ETag, which is what keeps a run with no
    changes at the source from writing or announcing anything. The comparison uses the ETag rather than a hash kept as
    object metadata, because ingestion copies a file's metadata into its document and into every chunk it embeds.
    """

    BATCH_SIZE = 100

    def __init__(
        self,
        bucket: Annotated[str, "Bucket name of the knowledge database the records are written to"],
        context: Annotated[OpExecutionContext, "The step writing the files, for its log"],
    ):
        self.bucket = bucket
        self.context = context
        self.written_keys: list[str] = []
        self.unchanged_count = 0

    def as_dlt_destination(self) -> Callable[[TDataItems, TTableSchema], None]:
        """Loads sequentially, so the counters stay exact and batches are announced in the order they were written."""

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
        client = build_s3_data_lake_client(self.bucket, ensure_bucket=False)
        key_column = AbstractStructuredSourceAdapter.OBJECT_KEY_COLUMN
        written = [row[key_column] for row in rows if self._write_if_changed(client, row)]
        notify_source_updated(self.bucket, written)
        self.written_keys.extend(written)

    def _write_if_changed(self, client: S3DataLakeClient, row: dict) -> bool:
        object_key = row[AbstractStructuredSourceAdapter.OBJECT_KEY_COLUMN]
        content = row[AbstractStructuredSourceAdapter.MARKDOWN_COLUMN].encode()
        if self._stored_etag(client, object_key) == hashlib.md5(content, usedforsecurity=False).hexdigest():
            self.unchanged_count += 1
            return False
        data_lake_file = DataLakeFile.from_content(uri=client.build_uri(object_key), content=content)
        try:
            S3DataLakeIOManager.write_data_lake_file(client.raw_client, data_lake_file, self.context)
        except ClientError as error:
            self._reraise(error)
        return True

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
