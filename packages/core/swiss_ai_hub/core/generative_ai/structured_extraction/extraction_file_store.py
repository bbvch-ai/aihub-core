import asyncio
import functools
import json
from typing import Annotated

from botocore.exceptions import ClientError
from mypy_boto3_s3 import S3Client

from swiss_ai_hub.core.events.agent.user.user_uploaded_file import UserUploadedFile
from swiss_ai_hub.core.generative_ai.document.accessor.s3_anonymous_file_access_service import (
    S3AnonymousFileAccessService,
)
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_record import RecordValue
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_csv import ExtractedTableCsv
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_file import ExtractedTableFile
from swiss_ai_hub.core.infrastructure.s3.use_s3 import create_s3_client, create_s3_service

# Under the shared agent-files bucket and its expiry: a table is a result to download, not a record to keep.
_PREFIX = "record-extraction"
_NOT_FOUND = {"404", "NoSuchKey", "NotFound"}
_SAFE_FILENAME = str.maketrans({"/": "_", "\\": "_", '"': "_"})


class ExtractionFileStore:
    """Keeps the rows and tables of record extractions in object storage, so events carry a reference instead.

    A document's rows can be many and long (whole contract clauses), and a table holds every document's; inside events
    they hit the message broker's size limit and are copied into the event store and every trace. Here each document's
    rows are one JSON object and the assembled table one CSV, under the extraction's id in the agent-files bucket.
    """

    BUCKET = UserUploadedFile.AGENT_FILES_BUCKET

    @staticmethod
    async def put_rows(
        extraction_id: Annotated[str, "The extraction the rows belong to"],
        request_id: Annotated[str, "The document request they answer, unique within the extraction"],
        rows: Annotated[list[dict[str, RecordValue]], "Field name to value, one entry per record"],
    ) -> str:
        key = f"{_PREFIX}/{extraction_id}/rows/{request_id}.json"
        body = json.dumps(rows, ensure_ascii=False).encode("utf-8")
        await asyncio.to_thread(
            ExtractionFileStore._client().put_object,
            Bucket=ExtractionFileStore.BUCKET,
            Key=key,
            Body=body,
            ContentType="application/json",
        )
        return key

    @staticmethod
    async def rows(key: Annotated[str, "A key `put_rows` returned"]) -> list[dict[str, RecordValue]]:
        response = await asyncio.to_thread(
            ExtractionFileStore._client().get_object, Bucket=ExtractionFileStore.BUCKET, Key=key
        )
        return json.loads(await asyncio.to_thread(response["Body"].read))

    @staticmethod
    async def put_table(
        extraction_id: Annotated[str, "The extraction the table answers"],
        filename: Annotated[str, "The name the file is downloaded under"],
        columns: Annotated[list[str], "The header"],
        rows: Annotated[list[list[RecordValue]], "Every row, cells in column order"],
    ) -> ExtractedTableFile:
        name = filename.translate(_SAFE_FILENAME)
        body = ExtractedTableCsv.encode(columns, rows)
        table = ExtractedTableFile(
            bucket=ExtractionFileStore.BUCKET,
            key=f"{_PREFIX}/{extraction_id}/{name}",
            filename=name,
            size=len(body),
            row_count=len(rows),
        )
        await asyncio.to_thread(
            ExtractionFileStore._client().put_object,
            Bucket=table.bucket,
            Key=table.key,
            Body=body,
            ContentType=table.content_type,
            ContentDisposition=f'attachment; filename="{name}"',
        )
        return table

    @staticmethod
    def holds(table: ExtractedTableFile) -> bool:
        """Whether the file is an extraction's table: the bucket also holds uploads and sandbox files, which a
        reference read from an event must never get a download link to."""
        return table.bucket == ExtractionFileStore.BUCKET and table.key.startswith(f"{_PREFIX}/")

    @staticmethod
    async def exists(table: ExtractedTableFile) -> bool:
        """False once the bucket's expiry removed the file, so a download can say so instead of failing."""
        try:
            await asyncio.to_thread(ExtractionFileStore._client().head_object, Bucket=table.bucket, Key=table.key)
        except ClientError as error:
            if error.response.get("Error", {}).get("Code") in _NOT_FOUND:
                return False
            raise
        return True

    @staticmethod
    def download_url(
        table: ExtractedTableFile, lifetime_hours: Annotated[int, "How long the link works, at most 168"] = 24
    ) -> str:
        """A presigned link on the public endpoint that downloads the file under its name; whoever holds it can use it
        until it expires, so it is only ever handed to someone allowed to see the table."""
        return ExtractionFileStore._service().generate_sas_url(
            table.bucket,
            table.key,
            lifetime_hours=lifetime_hours,
            response_content_disposition=f'attachment; filename="{table.filename}"',
        )

    @staticmethod
    @functools.cache
    def _client() -> S3Client:
        """One client per process: an extraction writes and reads one object per document, and a client is slow to
        build. boto3 clients are safe to share between threads."""
        return create_s3_client()

    @staticmethod
    @functools.cache
    def _service() -> S3AnonymousFileAccessService:
        return create_s3_service()
