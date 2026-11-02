from typing import Annotated

from pydantic import BaseModel, Field
from swiss_ai_hub.core.persistence import DOCUMENT_TITLE, SOURCE_ORIGIN

from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile


class StructuredFileReference(BaseModel):
    """A binary file a structured source offers next to its records, as a reference the destination downloads.

    The file never travels through dlt: a row carries this reference, and the destination reads the content through
    the adapter while it loads, one file at a time. Its key is built like a record's, so a listing and a write cannot
    disagree, but it keeps the file's own extension.
    """

    namespace: Annotated[str, Field(description="Top-level folder; the ingestion pipeline makes it the namespace.")]
    path_segments: Annotated[
        list[str],
        Field(min_length=1, description="Folders below the namespace, then the file name without its extension."),
    ]
    extension: Annotated[str, Field(min_length=1, description="The file's extension, lower case, without its dot.")]
    download_url: Annotated[str, Field(description="Where the adapter downloads the content from.")]
    size: Annotated[int, Field(ge=0, description="Size in bytes, as the source reports it.")]
    title: Annotated[str, Field(description="Title the document is cited with.")]
    url: Annotated[str, Field(description="Page a citation links to, where a user can open the file.")]

    @property
    def object_key(self) -> str:
        return StructuredRecordFile.object_key_for(self.namespace, self.path_segments, self.extension)

    def metadata(self) -> dict[str, str]:
        """The object metadata ingestion reads a document's title and link from; nothing else, because ingestion
        copies every key into the document and embeds it with each chunk."""
        return {DOCUMENT_TITLE: self.title, SOURCE_ORIGIN: self.url}
