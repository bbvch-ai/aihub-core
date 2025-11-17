---
title: RAG ingestion pipeline
---

# RAG ingestion pipeline

The RAG (Retrieval-Augmented Generation) pipeline is the default pipeline for document ingestion. It transforms
documents from file storage into searchable knowledge bases that agents can query. All documents you want agents to
access must go through this pipeline.

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
