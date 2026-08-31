---
title: Document ingestion pipeline
---

# Generic Document Ingestion Pipeline

The Generic Document Ingestion Pipeline is the platform's default pipeline for document ingestion. It transforms
documents from file storage into searchable knowledge bases that agents can query. All documents you want agents to
access must go through an ingestion pipeline.

The name is literal: this pipeline parses, chunks, embeds and indexes documents. It performs no retrieval and no
generation — that is the RAG agent's job, which queries what this pipeline produces.

## One pipeline, every knowledge database

A single deployment of this pipeline serves **every** knowledge database assigned to it, working out which database a
run belongs to as it goes. Creating a knowledge database therefore needs no new deployment, no configuration change, and
no restart — a database created in the admin UI is picked up automatically, and a document uploaded into it is normally
observed within about half a minute.

Each database keeps its own isolation: its own vector collection, its own document store, and its own file storage.
Sharing a pipeline shares the processing recipe, never the data.

A deployment can also run **its own** ingestion pipeline alongside this one — tuned differently, or built on entirely
different processing steps — and have it offered in the create-database dialog next to the platform's. See
[Building pipelines](../../../3_sdk/3_building_pipelines/) in the SDK documentation.

## Choosing models per database

Each knowledge database records the models it is ingested with, chosen when the database is created:

- an **embedding model**, which turns text chunks into the vectors agents search
- a **text-generation model**, used for the enrichment steps (summaries, table refinement, figure descriptions)

Databases that name no models use the deployment's defaults. Because a database's vectors are only comparable to other
vectors from the same embedding model, the choice is fixed for the database's lifetime — to change it, create a new
database and re-upload. The vector width follows automatically from the embedding model, so the two can never disagree.

## Processing stages

The pipeline processes documents through five stages:

1. Document parsing extracts text content and structure from PDFs, Word documents, PowerPoint presentations, and other
   formats. The parser identifies headings, paragraphs, lists, and tables while preserving the document's organization.

2. Chunking splits large documents into smaller text chunks. The pipeline uses a structural parser that breaks text at
   heading boundaries and paragraph breaks rather than at arbitrary character counts, ensuring each chunk contains
   coherent information.

3. Embedding generation converts each text chunk into a vector embedding using an AI model. These embeddings capture
   semantic meaning, enabling agents to find relevant information based on concepts rather than keyword matching.

4. Structural linking creates two types of connections between chunks:

   - Sequential links connect each chunk to the chunks before and after it in document order. When an agent finds a
     relevant chunk, it can retrieve surrounding chunks for complete context.
   - Hierarchical links connect chunks to section summaries based on heading levels. If a chunk comes from subsection
     3.2.4 (heading level 4), it links to a summary of section 3.2 (heading level 3), which links to a summary of
     section 3 (heading level 2).

5. Summary generation creates hierarchical summaries for document sections. These summaries help agents understand
   broader context when they retrieve specific details from nested sections.

## Storage and retrieval

After processing, the pipeline stores:

- Vector embeddings in the vector database for semantic search
- Original text chunks with metadata
- Sequential and hierarchical links between chunks
- Section summaries at each heading level

This creates a knowledge graph rather than disconnected text fragments. When an agent searches for information, it
retrieves relevant chunks and can navigate through sequential and hierarchical links to build complete context.

## Document lifecycle

The pipeline handles the complete document lifecycle:

When a document is added, the pipeline processes it through all five stages and stores the results in the knowledge
base.

When a document is modified, the pipeline removes all data from the old version before reprocessing the new version.

When a document is deleted, the pipeline removes all associated chunks, embeddings, links, and summaries from the
knowledge base.

This ensures agents never retrieve information from outdated or deleted documents.

## Document organization benefits

Structural linking provides the most value for documents with clear organization: technical manuals with sections and
subsections, legal documents with numbered articles, policy documents with hierarchical procedures, and long reports
where context spans multiple sections.

Documents without complex structure (announcements, emails, short articles) still benefit from semantic search and
sequential linking.
