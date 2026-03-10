---
title: Knowledge management
---

# Knowledge management

AI agents need access to relevant information to answer questions accurately. The knowledge management system processes
your documents and makes them searchable through semantic retrieval.

## Structure

Knowledge organizes into three levels:

Knowledge databases are isolated containers at the top level. Each database has its own data, permissions, and
processing pipeline. Organizations typically create databases per department, project, or security classification.

Namespaces (called "collections" in the UI) group related documents within a database. They function like folders
organized by topic or purpose. A product database might contain "technical," "guides," and "troubleshooting"
collections.

Documents are the actual files - PDFs, Word documents, PowerPoint presentations. The system processes them automatically
after upload.

::: info Multilingual support
Database names, namespace labels, and folder descriptions support German, English, French, and Italian. The interface
displays labels according to user language preference.
:::

## Managing content

### Manual management

By default, databases allow manual control:

1. Create collections through the web interface
2. Upload documents to specific collections
3. Wait for the next scheduled pipeline run

![Empty knowledge database](../../../media/knowledge/empty_knowledge_base.png)

You control what gets uploaded and where it lives. The pipeline runs on a schedule (commonly configured for nightly
processing) to handle document processing and indexing.

### Auto-sync from external sources

Mark a database as auto-sync to connect it to external content sources like SharePoint. The system then:

- Syncs files from the external source on a schedule (typically nightly)
- Creates collections automatically from folder structure
- Processes new content during the scheduled pipeline run
- Disables manual uploads through the UI

The external system becomes the source of truth. Your team continues working in SharePoint, and the sync pipeline brings
changes into the Swiss AI Hub on the configured schedule.

## Document processing

The system processes each uploaded document through several stages:

Parsing: MinerU extracts text, tables, figures, and structure from PDFs and Office documents. It handles complex
layouts, multi-column pages, and embedded content while preserving logical structure.

Chunking: Large documents split into smaller pieces that maintain context. A 50-page manual becomes hundreds of chunks,
each preserving its relationship to surrounding content.

Metadata extraction: The system captures creation dates, authors, source information, and detected language. Agents can
filter results using this metadata.

Vector embedding: Text chunks convert to vector representations that capture semantic meaning. Agents find relevant
content based on concepts, not just keyword matching. A query about "vehicle speed limits" matches content about
"maximum velocity constraints."

## Inspection and debugging

The system provides visibility into document processing:

Document reconstruction shows how the parser interpreted your document. Check whether it correctly identified tables,
sidebars, and other structural elements.

Chunk inspection displays how the system segmented content, what metadata it extracted, and how it represents chunks for
retrieval. Useful when agents aren't finding expected content.

Processing status indicates whether documents are uploading, processing, or ready.

## Access control

The permission system controls all knowledge operations:

- Viewing databases requires appropriate permissions
- Accessing namespaces checks user authorization
- Uploading documents validates user rights
- Inspecting processing details requires permission

Knowledge databases provide natural isolation boundaries. Organizations can create separate databases per department or
project, then use permissions to control who accesses each database.

## Agent integration

Agents connect to specific collections rather than entire databases. When configuring an agent, you specify which
collections it can search. A customer support agent might access "products" and "faq" but not "engineering."

Collection-scoped retrieval keeps agents focused on relevant content, improving both speed and accuracy.

Documents become available to agents after the pipeline processes them. The system tracks which source documents agents
used, enabling citation and verification of responses.

## Technical implementation

The architecture uses:

- FerretDB for document metadata and processing status
- Milvus for vector storage and semantic search
- MinerU for document parsing and structure extraction
- SeaweedFS for S3-compatible file storage
- LlamaIndex for chunking and embedding orchestration

Processing metadata lives in FerretDB, vector embeddings in Milvus, raw files in SeaweedFS. This separation optimizes
each component for its specific task.

## Limitations

No mixed modes: A database is either manually managed or auto-synced, not both. This prevents ambiguity about content
sources.

No manual chunk editing: The system generates chunks automatically from source documents. To fix incorrect chunks,
update the source document and reprocess.

No database merging: Databases remain isolated by design. Reorganization requires creating new structures and migrating
documents.
