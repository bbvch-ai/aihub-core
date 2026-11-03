from typing import Annotated

from pydantic import BaseModel, Field


class ExtractedTableFile(BaseModel):
    """Where the whole table of an extraction is stored, as CSV.

    Events carry this reference and a preview, never every row: a table of any size then stays out of the message
    broker, the event store and the traces, and clients download it from object storage instead.
    """

    bucket: Annotated[str, Field(description="The object storage bucket holding the file.")]
    key: Annotated[str, Field(description="The object key of the file within the bucket.")]
    filename: Annotated[str, Field(description="The name the file is downloaded under.", pattern=r"^[^/\\]+$")]
    size: Annotated[int, Field(description="The file's size in bytes.", ge=0)]
    row_count: Annotated[int, Field(description="Rows the file holds, without the header.", ge=0)]
    content_type: Annotated[str, Field(description="The file's media type.")] = "text/csv; charset=utf-8"
