from dagster import ConfigurableResource
from llama_index.core.readers.base import BaseReader
from llama_index.readers.file import EpubReader, IPYNBReader, RTFReader

from aihub_lib.generative_ai.document.loaders.DocumentIntelligenceLoader import DocumentIntelligenceLoader
from aihub_lib.generative_ai.document.loaders.RawLoader import RawLoader


class DocumentParserResource(ConfigurableResource):
    """
    This resource specifies what document parsers (Readers) to use for different file types.

    Note that this resource specifies a list of commonly used document parsers. If you have different requirements,
    either make this resource configurable or create a new resource with your specific parsers and decision logic.

    Example usage:

    1. Get the document parser for a file type:

    .. code-block:: python
        from aihub_pipeline.resources.app.DocumentParserResource import DocumentParserResource
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
                "document_parser": DocumentParserResource(),
                "data_lake_file_system": data_lake_file_system,
            },
        )
    """

    _readers_map = {
        DocumentIntelligenceLoader: [
            "jpg",
            "jpeg",
            "png",
            "bmp",
            "tiff",
            "heif",
            "pdf",
            "docx",
            "xlsx",
            "pptx",
            "html",
        ],
        EpubReader: ["epub"],
        IPYNBReader: ["ipynb"],
        RawLoader: ["txt", "md"],
        RTFReader: ["rtf"],
    }

    # Inverted mapping from file extensions to reader classes
    _extension_to_reader = {ext: reader_cls for reader_cls, extensions in _readers_map.items() for ext in extensions}

    def get_document_parser_for_filetype(self, filetype: str) -> BaseReader:
        filetype = filetype.lower()
        reader_cls = self._extension_to_reader.get(filetype)
        if reader_cls is None:
            raise ValueError(f"Unsupported file extension: {filetype}")
        return reader_cls()
