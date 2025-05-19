from typing import Any, Dict, Literal, Optional, TypedDict

from llama_index.vector_stores.azureaisearch import MetadataIndexFieldType

# Define literal types for various constants
NodeTypeValue = Literal["content", "summary"]
LanguageValue = Literal["de", "en", "fr", "it"]
HeadingLevelValue = Literal[0, 1, 2, 3, 4, 5, 6]

# Node Level - Required Attributes
NODE_ID: str = "id"
NODE_CONTENT: str = "content"
NODE_EMBEDDING: str = "embedding"
NODE_METADATA: str = "json_metadata"
DOCUMENT_ID: str = "document_id"
DOCUMENT_TITLE: str = "document_title"

# Document level - Metadata
NAMESPACE: str = "namespace"
SOURCE: str = "source"
HASH: str = "content_hash"
TYPE: str = "type"
LANGUAGE: str = "language"
VERSION: str = "version"
CREATED_AT: str = "created_at"
UPDATED_AT: str = "updated_at"
INSERTED_AT: str = "inserted_at"
DATA_LAKE_URI: str = "data_lake_uri"

# Node level - Metadata
INDEX: str = "index"
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

# Allowed node types with literal typing
NODE_TYPE_CONTENT: NodeTypeValue = "content"
NODE_TYPE_SUMMARY: NodeTypeValue = "summary"

# Allowed languages with literal typing
NODE_LANGUAGE_GERMAN: LanguageValue = "de"
NODE_LANGUAGE_ENGLISH: LanguageValue = "en"
NODE_LANGUAGE_FRENCH: LanguageValue = "fr"
NODE_LANGUAGE_ITALIAN: LanguageValue = "it"


class NodeMetadata(TypedDict, total=False):
    namespace: str
    source: str
    document_title: str
    type: NodeTypeValue
    language: LanguageValue
    version: int
    created_at: Optional[int]
    updated_at: Optional[int]
    inserted_at: Optional[int]
    index: int
    section_start_line: int
    section_end_line: int
    h1: Optional[str]
    h2: Optional[str]
    h3: Optional[str]
    h4: Optional[str]
    h5: Optional[str]
    h6: Optional[str]
    heading_level: HeadingLevelValue
    reference_name: Optional[str]
    reference_url: Optional[str]


DEFAULT_METADATA: Dict[str, Any] = {
    NAMESPACE: "",
    SOURCE: "",
    DOCUMENT_TITLE: "",
    TYPE: NODE_TYPE_CONTENT,
    LANGUAGE: NODE_LANGUAGE_ENGLISH,
    VERSION: 1,
    CREATED_AT: None,
    UPDATED_AT: None,
    INSERTED_AT: None,
    INDEX: 0,
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
}

# Field definitions with their types for Azure Search
DEFAULT_METADATA_FIELDS: Dict[str, tuple] = {
    NAMESPACE: (NAMESPACE, MetadataIndexFieldType.STRING),
    SOURCE: (SOURCE, MetadataIndexFieldType.STRING),
    DOCUMENT_TITLE: (DOCUMENT_TITLE, MetadataIndexFieldType.STRING),
    TYPE: (TYPE, MetadataIndexFieldType.STRING),
    LANGUAGE: (LANGUAGE, MetadataIndexFieldType.STRING),
    VERSION: (VERSION, MetadataIndexFieldType.INT32),
    CREATED_AT: (CREATED_AT, MetadataIndexFieldType.INT32),
    UPDATED_AT: (UPDATED_AT, MetadataIndexFieldType.INT32),
    INSERTED_AT: (INSERTED_AT, MetadataIndexFieldType.INT32),
    INDEX: (INDEX, MetadataIndexFieldType.INT32),
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
}
