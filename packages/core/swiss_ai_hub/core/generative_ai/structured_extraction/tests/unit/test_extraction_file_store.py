import io
import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_csv import ExtractedTableCsv
from swiss_ai_hub.core.generative_ai.structured_extraction.extracted_table_file import ExtractedTableFile
from swiss_ai_hub.core.generative_ai.structured_extraction.extraction_file_store import ExtractionFileStore

pytestmark = pytest.mark.unit

STORE = "swiss_ai_hub.core.generative_ai.structured_extraction.extraction_file_store"


class _S3:
    """A boto3 client in memory: what was put, and the response to every get."""

    def __init__(self) -> None:
        self.objects: dict[tuple[str, str], dict[str, Any]] = {}
        self.head_object = MagicMock()

    def put_object(self, **kwargs: Any) -> None:
        self.objects[(kwargs["Bucket"], kwargs["Key"])] = kwargs

    def get_object(self, Bucket: str, Key: str) -> dict[str, Any]:  # noqa: N803 - boto3's own argument names
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)]["Body"])}


@pytest.fixture
def s3() -> Any:
    client = _S3()
    with patch(f"{STORE}.ExtractionFileStore._client", return_value=client):
        yield client


def _table(**fields: Any) -> ExtractedTableFile:
    return ExtractedTableFile(
        **{"bucket": "agent-files", "key": "record-extraction/x1/t.csv", "filename": "t.csv", "size": 1, "row_count": 1}
        | fields
    )


@pytest.mark.asyncio
async def test_rows_round_trip_under_the_extractions_key(s3: _S3):
    rows = [{"item": "Gerät ü", "amount": 1.5, "unit": None, "ok": True}, {"item": "Kabel", "amount": 2}]

    key = await ExtractionFileStore.put_rows("x1", "req-1", rows)

    assert key == "record-extraction/x1/rows/req-1.json"
    stored = s3.objects[(ExtractionFileStore.BUCKET, key)]
    assert stored["ContentType"] == "application/json"
    assert "Gerät ü".encode() in stored["Body"]
    assert json.loads(stored["Body"]) == rows
    assert await ExtractionFileStore.rows(key) == rows


@pytest.mark.asyncio
async def test_a_table_is_stored_as_csv_with_its_reference(s3: _S3):
    columns, rows = ["Path", "Amount"], [["a.pdf", 1], ["b.pdf", 2.5]]

    table = await ExtractionFileStore.put_table("x1", "table-x1.csv", columns, rows)

    body = ExtractedTableCsv.encode(columns, rows)
    assert table == ExtractedTableFile(
        bucket=ExtractionFileStore.BUCKET,
        key="record-extraction/x1/table-x1.csv",
        filename="table-x1.csv",
        size=len(body),
        row_count=2,
    )
    stored = s3.objects[(table.bucket, table.key)]
    assert stored["Body"] == body
    assert stored["ContentType"] == "text/csv; charset=utf-8"
    assert stored["ContentDisposition"] == 'attachment; filename="table-x1.csv"'


@pytest.mark.asyncio
async def test_a_filename_cannot_leave_its_folder_or_break_the_disposition(s3: _S3):
    table = await ExtractionFileStore.put_table("x1", 'a/../b\\c"d.csv', ["a"], [])

    assert table.filename == "a_.._b_c_d.csv"
    assert table.key == "record-extraction/x1/a_.._b_c_d.csv"
    assert table.row_count == 0
    assert s3.objects[(table.bucket, table.key)]["ContentDisposition"] == 'attachment; filename="a_.._b_c_d.csv"'


@pytest.mark.parametrize("code", ["404", "NoSuchKey", "NotFound"])
@pytest.mark.asyncio
async def test_a_file_the_bucket_expired_does_not_exist(s3: _S3, code: str):
    s3.head_object.side_effect = ClientError({"Error": {"Code": code}}, "HeadObject")

    assert await ExtractionFileStore.exists(_table()) is False


@pytest.mark.asyncio
async def test_a_stored_file_exists(s3: _S3):
    assert await ExtractionFileStore.exists(_table()) is True
    s3.head_object.assert_called_once_with(Bucket="agent-files", Key="record-extraction/x1/t.csv")


@pytest.mark.asyncio
async def test_any_other_storage_error_is_raised(s3: _S3):
    s3.head_object.side_effect = ClientError({"Error": {"Code": "AccessDenied"}}, "HeadObject")

    with pytest.raises(ClientError):
        await ExtractionFileStore.exists(_table())


def test_the_download_link_names_the_file_as_an_attachment():
    service = MagicMock()
    service.generate_sas_url.return_value = "https://s3.example/t.csv?signed"
    with patch(f"{STORE}.ExtractionFileStore._service", return_value=service):
        url = ExtractionFileStore.download_url(_table(filename="table-x1.csv"), lifetime_hours=2)

    assert url == "https://s3.example/t.csv?signed"
    service.generate_sas_url.assert_called_once_with(
        "agent-files",
        "record-extraction/x1/t.csv",
        lifetime_hours=2,
        response_content_disposition='attachment; filename="table-x1.csv"',
    )


def test_a_reference_refuses_a_filename_with_a_path():
    with pytest.raises(ValueError):
        _table(filename="a/b.csv")
