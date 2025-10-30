---
title: RAG ingestion pipeline
index: 2
---

# RAG ingestion pipeline

The RAG (Retrieval-Augmented Generation) pipeline is how documents become searchable knowledge bases that agents can
query. This is the pipeline you use for all agent document ingestion.

The pipeline does more than extract text. It preserves document structure and creates relationships between chunks,
enabling agents to understand context and navigate complex documents.

## What makes RAG pipelines different

Consider a policy document where Section 5 refers to "the approval process described in Section 3." A simple text search
might find Section 5 but miss the critical details in Section 3.

The RAG pipeline creates a knowledge graph where every chunk knows its position in the document and its relationship to
other chunks. Agents can follow these connections to find referenced content and reconstruct complete context.

## How the pipeline builds structure

The RAG pipeline processes documents through parsing, chunking, and embedding. What sets it apart is relationship
mapping:

**Sequential links** connect consecutive chunks bidirectionally. Each chunk references its predecessor and successor.
When an agent finds a relevant chunk, it can follow these links forward or backward to reconstruct complete passages.

**Hierarchical links** capture document sections and subsections. The pipeline generates summaries at each level of the
document hierarchy. A chunk from subsection 3.2.4 links to its parent summary (3.2), which links to the top-level
section summary (Section 3).

The vector database stores these relationship links alongside the embedded chunks, creating a searchable knowledge graph
rather than a simple text index.

## Agent capabilities enabled

This structure enables agents to:

**Resolve cross-references** - References like "see above" or "described in Section 3" become actionable. The agent
follows links to find the referenced content.

**Provide context** - When returning a specific detail, agents can traverse parent links to explain where that detail
fits in the broader document structure.

**Reconstruct passages** - Sequential links let agents fetch surrounding chunks to provide complete context, even when
the initial search returns only a fragment.

## Document types that benefit most

While the RAG pipeline handles all document types, its structural features are particularly valuable for:

- Technical documentation with numbered sections and internal references
- Legal contracts with defined terms and clause references
- Policy handbooks that reference other sections for procedures
- Standards documents with hierarchical requirement structures
- Long reports where understanding context requires knowing section relationships

Even simple documents like announcements or blog posts benefit from the pipeline's semantic search capabilities, though
they may not use all the structural features.
