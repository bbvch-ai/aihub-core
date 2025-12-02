from enum import Enum
from typing import Annotated

from aihub_lib.generative_ai.document.loaders.DoclingLoader import DoclingLoader
from aihub_lib.generative_ai.document.loaders.DocumentIntelligenceLoader import DocumentIntelligenceLoader
from aihub_lib.generative_ai.document.loaders.ImageLoader import ImageLoader
from aihub_lib.generative_ai.document.loaders.RawLoader import RawLoader
from aihub_lib.generative_ai.resources.models.llm.LLMConfig import LLMConfig
from aihub_lib.infrastructure.azure_cognitive_services.AzureDocumentIntelligenceSettings import (
    AzureDocumentIntelligenceSettings,
)
from aihub_lib.infrastructure.docling.DoclingSettings import DoclingSettings
from dagster import ConfigurableResource, ResourceDependency
from llama_index.core.readers.base import BaseReader
from llama_index.readers.file import EpubReader, IPYNBReader, RTFReader
from pydantic import Field


class LoaderType(Enum):
    """Enum for document loader types."""

    DOCLING = "docling"
    DOCUMENT_INTELLIGENCE = "document_intelligence"


class DocumentParserResource(ConfigurableResource):
    """
    This resource specifies what document parsers (Readers) to use for different file types.

    Note that this resource specifies a list of commonly used document parsers. If you have different requirements,
    either make this resource configurable or create a new resource with your specific parsers and decision logic.

    The document parsers for DoclingLoader and DocumentIntelligenceLoader can be configured through environment
    variables in their configs.

    You can specify which loader to use through the `loader_type` parameter:
    - DOCLING: Use only DoclingLoader (default)
    - DOCUMENT_INTELLIGENCE: Use only DocumentIntelligenceLoader

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
                "document_parser": DocumentParserResource(loader_type=LoaderType.DOCLING),
                "data_lake_file_system": data_lake_file_system,
            },
        )
    """

    loader_type: Annotated[
        LoaderType,
        Field(
            description="Specifies which document loader to use. Options: DOCLING, DOCUMENT_INTELLIGENCE",
        ),
    ] = LoaderType.DOCLING

    include_images: Annotated[
        bool, Field(default=True, description="Specifies if images should be embedded into the documents and nodes.")
    ] = True

    refine_tables: Annotated[
        bool,
        Field(
            default=True,
            description="If True, uses LLM during parsing to analyze table structure. "
            "Set to False to defer table refinement to a separate pipeline step.",
        ),
    ] = True

    llm_config: ResourceDependency[LLMConfig]

    _base_readers = {
        EpubReader: ["epub"],
        IPYNBReader: ["ipynb"],
        RawLoader: ["txt", "md"],
        RTFReader: ["rtf"],
        ImageLoader: ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp", "tif", "heif"],
    }

    def _get_readers_map(self) -> dict[type[BaseReader], list[str]]:
        """
        Get the readers map based on the configured loader type.
        """
        readers_map = self._base_readers.copy()

        if self.loader_type == LoaderType.DOCLING:
            readers_map[DoclingLoader] = DoclingSettings().EXTENSIONS

        if self.loader_type == LoaderType.DOCUMENT_INTELLIGENCE:
            readers_map[DocumentIntelligenceLoader] = AzureDocumentIntelligenceSettings().EXTENSIONS

        return readers_map

    def get_document_parser_for_filetype(self, filetype: str) -> BaseReader:
        filetype = filetype.lower()

        # Build the extension to reader mapping based on the current configuration
        readers_map = self._get_readers_map()
        extension_to_reader = {ext: reader_cls for reader_cls, extensions in readers_map.items() for ext in extensions}

        reader_cls = extension_to_reader.get(filetype)
        if reader_cls is None:
            raise ValueError(f"Unsupported file extension: {filetype}")

        # Pass llm_config and refine_tables to DoclingLoader
        if reader_cls == DoclingLoader:
            return DoclingLoader(llm_config=self.llm_config, refine_tables=self.refine_tables)

        return reader_cls()
