from datetime import datetime

from dagster import MetadataValue, TableColumn, TableRecord, TableSchema
from llama_index.core.schema import TextNode
from swiss_ai_hub.core.persistence.rag.vectors.node_metadata import (
    CREATED_AT,
    H1,
    H2,
    H3,
    H4,
    H5,
    H6,
    HASH,
    INDEX,
    INSERTED_AT,
    LANGUAGE,
    NAMESPACE,
    NODE_CONTENT_TYPE,
    PAGE,
    REFERENCE_NAME,
    REFERENCE_URL,
    SECTION_END_LINE,
    SECTION_START_LINE,
    SOURCE,
    TYPE,
    UPDATED_AT,
    VERSION,
)

from swiss_ai_hub.pipeline.types.data_lake_file import DataLakeFile
from swiss_ai_hub.pipeline.types.rclone_file import MinimalRcloneFile
from swiss_ai_hub.pipeline.types.ref_doc_document import RefDocDocument
from swiss_ai_hub.pipeline.types.share_point_file import MinimalSharePointFile
from swiss_ai_hub.pipeline.types.source_file import MinimalSourceFile


def readable_date(timestamp: int):
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp).strftime("%Y.%m.%d %H:%M:%S")


def readable_size(num, suffix="B"):
    for unit in ("", "K", "M", "G", "T"):
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


def meta_timestamp_or_none(timestamp: int):
    if not timestamp:
        return None
    return MetadataValue.timestamp(float(timestamp))


def _records_matching_schema(rows: list[dict], columns: list[TableColumn]) -> list[TableRecord]:
    """Coerce each row to exactly the schema columns.

    Row builders spread arbitrary document metadata, so heterogeneous documents (e.g. a fully
    ingested doc next to a placeholder) yield records with differing field sets. Dagster's
    ``MetadataValue.table`` requires every record to share the same fields, so we project each
    row onto the declared columns, filling missing keys with ``None`` and dropping extras.
    """
    column_names = [column.name for column in columns]
    return [TableRecord({name: row.get(name) for name in column_names}) for row in rows]


def node_table_row(node: TextNode):
    return {
        "id": node.id_,
        "text": node.get_text(),
        "content": node.get_content(),
        "created_at_str": readable_date(node.metadata.get(CREATED_AT)),
        "updated_at_str": readable_date(node.metadata.get(UPDATED_AT)),
        "inserted_at_str": readable_date(node.metadata.get(INSERTED_AT)),
        **node.metadata,
    }


def node_metadata(node: TextNode):
    return {
        "Node ID": node.id_,
        "Text": MetadataValue.md(node.get_text()),
        "Metadata": MetadataValue.json(node.metadata),
    }


def data_lake_file_table_row(data_lake_file: DataLakeFile):
    return {
        "name": data_lake_file.name,
        "updated": readable_date(data_lake_file.updated),
        "uri": data_lake_file.uri,
        "size": readable_size(data_lake_file.size),
        "id": data_lake_file.id_,
        "hash": data_lake_file.hash,
    }


def data_lake_file_metadata(data_lake_file: DataLakeFile):
    return {
        "Name": data_lake_file.name,
        "Last modified": meta_timestamp_or_none(data_lake_file.updated),
        "Path in Data Lake": data_lake_file.uri,
        "Size": readable_size(data_lake_file.size),
        "Size in bytes": data_lake_file.size,
        "ID": data_lake_file.id_,
        "File Hash": data_lake_file.hash,
        "Metadata": MetadataValue.json(data_lake_file.metadata),
    }


def ref_doc_table_row(ref_doc: RefDocDocument):
    return {
        "id": ref_doc.id_,
        "content": ref_doc.get_content(),
        "created_at_str": readable_date(ref_doc.metadata.get(CREATED_AT)),
        "updated_at_str": readable_date(ref_doc.metadata.get(UPDATED_AT)),
        "inserted_at_str": readable_date(ref_doc.metadata.get(INSERTED_AT)),
        **ref_doc.metadata,
    }


def ref_doc_metadata(ref_doc: RefDocDocument):
    return {
        "Document ID": ref_doc.id_,
        "Text": MetadataValue.md(ref_doc.get_content()),
        "Metadata": MetadataValue.json(ref_doc.metadata),
    }


def nodes_metadata_table(nodes: list[TextNode]):
    columns = [
        TableColumn("id", "string"),
        TableColumn("text", "string"),
        TableColumn("content", "string"),
        TableColumn(NAMESPACE, "string"),
        TableColumn(SOURCE, "string"),
        TableColumn(HASH, "string"),
        TableColumn(TYPE, "string"),
        TableColumn(NODE_CONTENT_TYPE, "string"),
        TableColumn(LANGUAGE, "string"),
        TableColumn(VERSION, "int"),
        TableColumn(CREATED_AT, "int"),
        TableColumn(UPDATED_AT, "int"),
        TableColumn(INSERTED_AT, "int"),
        TableColumn(INDEX, "int"),
        TableColumn(PAGE, "int"),
        TableColumn(SECTION_START_LINE, "int"),
        TableColumn(SECTION_END_LINE, "int"),
        TableColumn(H1, "string"),
        TableColumn(H2, "string"),
        TableColumn(H3, "string"),
        TableColumn(H4, "string"),
        TableColumn(H5, "string"),
        TableColumn(H6, "string"),
        TableColumn(REFERENCE_NAME, "string"),
        TableColumn(REFERENCE_URL, "string"),
    ]
    rows = [node_table_row(node) for node in nodes]
    table_schema = TableSchema(columns=columns)
    return MetadataValue.table(records=_records_matching_schema(rows, columns), schema=table_schema)


def data_lake_metadata_table(data_lake_files: list[DataLakeFile]):
    columns = [
        TableColumn("name", "string"),
        TableColumn("updated", "string"),
        TableColumn("uri", "string"),
        TableColumn("size", "string"),
        TableColumn("id", "string"),
        TableColumn("hash", "string"),
    ]
    records = [TableRecord(data_lake_file_table_row(data_lake_file)) for data_lake_file in data_lake_files]
    table_schema = TableSchema(columns=columns)
    return MetadataValue.table(records=records, schema=table_schema)


def ref_doc_metadata_table(ref_docs: list[RefDocDocument]):
    columns = [
        TableColumn("id", "string"),
        TableColumn("text", "string"),
        TableColumn("content", "string"),
        TableColumn(NAMESPACE, "string"),
        TableColumn(SOURCE, "string"),
        TableColumn(HASH, "string"),
        TableColumn(TYPE, "string"),
        TableColumn(NODE_CONTENT_TYPE, "string"),
        TableColumn(LANGUAGE, "string"),
        TableColumn(VERSION, "int"),
        TableColumn(CREATED_AT, "int"),
        TableColumn(UPDATED_AT, "int"),
        TableColumn(INSERTED_AT, "int"),
    ]
    rows = [ref_doc_table_row(ref_doc) for ref_doc in ref_docs]
    table_schema = TableSchema(columns=columns)
    return MetadataValue.table(records=_records_matching_schema(rows, columns), schema=table_schema)


def share_point_file_table_row(share_point_file: MinimalSharePointFile) -> dict:
    modified_dt = datetime.fromtimestamp(share_point_file.modified)
    return {
        "name": share_point_file.name,
        "modified": modified_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "size": str(share_point_file.size),
        "id": share_point_file.id,
        "etag": share_point_file.etag or "",
        "content_type": share_point_file.content_type or "",
    }


def share_point_metadata_table(share_point_files: list[MinimalSharePointFile]):
    columns = [
        TableColumn("name", "string"),
        TableColumn("modified", "string"),
        TableColumn("size", "string"),
        TableColumn("id", "string"),
        TableColumn("etag", "string"),
        TableColumn("content_type", "string"),
    ]
    records = [TableRecord(share_point_file_table_row(share_point_file)) for share_point_file in share_point_files]
    table_schema = TableSchema(columns=columns)
    return MetadataValue.table(records=records, schema=table_schema)


def local_file_table_row(file: MinimalSourceFile) -> dict:
    """Convert MinimalSourceFile to table row dict."""
    modified_dt = datetime.fromtimestamp(file.modified)
    return {
        "name": file.name,
        "modified": modified_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "size": readable_size(file.size),
        "path": file.path,
    }


def local_file_metadata_table(files: list[MinimalSourceFile]) -> MetadataValue:
    """
    Create a Dagster metadata table from local file metadata.

    Displays file system files in a structured table format for monitoring and debugging.
    Limits display to first 100 files to avoid overwhelming the UI.
    """
    columns = [
        TableColumn("name", "string"),
        TableColumn("modified", "string"),
        TableColumn("size", "string"),
        TableColumn("path", "string"),
    ]

    sorted_files = sorted(files, key=lambda f: f.path)

    display_files = sorted_files[:100]

    records = [TableRecord(local_file_table_row(file)) for file in display_files]

    if len(sorted_files) > 100:
        records.append(
            TableRecord(
                {
                    "name": f"({len(sorted_files) - 100} more files)",
                    "modified": "...",
                    "size": "...",
                    "path": "...",
                }
            )
        )

    table_schema = TableSchema(columns=columns)
    return MetadataValue.table(records=records, schema=table_schema)


def rclone_file_table_row(file: MinimalRcloneFile) -> dict:
    """Convert MinimalRcloneFile to table row dict."""
    modified_dt = datetime.fromtimestamp(file.modified) if file.modified else None
    return {
        "remote": file.remote,
        "name": file.name,
        "modified": modified_dt.strftime("%Y-%m-%d %H:%M:%S") if modified_dt else "N/A",
        "size": readable_size(file.size),
        "path": file.path,
        "mime_type": file.mime_type or "",
    }


def rclone_file_metadata_table(files: list[MinimalRcloneFile]) -> MetadataValue:
    """
    Create a Dagster metadata table from rclone file metadata.

    Displays files from rclone remotes (OneDrive, SharePoint, S3, etc.) in a structured
    table format for monitoring and debugging.
    Limits display to first 100 files to avoid overwhelming the UI.
    """
    columns = [
        TableColumn("remote", "string"),
        TableColumn("name", "string"),
        TableColumn("modified", "string"),
        TableColumn("size", "string"),
        TableColumn("path", "string"),
        TableColumn("mime_type", "string"),
    ]

    sorted_files = sorted(files, key=lambda f: f.path)

    display_files = sorted_files[:100]

    records = [TableRecord(rclone_file_table_row(file)) for file in display_files]

    if len(sorted_files) > 100:
        records.append(
            TableRecord(
                {
                    "remote": "...",
                    "name": f"({len(sorted_files) - 100} more files)",
                    "modified": "...",
                    "size": "...",
                    "path": "...",
                    "mime_type": "...",
                }
            )
        )

    table_schema = TableSchema(columns=columns)
    return MetadataValue.table(records=records, schema=table_schema)
