from typing import Any, Literal, TypedDict

from llama_index.vector_stores.azureaisearch import MetadataIndexFieldType

# Define literal types for various constants
NodeTypeValue = Literal["content", "summary"]
NodeContentType = Literal["text", "figure", "table"]
LanguageValue = Literal["de", "en", "fr", "it"]
HeadingLevelValue = Literal[0, 1, 2, 3, 4, 5, 6]

# Node Level - Required Attributes
NODE_ID: str = "id"
NODE_CONTENT: str = "content"
NODE_CONTENT_TYPE: str = "content_type"
NODE_EMBEDDING: str = "embedding"
NODE_METADATA: str = "json_metadata"
DOCUMENT_ID: str = "document_id"
DOCUMENT_TITLE: str = "document_title"

# Document level - Metadata
NAMESPACE: str = "namespace"
SOURCE: str = "source"
SOURCE_ORIGIN: str = "source_origin"
HASH: str = "content_hash"
TYPE: str = "type"
LANGUAGE: str = "language"
VERSION: str = "version"
NUMBER_OF_PAGES: str = "number_of_pages"
CREATED_AT: str = "created_at"
UPDATED_AT: str = "updated_at"
INSERTED_AT: str = "inserted_at"

# Node level - Metadata
INDEX = "index"
PAGE = "page"
SECTION_START_LINE: str = "section_start_line"
SECTION_END_LINE: str = "section_end_line"
H1: str = "h1"
H2: str = "h2"
H3: str = "h3"
H4: str = "h4"
H5: str = "h5"
H6: str = "h6"
HEADING_LEVEL: str = "heading_level"
REFERENCE_NAME: str = "reference_name"
REFERENCE_URL: str = "reference_url"
DOCUMENT_STORE_NAME = "document_store_name"

# Allowed node types with literal typing
NODE_TYPE_CONTENT: NodeTypeValue = "content"
NODE_TYPE_SUMMARY: NodeTypeValue = "summary"

NODE_CONTENT_TYPE_TABLE: NodeContentType = "table"
NODE_CONTENT_TYPE_FIGURE: NodeContentType = "figure"
NODE_CONTENT_TYPE_TEXT: NodeContentType = "text"

# Allowed languages with literal typing
NODE_LANGUAGE_GERMAN: LanguageValue = "de"
NODE_LANGUAGE_ENGLISH: LanguageValue = "en"
NODE_LANGUAGE_FRENCH: LanguageValue = "fr"
NODE_LANGUAGE_ITALIAN: LanguageValue = "it"


class NodeMetadata(TypedDict, total=False):
    namespace: str
    source: str
    source_origin: str | None
    document_title: str
    type: NodeTypeValue
    content_type: NodeContentType
    language: LanguageValue
    version: int
    created_at: int | None
    updated_at: int | None
    inserted_at: int | None
    index: int
    section_start_line: int
    section_end_line: int
    h1: str | None
    h2: str | None
    h3: str | None
    h4: str | None
    h5: str | None
    h6: str | None
    heading_level: HeadingLevelValue
    reference_name: str | None
    reference_url: str | None


DEFAULT_METADATA: dict[str, Any] = {
    NAMESPACE: "",
    SOURCE: "",
    SOURCE_ORIGIN: None,
    DOCUMENT_TITLE: "",
    TYPE: NODE_TYPE_CONTENT,
    NODE_CONTENT_TYPE: NODE_CONTENT_TYPE_TEXT,
    LANGUAGE: NODE_LANGUAGE_ENGLISH,
    VERSION: 1,
    CREATED_AT: None,
    UPDATED_AT: None,
    INSERTED_AT: None,
    INDEX: 0,
    PAGE: 0,
    SECTION_START_LINE: 0,
    SECTION_END_LINE: 0,
    H1: None,
    H2: None,
    H3: None,
    H4: None,
    H5: None,
    H6: None,
    HEADING_LEVEL: 0,
    REFERENCE_NAME: None,
    REFERENCE_URL: None,
    DOCUMENT_STORE_NAME: None,
}

# Field definitions with their types for Azure Search
DEFAULT_METADATA_FIELDS: dict[str, tuple] = {
    NAMESPACE: (NAMESPACE, MetadataIndexFieldType.STRING),
    SOURCE: (SOURCE, MetadataIndexFieldType.STRING),
    SOURCE_ORIGIN: (SOURCE_ORIGIN, MetadataIndexFieldType.STRING),
    DOCUMENT_TITLE: (DOCUMENT_TITLE, MetadataIndexFieldType.STRING),
    TYPE: (TYPE, MetadataIndexFieldType.STRING),
    NODE_CONTENT_TYPE: (NODE_CONTENT_TYPE, MetadataIndexFieldType.STRING),
    LANGUAGE: (LANGUAGE, MetadataIndexFieldType.STRING),
    VERSION: (VERSION, MetadataIndexFieldType.INT32),
    CREATED_AT: (CREATED_AT, MetadataIndexFieldType.INT32),
    UPDATED_AT: (UPDATED_AT, MetadataIndexFieldType.INT32),
    INSERTED_AT: (INSERTED_AT, MetadataIndexFieldType.INT32),
    INDEX: (INDEX, MetadataIndexFieldType.INT32),
    PAGE: (PAGE, MetadataIndexFieldType.INT32),
    SECTION_START_LINE: (SECTION_START_LINE, MetadataIndexFieldType.INT32),
    SECTION_END_LINE: (SECTION_END_LINE, MetadataIndexFieldType.INT32),
    H1: (H1, MetadataIndexFieldType.STRING),
    H2: (H2, MetadataIndexFieldType.STRING),
    H3: (H3, MetadataIndexFieldType.STRING),
    H4: (H4, MetadataIndexFieldType.STRING),
    H5: (H5, MetadataIndexFieldType.STRING),
    H6: (H6, MetadataIndexFieldType.STRING),
    HEADING_LEVEL: (HEADING_LEVEL, MetadataIndexFieldType.INT32),
    REFERENCE_NAME: (REFERENCE_NAME, MetadataIndexFieldType.STRING),
    REFERENCE_URL: (REFERENCE_URL, MetadataIndexFieldType.STRING),
    DOCUMENT_STORE_NAME: (DOCUMENT_STORE_NAME, MetadataIndexFieldType.STRING),
}
