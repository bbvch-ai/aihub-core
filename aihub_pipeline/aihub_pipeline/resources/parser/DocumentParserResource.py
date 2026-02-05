from enum import StrEnum
from typing import Annotated

from aihub_lib.generative_ai.document.loaders.DocumentIntelligenceLoader import DocumentIntelligenceLoader
from aihub_lib.generative_ai.document.loaders.ImageLoader import ImageLoader
from aihub_lib.generative_ai.document.loaders.MarkItDownLoader import MarkItDownLoader
from aihub_lib.generative_ai.document.loaders.MineruLoader import MineruLoader
from aihub_lib.generative_ai.document.loaders.RawLoader import RawLoader
from aihub_lib.infrastructure.azure_cognitive_services.AzureDocumentIntelligenceSettings import (
    AzureDocumentIntelligenceSettings,
)
from aihub_lib.infrastructure.mineru.MineruSettings import MineruSettings
from dagster import ConfigurableResource
from llama_index.core.readers.base import BaseReader
from llama_index.readers.file import EpubReader, IPYNBReader, RTFReader
from pydantic import Field


class LoaderType(StrEnum):
    """Enum for document loader types."""

    MINERU = "mineru"
    DOCUMENT_INTELLIGENCE = "document_intelligence"


class DocumentParserResource(ConfigurableResource):
    """
    This resource specifies what document parsers (Readers) to use for different file types.

    Note that this resource specifies a list of commonly used document parsers. If you have different requirements,
    either make this resource configurable or create a new resource with your specific parsers and decision logic.

    The document parsers can be configured through environment variables in their respective settings classes.

    You can specify which loader to use through the `loader_type` parameter:
    - MINERU: Use MineruLoader for PDF/images and MarkItDownLoader for Office docs (default)
    - DOCUMENT_INTELLIGENCE: Use Azure DocumentIntelligenceLoader

    Example usage:

    1. Get the document parser for a file type:

    .. code-block:: python
        from aihub_pipeline.resources.app.DocumentParserResource import DocumentParserResource, LoaderType
        from aihub_pipeline.resources.data_lake.DataLakeFileSystemResource import DataLakeFileSystemResource

        from dagster import Definitions, asset

        @asset
        def asset1(
            data_lake_file: DataLakeFile,
            document_parser: DocumentParserResource,
            data_lake_file_system: ResourceParam[AbstractFileSystem],
        ):
            reader = document_parser.get_document_parser_for_filetype(data_lake_file.filetype)
            documents = reader.load_data(data_lake_file.uri, fs=data_lake_file_system)
            ...

        defs = Definitions(
            assets=[asset1],
            resources={
                "document_parser": DocumentParserResource(loader_type=LoaderType.MINERU),
                "data_lake_file_system": data_lake_file_system,
            },
        )
    """

    loader_type: Annotated[
        LoaderType,
        Field(
            description="Specifies which document loader to use. Options: MINERU (default), DOCUMENT_INTELLIGENCE",
        ),
    ] = LoaderType.MINERU

    include_images: Annotated[
        bool, Field(default=True, description="Specifies if images should be embedded into the documents and nodes.")
    ] = True

    _base_readers: dict[type[BaseReader], list[str]] = {
        EpubReader: ["epub"],
        IPYNBReader: ["ipynb"],
        RawLoader: ["txt", "md"],
        RTFReader: ["rtf"],
    }

    def _get_readers_map(self) -> dict[type[BaseReader], list[str]]:
        """
        Get the readers map based on the configured loader type.

        Note: Image extensions are handled by the document loaders (MinerU),
        not by ImageLoader, to ensure consistent parsing and image extraction.
        """
        readers_map = self._base_readers.copy()

        if self.loader_type == LoaderType.MINERU:
            # MinerU handles PDF and images
            readers_map[MineruLoader] = MineruSettings().EXTENSIONS
            # MarkItDown handles Office documents
            readers_map[MarkItDownLoader] = MarkItDownLoader.SUPPORTED_EXTENSIONS

        if self.loader_type == LoaderType.DOCUMENT_INTELLIGENCE:
            readers_map[DocumentIntelligenceLoader] = AzureDocumentIntelligenceSettings().EXTENSIONS
            # Fallback ImageLoader for Document Intelligence mode
            readers_map[ImageLoader] = ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "tif", "heif"]

        return readers_map

    def get_document_parser_for_filetype(self, filetype: str) -> BaseReader:
        filetype = filetype.lower()

        # Build the extension to reader mapping based on the current configuration
        readers_map = self._get_readers_map()
        extension_to_reader = {ext: reader_cls for reader_cls, extensions in readers_map.items() for ext in extensions}

        reader_cls = extension_to_reader.get(filetype)
        if reader_cls is None:
            raise ValueError(f"Unsupported file extension: {filetype}")

        return reader_cls()
