---
title: Document Reconstruction for Context
index: 2
---

# Document Reconstruction for Context

Vector similarity search operates at the granularity of text chunks—typically 500-1000 tokens—enabling precise
identification of relevant information within large documents. However, providing only these isolated chunks to language
models creates significant comprehension challenges. A chunk discussing "the requirement specified in Section 3.2" lacks
meaning without Section 3.2's content. A chunk referencing "this architecture" requires understanding what architecture
the document discusses.

The Swiss AI-Hub addresses this challenge through sophisticated document reconstruction mechanisms that restore
meaningful context around retrieved chunks, ensuring agents receive sufficient information to generate accurate,
well-grounded responses.

## The Context Challenge

Traditional RAG implementations face a fundamental tradeoff between retrieval precision and context completeness.
Retrieving small chunks enables precise relevance matching but sacrifices context. Retrieving large chunks or entire
documents ensures sufficient context but dilutes relevance signals and exceeds language model context limits.

The platform resolves this tradeoff through post-retrieval reconstruction. Initial retrieval operates on optimally-sized
chunks for relevance matching. After identifying relevant chunks, reconstruction mechanisms intelligently expand the
context by retrieving related content using explicit relationships preserved during document ingestion.

## Previous-Next Node Traversal

Documents undergo chunking during ingestion with explicit relationships preserved between sequential chunks. Each chunk
maintains references to its predecessor and successor, forming a bidirectional linked list representing the document's
original structure.

When retrieval identifies a relevant chunk, the reconstruction mechanism traverses these relationships to fetch
surrounding chunks—typically 2-3 chunks before and after the retrieved segment. This traversal reconstructs a coherent
passage providing sufficient context for comprehension.

The traversal mechanism includes intelligent boundaries ensuring reconstructed context remains coherent and
document-scoped. When reaching the document's beginning or end, traversal terminates, preventing inappropriate inclusion
of content from adjacent but unrelated documents.

Organizations configure expansion depth based on document characteristics and context requirements. The configuration
enables symmetric expansion (equal retrieval before and after), asymmetric expansion (different retrieval in each
direction), or directional expansion when context flows primarily in one direction.

## Hierarchical Summary Retrieval

Complex documents employ hierarchical structure—sections, subsections, and nested content. The platform captures this
structure during ingestion by generating summaries at each hierarchical level and linking content chunks to parent
summaries through explicit relationships.

When retrieval identifies a content chunk, the reconstruction mechanism traverses parent relationships to retrieve
hierarchical summaries. A chunk from subsection 3.2.4 can retrieve summaries for the subsection itself, parent section
3.2, and top-level section 3, providing progressively broader context that enables the agent to understand where
retrieved information fits within the document's overall narrative.

Organizations configure traversal depth (typically 1-3 levels) based on document complexity and context requirements.
Each additional level adds another summary to the context, consuming tokens that might otherwise be available for
retrieved content or response generation.

## Context Sufficiency and Multi-Hop Retrieval

Even sophisticated reconstruction cannot guarantee initial retrieval provides all necessary information for complex
queries. The platform includes mechanisms to assess context sufficiency and perform iterative refinement when needed.

After initial retrieval and reconstruction, a guard mechanism evaluates whether the agent possesses adequate information
to generate a comprehensive response. The guard assesses topical coverage, completeness, and coherence. When context
proves insufficient, the multi-hop mechanism activates.

The multi-hop retrieval mechanism automatically generates refined queries targeting missing information identified
during sufficiency assessment. For example, if initial retrieval provides installation procedures but the user asked
about installation and configuration, the guard identifies the configuration gap and generates a refined query
specifically targeting configuration information.

This iterative process continues until sufficient context accumulates or a configured maximum hop count is reached
(typically 2-5 hops). Hop limits prevent infinite retrieval loops, ensuring timely responses even when information gaps
exist.

Multi-hop retrieval proves particularly valuable for cross-reference questions requiring information from multiple
document sections, comparative questions, sequential processes documented in separate sections, and following causal
chains across document boundaries.
