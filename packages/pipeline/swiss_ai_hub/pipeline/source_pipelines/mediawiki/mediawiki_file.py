from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from swiss_ai_hub.pipeline.types.structured_file_reference import StructuredFileReference
from swiss_ai_hub.pipeline.types.structured_record_file import StructuredRecordFile


class MediaWikiFile(BaseModel):
    """One file a synced page shows or links to, as the sync yields it: where it is stored, where it is downloaded
    from, and the checksum that tells whether it changed.

    Its file lands in the collection named after the file namespace's canonical name, ``File``, under its own name and
    extension, once however many pages use it.
    """

    page_id: Annotated[int, Field(description="Id of the file's description page.")]
    name: Annotated[str, Field(description="The file name without the namespace prefix, e.g. Report 2026.pdf.")]
    namespace: Annotated[str, Field(description="Knowledge namespace, after the wiki's file namespace.")]
    download_url: Annotated[str, Field(description="URL of the file's latest version.")]
    description_url: Annotated[str, Field(description="The file's description page, which citations link to.")]
    size: Annotated[int, Field(description="Size in bytes of the latest version.")]
    sha1: Annotated[str, Field(description="Checksum of the latest version; it changes with every upload.")]

    @classmethod
    def from_listing(
        cls,
        file: Annotated[dict[str, Any], "A file page with its imageinfo, as files_used_by returns it"],
        namespace: Annotated[str, "Knowledge namespace of the wiki's file namespace"],
    ) -> Self:
        info = file["imageinfo"]
        return cls(
            page_id=file["pageid"],
            name=file["title"].split(":", 1)[1],
            namespace=namespace,
            download_url=info["url"],
            description_url=info["descriptionurl"],
            size=info["size"],
            sha1=info["sha1"],
        )

    @property
    def extension(self) -> str:
        """Lower case, so a listing and a write agree whatever case the uploader used; empty without a dot."""
        return self.name.rsplit(".", 1)[1].lower() if "." in self.name else ""

    @property
    def object_key(self) -> str:
        return StructuredRecordFile.object_key_for(self.namespace, [self._stem()], self.extension)

    @property
    def fingerprint(self) -> str:
        return f"{self.sha1}|{self.object_key}"

    def to_reference(self) -> StructuredFileReference:
        return StructuredFileReference(
            namespace=self.namespace,
            path_segments=[self._stem()],
            extension=self.extension,
            download_url=self.download_url,
            size=self.size,
            title=self.name,
            url=self.description_url,
        )

    def _stem(self) -> str:
        return self.name.rsplit(".", 1)[0]
