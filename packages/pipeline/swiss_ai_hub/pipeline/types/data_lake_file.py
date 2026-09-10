import base64
import hashlib
import mimetypes
import os
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, computed_field

from swiss_ai_hub.pipeline.util.id_utils import uri_to_id


class DataLakeFile(BaseModel):
    """
    A Pydantic model representing a file in Azure Data Lake, including its metadata and optional content.
    """

    name: Annotated[str, Field(description="The name of the file.")]
    namespace: Annotated[str, Field(description="The namespace to which the file belongs.")]
    filetype: Annotated[str, Field(description="The type of the file, derived from its extension.")]
    uri: Annotated[str, Field(description="The URI of the file in the data lake.")]
    size: Annotated[int, Field(description="The size of the file in bytes.")]
    content_type: Annotated[str, Field(description="The MIME type of the file content.")]
    owner: Annotated[str, Field(description="The owner of the file.")]
    hash: Annotated[
        str,
        Field(
            description="Opaque content-version token. Base64-encoded MD5 for locally produced content and for "
            "plain-MD5 S3 ETags, but a verbatim chunked ETag ('<md5hex>-<n>') for objects the store chunked. "
            "Only assume base64-MD5 where the file came from from_content() — see AzureDataLakeIOManager."
        ),
    ]

    created: Annotated[int, Field(description="The UNIX timestamp when the file was created.")]
    updated: Annotated[int, Field(description="The UNIX timestamp when the file was last updated.")]

    metadata: Annotated[dict, Field(description="A dictionary of metadata associated with the file.")]

    content: Annotated[bytes | None, Field(description="The binary content of the file.")] = None

    @computed_field
    @property
    def id_(self) -> str:
        return uri_to_id(self.uri)

    @staticmethod
    def from_content(uri: str, content: bytes, metadata: dict = None):
        """
        Create a DataLakeFile instance from given content to be uploaded to the data lake.
        Constructs the necessary file properties and metadata based on the provided content and URI.
        """
        uri_parts = uri.split("/")
        namespace = uri_parts[1]
        filename = uri_parts[-1]
        _, extension = os.path.splitext(filename)
        file_type = extension.lower()[1:] or "unknown"

        size = len(content)
        md5_hash = hashlib.md5(content).digest()
        md5_hash_str = base64.b64encode(md5_hash).decode("utf-8")

        current_timestamp = int(datetime.now().timestamp())
        mimetypes.add_type(
            "text/markdown", ".md"
        )  # Add custom MIME type for markdown files because it's not in the standard library
        return DataLakeFile(
            name=filename,
            namespace=namespace,
            filetype=file_type,
            uri=uri,
            size=size,
            content_type=mimetypes.guess_type(filename)[0] or "application/octet-stream",
            owner=os.getenv("USER")
            or os.getenv("USERNAME")
            or "pipeline-user",  #  Fallback chain: Unix USER -> Windows USERNAME -> default
            hash=md5_hash_str,
            created=current_timestamp,
            updated=current_timestamp,
            metadata=metadata or {},
            content=content,
        )
