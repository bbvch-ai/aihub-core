from llama_index.vector_stores.azureaisearch import MetadataIndexFieldType

# Node Level - Required Attributes
NODE_ID = "id"
NODE_CONTENT = "content"
NODE_EMBEDDING = "embedding"
NODE_METADATA = "json_metadata"
DOCUMENT_ID = "document_id"
DOCUMENT_TITLE = "document_title"

# Document level - Metadata
NAMESPACE = "namespace"
SOURCE = "source"
HASH = "content_hash"
TYPE = "type"
LANGUAGE = "language"
VERSION = "version"
CREATED_AT = "created_at"
UPDATED_AT = "updated_at"
INSERTED_AT = "inserted_at"
DATA_LAKE_URI = "data_lake_uri"

# Node level - Metadata
INDEX = "index"
SECTION_START_LINE = "section_start_line"
SECTION_END_LINE = "section_end_line"
H1 = "h1"
H2 = "h2"
H3 = "h3"
H4 = "h4"
H5 = "h5"
H6 = "h6"
HEADING_LEVEL = "heading_level"
REFERENCE = "reference"

# Allowed node types
NODE_TYPE_CONTENT = "content"
NODE_TYPE_SUMMARY = "summary"

# Allowed languages
NODE_LANGUAGE_GERMAN = "de"
NODE_LANGUAGE_ENGLISH = "en"
NODE_LANGUAGE_FRENCH = "fr"
NODE_LANGUAGE_ITALIAN = "it"

DEFAULT_METADATA = {
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
    REFERENCE: None,
}

DEFAULT_METADATA_FIELDS = {
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
    REFERENCE: (REFERENCE, MetadataIndexFieldType.STRING),
}
