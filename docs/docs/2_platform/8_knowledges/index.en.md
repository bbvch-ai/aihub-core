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

## Creating a knowledge database

You create knowledge databases yourself from the admin UI — no deployment, configuration change, or restart is involved,
and a new database starts accepting documents immediately.

When you create one you choose:

- **The ingestion pipeline** that will process its documents. Most deployments offer one, the Generic Document Ingestion
  Pipeline; a deployment that ships its own pipeline offers that here too.
- **A text-generation model**, used for the enrichment steps — summaries, table refinement, figure descriptions.
- **An embedding model**, which turns text into the vectors agents search.

Leave the models unset to use the deployment's defaults. Because a database's vectors are only comparable to other
vectors produced by the same embedding model, the models are fixed once the database exists — to change them, create a
new database and re-upload.

Whoever creates a database is granted administrative access to it automatically, so you can use what you just made
without asking an administrator for a second step.

## Managing content

### Manual management

By default, databases allow manual control:

1. Create collections through the web interface
2. Upload documents to specific collections
3. Watch them process

![Empty knowledge database](../../../media/knowledge/empty_knowledge_base.png)

You control what gets uploaded and where it lives. Uploading a document notifies the pipeline directly, so processing
normally begins within a minute or two rather than waiting for a scheduled run. A daily run still sweeps every database
as a safety net, catching anything a missed notification would otherwise have left behind.

### Syncing from an external source

Instead of uploading, a database can be given a **Source** when it is created, or later through **Edit source** on the
database. Pick the storage system (SharePoint or OneDrive, Google Drive, S3, Azure Blob, SFTP), enter its credentials,
the folder to sync and optional include/exclude patterns. Credentials are stored encrypted and shown masked afterwards;
re-saving the dialog without retyping them keeps the stored ones, so a rotation is a matter of editing the source. The
system then:

- Syncs files from the source on a daily schedule
- Creates collections automatically from the top-level folders of the synced root (files directly in the root are
  skipped and counted in the run)
- Processes each synced file within a minute or two, like an upload
- Disables manual uploads, hand-made collections and manual document deletion for that database

The external system becomes the source of truth. Your team continues working there, and the next sync brings changes,
including deletions, into the Swiss AI Hub. Giving a database that already holds uploaded documents a source asks for
confirmation first, because the first sync removes everything the source does not have. Clearing the source turns the
database back into a manually managed one; its files stay until you delete them.

### Deleting databases and collections

You can remove a whole knowledge database or an individual collection from the web interface. Both actions are
permanent.

- **Delete a collection** removes that collection's documents from storage and the vector index; the database and its
  other collections stay.
- **Delete a database** removes the database entirely — every collection, all its documents, its vector collection, and
  its file storage.

To prevent accidents, the confirmation dialog shows how many documents will be removed and requires you to type the
exact database or collection name before the delete button becomes active.

Deletion runs in the background. The moment you confirm, the item disappears from the list and stops accepting new
uploads, while the platform frees the underlying storage shortly afterwards. If you later re-upload a document that was
deleted, it is ingested again normally.

A database with a source can be deleted as a whole, which also stops its sync and forgets its credentials. Its
individual documents and collections cannot be deleted by hand, because the next sync would bring them back; remove them
at the source instead.

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

Processing status indicates whether documents are uploading, processing, or ready. A document counts as ready only once
its embeddings have been written to the vector database — until then it is still processing and agents cannot retrieve
it, even though its text has already been parsed.

## Access control

Knowledge permissions follow the same two-level hierarchy as agent classes and agent instances: the database is the
parent, its collections (namespaces) are the children, and a rule on one level never implies its neighbours.

| Rule                                  | Grants                                                                                      |
| ------------------------------------- | ------------------------------------------------------------------------------------------- |
| `aihub.admin.knowledge`               | Create new knowledge databases and list the pipelines they can be assigned                  |
| `aihub.admin.knowledge.<db>`          | See the database, create collections inside it, delete the whole database                   |
| `aihub.admin.knowledge.<db>.<ns>`     | Upload, edit, and delete documents in that collection; rename or delete the collection      |
| `aihub.user.knowledge.<db>`           | See that the database exists, its name and configured pipeline, but none of its collections |
| `aihub.user.knowledge.<db>.<ns>`      | Browse and search one collection                                                            |
| `aihub.user.knowledge.<db>.*` or `.>` | Browse every collection of one database                                                     |
| `aihub.user.knowledge.>`              | Browse every database and every collection                                                  |

The seeded `AIHubKnowledgeUser` and `AIHubKnowledgeAdmin` roles bundle the last row and the first two rows respectively,
and the role editor offers the same three rules as presets. Admin rules imply the matching user rule.
`aihub.admin.knowledge.>` covers every existing database and collection but not the bare `aihub.admin.knowledge` root,
so a role that should create databases needs the root rule explicitly.

Creating a resource grants access to it automatically, mirroring agent instances: the creator receives a per-resource
admin role (`Knowledge<Db>Admin` or `Knowledge<Db><Ns>Admin`) and the tenant ceiling is raised to include the new rule
unless a broader rule already covers it. Deleting a database or collection revokes those rules and roles again.

## Agent integration

An agent's knowledge scope is always explicit: it either names the collections to search or opts into every collection
of a database with the "Search all namespaces" switch. Leaving the selection empty is rejected when the configuration is
saved rather than silently widened to the whole database. Agents configured before this rule existed, with an empty
selection and no switch, fail validation until an administrator re-saves them with an explicit scope; the agent's error
message names the retriever field to fix.

Saving an agent configuration also checks that scope against the saving user's rules: each named collection needs
`aihub.user.knowledge.<db>.<ns>` (or a rule covering it), and opting into all collections needs a rule covering every
one of them (`...<db>.*`, `...<db>.>` or broader).

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

No mixed modes: A database is either manually managed or synced from one source, not both. This prevents ambiguity about
who owns its content.

No manual chunk editing: The system generates chunks automatically from source documents. To fix incorrect chunks,
update the source document and reprocess.

No database merging: Databases remain isolated by design. Reorganization requires creating new structures and migrating
documents.
