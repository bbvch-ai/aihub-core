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

### Sequential Context Expansion

When retrieval identifies a relevant chunk, the reconstruction mechanism traverses these relationships to fetch
surrounding chunks—typically 2-3 chunks before and after the retrieved segment. This traversal reconstructs a coherent
passage providing sufficient context for comprehension.

Consider a technical specification where retrieval identifies a chunk describing API authentication requirements. The
reconstruction mechanism retrieves:

- **Preceding chunks**: The API overview, connection establishment procedures, and general security considerations that
  frame the authentication requirements
- **Retrieved chunk**: The specific authentication mechanism details
- **Succeeding chunks**: Token refresh procedures, error handling for authentication failures, and example
  authentication flows

This reconstructed passage provides complete, comprehensible context rather than an isolated authentication fragment.

### Intelligent Boundary Handling

The traversal mechanism includes intelligent boundaries ensuring reconstructed context remains coherent and
document-scoped. When reaching the document's beginning (index 0), backward traversal terminates, preventing retrieval
of irrelevant preceding documents. Similarly, forward traversal stops at document end.

This boundary awareness proves essential for multi-document knowledge bases. Without boundary handling, reconstruction
might inappropriately include content from adjacent but unrelated documents that happened to be ingested sequentially.
Boundary handling ensures each reconstructed context represents a coherent excerpt from a single document.

### Configurable Expansion Depth

Organizations configure the expansion depth—the number of preceding and succeeding chunks retrieved—based on their
document characteristics and context requirements. Technical documentation with tightly coupled sections might require
3-chunk expansion, while independent policy statements might need only 1-chunk expansion.

The configuration enables different expansion strategies:

- **Symmetric Expansion**: Equal retrieval before and after (e.g., 2 previous + 2 next)
- **Asymmetric Expansion**: Different retrieval in each direction (e.g., 3 previous + 1 next) when context flows
  primarily in one direction
- **Forward-Only or Backward-Only**: Expansion in a single direction when directional context proves more valuable

## Hierarchical Summary Retrieval

Complex documents employ hierarchical structure—sections, subsections, and nested content—to organize information. The
platform captures this structure during ingestion by generating summaries at each hierarchical level and linking content
chunks to their parent summaries through explicit hierarchical relationships.

### Multi-Level Context

When retrieval identifies a content chunk, the reconstruction mechanism traverses these parent relationships to retrieve
hierarchical summaries. A chunk from subsection 3.2.4 can retrieve:

- **Level 1**: The summary for subsection 3.2.4 itself
- **Level 2**: The summary for parent section 3.2
- **Level 3**: The summary for top-level section 3
- **Level 4**: The document-level executive summary (if configured for deep traversal)

These summaries provide progressively broader context, enabling the agent to understand where retrieved information fits
within the document's overall narrative.

### Progressive Contextualization

Hierarchical summaries enable progressive contextualization—starting from specific retrieved content and broadening to
encompass larger organizational structures. This progression mirrors how humans understand documents: understanding
specific details in the context of their section, understanding sections in the context of their chapters, and
understanding chapters in the context of the entire document.

Consider a legal contract where retrieval identifies a specific termination clause. Hierarchical summary retrieval
provides:

- **Immediate parent summary**: Overview of the termination section, including notice requirements, conditions, and
  procedures
- **Document parent summary**: The contract's overall structure, parties involved, and key terms
- **Contract type summary**: Standard provisions for this contract type and how this specific contract instantiates them

This layered context enables the agent to interpret the specific termination clause accurately within the contract's
full legal framework.

### Configurable Traversal Depth

Organizations configure the traversal depth (typically 1-3 levels) based on their document complexity and context
requirements. Deeply nested technical specifications might benefit from 3-level traversal, while flatter organizational
policies might require only 1-2 levels.

Traversal depth significantly impacts context window consumption. Each additional level adds another summary to the
context, consuming tokens that might otherwise be available for retrieved content or response generation. Organizations
balance comprehensive context against context window constraints based on their specific needs.

## Context Sufficiency and Multi-Hop Retrieval

Even sophisticated reconstruction mechanisms cannot guarantee that initial retrieval provides all information necessary
to answer complex queries. The platform includes mechanisms to assess context sufficiency and perform iterative
refinement when initial retrieval proves inadequate.

### Context Sufficiency Assessment

After initial retrieval and reconstruction, a guard mechanism evaluates context sufficiency—determining whether the
agent possesses adequate information to generate a comprehensive response. This assessment uses the language model
itself to evaluate whether the retrieved context enables answering the user query completely and accurately.

The guard mechanism considers several factors:

- **Topical Coverage**: Does the context address all aspects of the user query?
- **Completeness**: Are there obvious gaps or missing information preventing full response generation?
- **Coherence**: Is the assembled context internally consistent and comprehensible?

When context proves sufficient, the workflow proceeds to response generation. When context proves insufficient, the
multi-hop mechanism activates.

### Iterative Query Refinement

The multi-hop retrieval mechanism automatically generates refined queries targeting missing information identified
during sufficiency assessment. These refined queries specifically target gaps in the initial retrieval, using language
model reasoning to formulate questions that will retrieve the missing context.

For example, if initial retrieval provides installation procedures but the user asked about both installation and
configuration, the guard mechanism identifies the configuration gap and generates a refined query specifically targeting
configuration information. The second retrieval operation fetches configuration content, which combines with the
installation content to provide comprehensive context.

### Hop Limits and Termination

This iterative process continues until sufficient context accumulates or a configured maximum hop count is reached. Hop
limits prevent infinite retrieval loops when queries cannot be satisfactorily answered from available knowledge,
ensuring timely responses even when information gaps exist.

Typical hop limits range from 2-5, balancing thoroughness against response latency. Higher hop counts enable more
comprehensive context accumulation for complex queries but increase both latency and computational costs.

### Multi-Hop Use Cases

Multi-hop retrieval proves particularly valuable for:

- **Cross-Reference Questions**: Queries requiring information from multiple document sections or sources
- **Comparative Questions**: Questions asking to compare or contrast different approaches, products, or specifications
- **Sequential Processes**: Understanding multi-step procedures where steps are documented in separate sections
- **Causal Chains**: Following chains of reasoning or causation across document boundaries

---

## Questions Requiring Clarification

The following aspects require clarification to ensure documentation accuracy:

01. **Chunk Size Optimization**: What are the specific chunk size configurations (min, max, overlap)? How do
    organizations optimize chunk size for different document types?

02. **Relationship Preservation**: How exactly are prev/next and parent/child relationships stored in the vector store?
    What metadata fields encode these relationships?

03. **Summary Generation**: How are hierarchical summaries generated during ingestion? Are they AI-generated or
    extracted from existing document structure? What controls summary quality?

04. **Reconstruction Performance**: What are the performance implications of reconstruction (latency, cost)? How does
    reconstruction scale with expansion depth and traversal levels?

05. **Context Window Management**: How does the system manage total context window consumption when combining retrieval,
    reconstruction, chat history, and system prompts?

06. **Guard Mechanism Details**: What specific criteria and thresholds does the context sufficiency guard use? Can
    organizations tune guard sensitivity?

07. **Refined Query Generation**: How does the system generate refined queries for multi-hop retrieval? What prompts or
    mechanisms guide this generation?

08. **Hop Performance**: What are typical performance characteristics for multi-hop retrieval? How much additional
    latency does each hop introduce?

09. **Reconstruction Deduplication**: How does the system handle duplicate content when reconstruction fetches chunks
    that overlap with initial retrieval results?

10. **Fallback Strategies**: What happens when reconstruction cannot retrieve expected related nodes (broken
    relationships, missing chunks)? How does the system degrade gracefully?
